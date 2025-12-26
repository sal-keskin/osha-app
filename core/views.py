from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import (
    LoginForm, WorkplaceForm, WorkerForm, EducatorForm, ProfessionalForm,
    EducationForm, InspectionForm, ExaminationForm
)
from .models import (
    Workplace, Worker, Educator, Professional, Education, Inspection, Examination
)

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST, request=request)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                # Clear captcha session data
                if 'captcha_question' in request.session:
                    del request.session['captcha_question']
                if 'captcha_answer' in request.session:
                    del request.session['captcha_answer']
                return redirect('dashboard')
            else:
                messages.error(request, 'Hatalı kullanıcı adı veya şifre.')
    else:
        # Reset captcha on new load
        if 'captcha_answer' in request.session:
             del request.session['captcha_answer']
        form = LoginForm(request=request)
    
    return render(request, 'core/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def dashboard(request):
    context = {
        'workplace_count': Workplace.objects.count(),
        'worker_count': Worker.objects.count(),
        'educator_count': Educator.objects.count(),
        'professional_count': Professional.objects.count(),
        'education_count': Education.objects.count(),
        'inspection_count': Inspection.objects.count(),
        'examination_count': Examination.objects.count(),
    }
    return render(request, 'core/dashboard.html', context)

# Generic helper for CRUD views
def generic_list_view(request, model_class, title, create_url_name, update_url_name, fields_to_show):
    items = model_class.objects.all()
    context = {
        'items': items,
        'title': title,
        'create_url_name': create_url_name,
        'update_url_name': update_url_name,
        'fields': fields_to_show,
    }
    return render(request, 'core/list_template.html', context)

def generic_create_view(request, form_class, title, list_url_name):
    if request.method == 'POST':
        form = form_class(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Kayıt başarıyla oluşturuldu.')
            return redirect(list_url_name)
    else:
        form = form_class()
    return render(request, 'core/form_template.html', {'form': form, 'title': title})

def generic_update_view(request, model_class, form_class, pk, title, list_url_name):
    item = get_object_or_404(model_class, pk=pk)
    if request.method == 'POST':
        form = form_class(request.POST, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, 'Kayıt güncellendi.')
            return redirect(list_url_name)
    else:
        form = form_class(instance=item)
    return render(request, 'core/form_template.html', {'form': form, 'title': title})

# Specific Views using helpers
@login_required
def workplace_list(request):
    return generic_list_view(request, Workplace, "İşyerleri", 'workplace_create', 'workplace_update', [('name', 'İşyeri Adı'), ('detsis_number', 'DETSİS No')])

@login_required
def workplace_create(request):
    return generic_create_view(request, WorkplaceForm, "Yeni İşyeri", 'workplace_list')

@login_required
def workplace_update(request, pk):
    return generic_update_view(request, Workplace, WorkplaceForm, pk, "İşyeri Düzenle", 'workplace_list')

@login_required
def worker_list(request):
    return generic_list_view(request, Worker, "Çalışanlar", 'worker_create', 'worker_update', [('name', 'Ad Soyad'), ('tckn', 'TCKN'), ('workplace', 'İşyeri')])

@login_required
def worker_create(request):
    return generic_create_view(request, WorkerForm, "Yeni Çalışan", 'worker_list')

@login_required
def worker_update(request, pk):
    return generic_update_view(request, Worker, WorkerForm, pk, "Çalışan Düzenle", 'worker_list')

@login_required
def educator_list(request):
    return generic_list_view(request, Educator, "Eğiticiler", 'educator_create', 'educator_update', [('name', 'Ad Soyad'), ('license_id', 'Lisans No')])

@login_required
def educator_create(request):
    return generic_create_view(request, EducatorForm, "Yeni Eğitici", 'educator_list')

@login_required
def educator_update(request, pk):
    return generic_update_view(request, Educator, EducatorForm, pk, "Eğitici Düzenle", 'educator_list')

@login_required
def professional_list(request):
    return generic_list_view(request, Professional, "Profesyoneller", 'professional_create', 'professional_update', [('name', 'Ad Soyad'), ('license_id', 'Lisans No'), ('get_role_display', 'Görevi')])

@login_required
def professional_create(request):
    return generic_create_view(request, ProfessionalForm, "Yeni Profesyonel", 'professional_list')

@login_required
def professional_update(request, pk):
    return generic_update_view(request, Professional, ProfessionalForm, pk, "Profesyonel Düzenle", 'professional_list')

@login_required
def education_list(request):
    return generic_list_view(request, Education, "İSG Eğitimleri", 'education_create', 'education_update', [('date', 'Tarih'), ('topic', 'Konu'), ('workplace', 'İşyeri')])

@login_required
def education_create(request):
    return generic_create_view(request, EducationForm, "Yeni Eğitim", 'education_list')

@login_required
def education_update(request, pk):
    return generic_update_view(request, Education, EducationForm, pk, "Eğitim Düzenle", 'education_list')

@login_required
def inspection_list(request):
    return generic_list_view(request, Inspection, "Denetimler", 'inspection_create', 'inspection_update', [('date', 'Tarih'), ('workplace', 'İşyeri'), ('professional', 'Denetleyen')])

@login_required
def inspection_create(request):
    return generic_create_view(request, InspectionForm, "Yeni Denetim", 'inspection_list')

@login_required
def inspection_update(request, pk):
    return generic_update_view(request, Inspection, InspectionForm, pk, "Denetim Düzenle", 'inspection_list')

@login_required
def examination_list(request):
    return generic_list_view(request, Examination, "Sağlık Muayeneleri", 'examination_create', 'examination_update', [('date', 'Tarih'), ('worker', 'Çalışan'), ('professional', 'Hekim')])

@login_required
def examination_create(request):
    return generic_create_view(request, ExaminationForm, "Yeni Muayene", 'examination_list')

@login_required
def examination_update(request, pk):
    return generic_update_view(request, Examination, ExaminationForm, pk, "Muayene Düzenle", 'examination_list')
