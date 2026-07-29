from pathlib import Path
import re

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from models.customer import Customer
from models.estimate import Estimate


PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIRECTORY = PROJECT_ROOT / "generated_documents"


DEFAULT_COMPANY = {
    "name": "Palm Coast Pros",
    "address": "59 Brockton Ln<br/>Palm Coast, FL 32137-8728",
    "email": "dany.nawrocki@gmail.com",
    "phone": "(386) 585-0437",
    "website": "www.palmcoastpros.com",
}


def format_currency(cents: int) -> str:
    return f"${cents / 100:,.2f}"


def safe_filename(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", value.strip())
    return cleaned.strip("_") or "Customer"


def multiline(value: str) -> str:
    return value.strip().replace("\n", "<br/>")


def generate_estimate_pdf(
    estimate: Estimate,
    customer: Customer,
    company: dict[str, str] | None = None,
) -> Path:
    company = company or DEFAULT_COMPANY
    OUTPUT_DIRECTORY.mkdir(parents=True, exist_ok=True)

    output_path = OUTPUT_DIRECTORY / (
        f"Estimate_{estimate.estimate_number}_"
        f"{safe_filename(customer.name)}.pdf"
    )

    styles = getSampleStyleSheet()

    normal = ParagraphStyle(
        "AtlasNormal",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=13,
        textColor=colors.HexColor("#263B57"),
    )

    small = ParagraphStyle(
        "AtlasSmall",
        parent=normal,
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#64748B"),
    )

    label = ParagraphStyle(
        "AtlasLabel",
        parent=normal,
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#64748B"),
        spaceAfter=3,
    )

    company_name = ParagraphStyle(
        "CompanyName",
        parent=normal,
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=23,
        textColor=colors.HexColor("#10233E"),
    )

    document_title = ParagraphStyle(
        "DocumentTitle",
        parent=normal,
        fontName="Helvetica-Bold",
        fontSize=24,
        leading=27,
        alignment=TA_RIGHT,
        textColor=colors.HexColor("#1769E0"),
    )

    right = ParagraphStyle(
        "AtlasRight",
        parent=normal,
        alignment=TA_RIGHT,
    )

    total_style = ParagraphStyle(
        "AtlasTotal",
        parent=right,
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=18,
        textColor=colors.HexColor("#10233E"),
    )

    document = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        rightMargin=0.55 * inch,
        leftMargin=0.55 * inch,
        topMargin=0.5 * inch,
        bottomMargin=0.55 * inch,
        title=f"Estimate #{estimate.estimate_number}",
        author=company["name"],
    )

    story = []

    company_block = [
        Paragraph(company["name"], company_name),
        Spacer(1, 5),
        Paragraph(company["address"], normal),
        Paragraph(company["email"], normal),
        Paragraph(company["phone"], normal),
        Paragraph(company["website"], normal),
    ]

    estimate_block = [
        Paragraph("ESTIMATE", document_title),
        Spacer(1, 8),
        Paragraph(
            f"<b>Estimate no.:</b> {estimate.estimate_number}",
            right,
        ),
        Paragraph(
            f"<b>Estimate date:</b> {estimate.estimate_date}",
            right,
        ),
        Paragraph(
            f"<b>Expiration date:</b> {estimate.expiration_date}",
            right,
        ),
        Paragraph(f"<b>Status:</b> {estimate.status}", right),
    ]

    header = Table(
        [[company_block, estimate_block]],
        colWidths=[4.15 * inch, 3.0 * inch],
    )
    header.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )

    story.append(header)
    story.append(Spacer(1, 22))

    customer_address = customer.billing_address or customer.job_address
    bill_to = [
        Paragraph("BILL TO", label),
        Paragraph(f"<b>{customer.name}</b>", normal),
    ]

    if customer.company:
        bill_to.append(Paragraph(customer.company, normal))
    if customer_address:
        bill_to.append(Paragraph(multiline(customer_address), normal))
    if customer.phone:
        bill_to.append(Paragraph(customer.phone, normal))
    if customer.email:
        bill_to.append(Paragraph(customer.email, normal))

    job_to = [
        Paragraph("JOB LOCATION", label),
        Paragraph(
            multiline(estimate.job_address)
            if estimate.job_address
            else "Same as billing address",
            normal,
        ),
    ]

    address_table = Table(
        [[bill_to, job_to]],
        colWidths=[3.6 * inch, 3.55 * inch],
    )
    address_table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFF")),
                ("BOX", (0, 0), (-1, -1), 0.75, colors.HexColor("#DFE7F1")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#DFE7F1")),
                ("LEFTPADDING", (0, 0), (-1, -1), 12),
                ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                ("TOPPADDING", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ]
        )
    )

    story.append(address_table)
    story.append(Spacer(1, 22))

    item_rows = [
        [
            Paragraph("#", label),
            Paragraph("PRODUCT OR SERVICE", label),
            Paragraph("QTY", label),
            Paragraph("RATE", label),
            Paragraph("AMOUNT", label),
        ]
    ]

    for index, item in enumerate(estimate.items, start=1):
        item_rows.append(
            [
                Paragraph(str(index), normal),
                Paragraph(multiline(item.description), normal),
                Paragraph(f"{item.quantity:g}", right),
                Paragraph(format_currency(item.rate_cents), right),
                Paragraph(format_currency(item.amount_cents), right),
            ]
        )

    items_table = Table(
        item_rows,
        colWidths=[
            0.35 * inch,
            4.25 * inch,
            0.65 * inch,
            0.9 * inch,
            1.0 * inch,
        ],
        repeatRows=1,
    )
    items_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#0B1F3A"),
                ),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ALIGN", (2, 1), (-1, -1), "RIGHT"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#DFE7F1")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [
                    colors.white,
                    colors.HexColor("#F8FAFF"),
                ]),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )

    story.append(items_table)
    story.append(Spacer(1, 16))

    notes_content = estimate.notes or "No additional notes."

    notes_box = Table(
        [[
            [
                Paragraph("NOTES", label),
                Paragraph(multiline(notes_content), normal),
            ],
            [
                Paragraph("Subtotal", right),
                Paragraph("Tax", right),
                Paragraph("TOTAL", total_style),
            ],
            [
                Paragraph(format_currency(estimate.subtotal_cents), right),
                Paragraph(format_currency(estimate.tax_cents), right),
                Paragraph(format_currency(estimate.total_cents), total_style),
            ],
        ]],
        colWidths=[4.45 * inch, 1.15 * inch, 1.55 * inch],
    )
    notes_box.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BACKGROUND", (0, 0), (0, 0), colors.HexColor("#F8FAFF")),
                ("BOX", (0, 0), (0, 0), 0.75, colors.HexColor("#DFE7F1")),
                ("LEFTPADDING", (0, 0), (0, 0), 12),
                ("RIGHTPADDING", (0, 0), (0, 0), 12),
                ("TOPPADDING", (0, 0), (0, 0), 10),
                ("BOTTOMPADDING", (0, 0), (0, 0), 10),
                ("ALIGN", (1, 0), (-1, 0), "RIGHT"),
                ("LEFTPADDING", (1, 0), (-1, 0), 8),
                ("RIGHTPADDING", (1, 0), (-1, 0), 0),
            ]
        )
    )

    story.append(notes_box)
    story.append(Spacer(1, 28))

    acceptance = KeepTogether(
        [
            Paragraph("ESTIMATE ACCEPTANCE", label),
            Paragraph(
                "By signing below, the customer accepts the work, pricing, "
                "and terms described in this estimate.",
                small,
            ),
            Spacer(1, 24),
            Table(
                [
                    [
                        Paragraph("Accepted by", small),
                        Paragraph("Signature", small),
                        Paragraph("Date", small),
                    ],
                    ["", "", ""],
                ],
                colWidths=[2.25 * inch, 3.0 * inch, 1.65 * inch],
                rowHeights=[0.22 * inch, 0.42 * inch],
                style=TableStyle(
                    [
                        ("LINEBELOW", (0, 1), (-1, 1), 0.75, colors.HexColor("#64748B")),
                        ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 0),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                    ]
                ),
            ),
        ]
    )

    story.append(acceptance)

    def draw_footer(canvas, doc) -> None:
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor("#DFE7F1"))
        canvas.line(
            doc.leftMargin,
            0.38 * inch,
            letter[0] - doc.rightMargin,
            0.38 * inch,
        )
        canvas.setFont("Helvetica", 7.5)
        canvas.setFillColor(colors.HexColor("#7A899C"))
        canvas.drawString(
            doc.leftMargin,
            0.22 * inch,
            "Generated with Atlas Invoice Studio",
        )
        canvas.drawRightString(
            letter[0] - doc.rightMargin,
            0.22 * inch,
            f"Page {doc.page}",
        )
        canvas.restoreState()

    document.build(
        story,
        onFirstPage=draw_footer,
        onLaterPages=draw_footer,
    )

    return output_path
