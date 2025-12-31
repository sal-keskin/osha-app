import os
import django
from django.conf import settings

# Configure settings manually if not already configured
if not settings.configured:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'osha_app.settings')
    django.setup()

from core.pdf_generator import generate_certificate_pdf
from core.models import CertificateTemplate
import io

# Mock Objects
class MockProfessional:
    name = "Dr. Test Instructor (İşgücü)" # Turkish chars

class MockWorkplace:
    name = "Test Workplace (Şantiye)"

class MockWorker:
    id = 1
    name = "Test Worker (Öğrenci)"
    tckn = "12345678901"

class MockEducation:
    id = 99
    duration = 4

    class ProfessionalsMgr:
        def all(self): return [MockProfessional()]

    class WorkersMgr:
        def all(self): return [MockWorker()]

    professionals = ProfessionalsMgr()
    workers = WorkersMgr()
    workplace = MockWorkplace()

    from datetime import date
    date = date(2023, 1, 1)

def test():
    # Now we can use real models or mocks
    try:
        # Create a dummy template to trigger text drawing
        CertificateTemplate.objects.get_or_create(name="Global", defaults={'layout_config': {'worker_name': {'x': 10, 'y': 10}}})

        pdf_buffer = generate_certificate_pdf(MockEducation())
        if pdf_buffer and len(pdf_buffer.getvalue()) > 0:
            print("PDF Generated Successfully. Size:", len(pdf_buffer.getvalue()))

            # Optional: Check if font was embedded (simple string check)
            content = pdf_buffer.getvalue()
            if b'DejaVuSans' in content:
                print("DejaVuSans font found in PDF.")
            else:
                print("WARNING: DejaVuSans font NOT found in PDF.")

        else:
            print("PDF Generation Failed (Empty)")
    except Exception as e:
        print("Error:", e)
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test()
