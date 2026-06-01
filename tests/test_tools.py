"""Unit tests for tools."""

import pytest

from afw_d.tools import (
    MaterialDBQueryTool,
    EngineDBQueryTool,
    CADGeneratorTool,
    CFDSolverTool,
    FEASolverTool,
    CostEstimatorTool,
    ComplianceCheckerTool,
    OptimizationTool,
    VersionControlTool,
    ExportTool,
)
from afw_d.models import (
    DesignParams,
    MaterialProperties,
    EngineSpecs,
    DesignState,
    SimulationResult,
    CostEstimate,
    CFDSimulationResult,
    FEASimulationResult,
    ComplianceReport,
)


class TestMaterialDBQueryTool:
    """Tests for MaterialDBQueryTool."""

    def test_invoke_valid_material(self):
        """Test querying a valid material family."""
        tool = MaterialDBQueryTool()
        props = tool.invoke("Al-Mg-Si")

        assert isinstance(props, MaterialProperties)
        assert props.family == "Al-Mg-Si"
        assert props.density > 0
        assert props.modulus > 0

    def test_invoke_invalid_material(self):
        """Test querying an invalid material family."""
        tool = MaterialDBQueryTool()

        with pytest.raises(ValueError):
            tool.invoke("Invalid-Material")

    def test_list_families(self):
        """Test listing available material families."""
        tool = MaterialDBQueryTool()
        families = tool.list_families()

        assert len(families) > 0
        assert "Al-Mg-Si" in families

    def test_cache_enabled(self):
        """Test caching functionality."""
        tool = MaterialDBQueryTool(cache_enabled=True)

        # First call
        props1 = tool.invoke("Al-Mg-Si")
        # Second call should use cache
        props2 = tool.invoke("Al-Mg-Si")

        assert props1 == props2


class TestEngineDBQueryTool:
    """Tests for EngineDBQueryTool."""

    def test_invoke_valid_engine(self):
        """Test querying a valid engine family."""
        tool = EngineDBQueryTool()
        specs = tool.invoke("Turboprop-A")

        assert isinstance(specs, EngineSpecs)
        assert specs.family == "Turboprop-A"
        assert specs.thrust > 0

    def test_invoke_invalid_engine(self):
        """Test querying an invalid engine family."""
        tool = EngineDBQueryTool()

        with pytest.raises(ValueError):
            tool.invoke("Invalid-Engine")

    def test_list_families(self):
        """Test listing available engine families."""
        tool = EngineDBQueryTool()
        families = tool.list_families()

        assert len(families) > 0
        assert "Turboprop-A" in families


class TestCADGeneratorTool:
    """Tests for CADGeneratorTool."""

    @pytest.fixture
    def valid_design_params(self):
        """Create valid design parameters."""
        return DesignParams(
            wing_area=20.0,
            aspect_ratio=8.0,
            sweep=15.0,
            fuselage_length=10.0,
            tail_area=3.0,
            max_takeoff_weight=5000.0,
            empty_weight=3000.0,
            wing_thickness_ratio=0.15,
            taper_ratio=0.6,
        )

    def test_invoke_valid_params(self, valid_design_params):
        """Test CAD generation with valid params."""
        tool = CADGeneratorTool()
        cad_file = tool.invoke(valid_design_params)

        assert cad_file.file_id is not None
        assert cad_file.url is not None
        assert cad_file.format in ["STEP", "IGES", "STL"]

    def test_invoke_invalid_params(self):
        """Test CAD generation with invalid params.

        Note: Pydantic validation prevents creating DesignParams with wing_area <= 0.
        """
        with pytest.raises(Exception):  # ValidationError
            DesignParams(
                wing_area=0.0,  # Invalid
                aspect_ratio=8.0,
                sweep=15.0,
                fuselage_length=10.0,
                tail_area=3.0,
                max_takeoff_weight=5000.0,
                empty_weight=3000.0,
                wing_thickness_ratio=0.15,
                taper_ratio=0.6,
            )

    def test_set_format(self):
        """Test setting output format."""
        tool = CADGeneratorTool(default_format="IGES")
        assert tool.default_format == "IGES"

        tool.set_format("STL")
        assert tool.default_format == "STL"

        with pytest.raises(ValueError):
            tool.set_format("INVALID")

    def test_cache_functionality(self, valid_design_params):
        """Test that CAD generation is cached."""
        tool = CADGeneratorTool()

        cad1 = tool.invoke(valid_design_params)
        cad2 = tool.invoke(valid_design_params)

        assert cad1.file_id == cad2.file_id


