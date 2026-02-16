"""
Risk Library Utility Module

Reads and combines all JSON risk files from the external data directory.
"""

import os
import json
from django.conf import settings


def get_risk_library():
    """
    Read all JSON files from static/external_data/risks/ directory
    and return a combined list of risk objects with unique IDs.
    
    Returns:
        list: Combined list of risk dictionaries with added 'id' field
    """
    risks_dir = os.path.join(settings.BASE_DIR, 'static', 'external_data', 'risks')
    combined_risks = []
    risk_id = 0
    
    if not os.path.exists(risks_dir):
        return []
    
    for filename in os.listdir(risks_dir):
        if filename.endswith('.json'):
            filepath = os.path.join(risks_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        for item in data:
                            risk_id += 1
                            item['id'] = risk_id
                            item['source_file'] = filename
                            combined_risks.append(item)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error reading {filename}: {e}")
                continue
    
    return combined_risks


def get_risk_categories():
    """
    Extract unique category names (Grup Adı) from the risk library.
    
    Returns:
        list: Sorted list of unique category names
    """
    risks = get_risk_library()
    categories = set()
    
    for risk in risks:
        group_name = risk.get('Grup Adı', '').strip()
        if group_name:
            categories.add(group_name)
    
    return sorted(categories)


def search_risks(query='', category='', limit=100, offset=0):
    """
    Search and filter risks from the library.
    
    Args:
        query: Text search query (searches in Tehlike and Risk fields)
        category: Filter by Grup Adı
        limit: Maximum number of results
        offset: Starting offset for pagination
        
    Returns:
        dict: {'results': list, 'total': int, 'has_more': bool}
    """
    all_risks = get_risk_library()
    filtered = []
    
    query_lower = query.lower().strip() if query else ''
    category_lower = category.lower().strip() if category else ''
    
    for risk in all_risks:
        # Category filter
        if category_lower:
            risk_category = risk.get('Grup Adı', '').lower()
            if category_lower not in risk_category:
                continue
        
        # Text search
        if query_lower:
            tehlike = risk.get('Tehlike', '').lower()
            risk_text = risk.get('Risk', '').lower()
            konu = risk.get('Konu', '').lower()
            
            if query_lower not in tehlike and query_lower not in risk_text and query_lower not in konu:
                continue
        
        filtered.append(risk)
    
    total = len(filtered)
    paginated = filtered[offset:offset + limit]
    
    return {
        'results': paginated,
        'total': total,
        'has_more': (offset + limit) < total
    }
