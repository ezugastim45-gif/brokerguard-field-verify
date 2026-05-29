"""Professional PDF report generation with ReportLab."""

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from PIL import Image
from datetime import datetime
from typing import Optional, Dict, Any
from io import BytesIO
import os


def generate_pdf_report(
    stamped_image_path: str,
    metadata: Dict[str, Any],
    qr_code_image: Image.Image,
    output_path: str,
    logo_path: Optional[str] = None,
) -> str:
    """
    Generates professional PDF report.

    Layout:
    ┌─────────────────────────────────────┐
    │  BROKERGUARD FIELD VERIFICATION     │
    │  Report ID: [hash]                  │
    ├─────────────────────────────────────┤
    │                                     │
    │      [Stamped Image - 15cm wide]    │
    │                                     │
    ├─────────────────────────────────────┤
    │  VERIFICATION DETAILS               │
    │  ┌───────────────┬────────────────┐ │
    │  │ Timestamp     │ 2026-05-29...  │ │
    │  │ Coordinates   │ -23.55, -46.63 │ │
    │  │ Altitude      │ 760.5m         │ │
    │  │ Broker ID     │ uuid-123       │ │
    │  │ Property ID   │ PROP-456       │ │
    │  │ Hash (SHA256) │ a3f5d8c2...    │ │
    │  └───────────────┴────────────────┘ │
    ├─────────────────────────────────────┤
    │  SCAN TO VERIFY ONLINE              │
    │       [QR Code - 4cm x 4cm]         │
    └─────────────────────────────────────┘

    Args:
        stamped_image_path: Path to stamped image
        metadata: Dict with verification data
        qr_code_image: PIL Image of QR code
        output_path: Where to save PDF
        logo_path: Optional path to logo

    Returns:
        Path to generated PDF

    Example:
        >>> from PIL import Image
        >>> qr = Image.new('RGB', (150, 150), 'white')
        >>> metadata = {
        ...     'timestamp': '2026-05-29 14:30:00',
        ...     'lat': -23.55,
        ...     'lon': -46.63,
        ...     'hash': 'abc123',
        ...     'broker_id': 'broker-1',
        ...     'property_id': 'prop-1'
        ... }
        >>> # pdf = generate_pdf_report('img.jpg', metadata, qr, 'out.pdf')
    """
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Create PDF
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    # Container for elements
    elements = []

    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Heading1"],
        fontSize=24,
        textColor=colors.HexColor("#1a1a1a"),
        spaceAfter=12,
        alignment=TA_CENTER,
        fontName="Helvetica-Bold",
    )

    subtitle_style = ParagraphStyle(
        "CustomSubtitle",
        parent=styles["Normal"],
        fontSize=10,
        textColor=colors.HexColor("#666666"),
        spaceAfter=20,
        alignment=TA_CENTER,
    )

    heading_style = ParagraphStyle(
        "CustomHeading",
        parent=styles["Heading2"],
        fontSize=14,
        textColor=colors.HexColor("#333333"),
        spaceAfter=12,
        spaceBefore=12,
        fontName="Helvetica-Bold",
    )

    # Title
    title = Paragraph("BROKERGUARD FIELD VERIFICATION", title_style)
    elements.append(title)

    # Subtitle with hash
    hash_value = metadata.get("hash", "N/A")
    subtitle = Paragraph(f"Report ID: {hash_value[:16]}...", subtitle_style)
    elements.append(subtitle)

    elements.append(Spacer(1, 0.5 * cm))

    # Stamped image
    try:
        img = RLImage(stamped_image_path, width=15 * cm, height=None)
        img.hAlign = "CENTER"
        elements.append(img)
    except Exception as e:
        error_text = Paragraph(f"[Image could not be loaded: {e}]", styles["Normal"])
        elements.append(error_text)

    elements.append(Spacer(1, 1 * cm))

    # Verification Details heading
    heading = Paragraph("VERIFICATION DETAILS", heading_style)
    elements.append(heading)

    # Details table
    details_data = [
        ["Timestamp", metadata.get("timestamp", "N/A")],
        [
            "Coordinates",
            f"{metadata.get('lat', 'N/A')}, {metadata.get('lon', 'N/A')}",
        ],
        ["Altitude", f"{metadata.get('altitude', 'N/A')} m"],
        ["Address", metadata.get("address", "N/A")],
        ["Broker ID", metadata.get("broker_id", "N/A")],
        ["Property ID", metadata.get("property_id", "N/A")],
        ["Weather", metadata.get("weather", "N/A")],
        ["Compass", metadata.get("compass", "N/A")],
        ["Hash (SHA256)", hash_value],
    ]

    # Add notes if present
    if metadata.get("notes"):
        details_data.append(["Notes", metadata.get("notes")])

    table = Table(details_data, colWidths=[5 * cm, 12 * cm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f0f0f0")),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
                ("ALIGN", (0, 0), (0, -1), "RIGHT"),
                ("ALIGN", (1, 0), (1, -1), "LEFT"),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    elements.append(table)

    elements.append(Spacer(1, 1.5 * cm))

    # QR Code section
    qr_heading = Paragraph("SCAN TO VERIFY ONLINE", heading_style)
    qr_heading.hAlign = "CENTER"
    elements.append(qr_heading)

    elements.append(Spacer(1, 0.5 * cm))

    # Convert PIL image to ReportLab image
    qr_buffer = BytesIO()
    qr_code_image.save(qr_buffer, format="PNG")
    qr_buffer.seek(0)

    qr_rl = RLImage(qr_buffer, width=4 * cm, height=4 * cm)
    qr_rl.hAlign = "CENTER"
    elements.append(qr_rl)

    elements.append(Spacer(1, 0.3 * cm))

    # QR URL text
    verification_url = metadata.get("verification_url", "N/A")
    url_text = Paragraph(
        f'<font size="8">{verification_url}</font>',
        ParagraphStyle("URLStyle", parent=styles["Normal"], alignment=TA_CENTER),
    )
    elements.append(url_text)

    # Footer
    elements.append(Spacer(1, 1 * cm))
    footer_text = Paragraph(
        '<font size="8" color="#999999">Generated by BrokerGuard Field Verify | MIT License | '
        f'Created: {datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")}</font>',
        ParagraphStyle("FooterStyle", parent=styles["Normal"], alignment=TA_CENTER),
    )
    elements.append(footer_text)

    # Build PDF
    doc.build(elements)

    return output_path
