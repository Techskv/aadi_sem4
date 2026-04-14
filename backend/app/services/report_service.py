
"""
Report Service - Generate PDF reports for evaluation results.
"""
import os
import io
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as ReportLabImage

from app.models.submission import Submission
from app.models.result import TotalResult, Result
from app.models.user import User

class ReportService:
    """Service to generate PDF reports."""
    
    def generate_pdf_report(self, submission: Submission, total_result: TotalResult, results: list[Result], student: User, exam_name: str) -> bytes:
        """
        Generate a PDF report for a submission.
        Returns: bytes content of the PDF
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=72, leftMargin=72,
            topMargin=72, bottomMargin=72,
            title=f"Evaluation Report - {student.name}"
        )
        
        # Styles
        styles = getSampleStyleSheet()
        title_style = styles["Heading1"]
        title_style.alignment = 1  # Center
        
        heading_style = styles["Heading2"]
        normal_style = styles["Normal"]
        
        elements = []
        
        # --- Header ---
        elements.append(Paragraph("Automated Evaluation Report", title_style))
        elements.append(Spacer(1, 0.5 * inch))
        
        # --- Student Info ---
        info_data = [
            ["Student Name:", student.name],
            ["Student Email:", student.email],
            ["Exam:", exam_name],
            ["Date:", total_result.created_at.strftime("%Y-%m-%d %H:%M")]
        ]
        t_info = Table(info_data, colWidths=[1.5*inch, 4*inch])
        t_info.setStyle(TableStyle([
            ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ]))
        elements.append(t_info)
        elements.append(Spacer(1, 0.5 * inch))
        
        # --- Score Summary ---
        elements.append(Paragraph("Performance Summary", heading_style))
        elements.append(Spacer(1, 0.2 * inch))
        
        score_data = [
            ["Total Score", f"{total_result.total_marks} / {total_result.max_marks}"],
            ["Percentage", f"{total_result.percentage:.2f}%"],
            ["Grade", total_result.grade],
            ["Status", submission.status.upper()]
        ]
        
        t_score = Table(score_data, colWidths=[2*inch, 2*inch])
        t_score.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (0,-1), colors.lightgrey),
            ('TEXTCOLOR', (0,0), (-1,-1), colors.black),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
            ('FONTSIZE', (0,0), (-1,-1), 12),
            ('BOTTOMPADDING', (0,0), (-1,-1), 12),
            ('GRID', (0,0), (-1,-1), 1, colors.black)
        ]))
        elements.append(t_score)
        elements.append(Spacer(1, 0.5 * inch))
        
        # --- Question Breakdown ---
        elements.append(Paragraph("Question Breakdown", heading_style))
        elements.append(Spacer(1, 0.2 * inch))
        
        # Table Header
        q_data = [["Q.No", "Marks", "Max", "Feedback"]]
        
        # Table Rows
        for r in results:
            feedback = r.feedback[:50] + "..." if r.feedback and len(r.feedback) > 50 else (r.feedback or "")
            q_data.append([
                str(r.question_no),
                str(r.marks_obtained),
                str(r.max_marks),
                feedback
            ])
            
        t_questions = Table(q_data, colWidths=[0.8*inch, 1*inch, 1*inch, 3.5*inch])
        t_questions.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.grey),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0,0), (-1,0), 12),
            ('GRID', (0,0), (-1,-1), 1, colors.black),
            ('ALIGN', (3,1), (3,-1), 'LEFT'), # Align feedback left
        ]))
        
        elements.append(t_questions)
        
        # --- Build PDF ---
        doc.build(elements)
        buffer.seek(0)
        return buffer.read()

report_service = ReportService()
