"""Unit tests for the AutoPlane Design Agent.

Tests cover:
- Data models
- Tools (generate_geometry, run_cfd_surrogate, etc.)
- Agent nodes
"""

import pytest
from pydantic import ValidationError

from autoplane.models.state import (
    DesignState,
    DesignJob,
    MaterialProps,
    EngineProps,
    AeroResult,
    StructResult,
    PerfResult,
    CostResult,
    RegResult,
    CADFile,
    GeometryJSON,
)
from autoplane.tools import (
    generate_geometry,
    run_cfd_surrogate,
    run_fea_surrogate,
    compute_performance,
    estimate_cost,
    check_regulations,
    export_cad,
    generate_report,
    reoptimize_design,
    get_tools,
)


class TestDataModels:
    """Tests for Pydantic data models."""

    def test_design_state_defaults(self):
        """Test DesignState default values."""
        state = DesignState(payload_kg=1000)
        assert state.payload_kg == 1000
        assert state.status == "pending"
        assert state.iteration == 0
        assert state.needs_reopt is False
        assert state.last_error is None

    def test_design_state_with_values(self):
        """Test DesignState with all values."""
        state = DesignState(
            payload_kg=1200,
            material="Al-6061",
            engine="Turbofan-1",
            job_id="test-job-123",
        )
        assert state.payload_kg == 1200
        assert state.material == "Al-6061"
        assert state.engine == "Turbofan-1"
        assert state.job_id == "test-job-123"

    def test_design_job_validation(self):
        """Test DesignJob validation."""
        job = DesignJob(payload_kg=1000)
        assert job.payload_kg == 1000
        assert job.material is None
        assert job.engine is None

    def test_design_job_with_optionals(self):
        """Test DesignJob with optional fields."""
        job = DesignJob(
            payload_kg=1500,
            material="Carbon Fiber",
            engine="Turbofan-2",
            payload_cg=0.5,
        )
        assert job.material == "Carbon Fiber"
        assert job.engine == "Turbofan-2"
        assert job.payload_cg == 0.5

    def test_material_props(self):
        """Test MaterialProps model."""
        material = MaterialProps(
            name="Al-6061",
            density=2700.0,
            tensile_strength=310.0,
            cost_per_kg=5.0,
        )
        assert material.name == "Al-6061"
        assert material.density == 2700.0

    def test_engine_props(self):
        """Test EngineProps model."""
        engine = EngineProps(
            name="Turbofan-1",
            thrust=50.0,
            fuel_flow=500.0,
            weight=800.0,
            cost=50000.0,
        )
        assert engine.name == "Turbofan-1"
        assert engine.thrust == 50.0

    def test_aero_result(self):
        """Test AeroResult model."""
        aero = AeroResult(
            lift_coefficient=0.5,
            drag_coefficient=0.03,
            stall_speed_kts=55.0,
            max_lift=1.5,
        )
        assert aero.lift_coefficient == 0.5
        assert aero.stall_speed_kts == 55.0

    def test_struct_result(self):
        """Test StructResult model."""
        struct = StructResult(
            max_bending_moment=100.0,
            max_stress=250.0,
            weight_kg=1500.0,
            fatigue_life_years=20.0,
        )
        assert struct.max_bending_moment == 100.0
        assert struct.weight_kg == 1500.0

    def test_perf_result(self):
        """Test PerfResult model."""
        perf = PerfResult(
            range_km=3000.0,
            cruise_speed_kts=250.0,
            fuel_burn_kg=800.0,
            endurance_hr=8.0,
        )
        assert perf.range_km == 3000.0
        assert perf.endurance_hr == 8.0

    def test_cost_result(self):
        """Test CostResult model."""
        cost = CostResult(
            material_cost=50000.0,
            manufacturing_cost=150000.0,
            assembly_cost=75000.0,
            total_cost=275000.0,
        )
        assert cost.total_cost == 275000.0

    def test_reg_result(self):
        """Test RegResult model."""
        reg = RegResult(
            stall_speed_ok=True,
            noise_limit_ok=True,
            max_takeoff_weight_ok=False,
            violations=["Max takeoff weight exceeded"],
        )
        assert reg.stall_speed_ok is True
        assert len(reg.violations) == 1

    def test_cad_file(self):
        """Test CADFile model."""
        cad = CADFile(
            format="STEP",
            url="s3://bucket/file.step",
            size_bytes=1000000,
        )
        assert cad.format == "STEP"
        assert cad.size_bytes == 1000000

    def test_geometry_json(self):
        """Test GeometryJSON model."""
        geo = GeometryJSON(
            wing_span=15.0,
            wing_area=30.0,
            fuselage_length=12.0,
            tail_area=5.0,
            aspect_ratio=7.5,
            mean_aerodynamic_chord=2.0,
        )
        assert geo.wing_span == 15.0
        assert geo.aspect_ratio == 7.5


