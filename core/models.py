from django.db import models
from encrypted_model_fields.fields import EncryptedCharField, EncryptedTextField, EncryptedDateField, EncryptedBooleanField
from django.utils.translation import gettext_lazy as _
from django.utils.safestring import mark_safe
from django.utils.html import escape
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from datetime import date, timedelta
from uuid import uuid4

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
    name = EncryptedCharField(max_length=255, verbose_name="İş Yeri Unvanı")
    address = EncryptedTextField(verbose_name="Adres", default="")
    detsis_number = EncryptedCharField(max_length=50, verbose_name="SGK Sicil No / DETSİS No")
    sgk_sicil_no = EncryptedCharField(max_length=50, blank=True, verbose_name="SGK Sicil No (İBYS)", help_text="26 haneli SGK sicil numarası")
    nace_code = EncryptedCharField(max_length=20, null=True, blank=True, verbose_name="NACE Kodu")
    activity_description = EncryptedTextField(null=True, blank=True, verbose_name="Faaliyet Tanımı")
    hazard_class = models.CharField(max_length=10, choices=HAZARD_CHOICES, default='LOW', verbose_name="Tehlike Sınıfı")
    employer_representative = EncryptedCharField(max_length=255, verbose_name="İşveren Vekili", default="")
    phone_number = EncryptedCharField(max_length=20, null=True, blank=True, verbose_name="İletişim Numarası")

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

    @property
    def contact_html(self):
        if not self.phone_number:
            return ""

        # Clean number for links
        clean_num = ''.join(filter(str.isdigit, self.phone_number))

        html = f"""
        <a href="tel:{clean_num}" class="text-decoration-none me-2" title="Ara">
            <i class="bi bi-telephone-fill"></i> {self.phone_number}
        </a>
        <a href="https://wa.me/{clean_num}" target="_blank" class="text-success text-decoration-none" title="WhatsApp">
            <i class="bi bi-whatsapp"></i>
        </a>
        """
        return mark_safe(html)


class Facility(models.Model):
    name = EncryptedCharField(max_length=255, verbose_name="Bina/Birim Adı")
    workplace = models.ForeignKey(Workplace, on_delete=models.CASCADE, verbose_name="İşyeri", related_name="facilities")
    address = EncryptedTextField(null=True, blank=True, verbose_name="Adres")
    coordinates = EncryptedCharField(max_length=100, null=True, blank=True, verbose_name="Koordinatlar", help_text="Örn: 39.6425, 27.9152")
    uuid = models.UUIDField(default=uuid4, unique=True, editable=False, verbose_name="Benzersiz Kimlik")

    def __str__(self):
        return f"{self.name} ({self.workplace.name})"

    class Meta:
        verbose_name = "Bina/Birim"
        verbose_name_plural = "Binalar/Birimler"

    def get_participation_url(self):
        """Returns the public participation forum URL for this facility"""
        from django.conf import settings
        base_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')
        return f"{base_url}/voice/{self.uuid}/"

    @property
    def location_link_html(self):
        if self.coordinates:
            query = self.coordinates.replace(" ", "")
            url = f"https://www.google.com/maps/search/?api=1&query={query}"
            return mark_safe(f'<a href="{url}" target="_blank" class="btn btn-sm btn-outline-primary"><i class="bi bi-geo-alt-fill"></i> Harita</a>')
        return ""
    location_link_html.fget.short_description = "Konum"


class SafetyEngagement(models.Model):
    """Worker safety feedback and engagement submissions"""
    TOPIC_CHOICES = [
        ('SUGGESTION', 'Öneri'),
        ('NEAR_MISS', 'Ramak Kala'),
        ('HAZARD', 'Tehlike'),
        ('COMPLAINT', 'Şikayet'),
    ]
    
    STATUS_CHOICES = [
        ('PENDING', 'Beklemede'),
        ('APPROVED', 'Onaylandı'),
        ('REJECTED', 'Reddedildi'),
    ]
    
    facility = models.ForeignKey(Facility, on_delete=models.CASCADE, related_name="safety_engagements", verbose_name="Birim")
    worker = models.ForeignKey('Worker', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Çalışan")
    topic = models.CharField(max_length=20, choices=TOPIC_CHOICES, verbose_name="Konu")
    message = models.TextField(verbose_name="Mesaj")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='APPROVED', verbose_name="Durum")
    
    is_anonymous = models.BooleanField(default=False, verbose_name="Anonim mi?")
    is_public_on_wall = models.BooleanField(default=False, verbose_name="Panoda Göster")
    likes = models.IntegerField(default=0, verbose_name="Beğeni Sayısı")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma Tarihi")
    resolved_at = models.DateTimeField(null=True, blank=True, verbose_name="Çözüm Tarihi")
    
    def __str__(self):
        return f"{self.get_topic_display()} - {self.facility.name} ({self.created_at.strftime('%d.%m.%Y')})"
    
    @property
    def has_expert_comment(self):
        """Check if there's a professional comment"""
        return self.comments.filter(is_professional=True).exists()
    
    @property
    def latest_expert_comment(self):
        """Get the most recent professional comment"""
        return self.comments.filter(is_professional=True).order_by('-created_at').first()
    
    @property
    def management_response(self):
        """Backwards compatibility: return latest management comment text"""
        latest = self.comments.filter(is_professional=True).order_by('-created_at').first()
        return latest.text if latest else ""
    
    class Meta:
        verbose_name = "Güvenlik Bildirimi"
        verbose_name_plural = "Güvenlik Bildirimleri"
        ordering = ['-created_at']


