from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.db.models import Q
import csv
import openpyxl
from datetime import datetime
from .forms import (
    LoginForm, WorkplaceForm, WorkerForm, EducatorForm, ProfessionalForm,
    EducationForm, InspectionForm, ExaminationForm, ProfessionForm,
    ExaminationNoteForm, FacilityForm
)
from .models import (
    Workplace, Worker, Educator, Professional, Education, Inspection, Examination, Profession, Facility
)
# Removed duplicate imports
from .import_utils import ImportHandler
import json

@login_required
def api_create_profession(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            name = data.get('name')
            if not name:
                return JsonResponse({'success': False, 'error': 'Name is required'})

            profession, created = Profession.objects.get_or_create(name=name)
            return JsonResponse({
                'success': True,
                'profession': {'id': profession.id, 'name': profession.name}
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid method'})

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
def get_workers_json(request):
    workplace_id = request.GET.get('workplace_id')
    workers = []
    if workplace_id:
        workers = list(Worker.objects.filter(workplace_id=workplace_id).values('id', 'name', 'tckn'))
    return JsonResponse({'workers': workers})

@login_required
def api_get_facilities(request):
    workplace_id = request.GET.get('workplace_id')
    facilities = []
    if workplace_id:
        facilities = list(Facility.objects.filter(workplace_id=workplace_id).values('id', 'name'))
    return JsonResponse({'facilities': facilities})

@login_required
def dashboard(request):
    context = {
        'workplace_count': Workplace.objects.count(),
        'facility_count': Facility.objects.count(),
        'worker_count': Worker.objects.count(),
        'educator_count': Educator.objects.count(),
        'professional_count': Professional.objects.count(),
        'education_count': Education.objects.count(),
        'inspection_count': Inspection.objects.count(),
        'examination_count': Examination.objects.count(),
    }
    return render(request, 'core/dashboard.html', context)

# Filtering Helper
def apply_filters(queryset, filter_config, params):
    """
    Applies filters to the queryset based on configuration and request parameters.
    """
    for config in filter_config:
        field_name = config['field']
        param_value = params.get(field_name)

        if param_value:
            filter_type = config.get('type', 'text')

            if filter_type == 'text':
                # Case-insensitive containment for text
                queryset = queryset.filter(**{f"{field_name}__icontains": param_value})
            elif filter_type == 'select':
                # Exact match for foreign keys or choices
                queryset = queryset.filter(**{field_name: param_value})
            elif filter_type == 'date':
                # Exact match for date
                queryset = queryset.filter(**{field_name: param_value})

            # Update config with the current value to repopulate the form
            config['value'] = param_value

    return queryset

# Generic helper for CRUD views
def generic_list_view(request, model_class, title, create_url_name, update_url_name, fields_to_show, bulk_delete_url_name=None, export_url_name=None, filter_config=None, import_url_name=None, queryset=None, extra_actions=None):
    if queryset is not None:
        items = queryset
    else:
        items = model_class.objects.all()

    if filter_config:
        # Populate options for select fields dynamically if not provided
        for config in filter_config:
            if config['type'] == 'select' and 'options' not in config:
                # Assuming the field name refers to a related model (e.g., 'workplace')
                # Or a field with choices
                try:
                    field_object = model_class._meta.get_field(config['field'])
                    if field_object.is_relation:
                        related_model = field_object.related_model
                        config['options'] = [(obj.pk, str(obj)) for obj in related_model.objects.all()]
                    elif field_object.choices:
                        config['options'] = field_object.choices
                except:
                    config['options'] = []

        items = apply_filters(items, filter_config, request.GET)

    context = {
        'items': items,
        'title': title,
        'create_url_name': create_url_name,
        'update_url_name': update_url_name,
        'bulk_delete_url_name': bulk_delete_url_name,
        'export_url_name': export_url_name,
        'import_url_name': import_url_name,
        'fields': fields_to_show,
        'filter_config': filter_config,
        'extra_actions': extra_actions,
    }
    return render(request, 'core/list_template.html', context)

def generic_import_view(request, model_class, title, list_url_name, step=1):
    handler = ImportHandler(request)

    # Step 1: Upload
    if step == 1:
        if request.method == 'POST':
            if 'import_file' in request.FILES:
                handler.save_file(request.FILES['import_file'])
                # Clear previous session data
                if 'import_mapping' in request.session: del request.session['import_mapping']
                if 'import_settings' in request.session: del request.session['import_settings']
                return redirect(f'import_{model_class.__name__.lower()}_step2')
        return render(request, 'core/import/import_step1.html', {'title': title, 'list_url_name': list_url_name})

    # Step 2: Settings
    elif step == 2:
        if request.method == 'POST':
            settings = {
                'delimiter': request.POST.get('delimiter', ';'),
                'date_format': request.POST.get('date_format', '%Y-%m-%d'),
                'encoding': request.POST.get('encoding', 'utf-8-sig')
            }
            request.session['import_settings'] = settings
            return redirect(f'import_{model_class.__name__.lower()}_step3')
        return render(request, 'core/import/import_step2.html', {'title': title})

    # Step 3: Mapping
    elif step == 3:
        settings = request.session.get('import_settings', {'delimiter': ';', 'encoding': 'utf-8-sig'})
        csv_headers = handler.get_headers(delimiter=settings['delimiter'], encoding=settings['encoding'])

        # Get Model Fields
        model_fields = []
        for field in model_class._meta.fields:
            if field.auto_created or field.name == 'id':
                continue

            field_type = field.get_internal_type()
            required = not field.blank and not field.null

            model_fields.append({
                'name': field.name,
                'verbose_name': field.verbose_name,
                'help_text': field.help_text,
                'required': required,
                'type': field_type
            })

        if request.method == 'POST':
            mapping = {}
            for field in model_fields:
                val = request.POST.get(f'map_{field["name"]}')
                mapping[field['name']] = val if val else None

            request.session['import_mapping'] = mapping
            return redirect(f'import_{model_class.__name__.lower()}_step4')

        return render(request, 'core/import/import_step3.html', {
            'title': title,
            'csv_headers': csv_headers,
            'model_fields': model_fields
        })

    # Step 4: Preview & Execute
    elif step == 4:
        settings = request.session.get('import_settings', {})
        mapping = request.session.get('import_mapping', {})

        if request.method == 'POST':
            count = handler.execute_import(
                model_class, mapping,
                delimiter=settings.get('delimiter', ';'),
                date_format=settings.get('date_format', '%Y-%m-%d'),
                encoding=settings.get('encoding', 'utf-8-sig')
            )
            messages.success(request, f'{count} kayıt başarıyla içe aktarıldı.')
            return redirect(list_url_name)

        summary = handler.get_preview_data(
            model_class, mapping,
            delimiter=settings.get('delimiter', ';'),
            date_format=settings.get('date_format', '%Y-%m-%d'),
            encoding=settings.get('encoding', 'utf-8-sig')
        )

        return render(request, 'core/import/import_step4.html', {'title': title, 'summary': summary})

    return redirect(list_url_name)

def generic_bulk_delete_view(request, model_class, list_url_name):
    if request.method == 'POST':
        selected_ids = request.POST.getlist('selected_items')
        if selected_ids:
            model_class.objects.filter(id__in=selected_ids).delete()
            messages.success(request, f'{len(selected_ids)} kayıt silindi.')
        else:
            messages.warning(request, 'Silinecek kayıt seçilmedi.')
    return redirect(list_url_name)

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

def generic_export_view(request, model_class, filter_config=None):
    queryset = model_class.objects.all()
    if filter_config:
         queryset = apply_filters(queryset, filter_config, request.GET)

    export_format = request.GET.get('format', 'csv')
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{model_class._meta.verbose_name_plural}_{timestamp}"

    # Get all field names
    field_names = [field.name for field in model_class._meta.fields]
    # Make header pretty (verbose names)
    headers = [field.verbose_name for field in model_class._meta.fields]

    if export_format == 'xlsx':
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename="{filename}.xlsx"'

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Export"

        ws.append(headers)

        for obj in queryset:
            row = []
            for field in field_names:
                val = getattr(obj, field)
                # Handle relations nicely (str representation)
                if hasattr(val, 'pk'): # It's a related object
                    val = str(val)
                # Handle choices nicely
                elif hasattr(obj, f'get_{field}_display'):
                    val = getattr(obj, f'get_{field}_display')()

                # Handle dates and None
                if val is None:
                    val = ""
                # Convert dates to string for Excel compatibility if needed,
                # but openpyxl handles datetime objects well.
                # Just ensuring timezone info is stripped if present/problematic
                if isinstance(val, datetime):
                     val = val.replace(tzinfo=None)

                row.append(val)
            ws.append(row)

        wb.save(response)
        return response

    else: # Default to CSV
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{filename}.csv"'
        response.write(u'\ufeff'.encode('utf8')) # BOM for Excel compatibility

        writer = csv.writer(response)
        writer.writerow(headers)

        for obj in queryset:
            row = []
            for field in field_names:
                val = getattr(obj, field)
                if hasattr(val, 'pk'):
                    val = str(val)
                elif hasattr(obj, f'get_{field}_display'):
                    val = getattr(obj, f'get_{field}_display')()
                if val is None:
                    val = ""
                row.append(val)
            writer.writerow(row)

        return response


# Specific Views using helpers
@login_required
def workplace_list(request):
    from django.db.models import Count, Max, Q, F, Case, When, IntegerField
    from datetime import date, timedelta

    # Calculate counts
    queryset = Workplace.objects.annotate(
        total_workers=Count('workers', distinct=True)
    )

    # We need to process validity in Python because logic is hazard-class dependent and complex for pure SQL/ORM
    # (specifically date differences varying by hazard class)
    # However, to keep it somewhat efficient, we can prefetch workers and their latest edu/exam dates.
    # But generic_list_view expects a queryset.

    # Let's try to annotate valid counts using conditional logic.
    # Validity Periods (Years):
    # Education: HIGH=1, MEDIUM=2, LOW=3
    # Examination: HIGH=1, MEDIUM=3, LOW=5

    today = date.today()

    # Helper for date subtraction expression is hard in Django ORM across different DBs (sqlite vs postgres).
    # Simple approach: fetch all and annotate in python, but generic_list_view needs a queryset to apply filters.
    # If we apply filters first, then annotate in Python, we break pagination or ordering if it was handled by generic view (it's not paginated currently).
    # But generic_list_view calls `apply_filters` on the passed queryset.

    # Let's do a hybrid approach:
    # 1. Apply annotations that are possible in SQL
    # 2. Iterate and update attributes (won't persist to DB but available in template)
    # Problem: generic_list_view renders fields using getattr.

    # Actually, we can define methods on the Workplace model, but they would be slow (N+1).
    # Better: Pre-calculate these values and stick them onto the objects.
    # But generic_list_view takes a queryset or class. If we pass a list, `apply_filters` (which does .filter()) will fail.

    # Revised approach:
    # Since the dataset is likely small (<1000 items based on "1-929" issue), we can:
    # 1. Get QuerySet.
    # 2. Convert to list.
    # 3. Annotate in Python.
    # 4. Pass list to generic_list_view?
    # generic_list_view does `if filter_config: items = apply_filters(items, ...)`
    # `apply_filters` uses `.filter()`. So `items` MUST be a QuerySet.

    # So we must annotate the QuerySet.
    # Since calculating dynamic date validity in SQL is painful and DB-dependent,
    # and given the user wants "count of workers who had education in time",
    # let's try a simplified approximation or exact SQL if possible.

    # Let's use Python iteration after the generic view does its filtering?
    # No, generic_list_view does everything.

    # Workaround:
    # Pass the queryset to generic_list_view.
    # But we can't easily annotate "valid_education_count" efficiently in pure ORM with SQLite without complex subqueries.
    # Let's add methods to Workplace that calculate this on the fly, and use prefetch_related to optimize.

    queryset = Workplace.objects.prefetch_related('workers__education_set', 'workers__examination_set')

    # We will attach the counts as properties/methods to the model or use a wrapper.
    # But generic_list_view uses `getattr(item, field_name)`.
    # If we define a property on the model `valid_education_count`, it can calculate it.
    # To avoid N+1, we rely on the prefetch.

    filter_config = [
        {'field': 'name', 'label': 'İşyeri Adı', 'type': 'text'},
        {'field': 'detsis_number', 'label': 'DETSİS No', 'type': 'text'},
        {'field': 'hazard_class', 'label': 'Tehlike Sınıfı', 'type': 'select'},
    ]

    # We need to wrap the queryset to calculate these counts when iterated,
    # OR we modify the generic_list_view to allow a "post-process" hook.
    # OR we just accept that we might iterate in the template.

    # Let's use model properties with prefetch.
    # I will modify Workplace model in the next step to add these properties using cached worker lists.
    # But wait, prefetch_related caches to `_prefetched_objects_cache`. Accessing `workplace.workers.all()` uses it.

    return generic_list_view(request, Workplace, "İşyerleri", 'workplace_create', 'workplace_update',
                             [('name', 'İşyeri Adı'),
                              ('get_hazard_class_display', 'Tehlike Sınıfı'),
                              ('total_workers_count', 'Toplam Çalışan'),
                              ('valid_education_count_display', 'Geçerli Eğitim'),
                              ('valid_examination_count_display', 'Geçerli Muayene'),
                              ('valid_first_aid_count_display', 'İlkyardım Sertifikası')],
                             'workplace_bulk_delete', 'workplace_export', filter_config, 'import_workplace_step1',
                             queryset=queryset)

@login_required
def workplace_import(request, step=1):
    return generic_import_view(request, Workplace, "İşyeri İçe Aktar", 'workplace_list', step=step)

@login_required
def workplace_bulk_delete(request):
    return generic_bulk_delete_view(request, Workplace, 'workplace_list')

@login_required
def workplace_export(request):
    filter_config = [
        {'field': 'name', 'type': 'text'},
        {'field': 'detsis_number', 'type': 'text'},
        {'field': 'hazard_class', 'type': 'select'},
    ]
    return generic_export_view(request, Workplace, filter_config)

@login_required
def workplace_create(request):
    return generic_create_view(request, WorkplaceForm, "Yeni İşyeri", 'workplace_list')

@login_required
def workplace_update(request, pk):
    item = get_object_or_404(Workplace, pk=pk)
    if request.method == 'POST':
        form = WorkplaceForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, 'Kayıt güncellendi.')
            return redirect('workplace_list')
    else:
        form = WorkplaceForm(instance=item)

    # Fetch facilities with their workers
    facilities = item.facilities.prefetch_related('worker_set').all()

    return render(request, 'core/workplace_form.html', {'form': form, 'title': "İşyeri Düzenle", 'facilities': facilities})

@login_required
def worker_list(request):
    filter_config = [
        {'field': 'name', 'label': 'Ad Soyad', 'type': 'text'},
        {'field': 'tckn', 'label': 'TCKN', 'type': 'text'},
        {'field': 'workplace', 'label': 'İşyeri', 'type': 'select'},
        {'field': 'profession', 'label': 'Meslek', 'type': 'select'},
    ]

    # Prefetch related data to optimize badge generation
    queryset = Worker.objects.select_related('workplace', 'facility').prefetch_related('education_set', 'examination_set')

    extra_actions = [
        {
            'url_name': 'examination_create',
            'label': 'Muayene Ekle',
            'icon': 'bi-heart-pulse',
            'btn_class': 'btn-outline-success',
            'query_param': 'worker_id'
        }
    ]

    return generic_list_view(request, Worker, "Çalışanlar", 'worker_create', 'worker_update',
                             [('name', 'Ad Soyad'),
                              ('tckn', 'TCKN'),
                              ('workplace', 'İşyeri'),
                              ('facility', 'Bina/Birim'),
                              ('education_status', 'Eğitim Durumu'),
                              ('examination_status', 'Muayene Durumu')],
                             'worker_bulk_delete', 'worker_export', filter_config, 'import_worker_step1',
                             queryset=queryset, extra_actions=extra_actions)

@login_required
def worker_import(request, step=1):
    return generic_import_view(request, Worker, "Çalışan İçe Aktar", 'worker_list', step=step)

@login_required
def worker_bulk_delete(request):
    return generic_bulk_delete_view(request, Worker, 'worker_list')

@login_required
def worker_export(request):
    filter_config = [
        {'field': 'name', 'type': 'text'},
        {'field': 'tckn', 'type': 'text'},
        {'field': 'workplace', 'type': 'select'},
        {'field': 'profession', 'type': 'select'},
    ]
    return generic_export_view(request, Worker, filter_config)

@login_required
def worker_create(request):
    if request.method == 'POST':
        form = WorkerForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Kayıt başarıyla oluşturuldu.')
            return redirect('worker_list')
    else:
        form = WorkerForm()
    return render(request, 'core/worker_form.html', {'form': form, 'title': "Yeni Çalışan"})

@login_required
def worker_update(request, pk):
    item = get_object_or_404(Worker, pk=pk)
    if request.method == 'POST':
        form = WorkerForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, 'Kayıt güncellendi.')
            return redirect('worker_list')
    else:
        form = WorkerForm(instance=item)

    examinations = item.examination_set.all().order_by('-date')
    return render(request, 'core/worker_form.html', {'form': form, 'title': "Çalışan Düzenle", 'examinations': examinations})

@login_required
def educator_list(request):
    filter_config = [
        {'field': 'name', 'label': 'Ad Soyad', 'type': 'text'},
        {'field': 'license_id', 'label': 'Lisans No', 'type': 'text'},
    ]
    return generic_list_view(request, Educator, "Eğiticiler", 'educator_create', 'educator_update',
                             [('name', 'Ad Soyad'), ('license_id', 'Lisans No')],
                             'educator_bulk_delete', 'educator_export', filter_config, 'import_educator_step1')

@login_required
def educator_import(request, step=1):
    return generic_import_view(request, Educator, "Eğitici İçe Aktar", 'educator_list', step=step)

@login_required
def educator_bulk_delete(request):
    return generic_bulk_delete_view(request, Educator, 'educator_list')

@login_required
def educator_export(request):
    filter_config = [
        {'field': 'name', 'type': 'text'},
        {'field': 'license_id', 'type': 'text'},
    ]
    return generic_export_view(request, Educator, filter_config)

@login_required
def educator_create(request):
    return generic_create_view(request, EducatorForm, "Yeni Eğitici", 'educator_list')

@login_required
def educator_update(request, pk):
    return generic_update_view(request, Educator, EducatorForm, pk, "Eğitici Düzenle", 'educator_list')

@login_required
def professional_list(request):
    filter_config = [
        {'field': 'name', 'label': 'Ad Soyad', 'type': 'text'},
        {'field': 'role', 'label': 'Görevi', 'type': 'select'},
    ]
    return generic_list_view(request, Professional, "Profesyoneller", 'professional_create', 'professional_update',
                             [('name', 'Ad Soyad'), ('license_id', 'Lisans No'), ('get_role_display', 'Görevi')],
                             'professional_bulk_delete', 'professional_export', filter_config, 'import_professional_step1')

@login_required
def professional_import(request, step=1):
    return generic_import_view(request, Professional, "Profesyonel İçe Aktar", 'professional_list', step=step)

@login_required
def professional_bulk_delete(request):
    return generic_bulk_delete_view(request, Professional, 'professional_list')

@login_required
def professional_export(request):
    filter_config = [
        {'field': 'name', 'type': 'text'},
        {'field': 'role', 'type': 'select'},
    ]
    return generic_export_view(request, Professional, filter_config)

@login_required
def professional_create(request):
    return generic_create_view(request, ProfessionalForm, "Yeni Profesyonel", 'professional_list')

@login_required
def professional_update(request, pk):
    return generic_update_view(request, Professional, ProfessionalForm, pk, "Profesyonel Düzenle", 'professional_list')

@login_required
def education_list(request):
    filter_config = [
        {'field': 'topic', 'label': 'Konu', 'type': 'text'},
        {'field': 'date', 'label': 'Tarih', 'type': 'date'},
        {'field': 'workplace', 'label': 'İşyeri', 'type': 'select'},
    ]
    return generic_list_view(request, Education, "İSG Eğitimleri", 'education_create', 'education_update',
                             [('date', 'Tarih'), ('topic', 'Konu'), ('workplace', 'İşyeri')],
                             'education_bulk_delete', 'education_export', filter_config, 'import_education_step1')

@login_required
def education_import(request, step=1):
    return generic_import_view(request, Education, "Eğitim İçe Aktar", 'education_list', step=step)

@login_required
def education_bulk_delete(request):
    return generic_bulk_delete_view(request, Education, 'education_list')

@login_required
def education_export(request):
    filter_config = [
        {'field': 'topic', 'type': 'text'},
        {'field': 'date', 'type': 'date'},
        {'field': 'workplace', 'type': 'select'},
    ]
    return generic_export_view(request, Education, filter_config)

@login_required
def education_create(request):
    if request.method == 'POST':
        form = EducationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Kayıt başarıyla oluşturuldu.')
            return redirect('education_list')
    else:
        form = EducationForm()
    return render(request, 'core/education_form.html', {'form': form, 'title': "Yeni Eğitim"})

@login_required
def education_update(request, pk):
    item = get_object_or_404(Education, pk=pk)
    if request.method == 'POST':
        form = EducationForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, 'Kayıt güncellendi.')
            return redirect('education_list')
    else:
        form = EducationForm(instance=item)
    return render(request, 'core/education_form.html', {'form': form, 'title': "Eğitim Düzenle"})

