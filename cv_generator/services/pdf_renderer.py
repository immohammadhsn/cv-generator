import os
import sys
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.enums import TA_CENTER

from .file_namer import generate_filename


def create_pdf(cv_data: dict, output_dir: str, job_title: str | None = None) -> str:
    """Create PDF from CV data"""
    try:
        # Convert to absolute path
        output_dir = os.path.abspath(output_dir)

        # Create output directory if it doesn't exist
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        print(f"Output directory: {output_dir}")

        # Generate filename based on job title if provided
        if job_title:
            filename = generate_filename(job_title)
        else:
            filename = "cv.pdf"

        pdf_file = os.path.join(output_dir, filename)

        print(f"Creating PDF: {filename}")
        print(f"Full path: {pdf_file}")

        # Create PDF
        doc = SimpleDocTemplate(
            pdf_file,
            pagesize=letter,
            topMargin=0.5 * inch,
            bottomMargin=0.5 * inch,
            leftMargin=0.75 * inch,
            rightMargin=0.75 * inch,
        )

        # Container for PDF elements
        elements = []

        # Define styles
        styles = getSampleStyleSheet()

        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor='#2C3E50',
            spaceAfter=6,
            alignment=TA_CENTER,
        )

        contact_style = ParagraphStyle(
            'Contact',
            parent=styles['Normal'],
            fontSize=10,
            alignment=TA_CENTER,
            spaceAfter=12,
        )

        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor='#2C3E50',
            spaceAfter=6,
            spaceBefore=12,
            borderWidth=1,
            borderColor='#2C3E50',
            borderPadding=5,
        )

        body_style = styles['Normal']
        body_style.fontSize = 10
        body_style.spaceAfter = 6

        # Add name
        elements.append(Paragraph(cv_data['name'], title_style))

        # Add contact info
        contact_info = f"{cv_data['email']} | {cv_data['phone']} | {cv_data['location']}"
        if cv_data.get('linkedin'):
            contact_info += f"<br/>{cv_data['linkedin']}"
        if cv_data.get('github'):
            contact_info += f" | {cv_data['github']}"
        elements.append(Paragraph(contact_info, contact_style))

        elements.append(Spacer(1, 0.2 * inch))

        # Professional Summary
        elements.append(Paragraph("PROFESSIONAL SUMMARY", heading_style))
        elements.append(Paragraph(cv_data['summary'], body_style))
        elements.append(Spacer(1, 0.1 * inch))

        # Skills
        if cv_data.get('skills'):
            elements.append(Paragraph("SKILLS", heading_style))
            skills_text = " • ".join(cv_data['skills'])
            elements.append(Paragraph(skills_text, body_style))
            elements.append(Spacer(1, 0.1 * inch))

        # Work Experience
        if cv_data.get('experience'):
            elements.append(Paragraph("WORK EXPERIENCE", heading_style))
            for exp in cv_data['experience']:
                job_title_line = f"<b>{exp['title']}</b> - {exp['company']}"
                elements.append(Paragraph(job_title_line, body_style))
                elements.append(Paragraph(f"<i>{exp['period']}</i>", body_style))
                for achievement in exp['achievements']:
                    elements.append(Paragraph(f"• {achievement}", body_style))
                elements.append(Spacer(1, 0.1 * inch))

        # Education
        if cv_data.get('education'):
            elements.append(Paragraph("EDUCATION", heading_style))
            for edu in cv_data['education']:
                edu_text = f"<b>{edu['degree']}</b> - {edu['institution']}, {edu['year']}"
                elements.append(Paragraph(edu_text, body_style))
            elements.append(Spacer(1, 0.1 * inch))

        # Projects
        if cv_data.get('projects'):
            elements.append(Paragraph("PROJECTS", heading_style))
            for project in cv_data['projects']:
                project_text = f"<b>{project['name']}</b>: {project['description']}"
                elements.append(Paragraph(project_text, body_style))
            elements.append(Spacer(1, 0.1 * inch))

        # Build PDF
        print("Building PDF document...")
        doc.build(elements)
        print("✓ PDF build completed")

        # Verify file exists and get details
        if os.path.exists(pdf_file):
            file_size = os.path.getsize(pdf_file)
            print("✓ PDF successfully created!")
            print(f"✓ File location: {pdf_file}")
            print(f"✓ File size: {file_size:,} bytes ({file_size / 1024:.1f} KB)")

            # List all files in output directory
            print("\n📁 Files in output directory:")
            for item in sorted(os.listdir(output_dir)):
                item_path = os.path.join(output_dir, item)
                if os.path.isfile(item_path):
                    size = os.path.getsize(item_path)
                    print(f"   - {item} ({size:,} bytes)")
        else:
            print("❌ ERROR: PDF file was not created!")
            raise FileNotFoundError(f"PDF file not found at {pdf_file}")

        return pdf_file

    except Exception as e:
        print(f"❌ Error creating PDF: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