class EngagementComment(models.Model):
    """Threaded comments for safety engagements"""
    engagement = models.ForeignKey(SafetyEngagement, on_delete=models.CASCADE, related_name="comments", verbose_name="Bildirim")
    author_name = models.CharField(max_length=100, verbose_name="Yazar")
    text = models.TextField(verbose_name="Yorum")
    is_professional = models.BooleanField(default=False, verbose_name="Uzman mı?")
    is_public_on_voice = models.BooleanField(default=False, verbose_name="Voice'da Göster")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma Tarihi")
    
    def __str__(self):
        badge = "👨‍⚕️" if self.is_professional else "💬"
        return f"{badge} {self.author_name}: {self.text[:30]}..."
    
    class Meta:
        verbose_name = "Yorum"
        verbose_name_plural = "Yorumlar"
        ordering = ['created_at']


class SafetyPoll(models.Model):
    """Polls for worker engagement"""
    facility = models.ForeignKey(Facility, on_delete=models.CASCADE, related_name="safety_polls", verbose_name="Birim")
    question = models.CharField(max_length=500, verbose_name="Soru")
    options = models.JSONField(default=list, verbose_name="Seçenekler")  # e.g., ['Evet', 'Hayır']
    votes = models.JSONField(default=dict, verbose_name="Oylar")  # e.g., {'Evet': 12, 'Hayır': 5}
    is_active = models.BooleanField(default=True, verbose_name="Aktif")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma Tarihi")
    
    def __str__(self):
        status = "✓" if self.is_active else "✗"
        return f"[{status}] {self.question[:50]}..."
    
    def get_total_votes(self):
        return sum(self.votes.values()) if self.votes else 0
    
    def get_percentages(self):
        """Return dict of option -> percentage"""
        total = self.get_total_votes()
        if total == 0:
            return {opt: 0 for opt in self.options}
        return {opt: round((self.votes.get(opt, 0) / total) * 100) for opt in self.options}
    
    class Meta:
        verbose_name = "Güvenlik Anketi"
        verbose_name_plural = "Güvenlik Anketleri"
        ordering = ['-created_at']


