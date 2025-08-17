from fastapi import FastAPI, Request, Form
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
import uuid
import os

app = FastAPI(title="Auto PDF Report Generator")

# Setup templates
templates = Jinja2Templates(directory="templates")

# Folder to save PDFs
OUTPUT_DIR = "generated_reports"
os.makedirs(OUTPUT_DIR, exist_ok=True)


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/generate/")
async def generate_pdf(heading: str = Form(...), content: str = Form(...)):
    file_name = f"{uuid.uuid4()}.pdf"
    file_path = os.path.join(OUTPUT_DIR, file_name)

    # Create PDF with thinner margins
    doc = SimpleDocTemplate(
        file_path,
        pagesize=letter,
        rightMargin=36,   # half-inch margins (~0.5 inch)
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    # Styles
    styles = getSampleStyleSheet()
    heading_style = ParagraphStyle(
        "Heading",
        parent=styles["Heading1"],
        fontSize=18,
        alignment=1,  # Center
        spaceAfter=20,
        textColor=colors.darkblue,
        bold=True
    )
    body_style = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontSize=12,
        leading=16,
        spaceAfter=12,
        alignment=0  # Left
    )

    elements = []

    # Add custom heading
    elements.append(Paragraph(heading, heading_style))
    elements.append(Spacer(1, 12))

    # Add paragraphs
    for para in content.split("\n"):
        if para.strip():
            elements.append(Paragraph(para.strip(), body_style))

    # Define a function to draw border on every page
    def draw_border(canvas, doc):
        width, height = letter
        canvas.saveState()
        # Draw rectangle around the page (thin border)
        canvas.setStrokeColor(colors.black)
        canvas.setLineWidth(1)  # thin line
        canvas.rect(20, 20, width - 40, height - 40)  # inset slightly
        canvas.restoreState()

    # Build PDF with border
    doc.build(elements, onFirstPage=draw_border, onLaterPages=draw_border)

    return RedirectResponse(url=f"/download/{file_name}", status_code=303)


@app.get("/download/{file_name}")
async def download_pdf(file_name: str):
    file_path = os.path.join(OUTPUT_DIR, file_name)
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="application/pdf", filename=file_name)
    return {"error": "File not found"}
