"""
TAYLOR VECTOR TERMINAL - Daily Edge Report Generator
Automated PDF reports with top 5 betting edges
"""

import sqlite3
import os
from datetime import datetime, timedelta
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.pdfgen import canvas

# Get the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(os.path.dirname(SCRIPT_DIR), 'taylor_62.db')
REPORTS_DIR = os.path.join(SCRIPT_DIR, 'reports')

def get_top_edges(date=None, limit=5):
    """
    Query database for top N edges from specified date (default: last 24 hours)
    Returns list of picks with full analysis
    """
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    if date:
        # Get picks from specific date
        start_date = f"{date} 00:00:00"
        end_date = f"{date} 23:59:59"
        query = '''
            SELECT * FROM picks 
            WHERE timestamp BETWEEN ? AND ?
            ORDER BY edge DESC 
            LIMIT ?
        '''
        picks = cursor.execute(query, (start_date, end_date, limit)).fetchall()
    else:
        # Get picks from last 24 hours
        query = '''
            SELECT * FROM picks 
            WHERE datetime(timestamp) >= datetime('now', '-24 hours')
            ORDER BY edge DESC 
            LIMIT ?
        '''
        picks = cursor.execute(query, (limit,)).fetchall()
    
    conn.close()
    return [dict(pick) for pick in picks]