class Worker(models.Model):
    GENDER_CHOICES = [
        ('F', 'Kadın'),
        ('M', 'Erkek'),
    ]
    name = EncryptedCharField(max_length=255, verbose_name="Ad Soyad")
    tckn = EncryptedCharField(max_length=11, verbose_name="TCKN")  # unique removed for encryption
    workplace = models.ForeignKey(Workplace, on_delete=models.CASCADE, related_name="workers", verbose_name="İşyeri")
    gender = EncryptedCharField(max_length=10, choices=GENDER_CHOICES, null=True, blank=True, verbose_name="Cinsiyet")
    birth_date = EncryptedDateField(null=True, blank=True, verbose_name="Doğum Tarihi")
    notes = EncryptedTextField(null=True, blank=True, verbose_name="Notlar")
    profession = models.ForeignKey(Profession, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Meslek")
    facility = models.ForeignKey(Facility, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Bina/Birim")

    first_aid_certificate = EncryptedBooleanField(default=False, blank=True, verbose_name="İlkyardım Sertifikası")
    # first_aid_expiry_date kept plaintext? User didn't specify. Assuming plaintext or encrypt if "personal certification details".
    # User said "certification details". Let's encrypt expiry too to be safe/consistent?
    # User list: `first_aid_certificate`. Didn't explicitly list `first_aid_expiry_date`. 
    # But logic: encrypting cert status but showing date leaks existence. 
    # Use judgement: Keep plaintext unless specified? Or Encrypt?
    # User instruction: "Expand encryption into personal and certification details."
    # I will encrypt `first_aid_expiry_date` as well to be safe, using EncryptedDateField.
    first_aid_expiry_date = EncryptedDateField(null=True, blank=True, verbose_name="Sertifika Bitiş Tarihi")

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

        # Filter out items with None dates to prevent crashes
        valid_items = [item for item in items if item.date is not None]
        
        if not valid_items:
            return mark_safe('<span class="badge bg-danger">Yok</span>')

        # Find latest date
        latest_item = max(valid_items, key=lambda x: x.date)
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
    SERTIFIKA_TIPI_CHOICES = [
        (1, 'İş Güvenliği Uzmanı'),
        (2, 'İşyeri Hekimi'),
    ]
    name = EncryptedCharField(max_length=255, verbose_name="Ad Soyad")
    tckn = EncryptedCharField(max_length=11, verbose_name="TCKN", help_text="11 haneli TC Kimlik Numarası")
    license_id = EncryptedCharField(max_length=6, verbose_name="Lisans No")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, verbose_name="Görevi")

    def __str__(self):
        return f"{self.name} - {self.get_role_display()}"

    class Meta:
        verbose_name = "Profesyonel"
        verbose_name_plural = "Profesyoneller"

    @property
    def sertifika_tipi(self):
        """Returns İBYS sertifikaTipi: 1=İSG Uzmanı, 2=İşyeri Hekimi"""
        if self.role == 'SPECIALIST':
            return 1
        elif self.role in ['DOCTOR', 'OTHER_HEALTH']:
            return 2
        return None


# İBYS Education Subject Codes (Ministry Reference List)
class EducationSubjects(models.TextChoices):
    # Genel Konular (100 serisi)
    LEGISLATION = '110', '110 - Çalışma mevzuatı ile ilgili bilgiler'
    RIGHTS = '120', '120 - Çalışanların yasal hak ve sorumlulukları'
    CLEANING = '130', '130 - İşyeri temizliği ve düzeni'
    LEGAL_RESULTS = '140', '140 - İş kazası ve meslek hastalığından doğan hukuki sonuçlar'
    # Sağlık Konuları (200 serisi)
    DISEASE_CAUSES = '210', '210 - Meslek hastalıklarının sebepleri'
    DISEASE_PREV = '220', '220 - Hastalıktan korunma prensipleri'
    RISK_FACTORS = '230', '230 - Biyolojik ve psikososyal risk etmenleri'
    FIRST_AID = '240', '240 - İlkyardım'
    TOBACCO = '250', '250 - Tütün ürünlerinin zararları'
    # Teknik Konular (300 serisi)
    CHEMICAL_PHYS = '310', '310 - Kimyasal, fiziksel ve ergonomik riskler'
    MANUAL_HANDLING = '320', '320 - Elle kaldırma ve taşıma'
    FIRE = '330', '330 - Parlama, patlama, yangın ve korunma'
    EQUIPMENT = '340', '340 - İş ekipmanlarının güvenli kullanımı'
    SCREEN = '350', '350 - Ekranlı araçlarla çalışma'
    ELECTRICITY = '360', '360 - Elektrik tehlikeleri, riskleri ve önlemleri'
    ACCIDENT_PREV = '370', '370 - İş kazalarının sebepleri ve korunma'
    SIGNS = '380', '380 - Güvenlik ve sağlık işaretleri'
    PPE = '390', '390 - Kişisel koruyucu donanım kullanımı'
    GENERAL_RULES = '395', '395 - İSG genel kuralları ve güvenlik kültürü'
    EVACUATION = '399', '399 - Tahliye ve kurtarma'


class Education(models.Model):
    # İBYS Location choices (egitimYeri)
    LOCATION_CHOICES = [
        (1, 'İş Yerinde'),
        (0, 'İş Yeri Dışında'),
    ]
    # İBYS Method choices (egitimYontemi)
    METHOD_CHOICES = [
        (1, 'Yüz Yüze Eğitim'),
        (0, 'Uzaktan Eğitim'),
    ]
    
    date = models.DateField(verbose_name="Tarih")
    topic = models.CharField(max_length=255, verbose_name="Konu Başlığı", blank=True, help_text="Genel eğitim başlığı (opsiyonel)")
    duration = models.PositiveIntegerField(default=8, verbose_name="Süre (Saat)", help_text="Toplam eğitim süresi")
    workplace = models.ForeignKey(Workplace, on_delete=models.CASCADE, verbose_name="İşyeri")
    professionals = models.ManyToManyField(Professional, verbose_name="Eğiticiler")
    workers = models.ManyToManyField(Worker, verbose_name="Katılımcılar")
    
    # İBYS Fields
    egitim_yeri = models.IntegerField(choices=LOCATION_CHOICES, default=1, verbose_name="Eğitim Yeri")
    egitim_yontemi = models.IntegerField(choices=METHOD_CHOICES, default=1, verbose_name="Eğitim Yöntemi")

    def __str__(self):
        return f"{self.topic or 'İSG Eğitimi'} - {self.date}"

    class Meta:
        verbose_name = "İSG Eğitimi"
        verbose_name_plural = "İSG Eğitimleri"

    @property
    def duration_minutes(self):
        """Returns duration in minutes for İBYS API (egitimSuresi)"""
        return self.duration * 60
    
    @property
    def total_topic_minutes(self):
        """Total duration from all topics in minutes"""
        return sum(t.duration_minutes for t in self.education_topics.all())
    
    def get_ibys_date(self):
        """Returns date in İBYS format (dd.MM.yyyy)"""
        return self.date.strftime('%d.%m.%Y')


class EducationTopic(models.Model):
    """Through model for education topics with individual durations (İBYS egitimKodu + egitimSuresi)"""
    education = models.ForeignKey(Education, on_delete=models.CASCADE, related_name='education_topics', verbose_name="Eğitim")
    topic_code = models.CharField(max_length=3, choices=EducationSubjects.choices, verbose_name="Eğitim Kodu")
    duration_minutes = models.PositiveIntegerField(default=30, verbose_name="Süre (Dakika)")
    
    class Meta:
        verbose_name = "Eğitim Konusu"
        verbose_name_plural = "Eğitim Konuları"
        unique_together = ['education', 'topic_code']  # Each topic can only appear once per education
    
    def __str__(self):
        return f"{self.get_topic_code_display()} - {self.duration_minutes} dk"
    
    @property
    def duration_hours(self):
        """Returns duration in hours (for display)"""
        return round(self.duration_minutes / 60, 2)


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
    date = EncryptedDateField(verbose_name="Tarih")
    notes = EncryptedTextField(verbose_name="Notlar/Sonuç", blank=True)
    worker = models.ForeignKey(Worker, on_delete=models.CASCADE, verbose_name="Çalışan")
    professional = models.ForeignKey(
        Professional, 
        on_delete=models.PROTECT, 
        limit_choices_to={'role': 'DOCTOR'},
        verbose_name="Hekim"
    )
    decision = EncryptedCharField(max_length=50, choices=DECISION_CHOICES, default='FIT', verbose_name="Karar")
    decision_conditions = EncryptedTextField(null=True, blank=True, verbose_name="Şartlar")

    # Caution Note
    is_caution = EncryptedBooleanField(default=False, verbose_name="Uyarı notu")
    caution_note = EncryptedTextField(null=True, blank=True, verbose_name="Not")

    # Checkups (all encrypted for KVKK)
    tetanus_vaccine = EncryptedBooleanField(default=False, verbose_name="Tetanoz Aşısı Önerildi")

    # REMOVED: tetanus_date

    hepatitis_b_vaccine = EncryptedBooleanField(default=False, verbose_name="Hepatit B Aşısı Önerildi")

    biochemistry = EncryptedBooleanField(default=False, verbose_name="Biyokimya")
    hemogram = EncryptedBooleanField(default=False, verbose_name="Hemogram")
    serology = EncryptedBooleanField(default=False, verbose_name="Seroloji")
    sft = EncryptedBooleanField(default=False, verbose_name="SFT")
    audiometry = EncryptedBooleanField(default=False, verbose_name="Odyometri")
    radiology = EncryptedBooleanField(default=False, verbose_name="Radyoloji")

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

DEFAULT_INSTITUTE = "T.C. Sağlık Bakanlığı\\nBalıkesir İl Sağlık Müdürlüğü\\nKaresi Çalışan Sağlığı Merkezi"
DEFAULT_TOPICS = """Çalışma mevzuatı ile ilgili bilgiler
Çalışanların yasal hak ve sorumlulukları
İş yeri temizliği ve düzeni
İş kazası ve meslek hastalıklarından doğan hukuki sonuçlar
Meslek hastalıklarının sebebi
Hastalıktan korunma prensip ve tekniklerinin uygulanması
Biyolojik ve psikososyal risk etmenleri
İlk yardım
Tütün ürünlerinin zararları ve pasif etkilenim
Kimyasal fiziksel risk etmenleri
Elle kaldırma taşıma
Patlama, patlama, yangın ve yangından korunma
İş ekipmanlarının güvenli kullanımı
Ekranlı araçlarla çalışma
Elektrik tehlikeleri riskleri ve önlemleri
İş kazası sebepleri ve korunma prensipleri ile tekniklerinin uygulanması
Güvenlik ve sağlık işaretleri
Kişisel koruyucu donanımın kullanımı
İş sağlığı ve güvenliği genel kuralları ve güvenlik kültürü
Tahliye kurtarma
Yüksekte çalışma
Kapalı ortamda çalışma"""

class CertificateTemplate(models.Model):
    name = models.CharField(max_length=255, default="Global", verbose_name="Şablon Adı")
    institute_name = models.TextField(default=DEFAULT_INSTITUTE, verbose_name="Kurum Başlığı (Satır boşlukları için Enter kullanın)")
    education_topics = models.TextField(default=DEFAULT_TOPICS, verbose_name="Eğitim Konuları (Her satıra bir konu)")
    # REMOVED: html_content

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Sertifika Şablonu"
        verbose_name_plural = "Sertifika Şablonları"


# =============================================================================
# Risk Assessment Module (OiRA-style)
# =============================================================================

class RiskTool(models.Model):
    """Master template for risk assessments (e.g., 'Ofisler', 'Depolar')"""
    title = models.CharField(max_length=255, verbose_name="Araç Adı")
    description = models.TextField(blank=True, verbose_name="Açıklama")
    sector = models.CharField(max_length=100, blank=True, verbose_name="Sektör")
    is_active = models.BooleanField(default=True, verbose_name="Aktif")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Risk Değerlendirme Aracı"
        verbose_name_plural = "Risk Değerlendirme Araçları"
        ordering = ['title']

    @property
    def question_count(self):
        """Total questions across all categories and topics"""
        return RiskQuestion.objects.filter(topic__category__tool=self).count()


class RiskCategory(models.Model):
    """Categories within a tool (e.g., 'Fiziksel Riskler', 'Kimyasal Riskler')"""
    tool = models.ForeignKey(RiskTool, on_delete=models.CASCADE, related_name="categories", verbose_name="Araç")
    title = models.CharField(max_length=255, verbose_name="Kategori Adı")
    order_index = models.PositiveIntegerField(default=0, verbose_name="Sıralama")

    def __str__(self):
        return f"{self.tool.title} - {self.title}"

    class Meta:
        verbose_name = "Risk Kategorisi"
        verbose_name_plural = "Risk Kategorileri"
        ordering = ['tool', 'order_index']


class RiskTopic(models.Model):
    """Topics within a category (e.g., 'Gürültü', 'Aydınlatma')"""
    category = models.ForeignKey(RiskCategory, on_delete=models.CASCADE, related_name="topics", verbose_name="Kategori")
    title = models.CharField(max_length=255, verbose_name="Konu Başlığı")
    order_index = models.PositiveIntegerField(default=0, verbose_name="Sıralama")

    def __str__(self):
        return f"{self.category.title} - {self.title}"

    class Meta:
        verbose_name = "Risk Konusu"
        verbose_name_plural = "Risk Konuları"
        ordering = ['category', 'order_index']


class RiskQuestion(models.Model):
    """Individual assessment questions"""
    topic = models.ForeignKey(RiskTopic, on_delete=models.CASCADE, related_name="questions", verbose_name="Konu")
    content = models.TextField(verbose_name="Soru İçeriği")
    explanation_text = models.TextField(blank=True, verbose_name="Açıklama")
    image_url = models.URLField(blank=True, null=True, verbose_name="Görsel URL")
    legal_reference = models.TextField(blank=True, verbose_name="Yasal Dayanak")
    order_index = models.PositiveIntegerField(default=0, verbose_name="Sıralama")

    def __str__(self):
        return f"{self.topic.title}: {self.content[:50]}..."

    class Meta:
        verbose_name = "Risk Sorusu"
        verbose_name_plural = "Risk Soruları"
        ordering = ['topic', 'order_index']


class AssessmentSession(models.Model):
    """A user's assessment instance for a specific facility"""
    STATUS_CHOICES = [
        ('DRAFT', 'Devam Ediyor'),
        ('COMPLETED', 'Tamamlandı'),
    ]
    WORKFLOW_CHOICES = [
        ('LIBRARY', 'Kütüphaneden Seçerek'),
        ('TEMPLATE', 'Hazır Şablon İle'),
    ]
    SCORING_METHOD_CHOICES = [
        ('KINNEY', 'Fine-Kinney'),
        ('MATRIX', 'L-Matris (5x5)'),
    ]

    facility = models.ForeignKey(Facility, on_delete=models.CASCADE, related_name="assessment_sessions", verbose_name="Birim")
    tool = models.ForeignKey(RiskTool, on_delete=models.PROTECT, null=True, blank=True, verbose_name="Değerlendirme Aracı")
    title = models.CharField(max_length=255, verbose_name="Değerlendirme Adı")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT', verbose_name="Durum")
    workflow_type = models.CharField(max_length=20, choices=WORKFLOW_CHOICES, default='LIBRARY', verbose_name="Yöntem")
    scoring_method = models.CharField(max_length=10, choices=SCORING_METHOD_CHOICES, default='KINNEY', verbose_name="Puanlama Yöntemi")
    final_comments = models.TextField(blank=True, null=True, verbose_name="Sonuç Yorumları")
    participants = models.TextField(blank=True, null=True, verbose_name="Katılımcılar")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma Tarihi")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Güncellenme Tarihi")

    def __str__(self):
        return f"{self.title} - {self.facility.name}"

    class Meta:
        verbose_name = "Değerlendirme Oturumu"
        verbose_name_plural = "Değerlendirme Oturumları"
        ordering = ['-created_at']

    @property
    def progress_percentage(self):
        """Calculate completion percentage based on answered questions"""
        if not self.tool:
            return 0
        total_questions = RiskQuestion.objects.filter(topic__category__tool=self.tool).count()
        if total_questions == 0:
            return 0
        answered = self.answers.exclude(response__isnull=True).exclude(response='').count()
        return round((answered / total_questions) * 100)