@login_required
def inspection_list(request):
    filter_config = [
        {'field': 'date', 'label': 'Tarih', 'type': 'date'},
        {'field': 'workplace', 'label': 'İşyeri', 'type': 'select'},
        {'field': 'professional', 'label': 'Denetleyen', 'type': 'select'},
    ]
    return generic_list_view(request, Inspection, "Denetimler", 'inspection_create', 'inspection_update',
                             [('date', 'Tarih'), ('workplace', 'İşyeri'), ('notes', 'Notlar')],
                             'inspection_bulk_delete', 'inspection_export', filter_config, 'import_inspection_step1')

@login_required
def inspection_import(request, step=1):
    return generic_import_view(request, Inspection, "Denetim İçe Aktar", 'inspection_list', step=step)

@login_required
def inspection_bulk_delete(request):
    return generic_bulk_delete_view(request, Inspection, 'inspection_list')

@login_required
def inspection_export(request):
    filter_config = [
        {'field': 'date', 'type': 'date'},
        {'field': 'workplace', 'type': 'select'},
        {'field': 'professional', 'type': 'select'},
    ]
    return generic_export_view(request, Inspection, filter_config)

@login_required
def inspection_create(request):
    return generic_create_view(request, InspectionForm, "Yeni Denetim", 'inspection_list')

