# -*- coding: utf-8 -*-
"""محرك استخراج الدروس من ملفات المذكرات"""

import re
from io import BytesIO
from docx import Document
from .schedule import NAME_MAPPING


# ═══════════════════════════════════════
#  تنظيف النصوص
# ═══════════════════════════════════════

def clean_text(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r'ـ+', '', text)
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[\.\s]+$', '', text)
    return text.strip()


def normalize_name(raw: str) -> str:
    cleaned = clean_text(raw)
    if cleaned in NAME_MAPPING:
        return NAME_MAPPING[cleaned]
    for key, val in NAME_MAPPING.items():
        if key in cleaned or cleaned in key:
            return val
    return cleaned


# ═══════════════════════════════════════
#  أنماط Regex
# ═══════════════════════════════════════

RE_ACT = re.compile(
    r'^(?:النشاط|المادة|مجال\s*التعل[ـم]*)\s*[:/\-]\s*(.*)'
)
RE_TOP = re.compile(
    r'^(?:الموضوع|الوحدة|عنوان\s*الدرس)\s*[:/\-]\s*(.*)'
)
RE_IND = re.compile(
    r'^(?:مؤشر\s*الكفا[ـءئ]*ة|الكفاءة\s*المستهدفة)\s*[:/\-]\s*(.*)'
)


# ═══════════════════════════════════════
#  محرك الاستخراج
# ═══════════════════════════════════════

def _extract_paragraphs(doc) -> dict:
    lessons = {}
    cur_act = None
    cur_les = {}

    def _save():
        nonlocal cur_act, cur_les
        if cur_act and cur_les.get('موضوع'):
            name = normalize_name(cur_act)
            lessons.setdefault(name, []).append(cur_les.copy())

    for para in doc.paragraphs:
        text = clean_text(para.text)
        if not text:
            continue

        m = RE_ACT.search(text)
        if m:
            _save()
            cur_act = m.group(1).strip()
            cur_les = {}
            continue

        m = RE_TOP.search(text)
        if m:
            cur_les['موضوع'] = clean_text(m.group(1))
            continue

        m = RE_IND.search(text)
        if m:
            cur_les['كفاءة'] = clean_text(m.group(1))
            continue

    _save()
    return lessons


def _extract_tables(doc, existing: dict = None) -> dict:
    if existing is None:
        existing = {}

    for table in doc.tables:
        cur_act = None
        cur_les = {}

        for row in table.rows:
            for cell in row.cells:
                text = clean_text(cell.text)
                if not text:
                    continue

                m = RE_ACT.search(text)
                if m:
                    if cur_act and cur_les.get('موضوع'):
                        name = normalize_name(cur_act)
                        existing.setdefault(name, []).append(
                            cur_les.copy()
                        )
                    cur_act = m.group(1).strip()
                    cur_les = {}
                    continue

                m = RE_TOP.search(text)
                if m:
                    cur_les['موضوع'] = clean_text(m.group(1))
                    continue

                m = RE_IND.search(text)
                if m:
                    cur_les['كفاءة'] = clean_text(m.group(1))
                    continue

        if cur_act and cur_les.get('موضوع'):
            name = normalize_name(cur_act)
            existing.setdefault(name, []).append(cur_les.copy())

    return existing


def extract_all_lessons(file_bytes: bytes) -> dict:
    """
    استخراج كل الدروس من ملف المذكرات

    Args:
        file_bytes: محتوى ملف docx كـ bytes

    Returns:
        قاموس {اسم_المادة: [{'موضوع': ..., 'كفاءة': ...}, ...]}
    """
    doc = Document(BytesIO(file_bytes))
    lessons = _extract_paragraphs(doc)
    lessons = _extract_tables(doc, lessons)
    return lessons