class RiskAssessmentTeamMember(models.Model):
    """Team members for risk assessment signature blocks"""
    ROLE_CHOICES = [
        ('EMPLOYER', 'İşveren / Vekili'),
        ('SAFETY_EXPERT', 'İSG Uzmanı'),
        ('DOCTOR', 'İş Yeri Hekimi'),
        ('WORKER_REP', 'Çalışan Temsilcisi'),
        ('OTHER', 'Diğer'),
    ]
    
    session = models.ForeignKey(AssessmentSession, on_delete=models.CASCADE, related_name="team_members", verbose_name="Oturum")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, verbose_name="Rol")
    name = models.CharField(max_length=255, verbose_name="Ad Soyad")
    title = models.CharField(max_length=255, blank=True, verbose_name="Unvan")
    
    def __str__(self):
        return f"{self.name} - {self.get_role_display()}"
    
    class Meta:
        verbose_name = "Değerlendirme Ekibi Üyesi"
        verbose_name_plural = "Değerlendirme Ekibi Üyeleri"
        ordering = ['role', 'name']


class AssessmentAnswer(models.Model):
    """User's response to each question"""
    RESPONSE_CHOICES = [
        ('YES', 'Evet'),
        ('NO', 'Hayır'),
        ('POSTPONED', 'Ertelenmiş'),
        ('NA', 'Uygulanamaz'),
    ]
    PRIORITY_CHOICES = [
        ('HIGH', 'Yüksek'),
        ('MEDIUM', 'Orta'),
        ('LOW', 'Düşük'),
    ]

    session = models.ForeignKey(AssessmentSession, on_delete=models.CASCADE, related_name="answers", verbose_name="Oturum")
    question = models.ForeignKey(RiskQuestion, on_delete=models.CASCADE, verbose_name="Soru")
    response = models.CharField(max_length=20, choices=RESPONSE_CHOICES, null=True, blank=True, verbose_name="Yanıt")
    notes = models.TextField(blank=True, verbose_name="Notlar")
    risk_priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, null=True, blank=True, verbose_name="Risk Önceliği")

    def __str__(self):
        return f"{self.session.title} - Q{self.question.id}: {self.response or 'Yanıtsız'}"

    class Meta:
        verbose_name = "Değerlendirme Yanıtı"
        verbose_name_plural = "Değerlendirme Yanıtları"
        unique_together = ['session', 'question']

    @property
    def action_plan_status(self):
        """Return status for action plan sidebar"""
        if self.response != 'NO':
            return None
        measures = self.measures.all()
        if not measures.exists():
            return 'no_measures'  # Red
        if measures.filter(description='').exists():
            return 'incomplete'  # Orange
        return 'complete'  # Green