@login_required
def inspection_update(request, pk):
    return generic_update_view(request, Inspection, InspectionForm, pk, "Denetim Düzenle", 'inspection_list')

@login_required
def examination_list(request):
    filter_config = [
        {'field': 'date', 'label': 'Tarih', 'type': 'date'},
        {'field': 'worker', 'label': 'Çalışan', 'type': 'select'},
        {'field': 'professional', 'label': 'Hekim', 'type': 'select'},
        {'field': 'decision', 'label': 'Karar', 'type': 'select'},
    ]
    return generic_list_view(request, Examination, "Sağlık Muayeneleri", 'examination_create', 'examination_update',
                             [('caution_icon_html', ''), ('date', 'Tarih'), ('worker', 'Çalışan'), ('get_decision_display', 'Karar')],
                             'examination_bulk_delete', 'examination_export', filter_config, 'import_examination_step1')

@login_required
def examination_import(request, step=1):
    return generic_import_view(request, Examination, "Muayene İçe Aktar", 'examination_list', step=step)

@login_required
def examination_bulk_delete(request):
    return generic_bulk_delete_view(request, Examination, 'examination_list')

@login_required
def examination_export(request):
    filter_config = [
        {'field': 'date', 'type': 'date'},
        {'field': 'worker', 'type': 'select'},
        {'field': 'professional', 'type': 'select'},
        {'field': 'decision', 'type': 'select'},
    ]
    return generic_export_view(request, Examination, filter_config)

