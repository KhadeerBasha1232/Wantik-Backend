import os
from django.conf import settings
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor

def generate_invoice_pdf(quote, file_path):
    doc = SimpleDocTemplate(file_path, pagesize=letter, leftMargin=0.5*inch, rightMargin=0.5*inch, topMargin=0.5*inch, bottomMargin=0.5*inch)
    styles = getSampleStyleSheet()
    elements = []

    COLOR_TEXT = HexColor("#333333") 
    COLOR_HEADER = HexColor("#000000")  
    COLOR_ACCENT = HexColor("#22c55e")  
    COLOR_ERROR = HexColor("#dc2626")  
    COLOR_TABLE_HEADER = HexColor("#d1d5db")  
    COLOR_TABLE_ROW1 = HexColor("#ffffff")  
    COLOR_TABLE_ROW2 = HexColor("#f5f5f4")  
    COLOR_BACKGROUND = HexColor("#f3f4f6")   

    
    title_style = ParagraphStyle(
        name='Title',
        fontName='Helvetica-Bold',
        fontSize=16,
        textColor=COLOR_HEADER,
        leading=20,
        alignment=1,  
        spaceAfter=12,
    )
    subtitle_style = ParagraphStyle(
        name='Subtitle',
        fontName='Helvetica-Bold',
        fontSize=12,
        textColor=COLOR_TEXT,
        leading=15,
        spaceAfter=8,
    )
    normal_style = ParagraphStyle(
        name='Normal',
        fontName='Helvetica',
        fontSize=10,
        textColor=COLOR_TEXT,
        leading=12,
        spaceAfter=6,
    )
    total_style = ParagraphStyle(
        name='Total',
        fontName='Helvetica-Bold',
        fontSize=11,
        textColor=COLOR_ACCENT,
        leading=14,
        spaceAfter=6,
    )
    notes_style = ParagraphStyle(
        name='Notes',
        fontName='Helvetica',
        fontSize=10,
        textColor=COLOR_TEXT,
        leading=12,
        spaceAfter=6,
        leftIndent=6,
        rightIndent=6,
        borderWidth=1,
        borderColor=COLOR_TEXT,
        borderPadding=6,
    )

    
    elements.append(Paragraph("Your Company Name", title_style))
    elements.append(Paragraph("Invoice", title_style))
    elements.append(HRFlowable(width="100%", thickness=1, color=COLOR_TEXT, spaceAfter=0.1*inch))
    elements.append(Paragraph(f"Quote No: {quote.quote_no}", subtitle_style))
    elements.append(Paragraph(f"Date: {quote.create_date.strftime('%B %d, %Y')}", subtitle_style))
    elements.append(Spacer(1, 0.25*inch))

    
    elements.append(Paragraph("Bill To:", subtitle_style))
    contact_info = [
        quote.company_name,
        f"Contact: {quote.contact_name or '-'}",
        f"Email: {quote.contact_email}",
        f"Phone: {quote.contact_number or '-'}",
        f"Company Email: {quote.company_email or '-'}",
    ]
    for line in contact_info:
        elements.append(Paragraph(line, normal_style))
    elements.append(Spacer(1, 0.25*inch))
    elements.append(HRFlowable(width="100%", thickness=1, color=COLOR_TEXT, spaceAfter=0.1*inch))

    
    elements.append(Paragraph(f"Quote Title: {quote.quote_title}", subtitle_style))
    elements.append(Paragraph(f"Year: {quote.year}", normal_style))
    elements.append(Paragraph(f"Status: {quote.get_status_display()}", normal_style))
    elements.append(Paragraph(f"Assigned To: {quote.assign_to.username if quote.assign_to else '-'}", normal_style))
    elements.append(Paragraph(f"Created By: {quote.created_by.username if quote.created_by else '-'}", normal_style))
    elements.append(Spacer(1, 0.25*inch))
    elements.append(HRFlowable(width="100%", thickness=1, color=COLOR_TEXT, spaceAfter=0.1*inch))

    
    data = [['Product', 'Specification', 'Quantity', 'Unit Price', 'Total']]
    for i, product in enumerate(quote.products.all()):
        data.append([
            product.product,
            product.specification or '-',
            str(product.qty),
            f"${product.unit_price:.2f}",
            f"${product.total_price:.2f}",
        ])
    
    table = Table(data, colWidths=[2*inch, 2*inch, 0.8*inch, 1*inch, 1*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), COLOR_TABLE_HEADER),
        ('TEXTCOLOR', (0, 0), (-1, 0), COLOR_TEXT),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, COLOR_TEXT),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    for i in range(1, len(data)):
        bg_color = COLOR_TABLE_ROW1 if i % 2 == 0 else COLOR_TABLE_ROW2
        table.setStyle(TableStyle([('BACKGROUND', (0, i), (-1, i), bg_color)]))
    elements.append(table)
    elements.append(Spacer(1, 0.25*inch))

    
    elements.append(Paragraph(f"Subtotal: ${quote.subtotal:.2f}", normal_style))
    elements.append(Paragraph(
        f"VAT ({quote.vat_percentage}%): ${quote.vat_amount:.2f}" if quote.vat_applicable else "VAT: $0.00",
        normal_style
    ))
    elements.append(Paragraph(f"Grand Total: ${quote.grand_total:.2f}", total_style))
    elements.append(Spacer(1, 0.25*inch))
    elements.append(HRFlowable(width="100%", thickness=1, color=COLOR_TEXT, spaceAfter=0.1*inch))

    
    if quote.notes_remarks:
        elements.append(Paragraph("Notes/Remarks:", subtitle_style))
        elements.append(Paragraph(quote.notes_remarks, notes_style))
        elements.append(Spacer(1, 0.25*inch))

    
    def add_footer(canvas, doc):
        canvas.saveState()
        canvas.setFont('Helvetica', 9)
        canvas.setFillColor(COLOR_TEXT)
        canvas.drawString(0.5*inch, 0.3*inch, f"Page {doc.page}")
        canvas.drawRightString(doc.rightMargin + doc.width, 0.3*inch, "Contact: info@yourcompany.com | +1-123-456-7890")
        canvas.restoreState()

    
    doc.build(elements, onFirstPage=add_footer, onLaterPages=add_footer)