"""
TAYLOR VECTOR TERMINAL - Daily Edge Report Generator
Automated PDF reports with analytics, charts, and email delivery
Task #19 - Professional daily betting edge reports
"""

import sqlite3
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime, timedelta
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfgen import canvas

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(os.path.dirname(SCRIPT_DIR), 'taylor_62.db')
REPORTS_DIR = os.path.join(SCRIPT_DIR, 'reports')
CHARTS_DIR = os.path.join(SCRIPT_DIR, 'charts')

EMAIL_LIST = os.getenv('EMAIL_LIST', '').split(',')
SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
SMTP_USER = os.getenv('SMTP_USER', '')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')

os.makedirs(REPORTS_DIR, exist_ok=True)
os.makedirs(CHARTS_DIR, exist_ok=True)

def get_picks_last_24h():
    """Query database for picks from last 24 hours"""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    query = '''
        SELECT * FROM picks 
        WHERE datetime(timestamp) >= datetime('now', '-24 hours')
        ORDER BY edge DESC
    '''
    picks = cursor.fetchall()
    conn.close()
    
    return [dict(pick) for pick in picks]

def get_picks_by_date(date):
    """Query database for picks from specific date"""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    start_date = f"{date} 00:00:00"
    end_date = f"{date} 23:59:59"
    
    query = '''
        SELECT * FROM picks 
        WHERE timestamp BETWEEN ? AND ?
        ORDER BY edge DESC
    '''
    picks = cursor.execute(query, (start_date, end_date)).fetchall()
    conn.close()
    
    return [dict(pick) for pick in picks]

def get_performance_metrics(picks):
    """Calculate performance metrics from picks data"""
    if not picks:
        return {
            'total_picks': 0,
            'avg_edge': 0,
            'max_edge': 0,
            'avg_confidence': 0,
            'avg_tusg_diff': 0,
            'avg_pvr_diff': 0
        }
    
    edges = [p.get('edge', 0) for p in picks]
    confidences = [p.get('confidence', 0) for p in picks if p.get('confidence', 0) > 0]
    
    tusg_diffs = []
    pvr_diffs = []
    
    for p in picks:
        if 'tusg_home' in p and 'tusg_away' in p:
            tusg_diffs.append(abs(p['tusg_home'] - p['tusg_away']))
        if 'pvr_home' in p and 'pvr_away' in p:
            pvr_diffs.append(abs(p['pvr_home'] - p['pvr_away']))
    
    return {
        'total_picks': len(picks),
        'avg_edge': round(sum(edges) / len(edges), 2) if edges else 0,
        'max_edge': round(max(edges), 2) if edges else 0,
        'avg_confidence': round(sum(confidences) / len(confidences), 2) if confidences else 0,
        'avg_tusg_diff': round(sum(tusg_diffs) / len(tusg_diffs), 2) if tusg_diffs else 0,
        'avg_pvr_diff': round(sum(pvr_diffs) / len(pvr_diffs), 2) if pvr_diffs else 0
    }

def create_edge_distribution_chart(picks, output_path):
    """Create edge distribution bar chart"""
    if not picks:
        return None
    
    edges = [p.get('edge', 0) for p in picks]
    
    plt.figure(figsize=(8, 5))
    plt.hist(edges, bins=10, color='#0f3460', edgecolor='black', alpha=0.7)
    plt.xlabel('Edge (%)', fontsize=12, fontweight='bold')
    plt.ylabel('Frequency', fontsize=12, fontweight='bold')
    plt.title('Edge Distribution - Last 24 Hours', fontsize=14, fontweight='bold')
    plt.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    return output_path

