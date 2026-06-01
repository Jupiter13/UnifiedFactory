"""Export Tool.

Converts CAD files to user-desired formats.
"""

from typing import Literal

from ..models import CADFile


class ExportTool:
    """Tool for exporting CAD files in various formats."""

    SUPPORTED_FORMATS = ["STEP", "IGES", "STL"]

    def __init__(self, s3_bucket: str = "afw-d-cad-exports"):
        """Initialize the export tool.

        Args:
            s3_bucket: S3 bucket for storing exports.
        """
        self.s3_bucket = s3_bucket

    def invoke(
        self,
        cad_file: CADFile,
        target_format: Literal["STEP", "IGES", "STL"],
    ) -> str:
        """Convert CAD file to target format.

        Args:
            cad_file: Source CAD file.
            target_format: Target export format.

        Returns:
            URL to exported file.

        Raises:
            ValueError: If format is not supported.
        """
        if target_format not in self.SUPPORTED_FORMATS:
            raise ValueError(
                f"Unsupported format: {target_format}. "
                f"Supported formats: {self.SUPPORTED_FORMATS}"
            )

        # In production, this would use CAD kernel to convert
        # For now, simulate the conversion
        export_url = (
            f"https://{self.s3_bucket}.s3.amazonaws.com/"
            f"{cad_file.file_id}_export.{target_format.lower()}"
        )

        return export_url

    def list_supported_formats(self) -> list[str]:
        """List all supported export formats.

        Returns:
            List of format names.
        """
        return self.SUPPORTED_FORMATS.copy()


class ExportError(Exception):
    """Error during CAD export."""

    pass