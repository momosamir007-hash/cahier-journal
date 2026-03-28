# -*- coding: utf-8 -*-
"""
🎓 الكراس اليومي — قسم التحضيري
الإصدار 4.0 — استخراج مُحسَّن + تشخيص
"""

import streamlit as st
import re
import copy
from io import BytesIO
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn


# ╔══════════════════════════════════════════════════════╗
# ║  القسم 1: الثوابت والتوقيت                          ║
# ╚══════════════════════════════════════════════════════╝

ROUTINE_ACTIVITIES = [
    "الاستقبال", "الاستراحة", "تهيئة الخروج", "نهاية الخروج",
]

DOMAIN_MAPPING = {
    "تعبير شفوي":           "المجال اللغوي",
    "مبادئ القراءة":        "المجال اللغوي",
    "تخطيط":                "المجال اللغوي",
    "رياضيات":              "المجال الرياضي",
    "ت علمية وتكنولوجية":   "المجال العلمي",
    "ت إسلامية":            "المجال الاجتماعي",
    "ت مدنية":              "المجال الاجتماعي",
    "تربية تشكيلية":        "المجال الفني",
    "موسيقى وإنشاد":       "المجال الفني",
    "مسرح وعرائس":         "المجال الفني",
    "ت بدنية":              "المجال البدني والإيقاعي",
    "ت إيقاعية":            "المجال البدني والإيقاعي",
}

SUBJECT_WEEKLY_COUNT = {
    "تعبير شفوي": 3, "مبادئ القراءة": 4, "تخطيط": 2,
    "رياضيات": 5, "ت علمية وتكنولوجية": 4,
    "ت إسلامية": 2, "ت مدنية": 2,
    "تربية تشكيلية": 2, "موسيقى وإنشاد": 2, "مسرح وعرائس": 2,
    "ت بدنية": 4, "ت إيقاعية": 2,
}

# قاموس توحيد شامل جداً
NAME_MAPPING = {
    # ── التربية العلمية والتكنولوجية ──
    "تربية علمية":                  "ت علمية وتكنولوجية",
    "تربية تكنولوجية":              "ت علمية وتكنولوجية",
    "تربية علمية وتكنولوجية":       "ت علمية وتكنولوجية",
    "ت علمية":                      "ت علمية وتكنولوجية",
    "ت تكنولوجية":                  "ت علمية وتكنولوجية",
    "علوم وتكنولوجيا":              "ت علمية وتكنولوجية",
    "ت علمية و تكنولوجية":          "ت علمية وتكنولوجية",
    "تربية علمية و تكنولوجية":      "ت علمية وتكنولوجية",
    "التربية العلمية":              "ت علمية وتكنولوجية",
    "التربية التكنولوجية":          "ت علمية وتكنولوجية",
    "التربية العلمية والتكنولوجية": "ت علمية وتكنولوجية",
    "علمية وتكنولوجية":             "ت علمية وتكنولوجية",
    "علمية":                        "ت علمية وتكنولوجية",
    "تكنولوجية":                    "ت علمية وتكنولوجية",

    # ── التعبير الشفوي ──
    "تعبير":                        "تعبير شفوي",
    "التعبير الشفوي":               "تعبير شفوي",
    "التعبير":                      "تعبير شفوي",
    "تعبير شفهي":                   "تعبير شفوي",
    "شفوي":                         "تعبير شفوي",
    "التعبير الشفهي":               "تعبير شفوي",

    # ── القراءة ──
    "قراءة":                        "مبادئ القراءة",
    "مبادئ في القراءة":             "مبادئ القراءة",
    "القراءة":                      "مبادئ القراءة",
    "مبادئ قراءة":                  "مبادئ القراءة",
    "مبادىء القراءة":               "مبادئ القراءة",
    "مبادىء في القراءة":            "مبادئ القراءة",

    # ── التخطيط / الكتابة ──
    "كتابة":                        "تخطيط",
    "خط":                           "تخطيط",
    "مبادئ التخطيط":                "تخطيط",
    "مبادئ في التخطيط":             "تخطيط",
    "مبادئ الكتابة":                "تخطيط",
    "الكتابة":                      "تخطيط",
    "الخط":                         "تخطيط",
    "مبادىء التخطيط":               "تخطيط",
    "مبادىء الكتابة":               "تخطيط",

    # ── الرياضيات ──
    "الرياضيات":                    "رياضيات",
    "رياضيات":                      "رياضيات",

    # ── التربية الإسلامية ──
    "تربية إسلامية":                "ت إسلامية",
    "التربية الإسلامية":            "ت إسلامية",
    "إسلامية":                      "ت إسلامية",
    "ت اسلامية":                    "ت إسلامية",
    "تربية اسلامية":                "ت إسلامية",
    "التربية الاسلامية":            "ت إسلامية",

    # ── التربية المدنية ──
    "تربية مدنية":                  "ت مدنية",
    "التربية المدنية":              "ت مدنية",
    "مدنية":                        "ت مدنية",

    # ── التربية التشكيلية ──
    "رسم":                          "تربية تشكيلية",
    "رسم وأشغال":                  "تربية تشكيلية",
    "أشغال يدوية":                  "تربية تشكيلية",
    "تربية فنية":                   "تربية تشكيلية",
    "فنون تشكيلية":                 "تربية تشكيلية",
    "التربية التشكيلية":            "تربية تشكيلية",
    "تشكيلية":                      "تربية تشكيلية",
    "رسم و أشغال":                  "تربية تشكيلية",

    # ── الموسيقى والإنشاد ──
    "موسيقى":                       "موسيقى وإنشاد",
    "إنشاد":                        "موسيقى وإنشاد",
    "تربية موسيقية":                "موسيقى وإنشاد",
    "الموسيقى":                     "موسيقى وإنشاد",
    "موسيقى و إنشاد":               "موسيقى وإنشاد",
    "الموسيقى والإنشاد":            "موسيقى وإنشاد",
    "التربية الموسيقية":            "موسيقى وإنشاد",

    # ── المسرح والعرائس ──
    "مسرح":                         "مسرح وعرائس",
    "المسرح":                       "مسرح وعرائس",
    "مسرح و عرائس":                 "مسرح وعرائس",
    "المسرح والعرائس":              "مسرح وعرائس",

    # ── التربية البدنية ──
    "تربية بدنية":                  "ت بدنية",
    "تربية بدنية ورياضية":          "ت بدنية",
    "التربية البدنية":              "ت بدنية",
    "بدنية":                        "ت بدنية",
    "التربية البدنية والرياضية":    "ت بدنية",

    # ── التربية الإيقاعية ──
    "تربية إيقاعية":                "ت إيقاعية",
    "التربية الإيقاعية":            "ت إيقاعية",
    "إيقاعية":                      "ت إيقاعية",
    "ت ايقاعية":                    "ت إيقاعية",
    "تربية ايقاعية":                "ت إيقاعية",
}