class TestCFDSolverTool:
    """Tests for CFDSolverTool."""

    @pytest.fixture
    def design_params(self):
        """Create design parameters."""
        return DesignParams(
            wing_area=20.0,
            aspect_ratio=8.0,
            sweep=15.0,
            fuselage_length=10.0,
            tail_area=3.0,
            max_takeoff_weight=5000.0,
            empty_weight=3000.0,
            wing_thickness_ratio=0.15,
            taper_ratio=0.6,
        )

    def test_invoke_without_engine(self, design_params):
        """Test CFD simulation without engine."""
        tool = CFDSolverTool()
        result = tool.invoke(design_params)

        assert result.lift > 0
        assert result.drag > 0
        assert result.max_speed > 0
        assert result.range > 0

    def test_invoke_with_engine(self, design_params):
        """Test CFD simulation with engine."""
        tool = CFDSolverTool()
        engine = EngineSpecs(
            family="Turboprop-A",
            thrust=850.0,
            weight=180.0,
            fuel_consumption=120.0,
            cost=85000.0,
        )
        result = tool.invoke(design_params, engine)

        assert result.lift > 0
        assert result.range > 0

    def test_cache_functionality(self, design_params):
        """Test CFD caching."""
        tool = CFDSolverTool(enable_cache=True)

        result1 = tool.invoke(design_params)
        result2 = tool.invoke(design_params)

        assert result1 == result2

    def test_clear_cache(self, design_params):
        """Test clearing CFD cache."""
        tool = CFDSolverTool(enable_cache=True)

        tool.invoke(design_params)
        tool.clear_cache()

        assert len(tool._cache) == 0


class TestFEASolverTool:
    """Tests for FEASolverTool."""

    @pytest.fixture
    def design_params(self):
        """Create design parameters."""
        return DesignParams(
            wing_area=20.0,
            aspect_ratio=8.0,
            sweep=15.0,
            fuselage_length=10.0,
            tail_area=3.0,
            max_takeoff_weight=5000.0,
            empty_weight=3000.0,
            wing_thickness_ratio=0.15,
            taper_ratio=0.6,
        )

    def test_invoke_without_material(self, design_params):
        """Test FEA simulation without material."""
        tool = FEASolverTool()
        result = tool.invoke(design_params)

        assert result.max_stress >= 0
        assert result.safety_factor > 0
        assert result.weight > 0

    def test_invoke_with_material(self, design_params):
        """Test FEA simulation with material."""
        tool = FEASolverTool()
        material = MaterialProperties(
            family="Al-Mg-Si",
            density=2700.0,
            modulus=70.0,
            fatigue_limit=150.0,
            cost_per_kg=8.5,
        )
        result = tool.invoke(design_params, material)

        assert result.safety_factor > 0


class TestCostEstimatorTool:
    """Tests for CostEstimatorTool."""

    @pytest.fixture
    def design_params(self):
        """Create design parameters."""
        return DesignParams(
            wing_area=20.0,
            aspect_ratio=8.0,
            sweep=15.0,
            fuselage_length=10.0,
            tail_area=3.0,
            max_takeoff_weight=5000.0,
            empty_weight=3000.0,
            wing_thickness_ratio=0.15,
            taper_ratio=0.6,
        )

    def test_invoke_basic(self, design_params):
        """Test basic cost estimation."""
        tool = CostEstimatorTool()
        estimate = tool.invoke(design_params)

        assert estimate.material_cost >= 0
        assert estimate.manufacturing_cost >= 0
        assert estimate.total_cost > 0

    def test_invoke_with_material_and_engine(self, design_params):
        """Test cost estimation with material and engine."""
        tool = CostEstimatorTool()
        material = MaterialProperties(
            family="Al-Mg-Si",
            density=2700.0,
            modulus=70.0,
            fatigue_limit=150.0,
            cost_per_kg=8.5,
        )
        engine = EngineSpecs(
            family="Turboprop-A",
            thrust=850.0,
            weight=180.0,
            fuel_consumption=120.0,
            cost=85000.0,
        )
        estimate = tool.invoke(design_params, material, engine)

        assert estimate.total_cost > estimate.manufacturing_cost

    def test_set_cost_factor(self):
        """Test setting cost factor multiplier."""
        tool = CostEstimatorTool()
        tool.set_cost_factor(1.5)

        assert tool.cost_factor_multiplier == 1.5

        with pytest.raises(ValueError):
            tool.set_cost_factor(-1.0)


