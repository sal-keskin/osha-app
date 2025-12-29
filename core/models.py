from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.safestring import mark_safe
from datetime import date, timedelta

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
    special_note = models.TextField(blank=True, null=True, verbose_name="Özel Not")

    def __str__(self):
        return f"{self.name} ({self.detsis_number})"

    class Meta:
        verbose_name = "İşyeri"
        verbose_name_plural = "İşyerleri"

    def get_workers_by_facility(self):
        """Returns a dict of facility_name -> [workers] and 'No Facility' -> [workers]"""
        facilities = self.facilities.all()
        workers = self.workers.all().select_related('facility')
        
        grouped = {}
        # Initialize facilities
        for f in facilities:
            grouped[f.name] = []
            
        grouped['Diğer'] = []

        for w in workers:
            if w.facility:
                if w.facility.name not in grouped:
                    grouped[w.facility.name] = [] # Should not happen if prefetched correctly
                grouped[w.facility.name].append(w)
            else:
                grouped['Diğer'].append(w)
        
        # Remove empty facilities if desired? No, user might want to see them.
        return grouped

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


class Facility(models.Model):
    name = models.CharField(max_length=255, verbose_name="Birim Adı")
    workplace = models.ForeignKey(Workplace, on_delete=models.CASCADE, related_name="facilities", verbose_name="İşyeri")

    def __str__(self):
        return f"{self.name} ({self.workplace.name})"

    class Meta:
        verbose_name = "Birim"
        verbose_name_plural = "Birimler"
        unique_together = ('name', 'workplace')


class Worker(models.Model):
    GENDER_CHOICES = [
        ('F', 'Kadın'),
        ('M', 'Erkek'),
    ]
    name = models.CharField(max_length=255, verbose_name="Ad Soyad")
    tckn = models.CharField(max_length=11, unique=True, verbose_name="TCKN")
    workplace = models.ForeignKey(Workplace, on_delete=models.CASCADE, related_name="workers", verbose_name="İşyeri")
    facility = models.ForeignKey(Facility, on_delete=models.SET_NULL, null=True, blank=True, related_name="workers", verbose_name="Birim")
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, null=True, blank=True, verbose_name="Cinsiyet")
    birth_date = models.DateField(null=True, blank=True, verbose_name="Doğum Tarihi")
    notes = models.TextField(null=True, blank=True, verbose_name="Notlar")
    special_note = models.TextField(blank=True, null=True, verbose_name="Özel Not")
    # Storing chronic diseases as comma-separated string for simplicity
    chronic_diseases = models.CharField(max_length=255, null=True, blank=True, verbose_name="Kronik Hastalıklar")
    profession = models.ForeignKey(Profession, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Meslek")

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

    # Checkups
    work_accident = models.BooleanField(default=False, verbose_name="İş Kazası")
    work_accident_date = models.DateField(null=True, blank=True, verbose_name="İş Kazası Tarihi")

    tetanus_vaccine = models.BooleanField(default=False, verbose_name="Tetanoz Aşısı")
    tetanus_date = models.DateField(null=True, blank=True, verbose_name="Tetanoz Aşısı Tarihi")

    hepatitis_b_vaccine = models.BooleanField(default=False, verbose_name="Hepatit B Aşısı")
    hepatitis_b_value = models.CharField(max_length=50, null=True, blank=True, verbose_name="Anti-HbS Değeri")

    biochemistry = models.BooleanField(default=False, verbose_name="Biyokimya")
    hemogram = models.BooleanField(default=False, verbose_name="Hemogram")
    serology = models.BooleanField(default=False, verbose_name="Seroloji")
    sft = models.BooleanField(default=False, verbose_name="SFT")
    audiometry = models.BooleanField(default=False, verbose_name="Odyometri")
    radiology = models.BooleanField(default=False, verbose_name="Radyoloji")

    def __str__(self):
        return f"{self.worker.name} - {self.date}"

    class Meta:
        verbose_name = "Sağlık Muayenesi"
        verbose_name_plural = "Sağlık Muayeneleri"
