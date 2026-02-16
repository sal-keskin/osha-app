from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from .models import Workplace, Worker, Professional, Education, Inspection, Examination, Profession, Facility, CertificateTemplate, RiskTool, AssessmentSession, AssessmentCustomRisk, SafetyEngagement, UserProfile
from .utils import get_allowed_workplaces
import random

class CustomUserCreationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}), label="Şifre")

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'is_staff', 'is_active', 'password']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'is_staff': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'username': 'Kullanıcı Adı',
            'first_name': 'Ad',
            'last_name': 'Soyad',
            'email': 'E-posta Adresi',
            'is_staff': 'Yönetici Paneli Erişimi',
            'is_active': 'Hesap Aktif',
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user

class CustomUserChangeForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'is_staff', 'is_active']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'is_staff': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'username': 'Kullanıcı Adı',
            'first_name': 'Ad',
            'last_name': 'Soyad',
            'email': 'E-posta Adresi',
            'is_staff': 'Yönetici Paneli Erişimi',
            'is_active': 'Hesap Aktif',
        }

class ProfessionForm(forms.ModelForm):
    class Meta:
        model = Profession
        fields = '__all__'
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
        }

class LoginForm(forms.Form):
    username = forms.CharField(label="Kullanıcı Adı", widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(label="Şifre", widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    captcha = forms.IntegerField(label="Güvenlik Sorusu", widget=forms.NumberInput(attrs={'class': 'form-control'}))

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        # Generate a simple math problem
        if self.request and 'captcha_answer' not in self.request.session:
            num1 = random.randint(1, 10)
            num2 = random.randint(1, 10)
            self.request.session['captcha_question'] = f"{num1} + {num2} = ?"
            self.request.session['captcha_answer'] = num1 + num2
        
        if self.request:
            self.fields['captcha'].label = self.request.session.get('captcha_question', "3 + 5 = ?")

    def clean_captcha(self):
        answer = self.cleaned_data.get('captcha')
        if self.request:
            expected = self.request.session.get('captcha_answer')
            if expected is not None and answer != expected:
                raise ValidationError("Yanlış cevap, lütfen tekrar deneyiniz.")
        return answer

class WorkplaceForm(forms.ModelForm):
    class Meta:
        model = Workplace
        fields = ['name', 'address', 'detsis_number', 'sgk_sicil_no', 'nace_code', 'activity_description', 
                  'hazard_class', 'employer_representative', 'phone_number']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Firma adı'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Adres'}),
            'detsis_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'SGK sicil no veya DETSİS no'}),
            'sgk_sicil_no': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '26', 'placeholder': '26 haneli SGK sicil numarası (İBYS)'}),
            'nace_code': forms.TextInput(attrs={'class': 'form-control', 'id': 'id_nace_code'}),
            'activity_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'readonly': 'readonly'}),
            'hazard_class': forms.Select(attrs={'class': 'form-select hazard-select'}),
            'employer_representative': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'İşveren vekili adı'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Telefon numarası'}),
        }

class FacilityForm(forms.ModelForm):
    class Meta:
        model = Facility
        fields = '__all__'
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'workplace': forms.Select(attrs={'class': 'form-select'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'coordinates': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Örn: 39.64266, 27.915561'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.user:
            allowed = get_allowed_workplaces(self.user)
            self.fields['workplace'].queryset = allowed
            if allowed.count() == 1:
                self.fields['workplace'].initial = allowed.first()
                self.fields['workplace'].widget = forms.HiddenInput()

class WorkerForm(forms.ModelForm):
    class Meta:
        model = Worker
        fields = '__all__'
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'tckn': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '11', 'minlength': '11'}),
            'workplace': forms.Select(attrs={'class': 'form-select'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'birth_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'profession': forms.Select(attrs={'class': 'form-select'}),
            'facility': forms.Select(attrs={'class': 'form-select', 'id': 'id_facility'}),

            'first_aid_certificate': forms.CheckboxInput(attrs={'class': 'form-check-input', 'id': 'id_first_aid_certificate'}),
            'first_aid_expiry_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.user:
            allowed = get_allowed_workplaces(self.user)
            self.fields['workplace'].queryset = allowed
            
            # Filter facilities based on allowed workplaces
            self.fields['facility'].queryset = Facility.objects.filter(workplace__in=allowed)

            if allowed.count() == 1:
                self.fields['workplace'].initial = allowed.first()
                self.fields['workplace'].widget = forms.HiddenInput()

    def clean_tckn(self):
        tckn = self.cleaned_data.get('tckn')
        if not tckn.isdigit() or len(tckn) != 11:
            raise ValidationError("TCKN 11 haneli bir sayı olmalıdır.")
        return tckn

class ProfessionalForm(forms.ModelForm):
    class Meta:
        model = Professional
        fields = ['name', 'tckn', 'license_id', 'role']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'tckn': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '11', 'minlength': '11', 'placeholder': '11 haneli TC Kimlik No'}),
            'license_id': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '6'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def clean_tckn(self):
        tckn = self.cleaned_data.get('tckn')
        if not tckn or not tckn.isdigit() or len(tckn) != 11:
            raise ValidationError("TCKN 11 haneli bir sayı olmalıdır.")
        return tckn
    
    def clean_license_id(self):
        license_id = self.cleaned_data.get('license_id')
        if not license_id.isdigit() or len(license_id) != 6:
            raise ValidationError("Lisans No 6 haneli bir sayı olmalıdır.")
        return license_id

