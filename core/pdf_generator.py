import io
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PIL import Image
from django.core.files.storage import default_storage
from django.conf import settings
from .models import CertificateTemplate

def generate_certificate_pdf(education_instance):
    """
    Generates a PDF certificate for all workers in the given education instance.
    Returns a bytes buffer.
    """
    # Register Font
    font_path = os.path.join(settings.BASE_DIR, 'core', 'static', 'fonts', 'DejaVuSans.ttf')
    font_registered = False
    if os.path.exists(font_path):
        try:
            pdfmetrics.registerFont(TTFont('DejaVuSans', font_path))
            font_registered = True
        except Exception as e:
            print(f"Failed to register font: {e}")

    # Get Template
    try:
        template = CertificateTemplate.objects.get(name="Global")
    except CertificateTemplate.DoesNotExist:
        # Fallback or error? For now, empty layout
        template = None

    if not template or not template.background_image:
        # Without a template/image, we can't do much.
        pass

    buffer = io.BytesIO()
    # Assume A4 Landscape for certificates usually
    page_width, page_height = landscape(A4)
    c = canvas.Canvas(buffer, pagesize=(page_width, page_height))

    layout = template.layout_config if template else {}

    # Pre-load image to avoid reading from storage every loop
    bg_image = None
    if template and template.background_image:
        try:
            # reportlab ImageReader accepts file path or file-like object
            # default_storage.open gives a file-like object
            with default_storage.open(template.background_image.name, 'rb') as f:
                img_data = io.BytesIO(f.read())
                bg_image = ImageReader(img_data)
        except Exception as e:
            print(f"Error loading image: {e}")
            bg_image = None

    # Helper to draw text at percentage coordinates
    def draw_text(text, x_percent, y_percent):
        x = (float(x_percent) / 100.0) * page_width
        y = page_height - ((float(y_percent) / 100.0) * page_height)

        if font_registered:
            c.setFont('DejaVuSans', 12)
        else:
            c.setFont('Helvetica', 12) # Fallback, might not support Turkish chars

        c.drawString(x, y - 10, str(text))

    professionals_str = ", ".join([p.name for p in education_instance.professionals.all()])
    workplace_str = education_instance.workplace.name
    date_str = education_instance.date.strftime('%d.%m.%Y')
    duration_str = str(education_instance.duration) + " Saat"

    workers = education_instance.workers.all()
    if not workers:
        # If no workers, just create one empty page or return empty?
        # But we loop workers. If empty, nothing happens.
        pass

    for worker in workers:
        # Draw Background
        if bg_image:
            # Draw image to fit page
            c.drawImage(bg_image, 0, 0, width=page_width, height=page_height)

        # Mapping fields
        data_map = {
            'worker_name': worker.name,
            'worker_tckn': worker.tckn,
            'date': date_str,
            'duration': duration_str,
            'workplace': workplace_str,
            'educators': professionals_str,
            'certificate_no': f"CERT-{education_instance.id}-{worker.id}"
        }

        # Draw Fields
        if layout:
            for field, coords in layout.items():
                if field in data_map:
                    draw_text(data_map[field], coords['x'], coords['y'])

        c.showPage()

    c.save()
    buffer.seek(0)
    return buffer
