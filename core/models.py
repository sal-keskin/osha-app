from django.db import models
from django.utils.translation import gettext_lazy as _

class Workplace(models.Model):
    name = models.CharField(max_length=255, verbose_name="İşyeri Adı")
    detsis_number = models.CharField(max_length=50, unique=True, verbose_name="DETSİS No")

    def __str__(self):
        return f"{self.name} ({self.detsis_number})"

    class Meta:
        verbose_name = "İşyeri"
        verbose_name_plural = "İşyerleri"


class Worker(models.Model):
    name = models.CharField(max_length=255, verbose_name="Ad Soyad")
    tckn = models.CharField(max_length=11, unique=True, verbose_name="TCKN")
    workplace = models.ForeignKey(Workplace, on_delete=models.CASCADE, related_name="workers", verbose_name="İşyeri")

    def __str__(self):
        return f"{self.name} ({self.tckn})"

    class Meta:
        verbose_name = "Çalışan"
        verbose_name_plural = "Çalışanlar"


class Educator(models.Model):
    name = models.CharField(max_length=255, verbose_name="Ad Soyad")
    license_id = models.CharField(max_length=6, unique=True, verbose_name="Lisans No")

    def __str__(self):
        return f"{self.name} ({self.license_id})"

    class Meta:
        verbose_name = "Eğitici"
        verbose_name_plural = "Eğiticiler"


class Professional(models.Model):
    ROLE_CHOICES = [
        ('DOCTOR', 'İşyeri Hekimi'),
        ('SPECIALIST', 'İş Güvenliği Uzmanı'),
    ]
    name = models.CharField(max_length=255, verbose_name="Ad Soyad")
    license_id = models.CharField(max_length=6, unique=True, verbose_name="Lisans No")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, verbose_name="Görevi")

    def __str__(self):
        return f"{self.name} - {self.get_role_display()}"

    class Meta:
        verbose_name = "Profesyonel"
        verbose_name_plural = "Profesyoneller"


class Education(models.Model):
    date = models.DateField(verbose_name="Tarih")
    topic = models.CharField(max_length=255, verbose_name="Konu")
    workplace = models.ForeignKey(Workplace, on_delete=models.CASCADE, verbose_name="İşyeri")
    educator = models.ForeignKey(Educator, on_delete=models.PROTECT, verbose_name="Eğitici")
    workers = models.ManyToManyField(Worker, verbose_name="Katılımcılar")

    def __str__(self):
        return f"{self.topic} - {self.date}"

    class Meta:
        verbose_name = "İSG Eğitimi"
        verbose_name_plural = "İSG Eğitimleri"


class Inspection(models.Model):
    date = models.DateField(verbose_name="Tarih")
    notes = models.TextField(verbose_name="Notlar")
    workplace = models.ForeignKey(Workplace, on_delete=models.CASCADE, verbose_name="İşyeri")
    professional = models.ForeignKey(Professional, on_delete=models.PROTECT, verbose_name="Denetleyen")

    def __str__(self):
        return f"{self.workplace} - {self.date}"

    class Meta:
        verbose_name = "Denetim"
        verbose_name_plural = "Denetimler"


class Examination(models.Model):
    date = models.DateField(verbose_name="Tarih")
    notes = models.TextField(verbose_name="Notlar/Sonuç")
    worker = models.ForeignKey(Worker, on_delete=models.CASCADE, verbose_name="Çalışan")
    professional = models.ForeignKey(
        Professional, 
        on_delete=models.PROTECT, 
        limit_choices_to={'role': 'DOCTOR'},
        verbose_name="Hekim"
    )

    def __str__(self):
        return f"{self.worker.name} - {self.date}"

    class Meta:
        verbose_name = "Sağlık Muayenesi"
        verbose_name_plural = "Sağlık Muayeneleri"