class EducationForm(forms.ModelForm):
    specialist = forms.ModelChoiceField(
        queryset=Professional.objects.filter(role='SPECIALIST'),
        label="İş Güvenliği Uzmanı",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    medic = forms.ModelChoiceField(
        queryset=Professional.objects.filter(role__in=['DOCTOR', 'OTHER_HEALTH']),
        label="İşyeri Hekimi / Diğer Sağlık Personeli",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = Education
        exclude = ['professionals']
        widgets = {
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'topic': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Genel eğitim başlığı (opsiyonel)'}),
            'duration': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'workplace': forms.Select(attrs={'class': 'form-select'}),
            'workers': forms.CheckboxSelectMultiple(),
            'egitim_yeri': forms.RadioSelect(attrs={'class': 'form-check-input'}),
            'egitim_yontemi': forms.RadioSelect(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        # Make topic optional
        self.fields['topic'].required = False
        
        if self.user:
            allowed = get_allowed_workplaces(self.user)
            self.fields['workplace'].queryset = allowed
            self.fields['workers'].queryset = Worker.objects.filter(workplace__in=allowed)
            
            if allowed.count() == 1:
                self.fields['workplace'].initial = allowed.first()
                self.fields['workplace'].widget = forms.HiddenInput()

        if self.instance.pk:
            # Populate initial values for specialist and medic if editing
            profs = self.instance.professionals.all()
            for p in profs:
                if p.role == 'SPECIALIST':
                    self.fields['specialist'].initial = p
                elif p.role in ['DOCTOR', 'OTHER_HEALTH']:
                    self.fields['medic'].initial = p

    def save(self, commit=True):
        instance = super().save(commit=False)
        if commit:
            instance.save()
            self.save_m2m() # Saves workers

            # Save professionals
            specialist = self.cleaned_data['specialist']
            medic = self.cleaned_data['medic']
            instance.professionals.set([specialist, medic])
        return instance

class InspectionForm(forms.ModelForm):
    class Meta:
        model = Inspection
        fields = '__all__'
        widgets = {
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'workplace': forms.Select(attrs={'class': 'form-select'}),
            'professional': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.user:
            allowed = get_allowed_workplaces(self.user)
            self.fields['workplace'].queryset = allowed
            if allowed.count() == 1:
                self.fields['workplace'].initial = allowed.first()
                self.fields['workplace'].widget = forms.HiddenInput()

class ExaminationForm(forms.ModelForm):
    field_order = ['worker', 'professional']
    class Meta:
        model = Examination
        fields = '__all__'
        widgets = {
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'worker': forms.Select(attrs={'class': 'form-select'}),
            'professional': forms.Select(attrs={'class': 'form-select'}),
            'decision': forms.Select(attrs={'class': 'form-select', 'id': 'id_decision'}),
            'decision_conditions': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'id': 'id_decision_conditions'}),

            'is_caution': forms.CheckboxInput(attrs={'class': 'form-check-input', 'id': 'id_is_caution'}),
            'caution_note': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'id': 'id_caution_note'}),

            # REMOVED: tetanus_date widget

            # Checkboxes can use default widget or added class if needed, standard checkbox is fine
            'tetanus_vaccine': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'hepatitis_b_vaccine': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'biochemistry': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'hemogram': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'serology': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'sft': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'audiometry': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'radiology': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.user:
            allowed = get_allowed_workplaces(self.user)
            self.fields['worker'].queryset = Worker.objects.filter(workplace__in=allowed)

class ExaminationNoteForm(forms.ModelForm):
    class Meta:
        model = Examination
        fields = ['caution_note']
        widgets = {
             'caution_note': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class CertificateTemplateForm(forms.ModelForm):
    class Meta:
        model = CertificateTemplate
        fields = ['institute_name', 'education_topics']
        widgets = {
            'institute_name': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'education_topics': forms.Textarea(attrs={'class': 'form-control', 'rows': 15}),
        }


class AssessmentSessionForm(forms.ModelForm):
    class Meta:
        model = AssessmentSession
        fields = ['tool', 'title']
        widgets = {
            'tool': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Değerlendirme adı'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['tool'].queryset = RiskTool.objects.filter(is_active=True)
        self.fields['tool'].label = "Değerlendirme Aracı"
        self.fields['title'].label = "Değerlendirme Adı"


class RiskToolForm(forms.ModelForm):
    class Meta:
        model = RiskTool
        fields = ['title', 'description', 'sector', 'is_active']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Araç adı'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'sector': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Örn: Ofis, Sağlık, Üretim'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class RiskToolImportForm(forms.Form):
    file = forms.FileField(
        label="Excel veya CSV Dosyası",
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.csv,.xlsx,.xls'
        }),
        help_text="Desteklenen formatlar: .csv, .xlsx, .xls"
    )
    tool_name = forms.CharField(
        label="Araç Adı",
        max_length=255,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Dosya adından otomatik alınabilir'}),
        required=False
    )
    sector = forms.CharField(
        label="Sektör",
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Örn: Ofis, Sağlık'}),
        required=False
    )


class CustomRiskForm(forms.ModelForm):
    ACCEPTABLE_CHOICES = [
        (None, '--- Seçiniz ---'),
        (True, 'Evet - Kabul edilebilir'),
        (False, 'Hayır - Risk mevcut'),
    ]

    is_acceptable = forms.TypedChoiceField(
        label="Bu risk kabul edilebilir mi?",
        choices=ACCEPTABLE_CHOICES,
        coerce=lambda x: x == 'True' if x in ['True', 'False'] else None,
        required=False,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'})
    )

    class Meta:
        model = AssessmentCustomRisk
        fields = ['description', 'is_acceptable', 'evidence', 'notes']
        widgets = {
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Tespit ettiğiniz riski açıklayın...'}),
            'evidence': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Bilgi veya kanıt ekleyin...'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Ek notlar (opsiyonel)'}),
        }