@login_required
def examination_create(request):
    if request.method == 'POST':
        form = ExaminationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Kayıt başarıyla oluşturuldu.')
            return redirect('examination_list')
    else:
        initial_data = {}
        worker_id = request.GET.get('worker_id')
        if worker_id:
            worker = get_object_or_404(Worker, pk=worker_id)
            initial_data['worker'] = worker
        form = ExaminationForm(initial=initial_data)
    return render(request, 'core/examination_form.html', {'form': form, 'title': "Yeni Muayene"})

@login_required
def examination_update(request, pk):
    item = get_object_or_404(Examination, pk=pk)
    if request.method == 'POST':
        form = ExaminationForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, 'Kayıt güncellendi.')
            return redirect('examination_list')
    else:
        form = ExaminationForm(instance=item)
    return render(request, 'core/examination_form.html', {'form': form, 'title': "Muayene Düzenle"})

@login_required
def update_examination_note(request, pk):
    examination = get_object_or_404(Examination, pk=pk)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'delete':
            examination.caution_note = ''
            examination.is_caution = False
            examination.save()
            messages.success(request, 'Uyarı notu silindi.')
        else:
            form = ExaminationNoteForm(request.POST, instance=examination)
            if form.is_valid():
                examination.is_caution = True # Ensure flag is set if note is saved
                form.save()
                messages.success(request, 'Uyarı notu güncellendi.')
            else:
                messages.error(request, 'Hata oluştu.')
    return redirect('examination_list')