class TestTools:
    """Tests for design tools."""

    def test_generate_geometry_basic(self):
        """Test geometry generation with basic payload."""
        geometry = generate_geometry(
            payload=1000,
            material="Al-6061",
            engine="Turbofan-1",
        )
        
        assert "wing_span" in geometry
        assert "wing_area" in geometry
        assert "fuselage_length" in geometry
        assert "tail_area" in geometry
        assert "aspect_ratio" in geometry
        assert geometry["metadata"]["payload"] == 1000
        assert geometry["metadata"]["material"] == "Al-6061"

    def test_generate_geometry_scaling(self):
        """Test that geometry scales with payload."""
        small = generate_geometry(500, "Al-6061", "Turbofan-1")
        large = generate_geometry(4000, "Al-6061", "Turbofan-1")
        
        assert small["wing_span"] < large["wing_span"]
        assert small["wing_area"] < large["wing_area"]

    def test_run_cfd_surrogate(self):
        """Test CFD surrogate."""
        geometry = generate_geometry(1000, "Al-6061", "Turbofan-1")
        aero = run_cfd_surrogate(geometry)
        
        assert "lift_coefficient" in aero
        assert "drag_coefficient" in aero
        assert "stall_speed_kts" in aero
        assert "max_lift" in aero
        assert 0 < aero["lift_coefficient"] < 2
        assert aero["drag_coefficient"] > 0
        assert aero["stall_speed_kts"] > 0

    def test_run_fea_surrogate(self):
        """Test FEA surrogate."""
        geometry = generate_geometry(1000, "Al-6061", "Turbofan-1")
        struct = run_fea_surrogate(geometry)
        
        assert "max_bending_moment" in struct
        assert "max_stress" in struct
        assert "weight_kg" in struct
        assert "fatigue_life_years" in struct
        assert struct["max_bending_moment"] > 0
        assert struct["weight_kg"] > 0

    def test_compute_performance(self):
        """Test performance computation."""
        aero = run_cfd_surrogate(generate_geometry(1000, "Al-6061", "Turbofan-1"))
        struct = run_fea_surrogate(generate_geometry(1000, "Al-6061", "Turbofan-1"))
        engine = EngineProps(
            name="Turbofan-1",
            thrust=50.0,
            fuel_flow=500.0,
            weight=800.0,
            cost=50000.0,
        ).model_dump()
        
        perf = compute_performance(aero, struct, engine)
        
        assert "range_km" in perf
        assert "cruise_speed_kts" in perf
        assert "fuel_burn_kg" in perf
        assert "endurance_hr" in perf
        assert perf["range_km"] > 0
        assert perf["cruise_speed_kts"] > 0

    def test_estimate_cost(self):
        """Test cost estimation."""
        geometry = generate_geometry(1000, "Al-6061", "Turbofan-1")
        cost = estimate_cost(geometry, "Al-6061", "Turbofan-1")
        
        assert "material_cost" in cost
        assert "manufacturing_cost" in cost
        assert "assembly_cost" in cost
        assert "total_cost" in cost
        assert cost["total_cost"] > 0
        # Total should be at least the sum of all components
        assert cost["total_cost"] >= cost["material_cost"] + cost["manufacturing_cost"] + cost["assembly_cost"]

    def test_estimate_cost_carbon_fiber(self):
        """Test cost estimation with expensive material."""
        geometry = generate_geometry(1000, "Carbon Fiber", "Turbofan-1")
        cost_carbon = estimate_cost(geometry, "Carbon Fiber", "Turbofan-1")
        cost_alum = estimate_cost(geometry, "Al-6061", "Turbofan-1")
        
        assert cost_carbon["material_cost"] > cost_alum["material_cost"]

    def test_check_regulations_pass(self):
        """Test regulatory check with passing design."""
        perf = PerfResult(
            range_km=3000,
            cruise_speed_kts=250,
            fuel_burn_kg=800,
            endurance_hr=8,
        ).model_dump()
        aero = AeroResult(
            lift_coefficient=0.5,
            drag_coefficient=0.03,
            stall_speed_kts=55,
            max_lift=1.5,
        ).model_dump()
        
        reg = check_regulations(perf, aero)
        
        assert "stall_speed_ok" in reg
        assert "noise_limit_ok" in reg
        assert "max_takeoff_weight_ok" in reg
        assert "violations" in reg

    def test_check_regulations_fail(self):
        """Test regulatory check with failing design."""
        perf = PerfResult(
            range_km=3000,
            cruise_speed_kts=250,
            fuel_burn_kg=800,
            endurance_hr=8,
        ).model_dump()
        aero = AeroResult(
            lift_coefficient=0.5,
            drag_coefficient=0.03,
            stall_speed_kts=70,  # Too high
            max_lift=1.5,
        ).model_dump()
        
        reg = check_regulations(perf, aero)
        
        assert reg["stall_speed_ok"] is False
        assert len(reg["violations"]) > 0

    def test_export_cad_step(self):
        """Test CAD export to STEP format."""
        geometry = generate_geometry(1000, "Al-6061", "Turbofan-1")
        cad = export_cad(geometry, "STEP")
        
        assert "format" in cad
        assert "url" in cad
        assert "size_bytes" in cad
        assert cad["format"] == "STEP"

    def test_export_cad_iges(self):
        """Test CAD export to IGES format."""
        geometry = generate_geometry(1000, "Al-6061", "Turbofan-1")
        cad = export_cad(geometry, "IGES")
        
        assert cad["format"] == "IGES"

    def test_export_cad_invalid_format(self):
        """Test CAD export with invalid format defaults to STEP."""
        geometry = generate_geometry(1000, "Al-6061", "Turbofan-1")
        cad = export_cad(geometry, "INVALID")
        
        assert cad["format"] == "STEP"

    def test_generate_report(self):
        """Test report generation."""
        state = DesignState(
            payload_kg=1000,
            job_id="test-job",
            status="completed",
            iteration=2,
        ).model_dump()
        
        report = generate_report(state)
        
        assert isinstance(report, bytes)
        assert b"test-job" in report

    def test_reoptimize_design(self):
        """Test design re-optimization."""
        geometry = generate_geometry(1000, "Al-6061", "Turbofan-1")
        state = {
            "geometry_json": geometry,
            "regulatory": {"stall_speed_ok": False},
            "performance": {"range_km": 800},
        }
        
        new_geometry = reoptimize_design(state)
        
        assert "wing_span" in new_geometry
        assert "wing_area" in new_geometry
        # Re-optimization should increase wing area for stall speed
        assert new_geometry["wing_area"] >= geometry["wing_area"]

    def test_get_tools(self):
        """Test that all tools are registered."""
        tools = get_tools()
        
        assert len(tools) == 9
        tool_names = [t.name for t in tools]
        assert "generate_geometry_tool" in tool_names
        assert "run_cfd_surrogate_tool" in tool_names
        assert "run_fea_surrogate_tool" in tool_names
        assert "compute_performance_tool" in tool_names
        assert "estimate_cost_tool" in tool_names
        assert "check_regulations_tool" in tool_names
        assert "export_cad_tool" in tool_names
        assert "generate_report_tool" in tool_names
        assert "reoptimize_design_tool" in tool_names


