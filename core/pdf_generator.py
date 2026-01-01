import io
import os
from django.conf import settings
from django.template import Template, Context
from xhtml2pdf import pisa
from .models import CertificateTemplate

def generate_certificate_pdf(education_instance):
    """
    Generates a PDF certificate for all workers in the given education instance.
    Returns a bytes buffer.
    """
    # 1. Fetch Template Content
    try:
        template_obj = CertificateTemplate.objects.get(name="Global")
        html_template_str = template_obj.html_content
    except CertificateTemplate.DoesNotExist:
        # Fallback if no template defined
        html_template_str = "<h1>Şablon Bulunamadı</h1>"

    # 2. Register Font via CSS
    # We embed the font face definition in the HTML style
    font_path = os.path.join(settings.BASE_DIR, 'core', 'static', 'fonts', 'DejaVuSans.ttf')

    # xhtml2pdf needs consistent font definition
    # Note: @font-face src must be a file path for xhtml2pdf usually, or url
    # We will prepend this style block to the template
    style_block = f"""
    <style>
        @font-face {{
            font-family: 'DejaVuSans';
            src: url('{font_path}');
        }}
        body {{
            font-family: 'DejaVuSans', sans-serif;
        }}
    </style>
    """

    # 3. Prepare Context for Loop
    professionals_str = ", ".join([p.name for p in education_instance.professionals.all()])
    workplace_str = education_instance.workplace.name
    date_str = education_instance.date.strftime('%d.%m.%Y')
    duration_str = str(education_instance.duration) + " Saat"

    workers = education_instance.workers.all()

    # 4. Generate Combined HTML
    # We will simply concatenate the HTML for each worker, separated by page breaks.
    full_html = f"<html><head><meta charset='utf-8'>{style_block}</head><body>"

    for i, worker in enumerate(workers):
        if i > 0:
            full_html += '<div style="page-break-before: always;"></div>'

        # Map variables
        # We can use Django's Template engine for robust replacement
        context_data = {
            'SAYI': f"{education_instance.id}-{worker.id}",
            'TCKN': worker.tckn,
            'AD_SOYAD': worker.name,
            'TARIH': date_str,
            'SURE': duration_str,
            'IS_YERI': workplace_str,
            'EGITICILER': professionals_str
        }

        t = Template(html_template_str)
        c = Context(context_data)
        rendered_cert = t.render(c)

        full_html += rendered_cert

    full_html += "</body></html>"

    # 5. Convert to PDF
    buffer = io.BytesIO()
    pisa_status = pisa.CreatePDF(
        src=full_html,
        dest=buffer,
        encoding='utf-8'
    )

    if pisa_status.err:
        return io.BytesIO(b"PDF Generation Error")

    buffer.seek(0)
    return buffer