# Facility Views
@login_required
def facility_list(request):
    filter_config = [
        {'field': 'name', 'label': 'Bina/Birim Adı', 'type': 'text'},
        {'field': 'workplace', 'label': 'İşyeri', 'type': 'select'},
    ]
    return generic_list_view(request, Facility, "Binalar/Birimler", 'facility_create', 'facility_update',
                             [('name', 'Bina/Birim Adı'), ('workplace', 'İşyeri')],
                             'facility_bulk_delete', None, filter_config, None) # No export/import yet

@login_required
def facility_bulk_delete(request):
    return generic_bulk_delete_view(request, Facility, 'facility_list')

@login_required
def facility_create(request):
    return generic_create_view(request, FacilityForm, "Yeni Bina/Birim", 'facility_list')

@login_required
def facility_update(request, pk):
    return generic_update_view(request, Facility, FacilityForm, pk, "Bina/Birim Düzenle", 'facility_list')

@login_required
def facility_import(request, step=1):
    return generic_import_view(request, Facility, "Bina/Birim İçe Aktar", 'facility_list', step=step)

@login_required
def profession_list(request):
    filter_config = [{'field': 'name', 'label': 'Meslek Adı', 'type': 'text'}]
    return generic_list_view(request, Profession, "Meslekler", 'profession_create', 'profession_update',
                             [('name', 'Meslek Adı')],
                             'profession_bulk_delete', 'profession_export', filter_config, 'import_profession_step1')