class TestNodes:
    """Tests for agent nodes."""

    def test_input_parser_basic(self):
        """Test input parser with valid input."""
        from autoplane.nodes import input_parser
        
        state = DesignState(payload_kg=1000)
        result = input_parser(state)
        
        assert result.status == "running"
        assert result.material == "Al-6061"  # Default
        assert result.engine == "Turbofan-1"  # Default
        assert result.job_id is not None

    def test_input_parser_invalid_payload(self):
        """Test input parser with invalid payload."""
        from autoplane.nodes import input_parser
        
        state = DesignState(payload_kg=-100)
        result = input_parser(state)
        
        assert result.status == "failed"
        assert result.last_error is not None

    def test_input_parser_exceeds_max(self):
        """Test input parser with payload exceeding maximum."""
        from autoplane.nodes import input_parser
        
        state = DesignState(payload_kg=100000)
        result = input_parser(state)
        
        assert result.status == "failed"
        assert "exceeds maximum" in result.last_error

    def test_material_selector_valid(self):
        """Test material selector with valid material."""
        from autoplane.nodes import material_selector
        
        state = DesignState(payload_kg=1000, material="Al-6061")
        result = material_selector(state)
        
        assert result.material_props is not None
        assert result.material_props.name == "Al-6061"
        assert result.material_props.density == 2700.0

    def test_material_selector_carbon_fiber(self):
        """Test material selector with carbon fiber."""
        from autoplane.nodes import material_selector
        
        state = DesignState(payload_kg=1000, material="Carbon Fiber")
        result = material_selector(state)
        
        assert result.material_props.name == "Carbon Fiber"
        assert result.material_props.cost_per_kg == 50.0

    def test_material_selector_invalid(self):
        """Test material selector with invalid material."""
        from autoplane.nodes import material_selector
        
        state = DesignState(payload_kg=1000, material="Invalid Material")
        result = material_selector(state)
        
        assert result.status == "failed"
        assert "Unknown material" in result.last_error

    def test_engine_selector_valid(self):
        """Test engine selector with valid engine."""
        from autoplane.nodes import engine_selector
        
        state = DesignState(payload_kg=1000, engine="Turbofan-1")
        result = engine_selector(state)
        
        assert result.engine_props is not None
        assert result.engine_props.name == "Turbofan-1"
        assert result.engine_props.thrust == 50.0

    def test_engine_selector_turbofan_2(self):
        """Test engine selector with Turbofan-2."""
        from autoplane.nodes import engine_selector
        
        state = DesignState(payload_kg=1000, engine="Turbofan-2")
        result = engine_selector(state)
        
        assert result.engine_props.name == "Turbofan-2"
        assert result.engine_props.thrust == 80.0

    def test_engine_selector_invalid(self):
        """Test engine selector with invalid engine."""
        from autoplane.nodes import engine_selector
        
        state = DesignState(payload_kg=1000, engine="Invalid Engine")
        result = engine_selector(state)
        
        assert result.status == "failed"
        assert "Unknown engine" in result.last_error

    def test_design_generator(self):
        """Test design generator node."""
        from autoplane.nodes import design_generator
        
        state = DesignState(
            payload_kg=1000,
            material="Al-6061",
            engine="Turbofan-1",
        )
        result = design_generator(state)
        
        assert result.geometry_json is not None
        assert result.wing_span is not None
        assert result.wing_area is not None
        assert result.fuselage_length is not None
        assert result.tail_area is not None

    def test_aerodynamic_evaluator(self):
        """Test aerodynamic evaluator node."""
        from autoplane.nodes import aerodynamic_evaluator
        
        geometry = GeometryJSON(
            wing_span=15.0,
            wing_area=30.0,
            fuselage_length=12.0,
            tail_area=5.0,
            aspect_ratio=7.5,
            mean_aerodynamic_chord=2.0,
        )
        state = DesignState(
            payload_kg=1000,
            geometry_json=geometry,
        )
        result = aerodynamic_evaluator(state)
        
        assert result.aerodynamic is not None
        assert result.aerodynamic.lift_coefficient > 0
        assert result.aerodynamic.drag_coefficient > 0

    def test_aerodynamic_evaluator_no_geometry(self):
        """Test aerodynamic evaluator without geometry."""
        from autoplane.nodes import aerodynamic_evaluator
        
        state = DesignState(payload_kg=1000)
        result = aerodynamic_evaluator(state)
        
        assert result.status == "failed"
        assert "No geometry" in result.last_error

    def test_structural_evaluator(self):
        """Test structural evaluator node."""
        from autoplane.nodes import structural_evaluator
        
        geometry = GeometryJSON(
            wing_span=15.0,
            wing_area=30.0,
            fuselage_length=12.0,
            tail_area=5.0,
            aspect_ratio=7.5,
            mean_aerodynamic_chord=2.0,
        )
        state = DesignState(
            payload_kg=1000,
            geometry_json=geometry,
        )
        result = structural_evaluator(state)
        
        assert result.structural is not None
        assert result.structural.weight_kg > 0

    def test_performance_estimator(self):
        """Test performance estimator node."""
        from autoplane.nodes import performance_estimator
        
        state = DesignState(
            payload_kg=1000,
            aerodynamic=AeroResult(
                lift_coefficient=0.5,
                drag_coefficient=0.03,
                stall_speed_kts=55,
                max_lift=1.5,
            ),
            structural=StructResult(
                max_bending_moment=100,
                max_stress=250,
                weight_kg=1500,
                fatigue_life_years=20,
            ),
            engine_props=EngineProps(
                name="Turbofan-1",
                thrust=50.0,
                fuel_flow=500.0,
                weight=800.0,
                cost=50000.0,
            ),
        )
        result = performance_estimator(state)
        
        assert result.performance is not None
        assert result.performance.range_km > 0
        assert result.performance.cruise_speed_kts > 0

    def test_cost_estimator_node(self):
        """Test cost estimator node."""
        from autoplane.nodes import cost_estimator
        
        geometry = GeometryJSON(
            wing_span=15.0,
            wing_area=30.0,
            fuselage_length=12.0,
            tail_area=5.0,
            aspect_ratio=7.5,
            mean_aerodynamic_chord=2.0,
        )
        state = DesignState(
            payload_kg=1000,
            geometry_json=geometry,
            material="Al-6061",
            engine="Turbofan-1",
        )
        result = cost_estimator(state)
        
        assert result.cost is not None
        assert result.cost.total_cost > 0

    def test_regulatory_checker_pass(self):
        """Test regulatory checker with passing design."""
        from autoplane.nodes import regulatory_checker
        
        state = DesignState(
            payload_kg=1000,
            performance=PerfResult(
                range_km=3000,
                cruise_speed_kts=250,
                fuel_burn_kg=800,
                endurance_hr=8,
            ),
            aerodynamic=AeroResult(
                lift_coefficient=0.5,
                drag_coefficient=0.03,
                stall_speed_kts=55,
                max_lift=1.5,
            ),
        )
        result = regulatory_checker(state)
        
        assert result.regulatory is not None
        assert result.needs_reopt is False

    def test_regulatory_checker_fail(self):
        """Test regulatory checker with failing design."""
        from autoplane.nodes import regulatory_checker
        
        state = DesignState(
            payload_kg=1000,
            performance=PerfResult(
                range_km=3000,
                cruise_speed_kts=250,
                fuel_burn_kg=800,
                endurance_hr=8,
            ),
            aerodynamic=AeroResult(
                lift_coefficient=0.5,
                drag_coefficient=0.03,
                stall_speed_kts=70,  # Too high
                max_lift=1.5,
            ),
        )
        result = regulatory_checker(state)
        
        assert result.regulatory.stall_speed_ok is False
        assert result.needs_reopt is True

    def test_cad_exporter(self):
        """Test CAD exporter node."""
        from autoplane.nodes import cad_exporter
        
        geometry = GeometryJSON(
            wing_span=15.0,
            wing_area=30.0,
            fuselage_length=12.0,
            tail_area=5.0,
            aspect_ratio=7.5,
            mean_aerodynamic_chord=2.0,
        )
        state = DesignState(
            payload_kg=1000,
            geometry_json=geometry,
        )
        result = cad_exporter(state)
        
        assert result.cad_file is not None
        assert result.cad_file.format == "STEP"

    def test_report_generator(self):
        """Test report generator node."""
        from autoplane.nodes import report_generator
        
        state = DesignState(
            payload_kg=1000,
            job_id="test-job",
            status="completed",
        )
        result = report_generator(state)
        
        assert result.report_pdf is not None
        assert len(result.report_pdf) > 0

    def test_feedback_loop_no_reopt(self):
        """Test feedback loop when re-optimization not needed."""
        from autoplane.nodes import feedback_loop
        
        state = DesignState(
            payload_kg=1000,
            needs_reopt=False,
            iteration=0,
        )
        result = feedback_loop(state)
        
        assert result.iteration == 0

    def test_feedback_loop_reopt(self):
        """Test feedback loop with re-optimization."""
        from autoplane.nodes import feedback_loop
        
        geometry = GeometryJSON(
            wing_span=15.0,
            wing_area=30.0,
            fuselage_length=12.0,
            tail_area=5.0,
            aspect_ratio=7.5,
            mean_aerodynamic_chord=2.0,
        )
        state = DesignState(
            payload_kg=1000,
            geometry_json=geometry,
            needs_reopt=True,
            iteration=0,
            max_iterations=5,
        )
        result = feedback_loop(state)
        
        assert result.iteration == 1
        assert result.needs_reopt is False

    def test_feedback_loop_max_iterations(self):
        """Test feedback loop at max iterations."""
        from autoplane.nodes import feedback_loop
        
        state = DesignState(
            payload_kg=1000,
            needs_reopt=True,
            iteration=5,
            max_iterations=5,
        )
        result = feedback_loop(state)
        
        assert result.needs_reopt is False
        assert "Max iterations" in result.last_error

    def test_should_reoptimize_true(self):
        """Test should_reoptimize returns 'reoptimize' when needed."""
        from autoplane.nodes import should_reoptimize
        
        state = DesignState(
            payload_kg=1000,
            needs_reopt=True,
            iteration=0,
            max_iterations=5,
        )
        result = should_reoptimize(state)
        
        assert result == "reoptimize"

    def test_should_reoptimize_false(self):
        """Test should_reoptimize returns 'complete' when not needed."""
        from autoplane.nodes import should_reoptimize
        
        state = DesignState(
            payload_kg=1000,
            needs_reopt=False,
            iteration=0,
        )
        result = should_reoptimize(state)
        
        assert result == "complete"

    def test_should_reoptimize_max_iterations(self):
        """Test should_reoptimize at max iterations."""
        from autoplane.nodes import should_reoptimize
        
        state = DesignState(
            payload_kg=1000,
            needs_reopt=True,
            iteration=5,
            max_iterations=5,
        )
        result = should_reoptimize(state)
        
        assert result == "complete"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])