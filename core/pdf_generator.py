import io
import os
from django.conf import settings
from django.template import Template, Context
from weasyprint import HTML, CSS
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
    professionals_str = ", ".join([p.name for p in education_instance.professionals.all()])
    workplace_str = education_instance.workplace.name
    date_str = education_instance.date.strftime('%d.%m.%Y')
    duration_str = str(education_instance.duration) + " Saat"

    workers = education_instance.workers.all()

    # 3. Path to Font
    font_path = os.path.join(settings.BASE_DIR, 'core', 'static', 'fonts', 'DejaVuSans.ttf')

    # 4. CSS (Hardcoded Layout)
    # We use @page to ensure A4 size.
    # We embed the font via file:// URL.
    css_string = f"""
    @font-face {{
        font-family: 'DejaVuSans';
        src: url('file://{font_path}');
    }}
    @page {{
        size: A4;
        margin: 0;
    }}
    body {{
        font-family: 'DejaVuSans', sans-serif;
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
                    Say &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;: {education_instance.id}-{worker.id}<br>
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
                            {professionals_str}
                        </div>
                    </div>
                    <div class="signature-box">
                        <div class="signature-line">
                            İş Yeri Hekimi/Hemşiresi
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