class AssessmentCustomRisk(models.Model):
    """User-defined site-specific risks"""
    PRIORITY_CHOICES = [
        ('HIGH', 'Yüksek'),
        ('MEDIUM', 'Orta'),
        ('LOW', 'Düşük'),
    ]
    
    SCORING_METHOD_CHOICES = [
        ('KINNEY', 'Fine-Kinney'),
        ('MATRIX', 'L-Matrix'),
    ]

    session = models.ForeignKey(AssessmentSession, on_delete=models.CASCADE, related_name="custom_risks", verbose_name="Oturum")
    description = models.TextField(verbose_name="Risk Tanımı")
    is_acceptable = models.BooleanField(null=True, blank=True, verbose_name="Kabul Edilebilir mi?")
    evidence = models.TextField(blank=True, verbose_name="Bilgi/Kanıt")
    notes = models.TextField(blank=True, verbose_name="Notlar")
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, null=True, blank=True, verbose_name="Öncelik")
    scoring_method = models.CharField(max_length=10, choices=SCORING_METHOD_CHOICES, default='KINNEY', verbose_name="Puanlama Yöntemi")

    # Library & classification fields
    source_library_id = models.IntegerField(null=True, blank=True, verbose_name="Kütüphane ID")
    category = models.CharField(max_length=500, blank=True, default='', verbose_name="Kategori")
    sub_category = models.CharField(max_length=500, blank=True, default='', verbose_name="Üst Grup")
    hazard_source = models.CharField(max_length=500, blank=True, default='', verbose_name="Tehlike Kaynağı")
    legal_basis = models.TextField(blank=True, default='', verbose_name="İlgili Mevzuat")
    affected_persons = models.CharField(max_length=500, blank=True, default='', verbose_name="Etkilenecek Kişiler")
    measure = models.TextField(blank=True, default='', verbose_name="Alınması Gereken Önlem")

    # Fine-Kinney scoring
    kinney_probability = models.FloatField(null=True, blank=True, verbose_name="Olasılık (P)")
    kinney_frequency = models.FloatField(null=True, blank=True, verbose_name="Frekans (F)")
    kinney_severity = models.IntegerField(null=True, blank=True, verbose_name="Şiddet (S)")
    kinney_score = models.IntegerField(null=True, blank=True, verbose_name="Kinney Skoru")

    # L-Matrix scoring
    matrix_probability = models.IntegerField(null=True, blank=True, verbose_name="Matris Olasılık (1-5)")
    matrix_severity = models.IntegerField(null=True, blank=True, verbose_name="Matris Şiddet (1-5)")
    matrix_score = models.IntegerField(null=True, blank=True, verbose_name="Matris Skoru")

    # DÖF (Corrective Action) fields
    mitigation_strategy = models.CharField(max_length=50, blank=True, default='', verbose_name="Kontrol Stratejisi")
    estimated_budget = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name="Tahmini Bütçe")
    responsible_person = models.CharField(max_length=255, blank=True, default='', verbose_name="Sorumlu Kişi")
    due_date = models.DateField(null=True, blank=True, verbose_name="Termin Tarihi")

    def save(self, *args, **kwargs):
        # Auto-calculate scores
        if self.kinney_probability and self.kinney_frequency and self.kinney_severity:
            self.kinney_score = int(self.kinney_probability * self.kinney_frequency * self.kinney_severity)
        else:
            self.kinney_score = None
        if self.matrix_probability and self.matrix_severity:
            self.matrix_score = self.matrix_probability * self.matrix_severity
        else:
            self.matrix_score = None
        super().save(*args, **kwargs)

    @property
    def risk_level(self):
        """Return (css_class, label) based on score and method"""
        if self.scoring_method == 'MATRIX' and self.matrix_score:
            s = self.matrix_score
            if s >= 20: return ('intolerable', 'Tolerans gösterilemez')
            if s >= 12: return ('important', 'Önemli')
            if s >= 6:  return ('possible', 'Orta')
            if s >= 3:  return ('trivial', 'Düşük')
            return ('trivial', 'Önemsiz')
        elif self.kinney_score:
            s = self.kinney_score
            if s >= 400: return ('intolerable', 'Tolerans gösterilemez')
            if s >= 200: return ('substantial', 'Esaslı')
            if s >= 70:  return ('important', 'Önemli')
            if s >= 20:  return ('possible', 'Olası')
            return ('trivial', 'Önemsiz')
        return (None, None)

    def __str__(self):
        return f"{self.session.title} - Custom Risk: {self.description[:30]}"
    
    class Meta:
        verbose_name = "Siteye Özel Risk"
        verbose_name_plural = "Siteye Özel Riskler"