DOMAIN_COLORS = {
    "المجال اللغوي":                "#1565C0",
    "المجال الرياضي":               "#C62828",
    "المجال العلمي":                "#2E7D32",
    "المجال الاجتماعي":             "#F57F17",
    "المجال الفني":                 "#6A1B9A",
    "المجال البدني والإيقاعي":      "#00838F",
}

weekly_schedule = {
    "الأحد": [
        {"النشاط": "الاستقبال",             "المدة": "15 د", "الفترة": "صباحية"},
        {"النشاط": "تعبير شفوي",            "المدة": "30 د", "الفترة": "صباحية"},
        {"النشاط": "مبادئ القراءة",          "المدة": "30 د", "الفترة": "صباحية"},
        {"النشاط": "رياضيات",               "المدة": "30 د", "الفترة": "صباحية"},
        {"النشاط": "ت علمية وتكنولوجية",    "المدة": "30 د", "الفترة": "صباحية"},
        {"النشاط": "ت إسلامية",             "المدة": "30 د", "الفترة": "صباحية"},
        {"النشاط": "تهيئة الخروج",          "المدة": "15 د", "الفترة": "صباحية"},
        {"النشاط": "الاستقبال",             "المدة": "15 د", "الفترة": "مسائية"},
        {"النشاط": "مسرح وعرائس",          "المدة": "30 د", "الفترة": "مسائية"},
        {"النشاط": "تربية تشكيلية",         "المدة": "30 د", "الفترة": "مسائية"},
        {"النشاط": "ت بدنية",               "المدة": "30 د", "الفترة": "مسائية"},
        {"النشاط": "نهاية الخروج",          "المدة": "15 د", "الفترة": "مسائية"},
    ],
    "الإثنين": [
        {"النشاط": "الاستقبال",             "المدة": "15 د", "الفترة": "صباحية"},
        {"النشاط": "رياضيات",               "المدة": "30 د", "الفترة": "صباحية"},
        {"النشاط": "تعبير شفوي",            "المدة": "30 د", "الفترة": "صباحية"},
        {"النشاط": "تخطيط",                 "المدة": "30 د", "الفترة": "صباحية"},
        {"النشاط": "ت علمية وتكنولوجية",    "المدة": "30 د", "الفترة": "صباحية"},
        {"النشاط": "ت مدنية",               "المدة": "30 د", "الفترة": "صباحية"},
        {"النشاط": "تهيئة الخروج",          "المدة": "15 د", "الفترة": "صباحية"},
        {"النشاط": "الاستقبال",             "المدة": "15 د", "الفترة": "مسائية"},
        {"النشاط": "مسرح وعرائس",          "المدة": "30 د", "الفترة": "مسائية"},
        {"النشاط": "تربية تشكيلية",         "المدة": "30 د", "الفترة": "مسائية"},
        {"النشاط": "ت بدنية",               "المدة": "30 د", "الفترة": "مسائية"},
        {"النشاط": "نهاية الخروج",          "المدة": "15 د", "الفترة": "مسائية"},
    ],
    "الثلاثاء": [
        {"النشاط": "الاستقبال",             "المدة": "15 د", "الفترة": "صباحية"},
        {"النشاط": "تعبير شفوي",            "المدة": "30 د", "الفترة": "صباحية"},
        {"النشاط": "مبادئ القراءة",          "المدة": "30 د", "الفترة": "صباحية"},
        {"النشاط": "رياضيات",               "المدة": "30 د", "الفترة": "صباحية"},
        {"النشاط": "ت إسلامية",             "المدة": "30 د", "الفترة": "صباحية"},
        {"النشاط": "ت بدنية",               "المدة": "30 د", "الفترة": "صباحية"},
        {"النشاط": "تهيئة الخروج",          "المدة": "15 د", "الفترة": "صباحية"},
    ],
    "الأربعاء": [
        {"النشاط": "الاستقبال",             "المدة": "15 د", "الفترة": "صباحية"},
        {"النشاط": "رياضيات",               "المدة": "30 د", "الفترة": "صباحية"},
        {"النشاط": "مبادئ القراءة",          "المدة": "30 د", "الفترة": "صباحية"},
        {"النشاط": "تخطيط",                 "المدة": "30 د", "الفترة": "صباحية"},
        {"النشاط": "ت علمية وتكنولوجية",    "المدة": "30 د", "الفترة": "صباحية"},
        {"النشاط": "ت مدنية",               "المدة": "30 د", "الفترة": "صباحية"},
        {"النشاط": "تهيئة الخروج",          "المدة": "15 د", "الفترة": "صباحية"},
        {"النشاط": "الاستقبال",             "المدة": "15 د", "الفترة": "مسائية"},
        {"النشاط": "ت إيقاعية",             "المدة": "30 د", "الفترة": "مسائية"},
        {"النشاط": "موسيقى وإنشاد",        "المدة": "30 د", "الفترة": "مسائية"},
        {"النشاط": "ت بدنية",               "المدة": "30 د", "الفترة": "مسائية"},
        {"النشاط": "نهاية الخروج",          "المدة": "15 د", "الفترة": "مسائية"},
    ],
    "الخميس": [
        {"النشاط": "الاستقبال",             "المدة": "15 د", "الفترة": "صباحية"},
        {"النشاط": "مبادئ القراءة",          "المدة": "30 د", "الفترة": "صباحية"},
        {"النشاط": "رياضيات",               "المدة": "30 د", "الفترة": "صباحية"},
        {"النشاط": "ت علمية وتكنولوجية",    "المدة": "30 د", "الفترة": "صباحية"},
        {"النشاط": "ت إيقاعية",             "المدة": "30 د", "الفترة": "صباحية"},
        {"النشاط": "موسيقى وإنشاد",        "المدة": "30 د", "الفترة": "صباحية"},
        {"النشاط": "تهيئة الخروج",          "المدة": "15 د", "الفترة": "صباحية"},
    ],
}