def create_metrics_comparison_chart(picks, output_path):
    """Create TUSG vs PVR comparison chart"""
    if not picks:
        return None
    
    tusg_home = [p.get('tusg_home', 0) for p in picks[:10]]
    tusg_away = [p.get('tusg_away', 0) for p in picks[:10]]
    pvr_home = [p.get('pvr_home', 0) for p in picks[:10]]
    pvr_away = [p.get('pvr_away', 0) for p in picks[:10]]
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    
    x = range(len(tusg_home))
    width = 0.35
    
    ax1.bar([i - width/2 for i in x], tusg_home, width, label='Home', color='#0f3460', alpha=0.8)
    ax1.bar([i + width/2 for i in x], tusg_away, width, label='Away', color='#e94560', alpha=0.8)
    ax1.set_xlabel('Game #', fontweight='bold')
    ax1.set_ylabel('TUSG %', fontweight='bold')
    ax1.set_title('TUSG% Comparison (Top 10 Picks)', fontweight='bold')
    ax1.legend()
    ax1.grid(axis='y', alpha=0.3)
    
    ax2.bar([i - width/2 for i in x], pvr_home, width, label='Home', color='#0f3460', alpha=0.8)
    ax2.bar([i + width/2 for i in x], pvr_away, width, label='Away', color='#e94560', alpha=0.8)
    ax2.set_xlabel('Game #', fontweight='bold')
    ax2.set_ylabel('PVR', fontweight='bold')
    ax2.set_title('PVR Comparison (Top 10 Picks)', fontweight='bold')
    ax2.legend()
    ax2.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    return output_path

def get_tomorrows_games_preview():
    """Generate preview of tomorrow's games (placeholder - would integrate with API)"""
    return [
        {"matchup": "Lakers @ Warriors", "time": "7:30 PM ET", "spread": "LAL -3.5"},
        {"matchup": "Celtics @ Heat", "time": "8:00 PM ET", "spread": "BOS -5.0"},
        {"matchup": "Nuggets @ Suns", "time": "9:00 PM ET", "spread": "DEN -2.5"}
    ]

def add_watermark(canvas, doc):
    """Add watermark to PDF pages"""
    canvas.saveState()
    canvas.setFont('Helvetica', 60)
    canvas.setFillColorRGB(0.9, 0.9, 0.9, alpha=0.1)
    canvas.translate(letter[0]/2, letter[1]/2)
    canvas.rotate(45)
    canvas.drawCentredString(0, 0, "TAYLOR VECTOR")
    canvas.restoreState()

