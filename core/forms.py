from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from .models import Workplace, Worker, Educator, Professional, Education, Inspection, Examination, Profession, Facility
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
        fields = '__all__'
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'detsis_number': forms.TextInput(attrs={'class': 'form-control'}),
            'hazard_class': forms.Select(attrs={'class': 'form-select'}),
        }

class FacilityForm(forms.ModelForm):
    class Meta:
        model = Facility
        fields = '__all__'
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'workplace': forms.Select(attrs={'class': 'form-select'}),
        }

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

    def clean_tckn(self):
        tckn = self.cleaned_data.get('tckn')
        if not tckn.isdigit() or len(tckn) != 11:
            raise ValidationError("TCKN 11 haneli bir sayı olmalıdır.")
        return tckn

class EducatorForm(forms.ModelForm):
    class Meta:
        model = Educator
        fields = '__all__'
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'license_id': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '6'}),
        }
    
    def clean_license_id(self):
        license_id = self.cleaned_data.get('license_id')
        if not license_id.isdigit() or len(license_id) != 6:
            raise ValidationError("Lisans No 6 haneli bir sayı olmalıdır.")
        return license_id

class ProfessionalForm(forms.ModelForm):
    class Meta:
        model = Professional
        fields = '__all__'
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'license_id': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '6'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def clean_license_id(self):
        license_id = self.cleaned_data.get('license_id')
        if not license_id.isdigit() or len(license_id) != 6:
            raise ValidationError("Lisans No 6 haneli bir sayı olmalıdır.")
        return license_id

class EducationForm(forms.ModelForm):
    class Meta:
        model = Education
        fields = '__all__'
        widgets = {
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'topic': forms.TextInput(attrs={'class': 'form-control'}),
            'workplace': forms.Select(attrs={'class': 'form-select'}),
            'educator': forms.Select(attrs={'class': 'form-select'}),
            'workers': forms.CheckboxSelectMultiple(),
        }

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

            'tetanus_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),

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

class ExaminationNoteForm(forms.ModelForm):
    class Meta:
        model = Examination
        fields = ['caution_note']
        widgets = {
             'caution_note': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