# =============================================================================
# RBAC & User Management (Phase 34)
# =============================================================================

class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('ADMIN', 'Sistem Yöneticisi'),
        ('MANAGER', 'Yardımcı Yönetici'),
        ('DOCTOR', 'İş Yeri Hekimi'),
        ('SPECIALIST', 'İş Güvenliği Uzmanı'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile', verbose_name="Kullanıcı")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='SPECIALIST', verbose_name="Rol")
    tckn = EncryptedCharField(max_length=11, verbose_name="TCKN", null=True, blank=True)
    phone = EncryptedCharField(max_length=20, verbose_name="Telefon", null=True, blank=True)
    is_mfa_enabled = models.BooleanField(default=False, verbose_name="2FA Aktif")
    
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"

    def has_medical_access(self):
        """Returns True if user is DOCTOR or ADMIN"""
        return self.role in ['DOCTOR', 'ADMIN']
    
    class Meta:
        verbose_name = "Kullanıcı Profili"
        verbose_name_plural = "Kullanıcı Profilleri"


class WorkplaceAssignment(models.Model):
    """Assigns users to specific workplaces with validity periods"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assignments', verbose_name="Kullanıcı")
    workplace = models.ForeignKey(Workplace, on_delete=models.CASCADE, related_name='assignments', verbose_name="İşyeri")
    role = models.CharField(max_length=50, blank=True, null=True, verbose_name="Atama Rolü (Opsiyonel)")
    start_date = models.DateField(verbose_name="Başlangıç Tarihi")
    end_date = models.DateField(null=True, blank=True, verbose_name="Bitiş Tarihi")
    is_active = models.BooleanField(default=True, verbose_name="Aktif")
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} -> {self.workplace.name}"

    @property
    def is_valid(self):
        today = date.today()
        if not self.is_active:
            return False
        if self.end_date and today > self.end_date:
            return False
        if today < self.start_date:
            return False
        return True

    class Meta:
        verbose_name = "İşyeri Ataması"
        verbose_name_plural = "İşyeri Atamaları"
        ordering = ['-created_at']
    



class ActionPlanMeasure(models.Model):
    """Measures to address a risk (one risk can have multiple measures)"""
    # Can be linked to either a standard answer OR a custom risk
    answer = models.ForeignKey(AssessmentAnswer, on_delete=models.CASCADE, related_name="measures", null=True, blank=True, verbose_name="Standart Risk")
    custom_risk = models.ForeignKey(AssessmentCustomRisk, on_delete=models.CASCADE, related_name="custom_measures", null=True, blank=True, verbose_name="Ek Risk")
    
    description = models.TextField(blank=True, verbose_name="Önlem Açıklaması")
    expertise = models.CharField(max_length=200, blank=True, verbose_name="Gerekli Uzmanlık")
    responsible_person = models.CharField(max_length=200, blank=True, verbose_name="Sorumlu Kişi")
    budget = models.CharField(max_length=100, blank=True, verbose_name="Bütçe")
    planning_start_date = models.DateField(null=True, blank=True, verbose_name="Başlangıç Tarihi")
    planning_end_date = models.DateField(null=True, blank=True, verbose_name="Bitiş Tarihi")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma Tarihi")

    def __str__(self):
        source = self.answer.question.content[:30] if self.answer else self.custom_risk.description[:30]
        return f"Önlem: {source}..."

    class Meta:
        verbose_name = "Eylem Planı Önlemi"
        verbose_name_plural = "Eylem Planı Önlemleri"
        ordering = ['created_at']


class RiskControlRecord(models.Model):
    """Audit/control record for a risk - tracks verification over time"""
    risk = models.ForeignKey(
        AssessmentCustomRisk, 
        on_delete=models.CASCADE, 
        related_name="control_records",
        verbose_name="Risk"
    )
    control_date = models.DateField(verbose_name="Kontrol Tarihi")
    auditor_name = models.CharField(max_length=255, verbose_name="Denetleyen")
    observation_note = models.TextField(blank=True, verbose_name="Gözlemler")
    
    # Scoring method to know how to interpret residual score
    scoring_method = models.CharField(max_length=10, blank=True, verbose_name="Puanlama Yöntemi")
    
    # Fine-Kinney scoring fields
    kinney_probability = models.FloatField(null=True, blank=True, verbose_name="Olasılık (P)")
    kinney_frequency = models.FloatField(null=True, blank=True, verbose_name="Frekans (F)")
    kinney_severity = models.IntegerField(null=True, blank=True, verbose_name="Şiddet (S)")
    
    # L-Matrix scoring fields
    matrix_probability = models.IntegerField(null=True, blank=True, verbose_name="Matris Olasılık (1-5)")
    matrix_severity = models.IntegerField(null=True, blank=True, verbose_name="Matris Şiddet (1-5)")
    
    residual_score = models.IntegerField(null=True, blank=True, verbose_name="Kalan Risk Skoru")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma Tarihi")
    
    def save(self, *args, **kwargs):
        # Auto-calculate residual score based on scoring method
        if self.scoring_method == 'MATRIX':
            if self.matrix_probability and self.matrix_severity:
                self.residual_score = self.matrix_probability * self.matrix_severity
        else:  # Default to Kinney
            if self.kinney_probability and self.kinney_frequency and self.kinney_severity:
                self.residual_score = int(self.kinney_probability * self.kinney_frequency * self.kinney_severity)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.risk.description[:30]}... - {self.control_date}"
    
    @property
    def risk_level(self):
        """Return risk level based on residual score and scoring method"""
        if self.residual_score:
            if self.scoring_method == 'MATRIX':
                # L-Matris thresholds (1-25 scale)
                if self.residual_score >= 20:
                    return ('intolerable', 'Tolerans gösterilemez')
                elif self.residual_score >= 12:
                    return ('important', 'Önemli')
                elif self.residual_score >= 6:
                    return ('possible', 'Orta')
                elif self.residual_score >= 3:
                    return ('trivial', 'Düşük')
                else:
                    return ('trivial', 'Önemsiz')
            else:
                # Fine-Kinney thresholds
                if self.residual_score < 20:
                    return ('trivial', 'Önemsiz')
                elif self.residual_score < 70:
                    return ('possible', 'Olası')
                elif self.residual_score < 200:
                    return ('important', 'Önemli')
                elif self.residual_score < 400:
                    return ('substantial', 'Esaslı')
                else:
                    return ('intolerable', 'Tolerans gösterilemez')
        return (None, None)
    
    class Meta:
        verbose_name = "Risk Kontrol Kaydı"
        verbose_name_plural = "Risk Kontrol Kayıtları"
        ordering = ['-control_date', '-created_at']

