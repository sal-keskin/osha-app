from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.safestring import mark_safe
from django.utils.html import escape
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from datetime import date, timedelta

class ActionLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Kullanıcı")
    action = models.CharField(max_length=50, verbose_name="İşlem")
    model_name = models.CharField(max_length=100, verbose_name="Veri Türü")
    object_id = models.CharField(max_length=50, null=True, blank=True, verbose_name="Kayıt ID")
    details = models.TextField(null=True, blank=True, verbose_name="Detaylar")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Zaman")

    class Meta:
        ordering = ['-timestamp']
        verbose_name = "İşlem Kaydı"
        verbose_name_plural = "İşlem Kayıtları"

class Profession(models.Model):
    name = models.CharField(max_length=255, unique=True, verbose_name="Meslek Adı")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Meslek"
        verbose_name_plural = "Meslekler"


class Workplace(models.Model):
    HAZARD_CHOICES = [
        ('LOW', 'Az Tehlikeli'),
        ('MEDIUM', 'Tehlikeli'),
        ('HIGH', 'Çok Tehlikeli'),
    ]
    name = models.CharField(max_length=255, verbose_name="İşyeri Adı")
    detsis_number = models.CharField(max_length=50, unique=True, verbose_name="DETSİS No")
    hazard_class = models.CharField(max_length=10, choices=HAZARD_CHOICES, default='LOW', verbose_name="Tehlike Sınıfı")

    def __str__(self):
        return f"{self.name} ({self.detsis_number})"

    class Meta:
        verbose_name = "İşyeri"
        verbose_name_plural = "İşyerleri"

    @property
    def total_workers_count(self):
        # We try to use the annotated value first, fallback to count
        if hasattr(self, 'total_workers'):
            return self.total_workers
        return self.workers.count()

    def get_validity_years(self, type_):
        # type_: 'education' or 'examination'
        if type_ == 'education':
            # HIGH=1, MEDIUM=2, LOW=3
            if self.hazard_class == 'HIGH': return 1
            elif self.hazard_class == 'MEDIUM': return 2
            else: return 3
        elif type_ == 'examination':
            # HIGH=1, MEDIUM=3, LOW=5
            if self.hazard_class == 'HIGH': return 1
            elif self.hazard_class == 'MEDIUM': return 3
            else: return 5
        return 0

    @property
    def valid_education_count_display(self):
        # We need to count workers who have at least one education where date >= today - validity
        # This is expensive if not prefetched. We assume prefetch is done in view.
        today = date.today()
        years = self.get_validity_years('education')
        limit_date = today - timedelta(days=365*years)

        # Check if prefetch cache exists for workers
        if hasattr(self, '_prefetched_objects_cache') and 'workers' in self._prefetched_objects_cache:
            workers = self.workers.all()
        else:
            # Avoid N+1 if not prefetched by fetching IDs only? No, just iterate.
            workers = self.workers.prefetch_related('education_set').all()

        count = 0
        for w in workers:
            # Check education_set
            # If prefetched, use all()
            edus = w.education_set.all()
            # We need ANY education after limit_date?
            # Or the LATEST one must be after limit_date?
            # Usually compliance means "is currently valid", so if you had one 5 years ago and one 1 month ago, you are valid.
            # So ANY education >= limit_date.
            if any(e.date >= limit_date for e in edus):
                count += 1

        return f"{count}/{len(workers)}"

    @property
    def valid_examination_count_display(self):
        today = date.today()
        years = self.get_validity_years('examination')
        limit_date = today - timedelta(days=365*years)

        if hasattr(self, '_prefetched_objects_cache') and 'workers' in self._prefetched_objects_cache:
            workers = self.workers.all()
        else:
            workers = self.workers.prefetch_related('examination_set').all()

        count = 0
        for w in workers:
            exams = w.examination_set.all()
            if any(e.date >= limit_date for e in exams):
                count += 1

        return f"{count}/{len(workers)}"

    @property
    def valid_first_aid_count_display(self):
        today = date.today()
        # Use prefetched workers if available
        if hasattr(self, '_prefetched_objects_cache') and 'workers' in self._prefetched_objects_cache:
            workers = self.workers.all()
        else:
            workers = self.workers.all()

        count = 0
        for w in workers:
            if w.first_aid_certificate and w.first_aid_expiry_date and w.first_aid_expiry_date >= today:
                count += 1

        return f"{count}/{len(workers)} 🏥"


class Facility(models.Model):
    name = models.CharField(max_length=255, verbose_name="Bina/Birim Adı")
    workplace = models.ForeignKey(Workplace, on_delete=models.CASCADE, verbose_name="İşyeri", related_name="facilities")

    def __str__(self):
        return f"{self.name} ({self.workplace.name})"

    class Meta:
        verbose_name = "Bina/Birim"
        verbose_name_plural = "Binalar/Birimler"