def generate_pdf_report(date=None, send_email=False):
    """
    Generate comprehensive PDF report with charts and analytics
    
    Args:
        date: Optional date string (YYYY-MM-DD) - defaults to yesterday
        send_email: Whether to send report via email
    
    Returns:
        Path to generated PDF file
    """
    
    if date:
        report_date = datetime.strptime(date, '%Y-%m-%d')
        picks = get_picks_by_date(date)
    else:
        report_date = datetime.now() - timedelta(days=1)
        picks = get_picks_last_24h()
    
    date_str = report_date.strftime('%Y-%m-%d')
    output_filename = f"daily_edge_{date_str}.pdf"
    filepath = os.path.join(REPORTS_DIR, output_filename)
    
    doc = SimpleDocTemplate(
        filepath, 
        pagesize=letter,
        rightMargin=60, 
        leftMargin=60,
        topMargin=60, 
        bottomMargin=40
    )
    
    elements = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=28,
        textColor=colors.HexColor('#1a1a2e'),
        spaceAfter=10,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=16,
        textColor=colors.HexColor('#0f3460'),
        spaceAfter=20,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#0f3460'),
        spaceAfter=12,
        spaceBefore=16,
        fontName='Helvetica-Bold',
        borderPadding=(0, 0, 3, 0),
        borderColor=colors.HexColor('#0f3460'),
        borderWidth=2
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=12
    )
    
    title = Paragraph("⚡ TAYLOR VECTOR TERMINAL ⚡", title_style)
    elements.append(title)
    
    subtitle = Paragraph("Daily Edge Report", subtitle_style)
    elements.append(subtitle)
    
    date_text = Paragraph(
        f"<b>Report Date:</b> {report_date.strftime('%A, %B %d, %Y')}",
        normal_style
    )
    elements.append(date_text)
    
    generated_text = Paragraph(
        f"<i>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>",
        ParagraphStyle('Small', parent=styles['Normal'], fontSize=8, textColor=colors.grey, alignment=TA_CENTER)
    )
    elements.append(generated_text)
    elements.append(Spacer(1, 0.3*inch))
    
    metrics = get_performance_metrics(picks)
    
    elements.append(Paragraph("📊 EXECUTIVE SUMMARY", heading_style))
    
    summary_data = [
        ['Metric', 'Value'],
        ['Total Edges Generated', str(metrics['total_picks'])],
        ['Average Edge', f"{metrics['avg_edge']:.2f}%"],
        ['Maximum Edge', f"{metrics['max_edge']:.2f}%"],
        ['Average Confidence', f"{metrics['avg_confidence']:.2f}%"],
        ['Avg TUSG Differential', f"{metrics['avg_tusg_diff']:.2f}%"],
        ['Avg PVR Differential', f"{metrics['avg_pvr_diff']:.2f}"]
    ]
    
    summary_table = Table(summary_data, colWidths=[3.5*inch, 2.5*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0f3460')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('TOPPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f0f0f0')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f8f8')]),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cccccc')),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('PADDING', (0, 0), (-1, -1), 8)
    ]))
    
    elements.append(summary_table)
    elements.append(Spacer(1, 0.4*inch))
    
    if picks:
        top_5 = picks[:5]
        
        elements.append(Paragraph("🔥 TOP 5 BETTING EDGES", heading_style))
        elements.append(Spacer(1, 0.1*inch))
        
        top5_data = [['#', 'Game', 'Pick', 'Spread', 'TUSG%', 'PVR', 'Edge%']]
        
        for i, pick in enumerate(top_5, 1):
            tusg_home = pick.get('tusg_home', 0)
            tusg_away = pick.get('tusg_away', 0)
            pvr_home = pick.get('pvr_home', 0)
            pvr_away = pick.get('pvr_away', 0)
            
            top5_data.append([
                str(i),
                pick.get('game', 'N/A')[:30],
                pick.get('pick', 'N/A')[:20],
                f"{pick.get('spread', 0):+.1f}",
                f"H:{tusg_home:.1f}\nA:{tusg_away:.1f}",
                f"H:{pvr_home:.1f}\nA:{pvr_away:.1f}",
                f"{pick.get('edge', 0):.1f}%"
            ])
        
        top5_table = Table(top5_data, colWidths=[0.4*inch, 1.8*inch, 1.3*inch, 0.7*inch, 0.9*inch, 0.9*inch, 0.7*inch])
        top5_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e94560')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('TOPPADDING', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#fff5f5')]),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cccccc')),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('PADDING', (0, 0), (-1, -1), 6),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
        ]))
        
        elements.append(top5_table)
        elements.append(Spacer(1, 0.4*inch))
        
        elements.append(Paragraph("📈 METRIC BREAKDOWNS", heading_style))
        elements.append(Spacer(1, 0.1*inch))
        
        chart1_path = os.path.join(CHARTS_DIR, f'edge_dist_{date_str}.png')
        chart2_path = os.path.join(CHARTS_DIR, f'metrics_comp_{date_str}.png')
        
        create_edge_distribution_chart(picks, chart1_path)
        create_metrics_comparison_chart(picks, chart2_path)
        
        if os.path.exists(chart1_path):
            img1 = Image(chart1_path, width=6*inch, height=3.75*inch)
            elements.append(img1)
            elements.append(Spacer(1, 0.2*inch))
        
        if os.path.exists(chart2_path):
            img2 = Image(chart2_path, width=6*inch, height=2.5*inch)
            elements.append(img2)
            elements.append(Spacer(1, 0.4*inch))
    else:
        elements.append(Paragraph(
            "⚠️ No picks generated for this period.",
            normal_style
        ))
    
    elements.append(Paragraph("🔮 TOMORROW'S GAMES PREVIEW", heading_style))
    elements.append(Spacer(1, 0.1*inch))
    
    tomorrow_games = get_tomorrows_games_preview()
    
    preview_data = [['Matchup', 'Time', 'Spread']]
    for game in tomorrow_games:
        preview_data.append([
            game['matchup'],
            game['time'],
            game['spread']
        ])
    
    preview_table = Table(preview_data, colWidths=[2.5*inch, 1.8*inch, 1.5*inch])
    preview_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0f3460')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('TOPPADDING', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#f0f8ff'), colors.white]),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cccccc')),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('PADDING', (0, 0), (-1, -1), 8)
    ]))
    
    elements.append(preview_table)
    elements.append(Spacer(1, 0.4*inch))
    
    footer = Paragraph(
        f"<i>🔒 Confidential - Taylor Vector Terminal Premium Report | © {datetime.now().year}</i>",
        ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, textColor=colors.grey, alignment=TA_CENTER)
    )
    elements.append(footer)
    
    doc.build(elements, onFirstPage=add_watermark, onLaterPages=add_watermark)
    
    print(f"✅ PDF Report generated: {filepath}")
    
    if send_email and SMTP_USER and EMAIL_LIST:
        send_report_email(filepath, report_date)
    
    return filepath