# ╔══════════════════════════════════════════════════════╗
# ║  القسم 2: دوال مساعدة                               ║
# ╚══════════════════════════════════════════════════════╝

def get_all_teaching_subjects():
    subjects = set()
    for day_plan in weekly_schedule.values():
        for s in day_plan:
            if s["النشاط"] not in ROUTINE_ACTIVITIES:
                subjects.add(s["النشاط"])
    return subjects

def get_domain_for(act):
    return DOMAIN_MAPPING.get(act, "—")

def verify_schedule():
    count = {}
    for day, plan in weekly_schedule.items():
        for s in plan:
            act = s["النشاط"]
            if act not in ROUTINE_ACTIVITIES:
                count[act] = count.get(act, 0) + 1
    errors = []
    for subj, expected in SUBJECT_WEEKLY_COUNT.items():
        actual = count.get(subj, 0)
        if actual != expected:
            errors.append(f"  {subj}: متوقع {expected} | فعلي {actual}")
    return errors, count

def domain_badge(domain):
    color = DOMAIN_COLORS.get(domain, "#666")
    return (
        f'<span style="display:inline-block;padding:2px 10px;'
        f'border-radius:12px;font-size:0.75rem;font-weight:600;'
        f'background:{color}22;color:{color};'
        f'border:1px solid {color}44;">{domain}</span>'
    )


# ╔══════════════════════════════════════════════════════╗
# ║  القسم 3: محرك الاستخراج المُحسَّن                   ║
# ╚══════════════════════════════════════════════════════╝

def clean_text(text):
    """تنظيف شامل للنص العربي"""
    if not text:
        return ""
    # إزالة التطويل (ـ)
    text = re.sub(r'ـ+', '', text)
    # إزالة التشكيل
    text = re.sub(
        r'[\u0610-\u061A\u064B-\u065F\u0670'
        r'\u06D6-\u06DC\u06DF-\u06E4\u06E7\u06E8\u06EA-\u06ED]',
        '', text
    )
    # إزالة مسافات متعددة
    text = re.sub(r'\s+', ' ', text)
    # إزالة نقاط ومسافات في النهاية
    text = re.sub(r'[\.\s]+$', '', text)
    return text.strip()


def normalize_name(raw):
    """
    توحيد اسم المادة بعدة طرق بحث
    """
    cleaned = clean_text(raw)
    if not cleaned:
        return cleaned

    # 1) مطابقة تامة
    if cleaned in NAME_MAPPING:
        return NAME_MAPPING[cleaned]

    # 2) بدون "ال" التعريف
    without_al = re.sub(r'^ال', '', cleaned)
    if without_al in NAME_MAPPING:
        return NAME_MAPPING[without_al]

    # 3) بحث جزئي (المفتاح يحتوي على النص أو العكس)
    for key, val in NAME_MAPPING.items():
        if key in cleaned or cleaned in key:
            return val

    # 4) تطبيع الهمزات والألفات
    normalized = cleaned
    normalized = normalized.replace('أ', 'ا').replace('إ', 'ا').replace('آ', 'ا')
    normalized = normalized.replace('ى', 'ي').replace('ة', 'ه')
    for key, val in NAME_MAPPING.items():
        key_norm = key.replace('أ', 'ا').replace('إ', 'ا').replace('آ', 'ا')
        key_norm = key_norm.replace('ى', 'ي').replace('ة', 'ه')
        if key_norm == normalized or key_norm in normalized or normalized in key_norm:
            return val

    # 5) بحث بالكلمات الجذرية
    root_map = {
        "علم": "ت علمية وتكنولوجية",
        "تكنولوج": "ت علمية وتكنولوجية",
        "إسلام": "ت إسلامية",
        "اسلام": "ت إسلامية",
        "مدن": "ت مدنية",
        "بدن": "ت بدنية",
        "إيقاع": "ت إيقاعية",
        "ايقاع": "ت إيقاعية",
        "تشكيل": "تربية تشكيلية",
        "رياض": "رياضيات",
        "قراء": "مبادئ القراءة",
        "تخطيط": "تخطيط",
        "كتاب": "تخطيط",
        "شفو": "تعبير شفوي",
        "شفه": "تعبير شفوي",
        "تعبير": "تعبير شفوي",
        "مسرح": "مسرح وعرائس",
        "عرائس": "مسرح وعرائس",
        "موسيق": "موسيقى وإنشاد",
        "إنشاد": "موسيقى وإنشاد",
        "انشاد": "موسيقى وإنشاد",
        "رسم": "تربية تشكيلية",
        "أشغال": "تربية تشكيلية",
        "اشغال": "تربية تشكيلية",
    }
    for root, target in root_map.items():
        if root in cleaned:
            return target

    return cleaned


# أنماط Regex مرنة جداً
# بدون ^ لتعمل حتى لو سبقها نص
# مع دعم فواصل متعددة: / : - أو حتى مسافة فقط

RE_ACT = re.compile(
    r'(?:النشاط|المادة|نشاط|مادة|المجال|مجال\s*التعلم?|الميدان)'
    r'\s*[:/\-\.\|]*\s*(.+)',
)

RE_TOP = re.compile(
    r'(?:الموضوع|موضوع|الوحدة|وحدة|عنوان\s*الدرس|المحتوى|محتوى)'
    r'\s*[:/\-\.\|]*\s*(.+)',
)

RE_IND = re.compile(
    r'(?:مؤشر\s*(?:ات)?\s*الكفاء\w*|الكفاءة\s*المستهدفة|كفاءة)'
    r'\s*[:/\-\.\|]*\s*(.+)',
)