class TestComplianceCheckerTool:
    """Tests for ComplianceCheckerTool."""

    @pytest.fixture
    def design_params(self):
        """Create design parameters."""
        return DesignParams(
            wing_area=20.0,
            aspect_ratio=8.0,
            sweep=15.0,
            fuselage_length=10.0,
            tail_area=3.0,
            max_takeoff_weight=5000.0,
            empty_weight=3000.0,
            wing_thickness_ratio=0.15,
            taper_ratio=0.6,
        )

    def test_invoke_passing(self, design_params):
        """Test compliance check with valid design."""
        tool = ComplianceCheckerTool()
        report = tool.invoke(design_params)

        # Note: May pass or fail depending on design
        assert isinstance(report.passed, bool)
        assert isinstance(report.issues, list)

    def test_invoke_with_simulation(self, design_params):
        """Test compliance check with simulation results."""
        tool = ComplianceCheckerTool()
        cfd_result = CFDSimulationResult(
            range=2000.0,
            max_speed=200.0,
            lift=50000.0,
            drag=5000.0,
            weight=3000.0,
        )
        fea_result = FEASimulationResult(
            safety_factor=2.0,
            max_stress=100.0,
            weight=3000.0,
        )
        simulation = SimulationResult(cfd=cfd_result, fea=fea_result)

        report = tool.invoke(design_params, simulation)

        assert isinstance(report, ComplianceReport)
        assert hasattr(report, "passed")
        assert hasattr(report, "issues")


class TestOptimizationTool:
    """Tests for OptimizationTool."""

    @pytest.fixture
    def design_params(self):
        """Create design parameters."""
        return DesignParams(
            wing_area=20.0,
            aspect_ratio=8.0,
            sweep=15.0,
            fuselage_length=10.0,
            tail_area=3.0,
            max_takeoff_weight=5000.0,
            empty_weight=3000.0,
            wing_thickness_ratio=0.15,
            taper_ratio=0.6,
        )

    def test_invoke(self, design_params):
        """Test optimization."""
        tool = OptimizationTool(max_iterations=10)
        optimized = tool.invoke(design_params)

        assert isinstance(optimized, DesignParams)
        # Optimized params may or may not be different

    def test_set_bounds(self):
        """Test setting optimization bounds."""
        tool = OptimizationTool()
        tool.set_bounds("wing_area", 10.0, 50.0)

        assert tool.bounds["wing_area"] == (10.0, 50.0)


class TestVersionControlTool:
    """Tests for VersionControlTool."""

    def test_invoke_and_retrieve(self):
        """Test storing and retrieving design states."""
        tool = VersionControlTool()
        design_state = DesignState(
            design_params=DesignParams(
                wing_area=20.0,
                aspect_ratio=8.0,
                sweep=15.0,
                fuselage_length=10.0,
                tail_area=3.0,
                max_takeoff_weight=5000.0,
                empty_weight=3000.0,
                wing_thickness_ratio=0.15,
                taper_ratio=0.6,
            )
        )

        tool.invoke(design_state)
        history = tool.get_history()

        assert len(history) == 1

    def test_export_import_state(self):
        """Test exporting and importing state as JSON."""
        tool = VersionControlTool()
        design_state = DesignState(
            design_params=DesignParams(
                wing_area=20.0,
                aspect_ratio=8.0,
                sweep=15.0,
                fuselage_length=10.0,
                tail_area=3.0,
                max_takeoff_weight=5000.0,
                empty_weight=3000.0,
                wing_thickness_ratio=0.15,
                taper_ratio=0.6,
            )
        )

        json_str = tool.export_state(design_state)
        imported = tool.import_state(json_str)

        assert imported.design_params.wing_area == design_state.design_params.wing_area


class TestExportTool:
    """Tests for ExportTool."""

    def test_invoke_valid_format(self):
        """Test export with valid format."""
        tool = ExportTool()
        cad_file = type("CADFile", (), {
            "file_id": "test-123",
            "url": "https://example.com/test.step",
            "format": "STEP",
        })()

        url = tool.invoke(cad_file, "STEP")

        assert url is not None
        assert "STEP" in url or "step" in url

    def test_invoke_invalid_format(self):
        """Test export with invalid format."""
        tool = ExportTool()
        cad_file = type("CADFile", (), {
            "file_id": "test-123",
            "url": "https://example.com/test.step",
            "format": "STEP",
        })()

        with pytest.raises(ValueError):
            tool.invoke(cad_file, "INVALID")

    def test_list_supported_formats(self):
        """Test listing supported formats."""
        tool = ExportTool()
        formats = tool.list_supported_formats()

        assert len(formats) > 0
        assert "STEP" in formats