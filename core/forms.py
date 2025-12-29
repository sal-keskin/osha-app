from django import forms
from django.core.exceptions import ValidationError
from .models import Workplace, Worker, Educator, Professional, Education, Inspection, Examination, Profession
import random

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

class WorkerForm(forms.ModelForm):
    CHRONIC_DISEASES_CHOICES = [
        ('Diyabet', 'Diyabet'),
        ('KAH', 'KAH'),
        ('Astım', 'Astım'),
        ('Alerji', 'Alerji'),
    ]
    # We use a MultipleChoiceField to handle the rendering, but we need to process it back to a string
    chronic_diseases_list = forms.MultipleChoiceField(
        choices=CHRONIC_DISEASES_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Kronik Hastalıklar"
    )

    class Meta:
        model = Worker
        fields = '__all__'
        exclude = ['chronic_diseases'] # We handle this manually via chronic_diseases_list
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'tckn': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '11', 'minlength': '11'}),
            'workplace': forms.Select(attrs={'class': 'form-select'}),
            'facility': forms.Select(attrs={'class': 'form-select'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'birth_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'special_note': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'profession': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.chronic_diseases:
            self.fields['chronic_diseases_list'].initial = self.instance.chronic_diseases.split(',')

        # Order foreign keys
        self.fields['workplace'].queryset = Workplace.objects.order_by('name')
        self.fields['profession'].queryset = Profession.objects.order_by('name')
        # Facility should be filtered if instance exists, but dynamically loaded via JS
        if self.instance and self.instance.pk and self.instance.workplace:
             self.fields['facility'].queryset = self.instance.workplace.facilities.all()
        else:
             self.fields['facility'].queryset = self.instance.facility.__class__.objects.none()

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.chronic_diseases = ",".join(self.cleaned_data.get('chronic_diseases_list', []))
        if commit:
            instance.save()
        return instance

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

            'work_accident_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'tetanus_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'hepatitis_b_value': forms.TextInput(attrs={'class': 'form-control'}),

            # Checkboxes can use default widget or added class if needed, standard checkbox is fine
            'work_accident': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'tetanus_vaccine': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'hepatitis_b_vaccine': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'biochemistry': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'hemogram': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'serology': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'sft': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'audiometry': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'radiology': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