def read_file_content(file_bytes):
    """قراءة كل محتويات الملف للتشخيص"""
    doc = Document(BytesIO(file_bytes))
    content = {
        'paragraphs': [],
        'tables': [],
        'all_lines': [],
    }

    for para in doc.paragraphs:
        raw = para.text.strip()
        if raw:
            cleaned = clean_text(raw)
            content['paragraphs'].append({
                'raw': raw,
                'cleaned': cleaned,
            })
            content['all_lines'].append(cleaned)

    for t_idx, table in enumerate(doc.tables):
        table_data = []
        for r_idx, row in enumerate(table.rows):
            for c_idx, cell in enumerate(row.cells):
                raw = cell.text.strip()
                if raw:
                    cleaned = clean_text(raw)
                    table_data.append({
                        'row': r_idx,
                        'col': c_idx,
                        'raw': raw,
                        'cleaned': cleaned,
                    })
                    content['all_lines'].append(cleaned)
        content['tables'].append(table_data)

    return content


def extract_all_lessons(file_bytes):
    """
    استخراج مُحسَّن من الفقرات والجداول
    يُرجع: (lessons_db, debug_info)
    """
    doc = Document(BytesIO(file_bytes))
    lessons = {}
    debug = {
        'matched_activities': [],
        'matched_topics': [],
        'matched_indicators': [],
        'unmatched_lines': [],
        'normalized_names': {},
    }

    def _try_match(text):
        """محاولة مطابقة سطر واحد"""
        nonlocal cur_act, cur_les

        m = RE_ACT.search(text)
        if m:
            _save()
            raw_name = clean_text(m.group(1))
            cur_act = raw_name
            cur_les = {}
            normalized = normalize_name(raw_name)
            debug['matched_activities'].append({
                'raw': raw_name,
                'normalized': normalized,
            })
            debug['normalized_names'][raw_name] = normalized
            return True

        m = RE_TOP.search(text)
        if m:
            cur_les['موضوع'] = clean_text(m.group(1))
            debug['matched_topics'].append(clean_text(m.group(1)))
            return True

        m = RE_IND.search(text)
        if m:
            cur_les['كفاءة'] = clean_text(m.group(1))
            debug['matched_indicators'].append(clean_text(m.group(1)))
            return True

        return False

    cur_act = None
    cur_les = {}

    def _save():
        nonlocal cur_act, cur_les
        if cur_act and cur_les.get('موضوع'):
            name = normalize_name(cur_act)
            lessons.setdefault(name, []).append(cur_les.copy())

    # ── استخراج من الفقرات ──
    for para in doc.paragraphs:
        text = clean_text(para.text)
        if not text:
            continue
        matched = _try_match(text)
        if not matched and len(text) > 3:
            debug['unmatched_lines'].append(text)

    _save()

    # ── استخراج من الجداول ──
    cur_act = None
    cur_les = {}

    for table in doc.tables:
        for row in table.rows:
            # جمع نص كل خلية في الصف
            for cell in row.cells:
                cell_text = clean_text(cell.text)
                if not cell_text:
                    continue

                # بعض الخلايا تحتوي عدة أسطر
                lines = cell_text.split('\n')
                for line in lines:
                    line = clean_text(line)
                    if line:
                        matched = _try_match(line)
                        if not matched and len(line) > 3:
                            # تجنب التكرار في debug
                            if line not in debug['unmatched_lines']:
                                debug['unmatched_lines'].append(line)

    _save()

    return lessons, debug


# ╔══════════════════════════════════════════════════════╗
# ║  القسم 4: بناء القالب                                ║
# ╚══════════════════════════════════════════════════════╝

def _rtl(paragraph):
    pPr = paragraph._p.get_or_add_pPr()
    pPr.append(pPr.makeelement(qn('w:bidi'), {}))

def _cell(cell, text, bold=False, size=10, color=None):
    cell.text = ""
    p = cell.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _rtl(p)
    run = p.add_run(text)
    run.bold = bold
    run.font.size = Pt(size)
    run.font.name = "Sakkal Majalla"
    if color:
        run.font.color.rgb = color
    rPr = run._r.get_or_add_rPr()
    rPr.append(rPr.makeelement(qn('w:rFonts'), {qn('w:cs'): 'Sakkal Majalla'}))

def _shade(row, hex_color):
    for c in row.cells:
        tcPr = c._tc.get_or_add_tcPr()
        tcPr.append(tcPr.makeelement(qn('w:shd'), {
            qn('w:fill'): hex_color, qn('w:val'): 'clear'
        }))

def _period_table(doc, title, start, count):
    h = doc.add_paragraph()
    h.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _rtl(h)
    r = h.add_run(title)
    r.bold = True
    r.font.size = Pt(13)
    r.font.color.rgb = RGBColor(0, 51, 102)

    headers = ['مؤشرات الكفاءة', 'عنوان الدرس', 'الميدان', 'النشاط', 'المدة']
    tbl = doc.add_table(rows=1 + count, cols=5)
    tbl.style = 'Table Grid'
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    widths = [Cm(5.5), Cm(5), Cm(3.5), Cm(3.5), Cm(2)]
    for row in tbl.rows:
        for i, w in enumerate(widths):
            row.cells[i].width = w
    hdr = tbl.rows[0]
    _shade(hdr, "1F4E79")
    for i, txt in enumerate(headers):
        _cell(hdr.cells[i], txt, bold=True, size=11, color=RGBColor(255, 255, 255))
    for j in range(count):
        n = start + j
        dr = tbl.rows[1 + j]
        if j % 2 == 0:
            _shade(dr, "EDF2F9")
        for i, ph in enumerate([
            f'{{{{كفاءة_{n}}}}}', f'{{{{موضوع_{n}}}}}',
            f'{{{{ميدان_{n}}}}}', f'{{{{نشاط_{n}}}}}', f'{{{{مدة_{n}}}}}',
        ]):
            _cell(dr.cells[i], ph, size=9)

