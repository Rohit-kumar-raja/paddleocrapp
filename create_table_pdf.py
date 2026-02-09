from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors

def create_table_pdf(output_path):
    doc = SimpleDocTemplate(output_path, pagesize=letter)
    elements = []
    
    data = [
        ["Date", "Description", "Credit", "Debit", "Balance"],
        ["2023-01-01", "Opening Balance", "0", "0", "1000"],
        ["2023-01-02", "Salary", "5000", "0", "6000"],
        ["2023-01-03", "Rent", "0", "2000", "4000"],
        ["2023-01-04", "Groceries", "0", "500", "3500"]
    ]
    
    t = Table(data)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements.append(t)
    doc.build(elements)

if __name__ == "__main__":
    create_table_pdf("statement.pdf")
    print("Sample table PDF created.")