class PublicEngagementForm(forms.Form):
    """Form for public safety engagement submissions with honeypot + math captcha protection"""
    
    TOPIC_CHOICES = [
        ('SUGGESTION', 'Öneri'),
        ('NEAR_MISS', 'Ramak Kala'),
        ('HAZARD', 'Tehlike'),
        ('COMPLAINT', 'Şikayet'),
    ]
    
    topic = forms.ChoiceField(
        label="Konu",
        choices=TOPIC_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    message = forms.CharField(
        label="Mesaj",
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 5,
            'placeholder': 'Bildiriminizi buraya yazınız...'
        })
    )
    
    # Honeypot field (invisible trap for bots)
    website = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'style': 'position: absolute; left: -9999px; opacity: 0;',
            'tabindex': '-1',
            'autocomplete': 'off',
            'aria-hidden': 'true'
        })
    )
    
    # Safety Math field (visible check for humans)
    safety_math = forms.IntegerField(
        label="Güvenlik Sorusu",
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Cevabınızı yazın'
        })
    )
    
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        
        # Generate a simple math problem for CAPTCHA
        if self.request:
            if 'safety_math_answer' not in self.request.session:
                self._generate_math_problem()
            
            question = self.request.session.get('safety_math_question', '3 + 5 = ?')
            self.fields['safety_math'].label = question
    
    def _generate_math_problem(self):
        """Generate a simple addition problem"""
        num1 = random.randint(1, 10)
        num2 = random.randint(1, 10)
        self.request.session['safety_math_question'] = f"{num1} + {num2} = ?"
        self.request.session['safety_math_answer'] = num1 + num2
    
    def clean_website(self):
        """Honeypot validation - should be empty for legitimate users"""
        value = self.cleaned_data.get('website', '')
        if value:
            # Bot filled out the honeypot field, silently fail
            raise ValidationError("Spam detected")
        return value
    
    def clean_safety_math(self):
        """Validate the math captcha answer"""
        answer = self.cleaned_data.get('safety_math')
        if self.request:
            expected = self.request.session.get('safety_math_answer')
            if expected is not None and answer != expected:
                # Regenerate the problem for next attempt
                self._generate_math_problem()
                raise ValidationError("Yanlış cevap, lütfen tekrar deneyiniz.")
        return answer


class SafetyPollForm(forms.Form):
    """Form for creating polls with question and multiple options"""
    
    question = forms.CharField(
        label="Soru",
        max_length=500,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Anket sorunuzu yazın...'
        })
    )
    
    options = forms.CharField(
        label="Seçenekler (Her satıra bir seçenek)",
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 5,
            'placeholder': 'Evet\nHayır\nKararsızım'
        })
    )
    
    def clean_options(self):
        """Split options by newline and return as list"""
        raw = self.cleaned_data.get('options', '')
        options = [opt.strip() for opt in raw.split('\n') if opt.strip()]
        if len(options) < 2:
            raise ValidationError("En az 2 seçenek gereklidir.")
        return options


class EngagementCommentForm(forms.Form):
    """Form for adding comments to engagements"""
    
    text = forms.CharField(
        label="Yorum",
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Yorumunuzu yazın...'
        })
    )
