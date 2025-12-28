from django.test import TestCase, Client
from django.urls import reverse
from core.models import Workplace, Worker, Educator, Professional, Education, Inspection, Examination
from datetime import date

class ModelTests(TestCase):
    def setUp(self):
        self.workplace = Workplace.objects.create(name="Test İşyeri", detsis_number="12345")
        self.worker = Worker.objects.create(name="Ahmet Yılmaz", tckn="12345678901", workplace=self.workplace)
        self.educator = Educator.objects.create(name="Mehmet Hoca", license_id="111111")
        self.doctor = Professional.objects.create(name="Dr. Ayşe", license_id="222222", role="DOCTOR")
        self.specialist = Professional.objects.create(name="Uzman Ali", license_id="333333", role="SPECIALIST")

    def test_workplace_creation(self):
        self.assertEqual(Workplace.objects.count(), 1)
        self.assertEqual(str(self.workplace), "Test İşyeri (12345)")

    def test_worker_creation(self):
        self.assertEqual(Worker.objects.count(), 1)
        self.assertEqual(self.worker.workplace, self.workplace)

    def test_education_creation(self):
        edu = Education.objects.create(
            date=date.today(),
            topic="İSG Temel Eğitim",
            workplace=self.workplace,
            educator=self.educator
        )
        edu.workers.add(self.worker)
        self.assertEqual(edu.workers.count(), 1)

    def test_inspection_creation(self):
        insp = Inspection.objects.create(
            date=date.today(),
            notes="Her şey yolunda",
            workplace=self.workplace,
            professional=self.specialist
        )
        self.assertEqual(Inspection.objects.count(), 1)

    def test_examination_creation(self):
        exam = Examination.objects.create(
            date=date.today(),
            notes="Sağlam",
            worker=self.worker,
            professional=self.doctor
        )
        self.assertEqual(Examination.objects.count(), 1)

class ViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        # Create a user and login
        from django.contrib.auth.models import User
        self.user = User.objects.create_user(username='testuser', password='password')
        self.client.login(username='testuser', password='password')
        
        self.workplace = Workplace.objects.create(name="Test İşyeri", detsis_number="12345")

    def test_dashboard_access(self):
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_workplace_list_access(self):
        response = self.client.get(reverse('workplace_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test İşyeri")

    def test_login_page(self):
        self.client.logout()
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