def create_template_bytes():
    doc = Document()
    for sec in doc.sections:
        sec._sectPr.append(sec._sectPr.makeelement(qn('w:bidi'), {}))
    for txt, sz, b in [
        ('الجمهورية الجزائرية الديمقراطية الشعبية', 12, True),
        ('وزارة التربية الوطنية', 11, False),
    ]:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        _rtl(p)
        r = p.add_run(txt)
        r.bold = b
        r.font.size = Pt(sz)
    tp = doc.add_paragraph()
    tp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _rtl(tp)
    tr = tp.add_run('الكراس اليومي')
    tr.bold = True
    tr.font.size = Pt(18)
    tr.font.color.rgb = RGBColor(0, 51, 102)
    info = doc.add_table(rows=1, cols=3)
    info.alignment = WD_TABLE_ALIGNMENT.CENTER
    _cell(info.rows[0].cells[2], 'اليوم : {{اليوم}}', True, 12)
    _cell(info.rows[0].cells[1], 'التاريخ : {{التاريخ}}', size=11)
    _cell(info.rows[0].cells[0], 'الأسبوع : {{الأسبوع}}', size=11)
    doc.add_paragraph('')
    _period_table(doc, '☀ الفترة الصباحية', 1, 7)
    doc.add_paragraph('')
    _period_table(doc, '🌙 الفترة المسائية', 8, 5)
    doc.add_paragraph('')
    np2 = doc.add_paragraph()
    np2.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    _rtl(np2)
    nr = np2.add_run('ملاحظات : ' + '.' * 80)
    nr.font.size = Pt(10)
    buf = BytesIO()
    doc.save(buf)
    return buf.getvalue()


# ╔══════════════════════════════════════════════════════╗
# ║  القسم 5: محرك الحقن                                 ║
# ╚══════════════════════════════════════════════════════╝

def _safe_replace(paragraph, old, new):
    if old not in paragraph.text:
        return False
    for run in paragraph.runs:
        if old in run.text:
            run.text = run.text.replace(old, new)
            return True
    full = paragraph.text.replace(old, new)
    if paragraph.runs:
        for run in paragraph.runs:
            run.text = ""
        paragraph.runs[0].text = full
    return True

def build_daily_planner(day, template_bytes, lessons_db, week_num="", date_str=""):
    plan = weekly_schedule.get(day, [])
    if not plan:
        return None, [], [f"اليوم '{day}' غير موجود"]
    doc = Document(BytesIO(template_bytes))
    replacements = {"{{اليوم}}": day, "{{التاريخ}}": date_str, "{{الأسبوع}}": week_num}
    sessions_info = []
    warnings = []
    for i, session in enumerate(plan, 1):
        act = session["النشاط"]
        dur = session["المدة"]
        per = session.get("الفترة", "")
        domain = DOMAIN_MAPPING.get(act, "—")
        k_act = f"{{{{نشاط_{i}}}}}"
        k_top = f"{{{{موضوع_{i}}}}}"
        k_ind = f"{{{{كفاءة_{i}}}}}"
        k_dur = f"{{{{مدة_{i}}}}}"
        k_fld = f"{{{{ميدان_{i}}}}}"
        replacements[k_dur] = dur
        replacements[k_act] = act
        info = {
            "رقم": i, "النشاط": act, "المدة": dur,
            "الفترة": per, "المجال": domain,
            "نوع": "روتيني", "الموضوع": "—", "الكفاءة": "—",
        }
        if act in ROUTINE_ACTIVITIES:
            replacements[k_top] = "—"
            replacements[k_ind] = "—"
            replacements[k_fld] = "—"
        elif act in lessons_db and lessons_db[act]:
            lesson = lessons_db[act].pop(0)
            topic = lesson.get('موضوع', '—')
            indic = lesson.get('كفاءة', '—')
            replacements[k_top] = topic
            replacements[k_ind] = indic
            replacements[k_fld] = domain
            info["نوع"] = "تعليمي"
            info["الموضوع"] = topic
            info["الكفاءة"] = indic
        else:
            replacements[k_top] = "⚠ لا توجد مذكرة"
            replacements[k_ind] = "⚠ لا توجد مذكرة"
            replacements[k_fld] = domain
            info["نوع"] = "ناقص"
            warnings.append(act)
        sessions_info.append(info)
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for para in cell.paragraphs:
                    for k, v in replacements.items():
                        if k in para.text:
                            _safe_replace(para, k, str(v))
    for para in doc.paragraphs:
        for k, v in replacements.items():
            if k in para.text:
                _safe_replace(para, k, str(v))
    buf = BytesIO()
    doc.save(buf)
    return buf.getvalue(), sessions_info, warnings


# ╔══════════════════════════════════════════════════════╗
# ║  القسم 6: واجهة Streamlit                            ║
# ╚══════════════════════════════════════════════════════╝

