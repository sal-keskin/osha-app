"""
Shared helper functions for Word and PDF report exports.
"""
from datetime import timedelta


STRATEGY_MAP = {
    'ELIMINATE': 'Yok Etme',
    'SUBSTITUTE': 'Yerine Koyma',
    'ENGINEERING': 'Mühendislik Kontrolleri',
    'ADMINISTRATIVE': 'İdari Önlemler',
    'PPE': 'KKD Kullanımı',
}

HAZARD_CLASS_MAP = {
    'HIGH': 'Çok Tehlikeli',
    'MEDIUM': 'Tehlikeli',
    'LOW': 'Az Tehlikeli',
}

# Risk değerlendirmesi geçerlilik süreleri (yıl)
VALIDITY_YEARS = {
    'HIGH': 2,
    'MEDIUM': 4,
    'LOW': 6,
}


def get_scoring_label(session):
    if session.scoring_method == 'MATRIX':
        return 'L-Matris (5×5) P × S'
    return 'Fine-Kinney (P × F × S)'


def get_validity_date(session):
    """Calculate Geçerlilik Tarihi from assessment date + hazard class."""
    workplace = session.facility.workplace
    years = VALIDITY_YEARS.get(workplace.hazard_class, 6)
    return session.created_at + timedelta(days=365 * years)


def get_risk_level_label(score, method):
    if not score:
        return '-'
    if method == 'MATRIX':
        if score >= 20: return 'Tolerans gösterilemez'
        if score >= 12: return 'Önemli'
        if score >= 6:  return 'Orta'
        if score >= 3:  return 'Düşük'
        return 'Önemsiz'
    else:  # KINNEY
        if score >= 400: return 'Tolerans gösterilemez'
        if score >= 200: return 'Esaslı'
        if score >= 70:  return 'Önemli'
        if score >= 20:  return 'Olası'
        return 'Önemsiz'


def get_level_color(label):
    colors = {
        'Tolerans gösterilemez': '#DC2626',
        'Esaslı': '#EA580C',
        'Önemli': '#F97316',
        'Olası': '#FBBF24',
        'Orta': '#FBBF24',
        'Düşük': '#22C55E',
        'Önemsiz': '#22C55E',
    }
    return colors.get(label, '#9CA3AF')


def get_level_text_color(label):
    if label in ('Tolerans gösterilemez', 'Esaslı', 'Önemli', 'Düşük', 'Önemsiz'):
        return '#FFFFFF'
    return '#1F2937'


def get_cover_page_data(session):
    """Gather all cover page info from session → facility → workplace."""
    workplace = session.facility.workplace
    is_kinney = session.scoring_method != 'MATRIX'
    validity_date = get_validity_date(session)

    return {
        'workplace_name': workplace.name,
        'address': workplace.address or '-',
        'nace_code': workplace.nace_code or '-',
        'hazard_class': HAZARD_CLASS_MAP.get(workplace.hazard_class, '-'),
        'hazard_class_raw': workplace.hazard_class,
        'activity': workplace.activity_description or '-',
        'facility_name': session.facility.name,
        'scoring_label': get_scoring_label(session),
        'assessment_date': session.created_at.strftime('%d.%m.%Y'),
        'validity_date': validity_date.strftime('%d.%m.%Y'),
        'validity_years': VALIDITY_YEARS.get(workplace.hazard_class, 6),
        'status': session.get_status_display(),
        'participants': session.participants or '-',
        'is_kinney': is_kinney,
    }


def get_methodology_text(is_kinney):
    if is_kinney:
        return """Bu değerlendirme, Fine-Kinney (P × F × S) risk puanlama yöntemi kullanılarak gerçekleştirilmiştir.

Olasılık (P) × Frekans (F) × Şiddet (S) = Risk Skoru

Risk skoru eşik değerleri:
• < 20: Önemsiz Risk — Kabul edilebilir
• 20-69: Olası Risk — Gözetim altında tutulmalı
• 70-199: Önemli Risk — Düzeltici faaliyet planlanmalı
• 200-399: Esaslı Risk — Kısa vadede önlem alınmalı
• ≥ 400: Tolerans Gösterilemez — Derhal çalışma durdurulmalı"""
    else:
        return """Bu değerlendirme, L-Matris (5×5) risk puanlama yöntemi kullanılarak gerçekleştirilmiştir.

Olasılık (P) × Şiddet (S) = Risk Skoru (1-25 arası)

Risk skoru eşik değerleri:
• 1-2: Önemsiz Risk
• 3-5: Düşük Risk
• 6-11: Orta Risk
• 12-19: Önemli Risk
• 20-25: Tolerans Gösterilemez"""


def build_risk_data(session):
    """Build structured risk data list for both exports."""
    is_kinney = session.scoring_method != 'MATRIX'
    custom_risks = list(session.custom_risks.all().prefetch_related('custom_measures', 'control_records'))
    method = 'KINNEY' if is_kinney else 'MATRIX'

    risks = []
    level_counts = {}
    scored_count = 0

    for idx, cr in enumerate(custom_risks, 1):
        if is_kinney:
            score = cr.kinney_score
            p, f, s = cr.kinney_probability, cr.kinney_frequency, cr.kinney_severity
        else:
            score = cr.matrix_score
            p, s = cr.matrix_probability, cr.matrix_severity
            f = None

        level = get_risk_level_label(score, method)

        if score:
            scored_count += 1
            level_counts[level] = level_counts.get(level, 0) + 1

        strategy = STRATEGY_MAP.get(cr.mitigation_strategy, cr.mitigation_strategy or '-')
        budget = f'{cr.estimated_budget:,.2f} ₺' if cr.estimated_budget else '-'
        due = cr.due_date.strftime('%d.%m.%Y') if cr.due_date else '-'

        risks.append({
            'no': idx,
            'category': cr.category or '-',
            'description': cr.description or '-',
            'legal_basis': cr.legal_basis or '-',
            'p': p, 'f': f, 's': s,
            'score': score,
            'level': level,
            'level_color': get_level_color(level),
            'level_text_color': get_level_text_color(level),
            'measure': cr.measure or '-',
            'strategy': strategy,
            'budget': budget,
            'responsible': cr.responsible_person or '-',
            'due_date': due,
        })

    unscored = len(custom_risks) - scored_count

    summary = []
    for lvl, cnt in sorted(level_counts.items(), key=lambda x: x[1], reverse=True):
        summary.append({'level': lvl, 'count': cnt, 'color': get_level_color(lvl), 'text_color': get_level_text_color(lvl)})
    if unscored > 0:
        summary.append({'level': 'Puanlanmamış', 'count': unscored, 'color': '#9CA3AF', 'text_color': '#FFFFFF'})

    return {
        'risks': risks,
        'summary': summary,
        'total': len(custom_risks),
        'is_kinney': is_kinney,
    }


def get_team_signatures(session):
    """Build team member list for signatures."""
    members = list(session.team_members.all())
    if members:
        return [{'role': m.get_role_display(), 'name': m.name, 'title': m.title or ''} for m in members]
    # Default roles
    return [
        {'role': 'İşveren / Vekili', 'name': '', 'title': ''},
        {'role': 'İSG Uzmanı', 'name': '', 'title': ''},
        {'role': 'İş Yeri Hekimi', 'name': '', 'title': ''},
        {'role': 'Çalışan Temsilcisi', 'name': '', 'title': ''},
    ]
