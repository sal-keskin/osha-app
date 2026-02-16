import io
import os
import logging
from django.conf import settings
from django.template import Template, Context

logger = logging.getLogger(__name__)

# WeasyPrint requires system libraries: pango, cairo, gdk-pixbuf, gobject
# On macOS: brew install pango cairo gdk-pixbuf glib
# If libraries are installed but not found, set DYLD_LIBRARY_PATH
WEASYPRINT_AVAILABLE = False
try:
    from weasyprint import HTML, CSS
    WEASYPRINT_AVAILABLE = True
except OSError as e:
    logger.warning(f"WeasyPrint could not load system libraries: {e}")
    logger.warning("PDF generation will not work. Install: brew install pango cairo gdk-pixbuf glib")
    
    class HTML:
        def __init__(self, *args, **kwargs): 
            pass
        def write_pdf(self, *args, **kwargs): 
            raise RuntimeError("WeasyPrint is not available. Install system dependencies: brew install pango cairo gdk-pixbuf glib")
    class CSS:
        def __init__(self, *args, **kwargs): 
            pass

from .models import CertificateTemplate

def generate_certificate_pdf(education_instance):
    """
    Generates a PDF certificate using WeasyPrint with a hardcoded A4 layout.
    """
    # 1. Fetch Template Settings (Header & Topics)
    try:
        template_obj = CertificateTemplate.objects.get(name="Global")
        institute_name = template_obj.institute_name.replace('\n', '<br>')
        education_topics = template_obj.education_topics.replace('\n', '<br>')
    except CertificateTemplate.DoesNotExist:
        institute_name = "Kurum Adı Girilmedi"
        education_topics = "Konular Girilmedi"

    # 2. Prepare Data
    # Separate professionals by role
    specialist_name = ""
    medic_name = ""

    for p in education_instance.professionals.all():
        if p.role == 'SPECIALIST':
            specialist_name = p.name
        elif p.role in ['DOCTOR', 'OTHER_HEALTH']:
            medic_name = p.name

    # Fallback if filtered incorrectly or empty
    # If multiple, it takes the last one found in loop, but form ensures 1 of each.

    workplace_str = education_instance.workplace.name
    date_str = education_instance.date.strftime('%d.%m.%Y')
    duration_str = str(education_instance.duration) + " Saat"

    workers = education_instance.workers.all()

    # 3. Path to Font - Use Roboto for Turkish character support
    font_path = os.path.join(settings.BASE_DIR, 'static', 'fonts', 'Roboto-Regular.ttf')

    # 4. CSS (Hardcoded Layout)
    css_string = f"""
    @font-face {{
        font-family: 'TurkishFont';
        src: url('file://{font_path}');
    }}
    @page {{
        size: A4;
        margin: 0;
    }}
    body {{
        font-family: 'TurkishFont', sans-serif;
        margin: 0;
        padding: 0;
        background-color: #fff;
    }}
    .page-container {{
        width: 210mm;
        height: 297mm;
        position: relative;
        page-break-after: always;
        overflow: hidden;
        box-sizing: border-box;
        padding: 20mm;
    }}
    .border-box {{
        width: 100%;
        height: 100%;
        border: 5px solid #5d7083;
        padding: 20px;
        box-sizing: border-box;
        position: relative;
    }}
    .header {{
        text-align: center;
        color: #c62828;
        font-size: 10pt;
        font-weight: bold;
        margin-bottom: 20px;
        line-height: 1.4;
    }}
    .title {{
        text-align: center;
        color: #1f3a58;
        font-size: 32pt;
        margin-bottom: 30px;
        letter-spacing: 2px;
        font-weight: bold;
    }}
    .info-section {{
        margin-bottom: 30px;
        padding-left: 20px;
        font-size: 12pt;
        line-height: 1.6;
        font-weight: bold;
    }}
    .worker-name {{
        text-align: center;
        border-bottom: 1px solid #000;
        width: 70%;
        margin: 0 auto 20px auto;
        font-size: 18pt;
        font-weight: bold;
        padding-bottom: 5px;
    }}
    .body-text {{
        text-align: center;
        font-size: 11pt;
        color: #444;
        margin-bottom: 20px;
        padding: 0 20px;
        line-height: 1.4;
    }}
    .topics-title {{
        text-align: center;
        font-weight: bold;
        font-size: 12pt;
        margin-bottom: 10px;
        font-variant: small-caps;
    }}
    .separator {{
        text-align: center;
        color: #fdd835;
        margin-bottom: 15px;
        font-size: 20px;
    }}
    .topics-list {{
        font-size: 9pt;
        line-height: 1.3;
        text-align: left;
        margin-bottom: 30px;
        column-count: 2;
        column-gap: 20px;
    }}
    .signatures {{
        width: 100%;
        margin-top: 40px;
    }}
    .signature-box {{
        width: 33%;
        float: left;
        text-align: center;
        font-size: 10pt;
        color: #555;
        vertical-align: bottom;
    }}
    .signature-line {{
        border-top: 1px solid #555;
        width: 90%;
        margin: 0 auto;
        padding-top: 5px;
    }}
    """

    # 5. Build HTML
    full_html = "<html><head><meta charset='utf-8'></head><body>"

    for worker in workers:
        full_html += f"""
        <div class="page-container">
            <div class="border-box">
                <div class="header">
                    {institute_name}
                </div>

                <div class="title">
                    EĞİTİM BELGESİ
                </div>

                <div class="info-section">
                    Sayı &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;: {education_instance.id}-{worker.id}<br>
                    TCKN &nbsp;&nbsp;: {worker.tckn}<br>
                    Tarih &nbsp;&nbsp;&nbsp;: {date_str}<br>
                    Süre &nbsp;&nbsp;&nbsp;&nbsp;: {duration_str}<br>
                    İş Yeri : {workplace_str}
                </div>

                <div class="worker-name">
                    {worker.name}
                </div>

                <div class="body-text">
                    Yukarıda adı geçen çalışan,<br>
                    Çalışanların İş Sağlığı ve Güvenliği Eğitimlerinin Usul ve Esasları Hakkında Yönetmelik
                    kapsamında verilen örgün <strong>İş Sağlığı ve Güvenliği Eğitimini</strong> başarıyla tamamlayarak bu
                    belgeyi almaya hak kazanmıştır.
                </div>

                <div class="topics-title">
                    Eğitim Konuları
                </div>

                <div class="separator">
                    ~ ☚ ~
                </div>

                <div class="topics-list">
                    {education_topics}
                </div>

                <div class="signatures">
                    <div class="signature-box">
                        <div class="signature-line">
                            İş Güvenliği Uzmanı<br>
                            {specialist_name}
                        </div>
                    </div>
                    <div class="signature-box">
                        <div class="signature-line">
                            İş Yeri Hekimi/Hemşiresi<br>
                            {medic_name}
                        </div>
                    </div>
                    <div class="signature-box">
                        <div class="signature-line">
                            İşveren/İşveren Vekili
                        </div>
                    </div>
                </div>
            </div>
        </div>
        """

    full_html += "</body></html>"

    # 6. Convert to PDF
    buffer = io.BytesIO()
    HTML(string=full_html, base_url=str(settings.BASE_DIR)).write_pdf(target=buffer, stylesheets=[CSS(string=css_string)])

    buffer.seek(0)
    return buffer