def send_report_email(pdf_path, report_date):
    """
    Send PDF report via email to subscriber list
    
    Args:
        pdf_path: Path to PDF file
        report_date: Date of the report
    """
    if not SMTP_USER or not SMTP_PASSWORD:
        print("⚠️ Email credentials not configured. Skipping email send.")
        return False
    
    if not EMAIL_LIST or EMAIL_LIST == ['']:
        print("⚠️ No email recipients configured. Skipping email send.")
        return False
    
    try:
        msg = MIMEMultipart()
        msg['From'] = SMTP_USER
        msg['To'] = ', '.join(EMAIL_LIST)
        msg['Subject'] = f"Taylor Vector Terminal - Daily Edge Report ({report_date.strftime('%Y-%m-%d')})"
        
        body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <div style="background: linear-gradient(135deg, #0f3460 0%, #1a1a2e 100%); padding: 30px; text-align: center;">
                    <h1 style="color: white; margin: 0;">⚡ TAYLOR VECTOR TERMINAL ⚡</h1>
                    <p style="color: #e8f4f8; margin-top: 10px;">Daily Edge Report</p>
                </div>
                
                <div style="padding: 30px; background-color: #f8f9fa;">
                    <h2 style="color: #0f3460;">Daily Report - {report_date.strftime('%B %d, %Y')}</h2>
                    
                    <p>Your daily betting edge report is ready!</p>
                    
                    <p style="background-color: #e8f4f8; padding: 15px; border-left: 4px solid #0f3460;">
                        📊 <strong>What's Inside:</strong><br>
                        • Executive Summary with key metrics<br>
                        • Top 5 Betting Edges<br>
                        • TUSG% and PVR Analytics<br>
                        • Visual Charts & Breakdowns<br>
                        • Tomorrow's Games Preview
                    </p>
                    
                    <p>The full report is attached as a PDF. Review the picks and make informed decisions!</p>
                    
                    <div style="text-align: center; margin-top: 30px;">
                        <a href="#" style="background-color: #e94560; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">View Dashboard</a>
                    </div>
                </div>
                
                <div style="background-color: #1a1a2e; padding: 20px; text-align: center; color: #888;">
                    <p style="margin: 0; font-size: 12px;">© {datetime.now().year} Taylor Vector Terminal. All rights reserved.</p>
                </div>
            </body>
        </html>
        """
        
        msg.attach(MIMEText(body, 'html'))
        
        with open(pdf_path, 'rb') as attachment:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())
        
        encoders.encode_base64(part)
        part.add_header(
            'Content-Disposition',
            f'attachment; filename= {os.path.basename(pdf_path)}'
        )
        msg.attach(part)
        
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        text = msg.as_string()
        server.sendmail(SMTP_USER, EMAIL_LIST, text)
        server.quit()
        
        print(f"✅ Email sent to {len(EMAIL_LIST)} recipients")
        return True
        
    except Exception as e:
        print(f"❌ Error sending email: {e}")
        import traceback
        traceback.print_exc()
        return False

def get_recent_reports(limit=10):
    """Get list of recent report files"""
    if not os.path.exists(REPORTS_DIR):
        return []
    
    files = []
    for filename in os.listdir(REPORTS_DIR):
        if filename.startswith('daily_edge_') and filename.endswith('.pdf'):
            filepath = os.path.join(REPORTS_DIR, filename)
            files.append({
                'filename': filename,
                'filepath': filepath,
                'created': os.path.getctime(filepath),
                'size': os.path.getsize(filepath)
            })
    
    files.sort(key=lambda x: x['created'], reverse=True)
    return files[:limit]

if __name__ == '__main__':
    print("🏀 Taylor Vector Terminal - Daily Edge Report Generator")
    print("=" * 60)
    
    print("\nGenerating daily report...")
    filepath = generate_pdf_report(send_email=False)
    print(f"✅ Report generated: {filepath}")
    
    print("\n📄 Recent reports:")
    for report in get_recent_reports(5):
        created_date = datetime.fromtimestamp(report['created'])
        print(f"  - {report['filename']} ({report['size']} bytes) - {created_date.strftime('%Y-%m-%d %H:%M')}")
    
    print("\n" + "=" * 60)
    print("Report generation complete!")