def get_performance_metrics(date=None):
    """
    Calculate performance metrics for the specified date or last 24 hours
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    if date:
        start_date = f"{date} 00:00:00"
        end_date = f"{date} 23:59:59"
        
        total_picks = cursor.execute(
            'SELECT COUNT(*) FROM picks WHERE timestamp BETWEEN ? AND ?',
            (start_date, end_date)
        ).fetchone()[0]
        
        avg_edge = cursor.execute(
            'SELECT AVG(edge) FROM picks WHERE timestamp BETWEEN ? AND ?',
            (start_date, end_date)
        ).fetchone()[0]
        
        max_edge = cursor.execute(
            'SELECT MAX(edge) FROM picks WHERE timestamp BETWEEN ? AND ?',
            (start_date, end_date)
        ).fetchone()[0]
    else:
        total_picks = cursor.execute(
            "SELECT COUNT(*) FROM picks WHERE datetime(timestamp) >= datetime('now', '-24 hours')"
        ).fetchone()[0]
        
        avg_edge = cursor.execute(
            "SELECT AVG(edge) FROM picks WHERE datetime(timestamp) >= datetime('now', '-24 hours')"
        ).fetchone()[0]
        
        max_edge = cursor.execute(
            "SELECT MAX(edge) FROM picks WHERE datetime(timestamp) >= datetime('now', '-24 hours')"
        ).fetchone()[0]
    
    conn.close()
    
    return {
        'total_picks': total_picks or 0,
        'avg_edge': round(avg_edge, 2) if avg_edge else 0,
        'max_edge': round(max_edge, 2) if max_edge else 0,
        'win_rate': 0  # Placeholder - would need actual results tracking
    }

def generate_pdf_report(date=None, output_filename=None):
    """
    Generate PDF report with top 5 edges
    
    Args:
        date: Optional date string in YYYY-MM-DD format
        output_filename: Optional custom filename (defaults to daily_YYYY-MM-DD.pdf)
    
    Returns:
        Path to generated PDF file
    """
    # Ensure reports directory exists
    os.makedirs(REPORTS_DIR, exist_ok=True)
    
    # Determine report date
    if date:
        report_date = datetime.strptime(date, '%Y-%m-%d')
    else:
        report_date = datetime.now()
    
    # Set output filename
    if not output_filename:
        output_filename = f"daily_{report_date.strftime('%Y-%m-%d')}.pdf"
    
    filepath = os.path.join(REPORTS_DIR, output_filename)
    
    # Create PDF document
    doc = SimpleDocTemplate(filepath, pagesize=letter,
                           rightMargin=72, leftMargin=72,
                           topMargin=72, bottomMargin=18)
    
    # Container for the 'Flowable' objects
    elements = []
    
    # Define styles
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1a1a2e'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#0f3460'),
        spaceAfter=12,
        fontName='Helvetica-Bold'
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=12
    )
    
    # Header
    title = Paragraph("TAYLOR VECTOR TERMINAL", title_style)
    elements.append(title)
    
    subtitle = Paragraph("Daily Edge Report", heading_style)
    elements.append(subtitle)
    
    # Date and summary info
    date_text = Paragraph(
        f"<b>Report Date:</b> {report_date.strftime('%A, %B %d, %Y')}",
        normal_style
    )
    elements.append(date_text)
    elements.append(Spacer(1, 0.2*inch))
    
    # Get data
    top_picks = get_top_edges(date, limit=5)
    metrics = get_performance_metrics(date)
    
    # Performance Metrics Section
    elements.append(Paragraph("Performance Metrics", heading_style))
    
    metrics_data = [
        ['Metric', 'Value'],
        ['Total Picks Generated', str(metrics['total_picks'])],
        ['Average Edge', f"{metrics['avg_edge']}%"],
        ['Highest Edge', f"{metrics['max_edge']}%"],
        ['Win Rate', f"{metrics['win_rate']}%"]
    ]
    
    metrics_table = Table(metrics_data, colWidths=[3*inch, 2*inch])
    metrics_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0f3460')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements.append(metrics_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Top 5 Picks Section
    if top_picks:
        elements.append(Paragraph("Top 5 Betting Edges", heading_style))
        elements.append(Spacer(1, 0.1*inch))
        
        for i, pick in enumerate(top_picks, 1):
            # Pick header
            pick_header = Paragraph(
                f"<b>#{i} - {pick['game']}</b>",
                heading_style
            )
            elements.append(pick_header)
            
            # Pick details
            pick_data = [
                ['Pick', pick['pick']],
                ['Edge', f"{pick['edge']:.1f}%"],
                ['Spread', f"{pick['spread']:+.1f}"],
                ['Home TUSG%', f"{pick['home_tusg']:.1f}%"],
                ['Away TUSG%', f"{pick['away_tusg']:.1f}%"],
                ['Home PVR', f"{pick['home_pvr']:.1f}"],
                ['Away PVR', f"{pick['away_pvr']:.1f}"],
                ['Timestamp', pick['timestamp']]
            ]
            
            pick_table = Table(pick_data, colWidths=[2*inch, 3.5*inch])
            pick_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e8f4f8')),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('PADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
            ]))
            
            elements.append(pick_table)
            elements.append(Spacer(1, 0.2*inch))
    else:
        elements.append(Paragraph(
            "No picks found for the selected date.",
            normal_style
        ))
    
    # Footer
    elements.append(Spacer(1, 0.3*inch))
    footer = Paragraph(
        f"<i>Generated by Taylor Vector Terminal on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>",
        ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, textColor=colors.grey, alignment=TA_CENTER)
    )
    elements.append(footer)
    
    # Build PDF
    doc.build(elements)
    
    return filepath

def get_recent_reports(limit=10):
    """
    Get list of recent report files
    """
    if not os.path.exists(REPORTS_DIR):
        return []
    
    files = []
    for filename in os.listdir(REPORTS_DIR):
        if filename.endswith('.pdf'):
            filepath = os.path.join(REPORTS_DIR, filename)
            files.append({
                'filename': filename,
                'filepath': filepath,
                'created': os.path.getctime(filepath),
                'size': os.path.getsize(filepath)
            })
    
    # Sort by creation time (newest first)
    files.sort(key=lambda x: x['created'], reverse=True)
    
    return files[:limit]

if __name__ == '__main__':
    # Test report generation
    print("Generating daily report...")
    filepath = generate_pdf_report()
    print(f"✅ Report generated: {filepath}")
    
    # Show recent reports
    print("\nRecent reports:")
    for report in get_recent_reports(5):
        print(f"  - {report['filename']} ({report['size']} bytes)")
