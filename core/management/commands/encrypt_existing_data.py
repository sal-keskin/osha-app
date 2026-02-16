from django.core.management.base import BaseCommand
from core.models import Worker, Examination, Facility, Workplace, Professional
from django.db import transaction

class Command(BaseCommand):
    help = 'Encrypts existing plaintext data for Worker, Examination, Facility, Workplace, Professional models'

    def handle(self, *args, **options):
        self.stdout.write("Starting encryption of existing data...")

        # Process List
        models_to_process = [
            (Worker, "workers"),
            (Examination, "examinations"),
            (Facility, "facilities"),
            (Workplace, "workplaces"),
            (Professional, "professionals")
        ]

        with transaction.atomic():
            for model_class, name in models_to_process:
                self.stdout.write(f"Processing {name}...")
                items = model_class.objects.all()
                count = items.count()
                
                for item in items:
                    item.save()
                    self.stdout.write(f"Processed {model_class.__name__} {item.id}", ending='\r')
                
                self.stdout.write(f"\nSuccessfully encrypted {count} {name}.")

