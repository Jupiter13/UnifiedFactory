"""CAD Generator Tool.

Generates parametric STEP/IGES CAD files.
Uses simplified geometry generation (OpenCASCADE simulation).
"""

import hashlib
import uuid
from typing import Literal, Optional

from ..models import DesignParams, CADFile


class CADGeneratorTool:
    """Tool for generating parametric CAD files."""

    def __init__(
        self,
        output_dir: str = "/tmp/cad_output",
        default_format: Literal["STEP", "IGES", "STL"] = "STEP",
    ):
        """Initialize the CAD generator.

        Args:
            output_dir: Directory for CAD file output.
            default_format: Default output format.
        """
        self.output_dir = output_dir
        self.default_format = default_format
        self._cache = {}

    def invoke(self, design_params: DesignParams) -> CADFile:
        """Generate CAD file from design parameters.

        Args:
            design_params: Parametric design parameters.

        Returns:
            CADFile with file information.

        Raises:
            ValueError: If design parameters are invalid.
        """
        if design_params.is_invalid():
            raise ValueError("Invalid design parameters")

        # Generate cache key from design params
        cache_key = self._generate_cache_key(design_params)
        if cache_key in self._cache:
            return self._cache[cache_key]

        # Generate CAD file ID
        file_id = str(uuid.uuid4())

        # In production, this would use pythonocc to generate actual STEP/IGES
        # For now, we simulate the CAD generation
        file_url = f"{self.output_dir}/{file_id}.{self.default_format.lower()}"

        cad_file = CADFile(
            file_id=file_id,
            url=file_url,
            format=self.default_format,
        )

        # Cache the result
        self._cache[cache_key] = cad_file

        return cad_file

    def _generate_cache_key(self, design_params: DesignParams) -> str:
        """Generate cache key from design parameters."""
        param_str = (
            f"{design_params.wing_area}_{design_params.aspect_ratio}_"
            f"{design_params.sweep}_{design_params.fuselage_length}_"
            f"{design_params.tail_area}_{design_params.max_takeoff_weight}"
        )
        return hashlib.md5(param_str.encode()).hexdigest()

    def set_format(self, format: Literal["STEP", "IGES", "STL"]) -> None:
        """Set the default output format.

        Args:
            format: CAD file format.
        """
        if format not in ["STEP", "IGES", "STL"]:
            raise ValueError(f"Unsupported format: {format}")
        self.default_format = format


class CADGenerationError(Exception):
    """Error during CAD generation."""

    pass