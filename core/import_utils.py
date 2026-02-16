import csv
import os
from datetime import datetime
from django.core.files.storage import FileSystemStorage
from django.conf import settings
from django.db import models
from django.utils.dateparse import parse_date

class ImportHandler:
    def __init__(self, request):
        self.request = request
        self.session = request.session
        self.fs = FileSystemStorage(location=os.path.join(settings.BASE_DIR, 'tmp_uploads'))

    def save_file(self, file_obj):
        filename = self.fs.save(file_obj.name, file_obj)
        self.session['import_file_path'] = self.fs.path(filename)
        return filename

    def get_file_path(self):
        return self.session.get('import_file_path')

    def get_headers(self, delimiter=';', encoding='utf-8-sig'):
        path = self.get_file_path()
        if not path or not os.path.exists(path):
            return []

        try:
            with open(path, 'r', encoding=encoding) as f:
                reader = csv.reader(f, delimiter=delimiter)
                headers = next(reader)
                return headers
        except Exception:
            return []

    def get_preview_data(self, model_class, mapping, delimiter=';', date_format='%Y-%m-%d', encoding='utf-8-sig'):
        path = self.get_file_path()
        if not path or not os.path.exists(path):
            return {'error': 'File not found'}

        uppercase_names = self.session.get('import_settings', {}).get('uppercase_names', False)

        preview_rows = []
        valid_count = 0
        error_count = 0
        total_count = 0

        try:
            with open(path, 'r', encoding=encoding) as f:
                reader = csv.DictReader(f, delimiter=delimiter)

                for row_idx, row in enumerate(reader):
                    total_count += 1
                    model_data = {}
                    errors = []

                    for model_field, csv_header in mapping.items():
                        if not csv_header: # Skipped field
                            continue

                        val = row.get(csv_header, '').strip()
                        field_obj = model_class._meta.get_field(model_field)

                        # Empty check
                        if val == '' and not field_obj.blank and not field_obj.null:
                            errors.append(f"{model_field}: Bu alan boş bırakılamaz.")
                            continue

                        if val == '':
                            if isinstance(field_obj, models.BooleanField):
                                model_data[model_field] = False
                                continue
                            model_data[model_field] = None
                            continue

                        # Type Conversion & Validation
                        try:
                            if isinstance(field_obj, models.DateField):
                                model_data[model_field] = datetime.strptime(val, date_format).date()

                            elif isinstance(field_obj, models.ForeignKey):
                                rel_model = field_obj.related_model
                                # Try ID first
                                if val.isdigit():
                                    try:
                                        rel_obj = rel_model.objects.get(pk=int(val))
                                        model_data[model_field] = rel_obj
                                    except rel_model.DoesNotExist:
                                        errors.append(f"{model_field}: ID {val} ile kayıt bulunamadı.")
                                else:
                                    # Build filter - try name match
                                    filter_kwargs = {}
                                    if hasattr(rel_model, 'name'):
                                        filter_kwargs['name__iexact'] = val
                                    else:
                                        errors.append(f"{model_field}: '{val}' değeri ile kayıt bulunamadı.")
                                        continue
                                    
                                    # Special case: filter Facility by Workplace if already resolved
                                    if model_field == 'facility' and 'workplace' in model_data:
                                        filter_kwargs['workplace'] = model_data['workplace']
                                    
                                    qs = rel_model.objects.filter(**filter_kwargs)
                                    if qs.exists():
                                        model_data[model_field] = qs.first()
                                    else:
                                        errors.append(f"{model_field}: '{val}' değeri ile kayıt bulunamadı.")

                            elif field_obj.choices:
                                # Try to match human readable label or key
                                found = False
                                for key, label in field_obj.choices:
                                    if str(key) == val or str(label).lower() == val.lower():
                                        model_data[model_field] = key
                                        found = True
                                        break
                                if not found:
                                    errors.append(f"{model_field}: '{val}' geçerli bir seçenek değil.")

                            else:
                                model_data[model_field] = val

                        except ValueError as e:
                             errors.append(f"{model_field}: Format hatası ({val})")

                    # Unique Check (Simple)
                    if not errors:
                         # Exclude ManyToMany for uniqueness check initially
                        check_data = {k: v for k, v in model_data.items() if not isinstance(model_class._meta.get_field(k), models.ManyToManyField)}
                        if model_class.objects.filter(**check_data).exists():
                             errors.append("Bu kayıt zaten mevcut.")

                    status = 'Valid' if not errors else 'Error'
                    if status == 'Valid':
                        valid_count += 1
                    else:
                        error_count += 1

                    if len(preview_rows) < 10: # Only show first 10
                         preview_rows.append({
                             'row_idx': row_idx + 1,
                             'data': model_data,
                             'original': row,
                             'errors': errors,
                             'status': status
                         })

        except Exception as e:
            return {'error': str(e)}

        return {
            'total': total_count,
            'valid': valid_count,
            'error': error_count,
            'rows': preview_rows
        }

    def execute_import(self, model_class, mapping, delimiter=';', date_format='%Y-%m-%d', encoding='utf-8-sig'):
        path = self.get_file_path()
        if not path or not os.path.exists(path):
            return 0  # No file to import
        
        uppercase_names = self.session.get('import_settings', {}).get('uppercase_names', False)
        success_count = 0

        # Import models locally to avoid circular imports and check types
        from .models import Workplace, Facility

        try:
            with open(path, 'r', encoding=encoding) as f:
                reader = csv.DictReader(f, delimiter=delimiter)
                for row in reader:
                    model_data = {}
                    m2m_data = {}
                    skip = False

                    for model_field, csv_header in mapping.items():
                        if not csv_header: continue
                        val = row.get(csv_header, '').strip()
                        field_obj = model_class._meta.get_field(model_field)

                        if val == '':
                            if not field_obj.blank and not field_obj.null:
                                # Special case for BooleanField with default
                                if isinstance(field_obj, models.BooleanField):
                                    model_data[model_field] = False
                                    continue
                                skip = True; break

                            if isinstance(field_obj, models.BooleanField):
                                 model_data[model_field] = False
                                 continue

                            model_data[model_field] = None
                            continue

                        try:
                            if isinstance(field_obj, models.DateField):
                                model_data[model_field] = datetime.strptime(val, date_format).date()
                            elif isinstance(field_obj, models.ForeignKey):
                                rel_model = field_obj.related_model
                                if val.isdigit():
                                    try:
                                        model_data[model_field] = rel_model.objects.get(pk=int(val))
                                    except rel_model.DoesNotExist:
                                        skip = True; break
                                else:
                                    # Build filter - first try name match
                                    filter_kwargs = {}
                                    if hasattr(rel_model, 'name'):
                                        filter_kwargs['name__iexact'] = val
                                    else:
                                        # Fallback to pk if no name field
                                        skip = True; break
                                    
                                    # Special case: filter Facility by Workplace if already resolved
                                    if model_field == 'facility' and 'workplace' in model_data:
                                        filter_kwargs['workplace'] = model_data['workplace']
                                    
                                    qs = rel_model.objects.filter(**filter_kwargs)
                                    if qs.exists():
                                        model_data[model_field] = qs.first()
                                    else:
                                        skip = True; break
                            elif isinstance(field_obj, models.ManyToManyField):
                                # Handle M2M later
                                pass
                            elif field_obj.choices:
                                found_choice = False
                                for key, label in field_obj.choices:
                                    if str(key) == val or str(label).lower() == val.lower():
                                        model_data[model_field] = key
                                        found_choice = True
                                        break
                                if not found_choice:
                                    skip = True; break
                            else:
                                if uppercase_names and isinstance(val, str):
                                    model_data[model_field] = val.replace('i', 'İ').upper()
                                else:
                                    model_data[model_field] = val
                        except Exception:
                            skip = True; break

                    if skip: continue

                    # Check exist
                    check_data = {k: v for k, v in model_data.items() if not isinstance(model_class._meta.get_field(k), models.ManyToManyField)}
                    if not model_class.objects.filter(**check_data).exists():
                        obj = model_class.objects.create(**check_data)
                        success_count += 1

                        # Auto-create Facility for Workplace
                        if model_class == Workplace:
                            Facility.objects.create(name="MERKEZ BİNA", workplace=obj)

        except Exception as e:
            # Log the error but don't crash
            import logging
            logging.error(f"Import error: {e}")
            return success_count

        return success_count