class Worker(models.Model):
    GENDER_CHOICES = [
        ('F', 'Kadın'),
        ('M', 'Erkek'),
    ]
    name = models.CharField(max_length=255, verbose_name="Ad Soyad")
    tckn = models.CharField(max_length=11, unique=True, verbose_name="TCKN")
    workplace = models.ForeignKey(Workplace, on_delete=models.CASCADE, related_name="workers", verbose_name="İşyeri")
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, null=True, blank=True, verbose_name="Cinsiyet")
    birth_date = models.DateField(null=True, blank=True, verbose_name="Doğum Tarihi")
    notes = models.TextField(null=True, blank=True, verbose_name="Notlar")
    profession = models.ForeignKey(Profession, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Meslek")
    facility = models.ForeignKey(Facility, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Bina/Birim")

    first_aid_certificate = models.BooleanField(default=False, blank=True, verbose_name="İlkyardım Sertifikası")
    first_aid_expiry_date = models.DateField(null=True, blank=True, verbose_name="Sertifika Bitiş Tarihi")

    def clean(self):
        if self.facility and self.facility.workplace != self.workplace:
            raise ValidationError({'facility': "Seçilen birim, seçilen işyerine ait değil."})

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.tckn})"

    class Meta:
        verbose_name = "Çalışan"
        verbose_name_plural = "Çalışanlar"

    def _get_badge_html(self, type_):
        # type_: 'education' or 'examination'
        if not self.workplace:
            return mark_safe('<span class="badge bg-secondary">İşyeri Yok</span>')

        today = date.today()
        if type_ == 'education':
            years = self.workplace.get_validity_years('education')
            # Education is M2M. Get latest.
            items = self.education_set.all()
        else:
            years = self.workplace.get_validity_years('examination')
            # Examination is FK (reverse). Get latest.
            items = self.examination_set.all()

        if not items:
            return mark_safe('<span class="badge bg-danger">Yok</span>')

        # Find latest date
        latest_item = max(items, key=lambda x: x.date)
        expiry_date = latest_item.date + timedelta(days=365*years)

        if expiry_date >= today:
            return mark_safe(f'<span class="badge bg-success">{expiry_date.strftime("%d.%m.%Y")}</span>')
        else:
            return mark_safe(f'<span class="badge bg-warning text-dark">Gecikmiş ({expiry_date.strftime("%d.%m.%Y")})</span>')

    @property
    def education_status(self):
        return self._get_badge_html('education')

    @property
    def examination_status(self):
        return self._get_badge_html('examination')


class Professional(models.Model):
    ROLE_CHOICES = [
        ('DOCTOR', 'İşyeri Hekimi'),
        ('SPECIALIST', 'İş Güvenliği Uzmanı'),
        ('OTHER_HEALTH', 'Diğer Sağlık Personeli'),
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
    duration = models.PositiveIntegerField(default=4, verbose_name="Süre (Saat)")
    workplace = models.ForeignKey(Workplace, on_delete=models.CASCADE, verbose_name="İşyeri")
    professionals = models.ManyToManyField(Professional, verbose_name="Eğiticiler")
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
    DECISION_CHOICES = [
        ('FIT', 'Çalışmaya Elverişlidir'),
        ('CONDITIONAL', 'Şartlı Olarak Çalışmaya Elverişlidir'),
    ]
    date = models.DateField(verbose_name="Tarih")
    notes = models.TextField(verbose_name="Notlar/Sonuç", blank=True)
    worker = models.ForeignKey(Worker, on_delete=models.CASCADE, verbose_name="Çalışan")
    professional = models.ForeignKey(
        Professional, 
        on_delete=models.PROTECT, 
        limit_choices_to={'role': 'DOCTOR'},
        verbose_name="Hekim"
    )
    decision = models.CharField(max_length=20, choices=DECISION_CHOICES, default='FIT', verbose_name="Karar")
    decision_conditions = models.TextField(null=True, blank=True, verbose_name="Şartlar")

    # Caution Note
    is_caution = models.BooleanField(default=False, verbose_name="Uyarı notu")
    caution_note = models.TextField(null=True, blank=True, verbose_name="Not")

    # Checkups
    tetanus_vaccine = models.BooleanField(default=False, verbose_name="Tetanoz Aşısı Önerildi")
    tetanus_date = models.DateField(null=True, blank=True, verbose_name="Tetanoz Aşısı Tarihi")

    hepatitis_b_vaccine = models.BooleanField(default=False, verbose_name="Hepatit B Aşısı Önerildi")

    biochemistry = models.BooleanField(default=False, verbose_name="Biyokimya")
    hemogram = models.BooleanField(default=False, verbose_name="Hemogram")
    serology = models.BooleanField(default=False, verbose_name="Seroloji")
    sft = models.BooleanField(default=False, verbose_name="SFT")
    audiometry = models.BooleanField(default=False, verbose_name="Odyometri")
    radiology = models.BooleanField(default=False, verbose_name="Radyoloji")

    def __str__(self):
        return f"{self.worker.name} - {self.date}"

    @property
    def caution_icon_html(self):
        if self.is_caution:
            # We store the note in a data attribute for the modal
            # Escape the note to prevent XSS and breaking the HTML attribute
            note = escape(self.caution_note) if self.caution_note else ""
            # Add tooltip title
            from django.utils.text import Truncator
            short_note = Truncator(self.caution_note).chars(50) if self.caution_note else "Uyarı"
            html = f'<a href="#" class="text-warning caution-icon-btn" data-id="{self.id}" data-note="{note}" title="Uyarı: {escape(short_note)}">' \
                   f'<i class="bi bi-exclamation-triangle-fill" style="font-size: 1.2rem;"></i></a>'
            return mark_safe(html)
        return ""
    caution_icon_html.fget.short_description = "Uyarı"

    class Meta:
        verbose_name = "Sağlık Muayenesi"
        verbose_name_plural = "Sağlık Muayeneleri"

class CertificateTemplate(models.Model):
    name = models.CharField(max_length=255, default="Global", verbose_name="Şablon Adı")
    background_image = models.ImageField(upload_to='certificates/', verbose_name="Arkaplan Resmi", null=True, blank=True)
    layout_config = models.JSONField(default=dict, verbose_name="Yerleşim Ayarları", blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Sertifika Şablonu"
        verbose_name_plural = "Sertifika Şablonları"