@login_required
def profession_bulk_delete(request):
    return generic_bulk_delete_view(request, Profession, 'profession_list')

@login_required
def profession_export(request):
    return generic_export_view(request, Profession, [{'field': 'name', 'type': 'text'}])

@login_required
def profession_import(request, step=1):
    return generic_import_view(request, Profession, "Meslek İçe Aktar", 'profession_list', step=step)

@login_required
def profession_create(request):
    return generic_create_view(request, ProfessionForm, "Yeni Meslek", 'profession_list')

@login_required
def profession_update(request, pk):
    return generic_update_view(request, Profession, ProfessionForm, pk, "Meslek Düzenle", 'profession_list')

# Statistics Configuration
STATISTICS_CONFIG = {
    'Workplace': {
        'fields': [
            {'name': 'hazard_class', 'label': 'Tehlike Sınıfı', 'type': 'category'},
        ]
    },
    'Worker': {
        'fields': [
            {'name': 'workplace__name', 'label': 'İşyeri', 'type': 'category'},
            {'name': 'gender', 'label': 'Cinsiyet', 'type': 'category'},
            {'name': 'profession__name', 'label': 'Meslek', 'type': 'category'},
        ]
    },
    'Examination': {
        'fields': [
            {'name': 'decision', 'label': 'Karar', 'type': 'category'},
            {'name': 'worker__workplace__name', 'label': 'İşyeri', 'type': 'category'},
            {'name': 'professional__name', 'label': 'Hekim', 'type': 'category'},
            {'name': 'date', 'label': 'Tarih', 'type': 'date'},
        ]
    },
    'Education': {
        'fields': [
            {'name': 'topic', 'label': 'Konu', 'type': 'category'},
            {'name': 'educator__name', 'label': 'Eğitici', 'type': 'category'},
            {'name': 'workplace__name', 'label': 'İşyeri', 'type': 'category'},
            {'name': 'date', 'label': 'Tarih', 'type': 'date'},
        ]
    }
}