def generate_participation_form_pdf(education_instance):
    """
    Generates a participation form PDF for an education session.
    This form is used to collect wet signatures from workers.
    """
    # 1. Fetch Template Settings (Header & Topics)
    try:
        template_obj = CertificateTemplate.objects.get(name="Global")
        institute_name = template_obj.institute_name.replace('\n', '<br>')
        education_topics = template_obj.education_topics.replace('\n', '</li><li>')
        education_topics = f"<li>{education_topics}</li>"
    except CertificateTemplate.DoesNotExist:
        institute_name = "Kurum Adı Girilmedi"
        education_topics = "<li>Eğitim konuları girilmedi</li>"

    # 2. Prepare Data - Separate specialist and medic
    specialist_name = ""
    medic_name = ""
    
    for p in education_instance.professionals.all():
        if p.role == 'SPECIALIST':
            specialist_name = p.name
        elif p.role in ['DOCTOR', 'OTHER_HEALTH']:
            medic_name = p.name

    workplace_str = education_instance.workplace.name
    date_str = education_instance.date.strftime('%d %B %Y').replace(
        'January', 'Ocak').replace('February', 'Şubat').replace('March', 'Mart'
        ).replace('April', 'Nisan').replace('May', 'Mayıs').replace('June', 'Haziran'
        ).replace('July', 'Temmuz').replace('August', 'Ağustos').replace('September', 'Eylül'
        ).replace('October', 'Ekim').replace('November', 'Kasım').replace('December', 'Aralık')
    duration_str = f"{education_instance.duration} Saat"
    topic_title = education_instance.topic.upper()

    workers = education_instance.workers.all().select_related('facility', 'profession')

    # 3. Path to Font
    font_path = os.path.join(settings.BASE_DIR, 'static', 'fonts', 'Roboto-Regular.ttf')
    font_bold_path = os.path.join(settings.BASE_DIR, 'static', 'fonts', 'Roboto-Bold.ttf')

    # 4. CSS - Optimized for single page
    css_string = f"""
    @font-face {{
        font-family: 'TurkishFont';
        src: url('file://{font_path}');
    }}
    @font-face {{
        font-family: 'TurkishFontBold';
        src: url('file://{font_bold_path}');
        font-weight: bold;
    }}
    @page {{
        size: A4;
        margin: 12mm;
    }}
    body {{
        font-family: 'TurkishFont', sans-serif;
        font-size: 9pt;
        line-height: 1.3;
        color: #333;
    }}
    .header {{
        text-align: center;
        margin-bottom: 10px;
    }}
    .main-title {{
        color: #1565C0;
        font-size: 14pt;
        font-weight: bold;
        font-family: 'TurkishFontBold', sans-serif;
        margin-bottom: 3px;
    }}
    .sub-title {{
        color: #1565C0;
        font-size: 9pt;
    }}
    .section-header {{
        background: #1565C0;
        color: white;
        padding: 5px 10px;
        font-weight: bold;
        font-size: 9pt;
        margin-top: 8px;
        margin-bottom: 0;
    }}
    .info-box {{
        border: 1px solid #1565C0;
        border-top: none;
        padding: 8px 10px;
        margin-bottom: 8px;
        font-size: 9pt;
    }}
    .info-row {{
        margin-bottom: 2px;
    }}
    .info-label {{
        font-weight: bold;
    }}
    .topics-box {{
        border: 1px solid #1565C0;
        border-top: none;
        padding: 8px 10px;
        margin-bottom: 8px;
    }}
    .topics-list {{
        margin: 0;
        padding-left: 15px;
        column-count: 2;
        column-gap: 20px;
        font-size: 8pt;
        line-height: 1.2;
    }}
    .topics-list li {{
        margin-bottom: 1px;
    }}
    .participants-table {{
        width: 100%;
        border-collapse: collapse;
        margin-bottom: 8px;
        font-size: 8pt;
    }}
    .participants-table th {{
        background: #1565C0;
        color: white;
        padding: 4px 8px;
        text-align: left;
        font-weight: bold;
        border: 1px solid #1565C0;
    }}
    .participants-table td {{
        padding: 4px 8px;
        border: 1px solid #ccc;
        vertical-align: middle;
    }}
    .participants-table tr:nth-child(even) {{
        background: #f9f9f9;
    }}
    .signature-col {{
        width: 100px;
    }}
    .note-box {{
        background: #FFF9C4;
        border-left: 3px solid #FBC02D;
        padding: 6px 10px;
        margin: 10px 0;
        font-size: 7pt;
    }}
    .note-title {{
        font-weight: bold;
        color: #C62828;
        margin-bottom: 2px;
    }}
    .signatures-row {{
        display: table;
        width: 100%;
        margin-top: 15px;
    }}
    .signature-block {{
        display: table-cell;
        width: 33.33%;
        text-align: center;
        vertical-align: top;
        padding: 0 10px;
    }}
    .signature-line {{
        border-top: 1px solid #333;
        width: 80%;
        margin: 0 auto 5px auto;
    }}
    .signature-title {{
        font-weight: bold;
        font-size: 8pt;
    }}
    .signature-name {{
        color: #1565C0;
        font-style: italic;
        font-size: 8pt;
    }}
    """

    # 5. Build participant rows with masked TCKN
    participant_rows = ""
    for idx, worker in enumerate(workers, 1):
        # Mask TCKN (show first 3 and last 3 digits)
        tckn = str(worker.tckn) if worker.tckn else "---"
        if len(tckn) >= 11:
            masked_tckn = tckn[:3] + "*****" + tckn[-3:]
        else:
            masked_tckn = tckn
        
        participant_rows += f"""
        <tr>
            <td style="text-align: center; width: 30px;">{idx}</td>
            <td>{worker.name}</td>
            <td>{masked_tckn}</td>
            <td class="signature-col"></td>
        </tr>
        """

    # 6. Build HTML
    full_html = f"""
    <html>
    <head><meta charset='utf-8'></head>
    <body>
        <div class="header">
            <div class="main-title">{topic_title} KATILIM FORMU</div>
            <div class="sub-title">{institute_name}</div>
        </div>

        <div class="section-header">1. EĞİTİM BİLGİLERİ</div>
        <div class="info-box">
            <div class="info-row"><span class="info-label">Tarih:</span> {date_str} &nbsp;&nbsp;&nbsp;&nbsp; <span class="info-label">Süre:</span> {duration_str}</div>
            <div class="info-row"><span class="info-label">Bölüm:</span> {workplace_str}</div>
            <div class="info-row"><span class="info-label">Eğitimi Veren:</span> {", ".join(filter(None, [specialist_name, medic_name])) or '-'}</div>
        </div>

        <div class="section-header">2. EĞİTİM KONULARI</div>
        <div class="topics-box">
            <ul class="topics-list">
                {education_topics}
            </ul>
        </div>

        <div class="section-header">3. KATILIMCILAR</div>
        <table class="participants-table">
            <thead>
                <tr>
                    <th style="width: 30px;">Sıra</th>
                    <th>Ad Soyad</th>
                    <th>TCKN</th>
                    <th class="signature-col">İmza</th>
                </tr>
            </thead>
            <tbody>
                {participant_rows}
            </tbody>
        </table>

        <div class="note-box">
            <div class="note-title">NOT:</div>
            Bu form, 6331 sayılı İş Sağlığı ve Güvenliği Kanunu kapsamında düzenlenmiştir.
            Eğitime katılan tüm personelin imza atması zorunludur.
            Form, en az 5 yıl süreyle saklanmalıdır.
        </div>

        <div class="signatures-row">
            <div class="signature-block">
                <div class="signature-line"></div>
                <div class="signature-title">İş Güvenliği Uzmanı</div>
                <div class="signature-name">{specialist_name or '_____________'}</div>
            </div>
            <div class="signature-block">
                <div class="signature-line"></div>
                <div class="signature-title">İşyeri Hekimi</div>
                <div class="signature-name">{medic_name or '_____________'}</div>
            </div>
            <div class="signature-block">
                <div class="signature-line"></div>
                <div class="signature-title">İşveren / Vekili</div>
                <div class="signature-name">_____________</div>
            </div>
        </div>
    </body>
    </html>
    """

    # 7. Convert to PDF
    buffer = io.BytesIO()
    HTML(string=full_html, base_url=str(settings.BASE_DIR)).write_pdf(target=buffer, stylesheets=[CSS(string=css_string)])

    buffer.seek(0)
    return buffer
