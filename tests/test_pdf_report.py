"""Tests for PDF report generation."""

import pytest
from src.pdf_report import generate_pdf_report
from PIL import Image
import tempfile
import os
from pathlib import Path


def test_generate_pdf_report(
    sample_image: Image.Image, sample_qr_code: Image.Image, sample_metadata: dict
):
    """Should generate PDF report successfully."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Save image temporarily
        image_path = Path(tmp_dir) / "test.png"
        sample_image.save(image_path, "PNG")

        # Generate PDF
        pdf_path = Path(tmp_dir) / "report.pdf"
        result = generate_pdf_report(
            stamped_image_path=str(image_path),
            metadata=sample_metadata,
            qr_code_image=sample_qr_code,
            output_path=str(pdf_path),
        )

        # Verify PDF was created
        assert os.path.exists(result)
        assert Path(result).suffix == ".pdf"
        assert Path(result).stat().st_size > 0


def test_generate_pdf_creates_directory(
    sample_image: Image.Image, sample_qr_code: Image.Image, sample_metadata: dict
):
    """Should create output directory if it doesn't exist."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Save image temporarily
        image_path = Path(tmp_dir) / "test.png"
        sample_image.save(image_path, "PNG")

        # PDF in nested directory that doesn't exist
        pdf_path = Path(tmp_dir) / "nested" / "dir" / "report.pdf"

        result = generate_pdf_report(
            stamped_image_path=str(image_path),
            metadata=sample_metadata,
            qr_code_image=sample_qr_code,
            output_path=str(pdf_path),
        )

        assert os.path.exists(result)
        assert pdf_path.parent.exists()