@login_required
def statistics_view(request):
    return render(request, 'core/statistics.html', {'config': STATISTICS_CONFIG})

@login_required
def api_get_statistics(request):
    model_name = request.GET.get('model')
    x_field = request.GET.get('x_field')
    y_field = request.GET.get('y_field') # Optional Grouping

    if not model_name or not x_field:
        return JsonResponse({'error': 'Missing parameters'}, status=400)

    # Resolve Model
    model_map = {
        'Workplace': Workplace,
        'Worker': Worker,
        'Examination': Examination,
        'Education': Education
    }
    model_class = model_map.get(model_name)
    if not model_class:
        return JsonResponse({'error': 'Invalid model'}, status=400)

    queryset = model_class.objects.all()

    # Aggregation
    try:
        from django.db.models import Count
        if y_field:
            data = list(queryset.values(x_field, y_field).annotate(count=Count('id')).order_by(x_field, y_field))
        else:
            data = list(queryset.values(x_field).annotate(count=Count('id')).order_by(x_field))

        # Helper to find field object
        def get_field_choices(model, field_path):
            parts = field_path.split('__')
            current_model = model
            field = None
            for part in parts:
                try:
                    field = current_model._meta.get_field(part)
                    if field.is_relation and field.related_model:
                        current_model = field.related_model
                except: return None
            return field.choices if field else None

        x_choices = get_field_choices(model_class, x_field)
        y_choices = get_field_choices(model_class, y_field) if y_field else None

        processed_data = []
        for row in data:
            x_val = row[x_field]
            y_val = row.get(y_field)

            # Map X
            if x_choices:
                for k, v in x_choices:
                    if str(k) == str(x_val):
                        x_val = v; break

            # Map Y
            if y_field and y_choices:
                for k, v in y_choices:
                    if str(k) == str(y_val):
                        y_val = v; break

            # Handle None
            if x_val is None: x_val = "Belirtilmemiş"
            if y_field and y_val is None: y_val = "Belirtilmemiş"

            item = {'x': x_val, 'count': row['count']}
            if y_field:
                item['y'] = y_val
            processed_data.append(item)

        return JsonResponse({'data': processed_data})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