st.set_page_config(
    page_title="الكراس اليومي 🎓", page_icon="🎓",
    layout="wide", initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .main .block-container { direction: rtl; text-align: right; }
    h1, h2, h3 { text-align: center !important; }
    .card {
        padding: 1rem; border-radius: 12px; text-align: center;
        margin: 0.4rem 0; box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    }
    .card h4 { margin: 0 0 0.3rem 0; font-size: 0.9rem; }
    .card .num { font-size: 2rem; font-weight: 700; }
    .card-blue { background: linear-gradient(135deg,#1F4E79,#2E75B6); color:#fff; }
    .card-green { background: linear-gradient(135deg,#2E7D32,#43A047); color:#fff; }
    .card-amber { background: linear-gradient(135deg,#E65100,#FF9800); color:#fff; }
    .card-purple { background: linear-gradient(135deg,#4A148C,#7B1FA2); color:#fff; }
    .slot {
        display: flex; align-items: center; gap: 0.8rem;
        padding: 0.7rem 1rem; margin: 0.3rem 0;
        border-radius: 8px; direction: rtl;
    }
    .slot-routine { background:#f5f5f5; border-right:4px solid #9e9e9e; }
    .slot-teach { background:#e3f2fd; border-right:4px solid #1565c0; }
    .slot-warn { background:#fff3e0; border-right:4px solid #e65100; }
    .stDownloadButton > button {
        width: 100%;
        background: linear-gradient(135deg,#1F4E79,#2E75B6) !important;
        color: #fff !important; border: none !important; border-radius: 8px !important;
    }
    [data-testid="stSidebar"] { direction: rtl; text-align: right; }
    footer { visibility: hidden; }
    .ok-box {
        background: #e8f5e9; border: 1px solid #4caf50;
        border-radius: 10px; padding: 1rem; text-align: center;
    }
    .debug-line {
        background: #f5f5f5; padding: 4px 8px; margin: 2px 0;
        border-radius: 4px; font-family: monospace; font-size: 0.85rem;
        direction: rtl;
    }
    .debug-match {
        background: #e8f5e9; border-left: 3px solid #4caf50;
    }
    .debug-miss {
        background: #fff3e0; border-left: 3px solid #ff9800;
    }
</style>
""", unsafe_allow_html=True)

# Session State
for key in ['lessons_db', 'template_bytes', 'generated_files', 'debug_info', 'file_content']:
    if key not in st.session_state:
        st.session_state[key] = None if key != 'generated_files' else {}


# ═══════════════════════════════════════
#  الشريط الجانبي
# ═══════════════════════════════════════

with st.sidebar:
    st.markdown("## ⚙️ الإعدادات")
    st.markdown("---")
    week_num = st.text_input("📅 رقم الأسبوع", placeholder="10")
    date_str = st.text_input("📆 التاريخ", placeholder="2024/12/01")
    st.markdown("---")
    st.markdown("### 📤 ملف المذكرات")
    uploaded = st.file_uploader("اختر ملف .docx", type=["docx"])
    st.markdown("---")
    st.markdown("### 📥 القالب")
    if st.button("🔨 إنشاء قالب", use_container_width=True):
        st.session_state.template_bytes = create_template_bytes()
        st.success("✅ تم!")
    if st.session_state.template_bytes:
        st.download_button(
            "📄 تحميل القالب",
            data=st.session_state.template_bytes,
            file_name="template.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True,
        )
    st.markdown("---")
    errors, counts = verify_schedule()
    if errors:
        st.error("❌ خلل في التوقيت!")
        for e in errors:
            st.text(e)
    else:
        st.success(f"✅ التوقيت سليم ({sum(counts.values())} حصة)")
    st.caption("🎓 v4.0")

# --- معالجة الرفع ---
if uploaded:
    file_bytes = uploaded.read()
    if st.session_state.get('_last') != uploaded.name:
        with st.spinner("⏳ جارٍ الاستخراج..."):
            # قراءة المحتوى للتشخيص
            content = read_file_content(file_bytes)
            st.session_state.file_content = content

            # استخراج الدروس
            db, debug = extract_all_lessons(file_bytes)
            st.session_state.lessons_db = db
            st.session_state.debug_info = debug
            st.session_state._last = uploaded.name
            st.session_state.generated_files = {}

        if db:
            st.toast("✅ تم استخراج الدروس!", icon="📚")
        else:
            st.error("❌ لم يتم العثور على دروس! افتح تبويب 🔍 التشخيص")

    if not st.session_state.template_bytes:
        st.session_state.template_bytes = create_template_bytes()


# ═══════════════════════════════════════
#  العنوان
# ═══════════════════════════════════════

st.markdown("""
<h1 style="background:linear-gradient(135deg,#1F4E79,#2E75B6);
-webkit-background-clip:text;-webkit-text-fill-color:transparent;
font-size:2.5rem;">🎓 الكراس اليومي</h1>
<p style="text-align:center;color:#888;">أتمتة إعداد الكراس اليومي — قسم التحضيري</p>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════
#  التبويبات
# ═══════════════════════════════════════

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📚 الدروس", "📅 توليد", "👁️ معاينة",
    "📊 التوقيت", "🗺️ المجالات", "🔍 التشخيص"
])


# ──── تبويب 1: الدروس ────

with tab1:
    db = st.session_state.lessons_db
    if not db:
        st.info("👆 ارفع ملف المذكرات من الشريط الجانبي")
        with st.expander("📖 تعليمات"):
            st.markdown("""
            **الأنماط المدعومة في المذكرات:**
            ```
            النشاط : تعبير شفوي
            النشاط / تعبير شفوي
            المادة : تربية إسلامية
            المادة / قراءة
            مجال التعلم : رياضيات

            الموضوع : الصفات
            الوحدة : الحيوانات

            مؤشر الكفاءة : يستعمل الصفات في جمل
            ```
            **إذا لم يعمل الاستخراج:** افتح تبويب 🔍 التشخيص
            """)
    else:
        total = sum(len(v) for v in db.values())
        subjects = get_all_teaching_subjects()
        matched = subjects & set(db.keys())
        missing = subjects - set(db.keys())

        c1, c2, c3, c4 = st.columns(4)
        for col, title, num, cls in [
            (c1, "📘 المواد", len(db), "card-blue"),
            (c2, "📖 الدروس", total, "card-green"),
            (c3, "✅ متطابقة", len(matched), "card-purple"),
            (c4, "⚠ ناقصة", len(missing), "card-amber"),
        ]:
            with col:
                st.markdown(
                    f'<div class="card {cls}"><h4>{title}</h4>'
                    f'<div class="num">{num}</div></div>',
                    unsafe_allow_html=True,
                )

        if missing:
            st.warning(
                f"⚠️ مواد ناقصة: **{' ، '.join(missing)}**\n\n"
                "💡 افتح تبويب **🔍 التشخيص** لمعرفة السبب"
            )

        st.markdown("---")
        for subj in sorted(db.keys()):
            lessons = db[subj]
            domain = get_domain_for(subj)
            icon = "✅" if subj in subjects else "ℹ️"
            with st.expander(f"{icon} {subj} — {len(lessons)} درس — {domain}"):
                for j, les in enumerate(lessons, 1):
                    st.markdown(
                        f"**{j}.** 📝 {les.get('موضوع', '—')}\n\n"
                        f"🎯 {les.get('كفاءة', '—')}"
                    )
                    if j < len(lessons):
                        st.divider()


# ──── تبويب 2: توليد ────

with tab2:
    db = st.session_state.lessons_db
    if not db:
        st.info("👆 ارفع المذكرات أولاً")
    else:
        st.markdown("### 📅 اختر الأيام")
        days = list(weekly_schedule.keys())
        cols = st.columns(len(days))
        selected = []
        for i, d in enumerate(days):
            plan = weekly_schedule[d]
            teach = sum(1 for s in plan if s["النشاط"] not in ROUTINE_ACTIVITIES)
            has_ev = any(s.get("الفترة") == "مسائية" for s in plan)
            label = f"{d} ({teach} حصة)"
            if not has_ev:
                label += " ☀"
            with cols[i]:
                if st.checkbox(label, key=f"d_{d}"):
                    selected.append(d)
        if st.checkbox("✅ تحديد الكل"):
            selected = days
        st.markdown("---")
        if selected and st.button(
            f"🚀 توليد {len(selected)} كراس",
            type="primary", use_container_width=True,
        ):
            tmpl = st.session_state.template_bytes or create_template_bytes()
            st.session_state.template_bytes = tmpl
            wdb = copy.deepcopy(db)
            gen = {}
            bar = st.progress(0)
            msg = st.empty()
            for idx, d in enumerate(selected):
                msg.text(f"⏳ {d}...")
                bar.progress(idx / len(selected))
                result, info, warns = build_daily_planner(d, tmpl, wdb, week_num, date_str)
                if result:
                    gen[d] = {'bytes': result, 'sessions': info, 'warnings': warns}
            bar.progress(1.0)
            msg.empty()
            st.session_state.generated_files = gen
            st.markdown(
                f'<div class="ok-box"><h3>✅ تم توليد {len(gen)} كراس!</h3></div>',
                unsafe_allow_html=True,
            )
        gf = st.session_state.generated_files
        if gf:
            st.markdown("### 📥 التحميل")
            dl_cols = st.columns(min(len(gf), 3))
            for i, (d, data) in enumerate(gf.items()):
                with dl_cols[i % 3]:
                    w = data.get('warnings', [])
                    ic = "⚠️" if w else "📄"
                    st.download_button(
                        f"{ic} كراس {d}",
                        data=data['bytes'],
                        file_name=f"كراس_{d}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        use_container_width=True,
                        key=f"dl_{d}",
                    )
                    if w:
                        st.caption(f"⚠ {', '.join(set(w))}")


# ──── تبويب 3: معاينة ────

with tab3:
    gf = st.session_state.generated_files
    if not gf:
        st.info("📅 ولّد الكراسات أولاً")
    else:
        day_pick = st.selectbox("اختر اليوم", list(gf.keys()), key="preview")
        if day_pick:
            data = gf[day_pick]
            sessions = data['sessions']
            st.markdown(f"## 📋 كراس يوم {day_pick}")
            if data.get('warnings'):
                st.warning(f"⚠️ بدون مذكرة: **{', '.join(set(data['warnings']))}**")
            morning = [s for s in sessions if s['الفترة'] == 'صباحية']
            evening = [s for s in sessions if s['الفترة'] == 'مسائية']
            for pname, plist in [("☀️ الصباحية", morning), ("🌙 المسائية", evening)]:
                if not plist:
                    continue
                st.markdown(f"### {pname}")
                for s in plist:
                    typ = s['نوع']
                    css = {'روتيني': 'slot-routine', 'تعليمي': 'slot-teach', 'ناقص': 'slot-warn'}.get(typ, 'slot-routine')
                    icon = {'روتيني': '⏰', 'تعليمي': '📖', 'ناقص': '⚠️'}.get(typ, '⏰')
                    domain = s.get('المجال', '—')
                    badge = domain_badge(domain) if domain != '—' else ''
                    extra = ''
                    if typ == 'تعليمي':
                        extra = f"<br><small>📝 {s['الموضوع']}</small><br><small>🎯 {s['الكفاءة']}</small>"
                    elif typ == 'ناقص':
                        extra = "<br><small>⚠ لا توجد مذكرة</small>"
                    st.markdown(f"""
                    <div class="slot {css}">
                        <span style="font-size:1.3rem">{icon}</span>
                        <div style="flex:1">
                            <strong>{s['النشاط']}</strong>
                            <span style="color:#888">({s['المدة']})</span>
                            {badge} {extra}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)


# ──── تبويب 4: التوقيت ────

with tab4:
    st.markdown("### 📊 التوقيت الأسبوعي")
    view_day = st.selectbox("اليوم", list(weekly_schedule.keys()), key="sched")
    if view_day:
        plan = weekly_schedule[view_day]
        morning = [s for s in plan if s.get('الفترة') == 'صباحية']
        evening = [s for s in plan if s.get('الفترة') == 'مسائية']
        for name, sl in [("☀️ صباح", morning), ("🌙 مساء", evening)]:
            if not sl:
                continue
            st.markdown(f"#### {name}")
            rows = []
            for j, s in enumerate(sl, 1):
                act = s['النشاط']
                is_r = act in ROUTINE_ACTIVITIES
                rows.append({
                    "#": j, "النشاط": act, "المدة": s['المدة'],
                    "المجال": get_domain_for(act) if not is_r else "—",
                    "النوع": "🔄" if is_r else "📖",
                })
            st.dataframe(rows, use_container_width=True, hide_index=True)
    st.markdown("---")
    st.markdown("#### 📈 التحقق من التوزيع")
    _, counts = verify_schedule()
    for subj, expected in SUBJECT_WEEKLY_COUNT.items():
        actual = counts.get(subj, 0)
        ok = "✅" if actual == expected else "❌"
        domain = get_domain_for(subj)
        st.markdown(
            f"{ok} **{subj}** — {actual}/{expected} حصة — {domain_badge(domain)}",
            unsafe_allow_html=True,
        )


# ──── تبويب 5: المجالات ────

with tab5:
    st.markdown("### 🗺️ المجالات التعليمية")
    domains = {}
    for subj, dom in DOMAIN_MAPPING.items():
        domains.setdefault(dom, []).append(subj)
    cols5 = st.columns(2)
    for i, (dom, subjs) in enumerate(domains.items()):
        color = DOMAIN_COLORS.get(dom, "#666")
        total_h = sum(SUBJECT_WEEKLY_COUNT.get(s, 0) for s in subjs)
        with cols5[i % 2]:
            st.markdown(
                f'<div style="border:2px solid {color};border-radius:12px;'
                f'padding:1rem;margin:0.5rem 0;">'
                f'<h4 style="color:{color};text-align:center;">'
                f'{dom} ({total_h} ح/أسبوع)</h4>',
                unsafe_allow_html=True,
            )
            for s in subjs:
                cnt = SUBJECT_WEEKLY_COUNT.get(s, 0)
                st.markdown(
                    f'<div style="display:flex;align-items:center;gap:8px;'
                    f'margin:4px 0;direction:rtl;">'
                    f'<span style="min-width:140px">{s}</span>'
                    f'<div style="background:{color}44;border-radius:4px;'
                    f'height:20px;width:{cnt * 12}px;"></div>'
                    f'<span style="color:{color};font-weight:700;">{cnt}</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            st.markdown('</div>', unsafe_allow_html=True)
    st.markdown("---")
    grand = sum(SUBJECT_WEEKLY_COUNT.values())
    st.markdown(
        f'<div class="card card-blue"><h4>المجموع الأسبوعي</h4>'
        f'<div class="num">{grand} حصة</div>'
        f'<small>{len(SUBJECT_WEEKLY_COUNT)} مادة — {len(domains)} مجالات</small></div>',
        unsafe_allow_html=True,
    )


# ──────────────────────────────────────────
#  تبويب 6: 🔍 التشخيص (الجديد والأهم)
# ──────────────────────────────────────────

with tab6:
    st.markdown("### 🔍 تشخيص ملف المذكرات")
    st.markdown("""
    > هذا التبويب يُظهر **بالضبط** ما يقرأه السكربت من ملفك
    > ويكشف لماذا بعض المواد لا تُستخرج
    """)

    debug = st.session_state.debug_info
    content = st.session_state.file_content

    if not content and not debug:
        st.info("👆 ارفع ملف المذكرات أولاً لرؤية التشخيص")
    else:
        # ═══ القسم أ: ما تم العثور عليه ═══
        if debug:
            st.markdown("---")
            st.markdown("#### ✅ أسماء المواد التي تم التعرف عليها")

            if debug['matched_activities']:
                for act in debug['matched_activities']:
                    raw = act['raw']
                    norm = act['normalized']
                    in_schedule = norm in get_all_teaching_subjects()
                    icon = "✅" if in_schedule else "⚠️"
                    st.markdown(
                        f'<div class="debug-line debug-match">'
                        f'{icon} الأصلي: <strong>{raw}</strong> → '
                        f'تم تحويله إلى: <strong>{norm}</strong>'
                        f'{"" if in_schedule else " ⚠ غير موجود في التوقيت!"}'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
            else:
                st.error("❌ لم يتم التعرف على أي اسم مادة!")

            st.markdown(f"**المواضيع المكتشفة:** {len(debug['matched_topics'])}")
            st.markdown(f"**مؤشرات الكفاءة المكتشفة:** {len(debug['matched_indicators'])}")

        # ═══ القسم ب: الأسطر غير المتطابقة ═══
        if debug and debug.get('unmatched_lines'):
            st.markdown("---")
            st.markdown("#### ⚠️ أسطر لم يتعرف عليها السكربت")
            st.markdown("هذه الأسطر موجودة في ملفك لكن لم تطابق أي نمط:")

            # تصفية: إظهار الأسطر التي قد تحتوي على أسماء مواد
            keywords = [
                'نشاط', 'مادة', 'مجال', 'ميدان', 'موضوع',
                'وحدة', 'كفاءة', 'مؤشر', 'درس',
            ]

            important = []
            other = []
            for line in debug['unmatched_lines'][:100]:
                if any(kw in line for kw in keywords):
                    important.append(line)
                else:
                    other.append(line)

            if important:
                st.markdown("**🔴 أسطر مهمة (تحتوي كلمات مفتاحية لكن لم تُطابق):**")
                for line in important:
                    st.markdown(
                        f'<div class="debug-line debug-miss">{line}</div>',
                        unsafe_allow_html=True,
                    )
                st.markdown("""
                > 💡 **هذه هي المشكلة!** انسخ الصيغة الدقيقة من الأسطر أعلاه
                > وأخبرني بها حتى أضيفها للأنماط المدعومة
                """)

            if other:
                with st.expander(f"📝 أسطر أخرى ({len(other)} سطر)"):
                    for line in other[:50]:
                        st.text(line)

        # ═══ القسم ج: المحتوى الخام ═══
        if content:
            st.markdown("---")
            st.markdown("#### 📄 المحتوى الخام للملف")

            with st.expander(f"📝 الفقرات ({len(content['paragraphs'])} فقرة)"):
                for i, p in enumerate(content['paragraphs'][:100]):
                    st.markdown(
                        f'<div class="debug-line">'
                        f'<small style="color:#999">#{i+1}</small> '
                        f'{p["cleaned"]}</div>',
                        unsafe_allow_html=True,
                    )

            for t_idx, table_data in enumerate(content['tables']):
                if table_data:
                    with st.expander(f"📊 جدول {t_idx+1} ({len(table_data)} خلية)"):
                        for cell_info in table_data[:100]:
                            st.markdown(
                                f'<div class="debug-line">'
                                f'<small style="color:#999">'
                                f'[ص{cell_info["row"]+1},ع{cell_info["col"]+1}]'
                                f'</small> {cell_info["cleaned"]}</div>',
                                unsafe_allow_html=True,
                            )

        # ═══ القسم د: مقارنة التطابق ═══
        if debug:
            st.markdown("---")
            st.markdown("#### 🔄 مقارنة: المطلوب ↔ الموجود")

            subjects_needed = get_all_teaching_subjects()
            db = st.session_state.lessons_db or {}

            for subj in sorted(subjects_needed):
                if subj in db and db[subj]:
                    st.markdown(
                        f"✅ **{subj}** — {len(db[subj])} درس موجود"
                    )
                else:
                    st.markdown(
                        f"❌ **{subj}** — غير موجود! "
                        f"({get_domain_for(subj)})"
                    )

            # مواد مستخرجة لكن غير مستخدمة
            extra = set(db.keys()) - subjects_needed if db else set()
            if extra:
                st.markdown("---")
                st.markdown("#### ℹ️ مواد مستخرجة لكنها غير موجودة في التوقيت:")
                for s in extra:
                    st.markdown(f"• **{s}** — {len(db[s])} درس")
                st.info(
                    "💡 هذه المواد استُخرجت لكن اسمها لا يطابق التوقيت. "
                    "قد تحتاج إضافة اسمها في قاموس NAME_MAPPING"
                )
