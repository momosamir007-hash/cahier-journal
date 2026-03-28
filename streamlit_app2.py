# -*- coding: utf-8 -*-
"""
🎓 الكراس اليومي — جميع المراحل الابتدائية
الإصدار 6.0 — متعدد المستويات + AI
"""

import streamlit as st
import re, copy, json, math
from io import BytesIO
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False


# ╔══════════════════════════════════════════════════════════════╗
# ║     المرحلة 1: هيكلة البيانات — إعدادات المستويات           ║
# ╚══════════════════════════════════════════════════════════════╝

# كل مستوى = قاموس فيه: المواد + المجالات + التوقيت + الأنشطة الروتينية

LEVELS_CONFIG = {

    # ══════════════════════════════════════
    #  قسم التحضيري
    # ══════════════════════════════════════
    "قسم التحضيري": {
        "الأنشطة_الروتينية": ["الاستقبال", "الاستراحة", "تهيئة الخروج", "نهاية الخروج"],
        "المجالات": {
            "المجال اللغوي":              {"اللون": "#1565C0"},
            "المجال الرياضي":             {"اللون": "#C62828"},
            "المجال العلمي":              {"اللون": "#2E7D32"},
            "المجال الاجتماعي":           {"اللون": "#F57F17"},
            "المجال الفني":               {"اللون": "#6A1B9A"},
            "المجال البدني والإيقاعي":    {"اللون": "#00838F"},
        },
        "المواد": {
            "تعبير شفوي":           {"المجال": "المجال اللغوي",           "الحصص": 3},
            "مبادئ القراءة":        {"المجال": "المجال اللغوي",           "الحصص": 4},
            "تخطيط":                {"المجال": "المجال اللغوي",           "الحصص": 2},
            "رياضيات":              {"المجال": "المجال الرياضي",          "الحصص": 5},
            "ت علمية وتكنولوجية":   {"المجال": "المجال العلمي",          "الحصص": 4},
            "ت إسلامية":            {"المجال": "المجال الاجتماعي",       "الحصص": 2},
            "ت مدنية":              {"المجال": "المجال الاجتماعي",       "الحصص": 2},
            "تربية تشكيلية":        {"المجال": "المجال الفني",           "الحصص": 2},
            "موسيقى وإنشاد":       {"المجال": "المجال الفني",           "الحصص": 2},
            "مسرح وعرائس":         {"المجال": "المجال الفني",           "الحصص": 2},
            "ت بدنية":              {"المجال": "المجال البدني والإيقاعي", "الحصص": 4},
            "ت إيقاعية":            {"المجال": "المجال البدني والإيقاعي", "الحصص": 2},
        },
        "التوقيت": {
            "الأحد": [
                {"النشاط":"الاستقبال","المدة":"15 د","الفترة":"صباحية"},
                {"النشاط":"تعبير شفوي","المدة":"30 د","الفترة":"صباحية"},
                {"النشاط":"مبادئ القراءة","المدة":"30 د","الفترة":"صباحية"},
                {"النشاط":"رياضيات","المدة":"30 د","الفترة":"صباحية"},
                {"النشاط":"ت علمية وتكنولوجية","المدة":"30 د","الفترة":"صباحية"},
                {"النشاط":"ت إسلامية","المدة":"30 د","الفترة":"صباحية"},
                {"النشاط":"تهيئة الخروج","المدة":"15 د","الفترة":"صباحية"},
                {"النشاط":"الاستقبال","المدة":"15 د","الفترة":"مسائية"},
                {"النشاط":"مسرح وعرائس","المدة":"30 د","الفترة":"مسائية"},
                {"النشاط":"تربية تشكيلية","المدة":"30 د","الفترة":"مسائية"},
                {"النشاط":"ت بدنية","المدة":"30 د","الفترة":"مسائية"},
                {"النشاط":"نهاية الخروج","المدة":"15 د","الفترة":"مسائية"},
            ],
            "الإثنين": [
                {"النشاط":"الاستقبال","المدة":"15 د","الفترة":"صباحية"},
                {"النشاط":"رياضيات","المدة":"30 د","الفترة":"صباحية"},
                {"النشاط":"تعبير شفوي","المدة":"30 د","الفترة":"صباحية"},
                {"النشاط":"تخطيط","المدة":"30 د","الفترة":"صباحية"},
                {"النشاط":"ت علمية وتكنولوجية","المدة":"30 د","الفترة":"صباحية"},
                {"النشاط":"ت مدنية","المدة":"30 د","الفترة":"صباحية"},
                {"النشاط":"تهيئة الخروج","المدة":"15 د","الفترة":"صباحية"},
                {"النشاط":"الاستقبال","المدة":"15 د","الفترة":"مسائية"},
                {"النشاط":"مسرح وعرائس","المدة":"30 د","الفترة":"مسائية"},
                {"النشاط":"تربية تشكيلية","المدة":"30 د","الفترة":"مسائية"},
                {"النشاط":"ت بدنية","المدة":"30 د","الفترة":"مسائية"},
                {"النشاط":"نهاية الخروج","المدة":"15 د","الفترة":"مسائية"},
            ],
            "الثلاثاء": [
                {"النشاط":"الاستقبال","المدة":"15 د","الفترة":"صباحية"},
                {"النشاط":"تعبير شفوي","المدة":"30 د","الفترة":"صباحية"},
                {"النشاط":"مبادئ القراءة","المدة":"30 د","الفترة":"صباحية"},
                {"النشاط":"رياضيات","المدة":"30 د","الفترة":"صباحية"},
                {"النشاط":"ت إسلامية","المدة":"30 د","الفترة":"صباحية"},
                {"النشاط":"ت بدنية","المدة":"30 د","الفترة":"صباحية"},
                {"النشاط":"تهيئة الخروج","المدة":"15 د","الفترة":"صباحية"},
            ],
            "الأربعاء": [
                {"النشاط":"الاستقبال","المدة":"15 د","الفترة":"صباحية"},
                {"النشاط":"رياضيات","المدة":"30 د","الفترة":"صباحية"},
                {"النشاط":"مبادئ القراءة","المدة":"30 د","الفترة":"صباحية"},
                {"النشاط":"تخطيط","المدة":"30 د","الفترة":"صباحية"},
                {"النشاط":"ت علمية وتكنولوجية","المدة":"30 د","الفترة":"صباحية"},
                {"النشاط":"ت مدنية","المدة":"30 د","الفترة":"صباحية"},
                {"النشاط":"تهيئة الخروج","المدة":"15 د","الفترة":"صباحية"},
                {"النشاط":"الاستقبال","المدة":"15 د","الفترة":"مسائية"},
                {"النشاط":"ت إيقاعية","المدة":"30 د","الفترة":"مسائية"},
                {"النشاط":"موسيقى وإنشاد","المدة":"30 د","الفترة":"مسائية"},
                {"النشاط":"ت بدنية","المدة":"30 د","الفترة":"مسائية"},
                {"النشاط":"نهاية الخروج","المدة":"15 د","الفترة":"مسائية"},
            ],
            "الخميس": [
                {"النشاط":"الاستقبال","المدة":"15 د","الفترة":"صباحية"},
                {"النشاط":"مبادئ القراءة","المدة":"30 د","الفترة":"صباحية"},
                {"النشاط":"رياضيات","المدة":"30 د","الفترة":"صباحية"},
                {"النشاط":"ت علمية وتكنولوجية","المدة":"30 د","الفترة":"صباحية"},
                {"النشاط":"ت إيقاعية","المدة":"30 د","الفترة":"صباحية"},
                {"النشاط":"موسيقى وإنشاد","المدة":"30 د","الفترة":"صباحية"},
                {"النشاط":"تهيئة الخروج","المدة":"15 د","الفترة":"صباحية"},
            ],
        },
    },

    # ══════════════════════════════════════
    #  السنة الأولى ابتدائي
    # ══════════════════════════════════════
    "السنة 1 ابتدائي": {
        "الأنشطة_الروتينية": ["الاستقبال", "الاستراحة", "تهيئة الخروج", "نهاية الخروج"],
        "المجالات": {
            "اللغة العربية":       {"اللون": "#1565C0"},
            "الرياضيات":           {"اللون": "#C62828"},
            "التربية العلمية":     {"اللون": "#2E7D32"},
            "التربية الاجتماعية": {"اللون": "#F57F17"},
            "التربية الفنية":     {"اللون": "#6A1B9A"},
            "التربية البدنية":    {"اللون": "#00838F"},
        },
        "المواد": {
            "قراءة":              {"المجال": "اللغة العربية",       "الحصص": 6},
            "تعبير شفوي":        {"المجال": "اللغة العربية",       "الحصص": 2},
            "كتابة وخط":         {"المجال": "اللغة العربية",       "الحصص": 3},
            "محفوظات":            {"المجال": "اللغة العربية",       "الحصص": 1},
            "رياضيات":            {"المجال": "الرياضيات",           "الحصص": 5},
            "تربية علمية":        {"المجال": "التربية العلمية",     "الحصص": 2},
            "تربية إسلامية":      {"المجال": "التربية الاجتماعية", "الحصص": 2},
            "تربية مدنية":        {"المجال": "التربية الاجتماعية", "الحصص": 1},
            "تربية فنية":         {"المجال": "التربية الفنية",     "الحصص": 2},
            "تربية موسيقية":      {"المجال": "التربية الفنية",     "الحصص": 1},
            "تربية بدنية":        {"المجال": "التربية البدنية",    "الحصص": 2},
        },
        "التوقيت": {},  # فارغ — سيُبنى تلقائياً أو يُعدل يدوياً
    },

    # ══════════════════════════════════════
    #  السنة 2 ابتدائي
    # ══════════════════════════════════════
    "السنة 2 ابتدائي": {
        "الأنشطة_الروتينية": ["الاستقبال", "الاستراحة", "تهيئة الخروج", "نهاية الخروج"],
        "المجالات": {
            "اللغة العربية":       {"اللون": "#1565C0"},
            "الرياضيات":           {"اللون": "#C62828"},
            "التربية العلمية":     {"اللون": "#2E7D32"},
            "التربية الاجتماعية": {"اللون": "#F57F17"},
            "التربية الفنية":     {"اللون": "#6A1B9A"},
            "التربية البدنية":    {"اللون": "#00838F"},
        },
        "المواد": {
            "قراءة":              {"المجال": "اللغة العربية",       "الحصص": 5},
            "تعبير شفوي":        {"المجال": "اللغة العربية",       "الحصص": 2},
            "كتابة وخط":         {"المجال": "اللغة العربية",       "الحصص": 3},
            "إملاء":              {"المجال": "اللغة العربية",       "الحصص": 1},
            "محفوظات":            {"المجال": "اللغة العربية",       "الحصص": 1},
            "رياضيات":            {"المجال": "الرياضيات",           "الحصص": 5},
            "تربية علمية":        {"المجال": "التربية العلمية",     "الحصص": 2},
            "تربية إسلامية":      {"المجال": "التربية الاجتماعية", "الحصص": 2},
            "تربية مدنية":        {"المجال": "التربية الاجتماعية", "الحصص": 1},
            "تربية فنية":         {"المجال": "التربية الفنية",     "الحصص": 2},
            "تربية موسيقية":      {"المجال": "التربية الفنية",     "الحصص": 1},
            "تربية بدنية":        {"المجال": "التربية البدنية",    "الحصص": 2},
        },
        "التوقيت": {},
    },

    # ══════════════════════════════════════
    #  السنة 3 ابتدائي (تضاف الفرنسية)
    # ══════════════════════════════════════
    "السنة 3 ابتدائي": {
        "الأنشطة_الروتينية": ["الاستقبال", "الاستراحة", "تهيئة الخروج", "نهاية الخروج"],
        "المجالات": {
            "اللغة العربية":       {"اللون": "#1565C0"},
            "اللغة الفرنسية":     {"اللون": "#1976D2"},
            "الرياضيات":           {"اللون": "#C62828"},
            "التربية العلمية":     {"اللون": "#2E7D32"},
            "التربية الاجتماعية": {"اللون": "#F57F17"},
            "التربية الفنية":     {"اللون": "#6A1B9A"},
            "التربية البدنية":    {"اللون": "#00838F"},
        },
        "المواد": {
            "قراءة":              {"المجال": "اللغة العربية",       "الحصص": 4},
            "تعبير شفوي":        {"المجال": "اللغة العربية",       "الحصص": 2},
            "كتابة وإملاء":      {"المجال": "اللغة العربية",       "الحصص": 2},
            "قواعد":              {"المجال": "اللغة العربية",       "الحصص": 1},
            "محفوظات":            {"المجال": "اللغة العربية",       "الحصص": 1},
            "فرنسية":             {"المجال": "اللغة الفرنسية",     "الحصص": 3},
            "رياضيات":            {"المجال": "الرياضيات",           "الحصص": 5},
            "تربية علمية":        {"المجال": "التربية العلمية",     "الحصص": 2},
            "تربية إسلامية":      {"المجال": "التربية الاجتماعية", "الحصص": 1},
            "تربية مدنية":        {"المجال": "التربية الاجتماعية", "الحصص": 1},
            "تاريخ وجغرافيا":     {"المجال": "التربية الاجتماعية", "الحصص": 1},
            "تربية فنية":         {"المجال": "التربية الفنية",     "الحصص": 1},
            "تربية موسيقية":      {"المجال": "التربية الفنية",     "الحصص": 1},
            "تربية بدنية":        {"المجال": "التربية البدنية",    "الحصص": 2},
        },
        "التوقيت": {},
    },

    # ══════════════════════════════════════
    #  السنة 4 ابتدائي
    # ══════════════════════════════════════
    "السنة 4 ابتدائي": {
        "الأنشطة_الروتينية": ["الاستقبال", "الاستراحة", "تهيئة الخروج", "نهاية الخروج"],
        "المجالات": {
            "اللغة العربية":       {"اللون": "#1565C0"},
            "اللغة الفرنسية":     {"اللون": "#1976D2"},
            "الرياضيات":           {"اللون": "#C62828"},
            "التربية العلمية":     {"اللون": "#2E7D32"},
            "التربية الاجتماعية": {"اللون": "#F57F17"},
            "التربية الفنية":     {"اللون": "#6A1B9A"},
            "التربية البدنية":    {"اللون": "#00838F"},
        },
        "المواد": {
            "قراءة ودراسة نص":    {"المجال": "اللغة العربية",       "الحصص": 3},
            "قواعد صرفية ونحوية": {"المجال": "اللغة العربية",       "الحصص": 2},
            "تعبير كتابي":        {"المجال": "اللغة العربية",       "الحصص": 1},
            "تعبير شفوي":        {"المجال": "اللغة العربية",       "الحصص": 1},
            "إملاء":              {"المجال": "اللغة العربية",       "الحصص": 1},
            "محفوظات":            {"المجال": "اللغة العربية",       "الحصص": 1},
            "فرنسية":             {"المجال": "اللغة الفرنسية",     "الحصص": 3},
            "رياضيات":            {"المجال": "الرياضيات",           "الحصص": 5},
            "تربية علمية":        {"المجال": "التربية العلمية",     "الحصص": 2},
            "تربية إسلامية":      {"المجال": "التربية الاجتماعية", "الحصص": 1},
            "تربية مدنية":        {"المجال": "التربية الاجتماعية", "الحصص": 1},
            "تاريخ":              {"المجال": "التربية الاجتماعية", "الحصص": 1},
            "جغرافيا":            {"المجال": "التربية الاجتماعية", "الحصص": 1},
            "تربية فنية":         {"المجال": "التربية الفنية",     "الحصص": 1},
            "تربية موسيقية":      {"المجال": "التربية الفنية",     "الحصص": 1},
            "تربية بدنية":        {"المجال": "التربية البدنية",    "الحصص": 2},
        },
        "التوقيت": {},
    },

    # ══════════════════════════════════════
    #  السنة 5 ابتدائي
    # ══════════════════════════════════════
    "السنة 5 ابتدائي": {
        "الأنشطة_الروتينية": ["الاستقبال", "الاستراحة", "تهيئة الخروج", "نهاية الخروج"],
        "المجالات": {
            "اللغة العربية":       {"اللون": "#1565C0"},
            "اللغة الفرنسية":     {"اللون": "#1976D2"},
            "الرياضيات":           {"اللون": "#C62828"},
            "التربية العلمية":     {"اللون": "#2E7D32"},
            "التربية الاجتماعية": {"اللون": "#F57F17"},
            "التربية الفنية":     {"اللون": "#6A1B9A"},
            "التربية البدنية":    {"اللون": "#00838F"},
        },
        "المواد": {
            "قراءة ودراسة نص":    {"المجال": "اللغة العربية",       "الحصص": 3},
            "قواعد صرفية ونحوية": {"المجال": "اللغة العربية",       "الحصص": 2},
            "تعبير كتابي":        {"المجال": "اللغة العربية",       "الحصص": 1},
            "تعبير شفوي":        {"المجال": "اللغة العربية",       "الحصص": 1},
            "إملاء":              {"المجال": "اللغة العربية",       "الحصص": 1},
            "محفوظات":            {"المجال": "اللغة العربية",       "الحصص": 1},
            "فرنسية":             {"المجال": "اللغة الفرنسية",     "الحصص": 3},
            "رياضيات":            {"المجال": "الرياضيات",           "الحصص": 5},
            "تربية علمية":        {"المجال": "التربية العلمية",     "الحصص": 2},
            "تربية إسلامية":      {"المجال": "التربية الاجتماعية", "الحصص": 1},
            "تربية مدنية":        {"المجال": "التربية الاجتماعية", "الحصص": 1},
            "تاريخ":              {"المجال": "التربية الاجتماعية", "الحصص": 1},
            "جغرافيا":            {"المجال": "التربية الاجتماعية", "الحصص": 1},
            "تربية فنية":         {"المجال": "التربية الفنية",     "الحصص": 1},
            "تربية موسيقية":      {"المجال": "التربية الفنية",     "الحصص": 1},
            "تربية بدنية":        {"المجال": "التربية البدنية",    "الحصص": 2},
        },
        "التوقيت": {},
    },
}


# ╔══════════════════════════════════════════════════════════════╗
# ║  المرحلة 3: منشئ التوقيت التلقائي الذكي                     ║
# ╚══════════════════════════════════════════════════════════════╝

WEEKDAYS = ["الأحد", "الإثنين", "الثلاثاء", "الأربعاء", "الخميس"]
HALF_DAYS = {"الثلاثاء", "الخميس"}

def auto_generate_schedule(subjects_config, routine_acts, session_dur="45 د"):
    """
    توليد توقيت أسبوعي تلقائي من قائمة المواد

    المنطق:
    - أيام كاملة (أحد، إثنين، أربعاء): صباح 5 حصص + مساء 3 حصص = 8
    - أنصاف أيام (ثلاثاء، خميس): صباح 5 حصص فقط
    - المجموع المتاح = 3×8 + 2×5 = 34 حصة
    """
    # حساب الحصص المتاحة
    full_days = [d for d in WEEKDAYS if d not in HALF_DAYS]
    half_days = [d for d in WEEKDAYS if d in HALF_DAYS]

    morning_slots = 5
    afternoon_slots = 3

    # بناء قائمة كل الحصص المطلوبة
    all_sessions = []
    for subj, info in subjects_config.items():
        for _ in range(info["الحصص"]):
            all_sessions.append(subj)

    total_needed = len(all_sessions)
    total_available = len(full_days) * (morning_slots + afternoon_slots) + len(half_days) * morning_slots

    if total_needed > total_available:
        st.warning(f"⚠ عدد الحصص المطلوبة ({total_needed}) أكبر من المتاح ({total_available})!")

    schedule = {}
    idx = 0

    for day in WEEKDAYS:
        day_plan = []
        is_full = day not in HALF_DAYS

        # صباح
        day_plan.append({"النشاط": routine_acts[0] if routine_acts else "الاستقبال",
                         "المدة": "15 د", "الفترة": "صباحية"})
        for _ in range(morning_slots):
            if idx < len(all_sessions):
                day_plan.append({"النشاط": all_sessions[idx], "المدة": session_dur, "الفترة": "صباحية"})
                idx += 1
        day_plan.append({"النشاط": "تهيئة الخروج", "المدة": "15 د", "الفترة": "صباحية"})

        # مساء (أيام كاملة فقط)
        if is_full:
            day_plan.append({"النشاط": routine_acts[0] if routine_acts else "الاستقبال",
                             "المدة": "15 د", "الفترة": "مسائية"})
            for _ in range(afternoon_slots):
                if idx < len(all_sessions):
                    day_plan.append({"النشاط": all_sessions[idx], "المدة": session_dur, "الفترة": "مسائية"})
                    idx += 1
            day_plan.append({"النشاط": "نهاية الخروج", "المدة": "15 د", "الفترة": "مسائية"})

        schedule[day] = day_plan

    return schedule


# ╔══════════════════════════════════════════════════════════════╗
# ║              دوال مساعدة (تعمل مع أي مستوى)                 ║
# ╚══════════════════════════════════════════════════════════════╝

def get_level_config():
    """جلب إعدادات المستوى الحالي"""
    level = st.session_state.get('selected_level', 'قسم التحضيري')
    if 'custom_configs' in st.session_state and level in st.session_state.custom_configs:
        return st.session_state.custom_configs[level]
    return LEVELS_CONFIG.get(level, LEVELS_CONFIG['قسم التحضيري'])

def get_schedule():
    """جلب التوقيت الحالي (مخصص أو تلقائي)"""
    cfg = get_level_config()
    sched = cfg.get("التوقيت", {})
    if not sched:
        sched = auto_generate_schedule(cfg["المواد"], cfg["الأنشطة_الروتينية"])
    return sched

def get_subjects():
    return get_level_config().get("المواد", {})

def get_domains():
    return get_level_config().get("المجالات", {})

def get_routine():
    return get_level_config().get("الأنشطة_الروتينية", [])

def get_domain_for(act):
    subjects = get_subjects()
    if act in subjects:
        return subjects[act].get("المجال", "—")
    return "—"

def get_domain_color(domain):
    domains = get_domains()
    if domain in domains:
        return domains[domain].get("اللون", "#666")
    return "#666"

def domain_badge(d):
    c = get_domain_color(d)
    return (f'<span style="display:inline-block;padding:2px 10px;border-radius:12px;'
            f'font-size:0.75rem;font-weight:600;background:{c}22;color:{c};'
            f'border:1px solid {c}44;">{d}</span>')

def verify_schedule():
    sched = get_schedule()
    subjects = get_subjects()
    routine = get_routine()
    count = {}
    for plan in sched.values():
        for s in plan:
            a = s["النشاط"]
            if a not in routine:
                count[a] = count.get(a, 0) + 1
    errors = []
    for subj, info in subjects.items():
        exp = info["الحصص"]
        act = count.get(subj, 0)
        if act != exp:
            errors.append(f"{subj}: متوقع {exp} | فعلي {act}")
    return errors, count

def clean_text(text):
    if not text: return ""
    text = re.sub(r'ـ+', '', text)
    text = re.sub(r'[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06DC\u06DF-\u06E4\u06E7\u06E8\u06EA-\u06ED]', '', text)
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[\.\s]+$', '', text)
    return text.strip()


# ╔══════════════════════════════════════════════════════════════╗
# ║           استخراج الدروس بالذكاء الاصطناعي                  ║
# ╚══════════════════════════════════════════════════════════════╝

def read_docx_text(fb):
    doc = Document(BytesIO(fb))
    lines = []
    for p in doc.paragraphs:
        t = p.text.strip()
        if t: lines.append(t)
    for tbl in doc.tables:
        for row in tbl.rows:
            rt = []
            for c in row.cells:
                t = c.text.strip()
                if t: rt.append(t)
            if rt: lines.append(" | ".join(rt))
    return "\n".join(lines)

def build_ai_prompt(text, level_name):
    subjects = get_subjects()
    subj_list = "\n".join([f"- {s}" for s in subjects.keys()])
    return f"""أنت محلل وثائق تربوية جزائرية. المستوى: {level_name}

استخرج كل الدروس من المحتوى التالي.

المواد المتوقعة (استخدم هذه الأسماء بالضبط):
{subj_list}

لكل درس استخرج:
1. "مادة": اسم المادة بالضبط من القائمة أعلاه
2. "موضوع": عنوان الدرس
3. "كفاءة": مؤشر الكفاءة (إن لم يوجد اكتب "—")

أعد النتيجة كـ JSON فقط:
[{{"مادة":"...","موضوع":"...","كفاءة":"..."}}]

المحتوى:
---
{text[:12000]}
---"""

def extract_with_ai(text, api_key, model, level_name):
    if not GROQ_AVAILABLE:
        return None, None, "مكتبة groq غير مثبتة"
    if not api_key:
        return None, None, "مفتاح API مطلوب"
    prompt = build_ai_prompt(text, level_name)
    try:
        client = Groq(api_key=api_key)
        comp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "محلل وثائق تربوية. أجب بـ JSON فقط."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1, max_tokens=4000,
        )
        raw = comp.choices[0].message.content
        # تحليل JSON
        parsed = None
        for attempt in [
            lambda: json.loads(raw),
            lambda: json.loads(re.search(r'```(?:json)?\s*([\s\S]*?)```', raw).group(1)),
            lambda: json.loads(re.search(r'\[[\s\S]*\]', raw).group(0)),
        ]:
            try:
                parsed = attempt()
                break
            except: pass

        if not parsed:
            return None, raw, "فشل تحليل JSON"

        db = {}
        for item in parsed:
            if not isinstance(item, dict): continue
            s = item.get("مادة","").strip()
            t = item.get("موضوع","—").strip()
            k = item.get("كفاءة","—").strip()
            if s and t:
                db.setdefault(s, []).append({"موضوع": t, "كفاءة": k})
        return db, raw, None
    except Exception as e:
        return None, None, str(e)


# ╔══════════════════════════════════════════════════════════════╗
# ║                   التوزيع الذكي للحصص                       ║
# ╚══════════════════════════════════════════════════════════════╝

def distribute_lessons(raw_db):
    subjects = get_subjects()
    distributed = {}
    report = {}
    for subj, info in subjects.items():
        req = info["الحصص"]
        avail = raw_db.get(subj, [])
        count = len(avail)
        if count == 0:
            distributed[subj] = []
            report[subj] = {"مطلوب":req,"متوفر":0,"حالة":"❌","توزيع":[]}
            continue
        result = []
        dist_detail = []
        if count >= req:
            result = [l.copy() for l in avail[:req]]
            dist_detail = [f"درس {i+1}" for i in range(req)]
        else:
            pp = req / count
            for i, les in enumerate(avail):
                s = round(i*pp); e = round((i+1)*pp)
                for _ in range(e-s):
                    en = les.copy()
                    en["_رقم"] = len(result)+1; en["_مجموع"] = req
                    result.append(en)
                    dist_detail.append(f"درس {i+1}")
        distributed[subj] = result
        report[subj] = {"مطلوب":req,"متوفر":count,"حالة":"✅" if result else "❌","توزيع":dist_detail}
    return distributed, report


# ╔══════════════════════════════════════════════════════════════╗
# ║                 القالب والحقن (تكيفي)                        ║
# ╚══════════════════════════════════════════════════════════════╝

def _rtl(p):
    pPr = p._p.get_or_add_pPr()
    pPr.append(pPr.makeelement(qn('w:bidi'), {}))

def _cell(c, t, bold=False, size=10, color=None):
    c.text = ""; p = c.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER; _rtl(p)
    r = p.add_run(t); r.bold = bold; r.font.size = Pt(size)
    r.font.name = "Sakkal Majalla"
    if color: r.font.color.rgb = color
    rPr = r._r.get_or_add_rPr()
    rPr.append(rPr.makeelement(qn('w:rFonts'), {qn('w:cs'): 'Sakkal Majalla'}))

def _shade(row, hx):
    for c in row.cells:
        tc = c._tc.get_or_add_tcPr()
        tc.append(tc.makeelement(qn('w:shd'),{qn('w:fill'):hx,qn('w:val'):'clear'}))

def _ptable(doc, title, start, count):
    h = doc.add_paragraph(); h.alignment = WD_ALIGN_PARAGRAPH.CENTER; _rtl(h)
    r = h.add_run(title); r.bold=True; r.font.size=Pt(13)
    r.font.color.rgb=RGBColor(0,51,102)
    hdrs = ['مؤشرات الكفاءة','عنوان الدرس','الميدان','النشاط','المدة']
    tbl = doc.add_table(rows=1+count, cols=5)
    tbl.style = 'Table Grid'; tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    ws = [Cm(5.5),Cm(5),Cm(3.5),Cm(3.5),Cm(2)]
    for row in tbl.rows:
        for i,w in enumerate(ws): row.cells[i].width = w
    hdr = tbl.rows[0]; _shade(hdr,"1F4E79")
    for i,t in enumerate(hdrs):
        _cell(hdr.cells[i], t, True, 11, RGBColor(255,255,255))
    for j in range(count):
        n = start+j; dr = tbl.rows[1+j]
        if j%2==0: _shade(dr,"EDF2F9")
        for i,ph in enumerate([f'{{{{كفاءة_{n}}}}}',f'{{{{موضوع_{n}}}}}',
                                f'{{{{ميدان_{n}}}}}',f'{{{{نشاط_{n}}}}}',f'{{{{مدة_{n}}}}}']):
            _cell(dr.cells[i], ph, size=9)

def create_template_bytes(day_name=None):
    """إنشاء قالب تكيفي حسب عدد الحصص"""
    sched = get_schedule()
    level = st.session_state.get('selected_level','')

    # حساب أقصى عدد حصص صباحية ومسائية
    if day_name and day_name in sched:
        plan = sched[day_name]
        routine = get_routine()
        m_count = sum(1 for s in plan if s['الفترة']=='صباحية' and s['النشاط'] not in routine)
        e_count = sum(1 for s in plan if s.get('الفترة')=='مسائية' and s['النشاط'] not in routine)
        m_total = sum(1 for s in plan if s['الفترة']=='صباحية')
        e_total = sum(1 for s in plan if s.get('الفترة')=='مسائية')
    else:
        m_total = 7; e_total = 5

    doc = Document()
    for sec in doc.sections:
        sec._sectPr.append(sec._sectPr.makeelement(qn('w:bidi'), {}))
    for t,sz,b in [('الجمهورية الجزائرية الديمقراطية الشعبية',12,True),
                    ('وزارة التربية الوطنية',11,False)]:
        p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER; _rtl(p)
        r = p.add_run(t); r.bold = b; r.font.size = Pt(sz)
    tp = doc.add_paragraph(); tp.alignment = WD_ALIGN_PARAGRAPH.CENTER; _rtl(tp)
    tr = tp.add_run(f'الكراس اليومي — {level}')
    tr.bold=True; tr.font.size=Pt(16); tr.font.color.rgb=RGBColor(0,51,102)
    info = doc.add_table(rows=1, cols=3)
    info.alignment = WD_TABLE_ALIGNMENT.CENTER
    _cell(info.rows[0].cells[2],'اليوم : {{اليوم}}',True,12)
    _cell(info.rows[0].cells[1],'التاريخ : {{التاريخ}}',size=11)
    _cell(info.rows[0].cells[0],'الأسبوع : {{الأسبوع}}',size=11)
    doc.add_paragraph('')
    _ptable(doc,'☀ الفترة الصباحية',1, m_total)
    if e_total > 0:
        doc.add_paragraph('')
        _ptable(doc,'🌙 الفترة المسائية', m_total+1, e_total)
    doc.add_paragraph('')
    np2 = doc.add_paragraph()
    np2.alignment = WD_ALIGN_PARAGRAPH.RIGHT; _rtl(np2)
    np2.add_run('ملاحظات : '+'.'*80).font.size = Pt(10)
    buf = BytesIO(); doc.save(buf)
    return buf.getvalue()

def _sr(para, old, new):
    if old not in para.text: return
    for run in para.runs:
        if old in run.text: run.text = run.text.replace(old, new); return
    f = para.text.replace(old, new)
    if para.runs:
        for run in para.runs: run.text = ""
        para.runs[0].text = f

def build_daily_planner(day, template_bytes, dist_db, week_num="", date_str=""):
    sched = get_schedule()
    plan = sched.get(day, [])
    if not plan: return None, [], [f"اليوم '{day}' غير موجود"]
    routine = get_routine()
    doc = Document(BytesIO(template_bytes))
    reps = {"{{اليوم}}":day,"{{التاريخ}}":date_str,"{{الأسبوع}}":week_num}
    sessions_info = []; warnings = []
    for i, session in enumerate(plan, 1):
        act = session["النشاط"]; dur = session["المدة"]
        per = session.get("الفترة",""); domain = get_domain_for(act)
        reps[f"{{{{مدة_{i}}}}}"] = dur; reps[f"{{{{نشاط_{i}}}}}"] = act
        info = {"رقم":i,"النشاط":act,"المدة":dur,"الفترة":per,
                "المجال":domain,"نوع":"روتيني","الموضوع":"—","الكفاءة":"—"}
        if act in routine:
            reps[f"{{{{موضوع_{i}}}}}"]="—"; reps[f"{{{{كفاءة_{i}}}}}"]="—"
            reps[f"{{{{ميدان_{i}}}}}"]="—"
        elif act in dist_db and dist_db[act]:
            les = dist_db[act].pop(0)
            t=les.get('موضوع','—'); k=les.get('كفاءة','—')
            reps[f"{{{{موضوع_{i}}}}}"]= t; reps[f"{{{{كفاءة_{i}}}}}"]= k
            reps[f"{{{{ميدان_{i}}}}}"]= domain
            info.update({"نوع":"تعليمي","الموضوع":t,"الكفاءة":k})
        else:
            reps[f"{{{{موضوع_{i}}}}}"]="⚠ لا توجد مذكرة"
            reps[f"{{{{كفاءة_{i}}}}}"]="⚠ لا توجد مذكرة"
            reps[f"{{{{ميدان_{i}}}}}"]= domain
            info["نوع"]="ناقص"; warnings.append(act)
        sessions_info.append(info)
    for tbl in doc.tables:
        for row in tbl.rows:
            for cell in row.cells:
                for para in cell.paragraphs:
                    for k2,v in reps.items():
                        if k2 in para.text: _sr(para,k2,str(v))
    for para in doc.paragraphs:
        for k2,v in reps.items():
            if k2 in para.text: _sr(para,k2,str(v))
    buf = BytesIO(); doc.save(buf)
    return buf.getvalue(), sessions_info, warnings


# ╔══════════════════════════════════════════════════════════════╗
# ║                     واجهة Streamlit                          ║
# ╚══════════════════════════════════════════════════════════════╝

st.set_page_config(page_title="الكراس اليومي 🎓", page_icon="🎓",
                   layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
.main .block-container{direction:rtl;text-align:right}
h1,h2,h3{text-align:center!important}
.card{padding:1rem;border-radius:12px;text-align:center;margin:.4rem 0;box-shadow:0 2px 8px rgba(0,0,0,.08)}
.card h4{margin:0 0 .3rem 0;font-size:.9rem}.card .num{font-size:2rem;font-weight:700}
.card-blue{background:linear-gradient(135deg,#1F4E79,#2E75B6);color:#fff}
.card-green{background:linear-gradient(135deg,#2E7D32,#43A047);color:#fff}
.card-amber{background:linear-gradient(135deg,#E65100,#FF9800);color:#fff}
.card-purple{background:linear-gradient(135deg,#4A148C,#7B1FA2);color:#fff}
.slot{display:flex;align-items:center;gap:.8rem;padding:.7rem 1rem;margin:.3rem 0;border-radius:8px;direction:rtl}
.slot-routine{background:#f5f5f5;border-right:4px solid #9e9e9e}
.slot-teach{background:#e3f2fd;border-right:4px solid #1565c0}
.slot-warn{background:#fff3e0;border-right:4px solid #e65100}
.stDownloadButton>button{width:100%;background:linear-gradient(135deg,#1F4E79,#2E75B6)!important;color:#fff!important;border:none!important;border-radius:8px!important}
[data-testid="stSidebar"]{direction:rtl;text-align:right}
footer{visibility:hidden}
.ok-box{background:#e8f5e9;border:1px solid #4caf50;border-radius:10px;padding:1rem;text-align:center}
.ai-box{background:linear-gradient(135deg,#E8EAF6,#C5CAE9);border:2px solid #3F51B5;border-radius:12px;padding:1.2rem;margin:.5rem 0}
.level-card{border:2px solid #1F4E79;border-radius:12px;padding:1rem;margin:.5rem 0;text-align:center}
</style>""", unsafe_allow_html=True)

# Session State
for k in ['lessons_db','template_bytes','generated_files','dist_report',
          'ai_raw','file_text','selected_level','custom_configs']:
    if k not in st.session_state:
        if k == 'generated_files': st.session_state[k] = {}
        elif k == 'selected_level': st.session_state[k] = 'قسم التحضيري'
        elif k == 'custom_configs': st.session_state[k] = copy.deepcopy(LEVELS_CONFIG)
        else: st.session_state[k] = None


# ═══════════════════════════════════════
#  الشريط الجانبي
# ═══════════════════════════════════════

with st.sidebar:
    st.markdown("## 🎓 اختر المستوى")
    level_names = list(LEVELS_CONFIG.keys())
    selected = st.selectbox("المستوى الدراسي", level_names,
                             index=level_names.index(st.session_state.selected_level),
                             key="level_select")
    if selected != st.session_state.selected_level:
        st.session_state.selected_level = selected
        st.session_state.lessons_db = None
        st.session_state.generated_files = {}
        st.session_state.dist_report = None
        st.session_state.template_bytes = None
        st.rerun()

    # معلومات المستوى
    cfg = get_level_config()
    total_sessions = sum(i["الحصص"] for i in cfg["المواد"].values())
    total_subjects = len(cfg["المواد"])
    total_domains = len(cfg["المجالات"])
    st.markdown(f"""
    <div class="level-card">
        <strong>{selected}</strong><br>
        📘 {total_subjects} مادة | 📖 {total_sessions} حصة/أسبوع<br>
        🗺️ {total_domains} مجال
    </div>""", unsafe_allow_html=True)

    st.markdown("---")
    week_num = st.text_input("📅 الأسبوع", placeholder="10")
    date_str = st.text_input("📆 التاريخ", placeholder="2024/12/01")

    st.markdown("---")
    st.markdown("### 🧠 Groq AI")
    groq_key = st.text_input("🔑 API Key", type="password")
    ai_model = st.selectbox("النموذج", [
        "llama-3.3-70b-versatile","llama-3.1-70b-versatile",
        "mixtral-8x7b-32768","gemma2-9b-it"])

    st.markdown("---")
    uploaded = st.file_uploader("📤 ملف المذكرات", type=["docx"])
    st.caption("🎓 v6.0 — متعدد المستويات")


# معالجة الرفع
if uploaded:
    fb = uploaded.read()
    if st.session_state.get('_last') != uploaded.name:
        st.session_state.file_text = read_docx_text(fb)
        st.session_state._fb = fb
        st.session_state._last = uploaded.name
        st.session_state.lessons_db = None
        st.session_state.generated_files = {}
    if not st.session_state.template_bytes:
        st.session_state.template_bytes = create_template_bytes()


# العنوان
level = st.session_state.selected_level
st.markdown(f"""
<h1 style="background:linear-gradient(135deg,#1F4E79,#2E75B6);
-webkit-background-clip:text;-webkit-text-fill-color:transparent;
font-size:2.2rem;">🎓 الكراس اليومي — {level}</h1>
<p style="text-align:center;color:#888;">مدعوم بالذكاء الاصطناعي — جميع المراحل الابتدائية</p>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════
#  التبويبات
# ═══════════════════════════════════════

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "⚙️ إعداد المستوى", "🧠 الاستخراج", "📅 توليد ومعاينة",
    "📊 التوقيت", "🗺️ المجالات"
])


# ──── تبويب 1: إعداد المستوى (المحرر) ────

with tab1:
    st.markdown("### ⚙️ تخصيص المواد والحصص")
    st.markdown(f"**المستوى:** {level}")

    cfg = get_level_config()
    subjects = cfg["المواد"]
    domains = cfg["المجالات"]

    # تحويل إلى جدول قابل للتعديل
    subj_data = []
    for name, info in subjects.items():
        subj_data.append({
            "المادة": name,
            "المجال": info["المجال"],
            "الحصص الأسبوعية": info["الحصص"],
        })

    st.markdown("#### 📘 جدول المواد")
    edited = st.data_editor(
        subj_data,
        num_rows="dynamic",
        column_config={
            "المادة": st.column_config.TextColumn("المادة", width="medium"),
            "المجال": st.column_config.SelectboxColumn("المجال",
                       options=list(domains.keys()), width="medium"),
            "الحصص الأسبوعية": st.column_config.NumberColumn("الحصص", min_value=1, max_value=10, width="small"),
        },
        use_container_width=True,
        key="subjects_editor",
    )

    col_save, col_gen = st.columns(2)

    with col_save:
        if st.button("💾 حفظ التعديلات", use_container_width=True, type="primary"):
            new_subjects = {}
            for row in edited:
                if row.get("المادة") and row.get("المجال"):
                    new_subjects[row["المادة"]] = {
                        "المجال": row["المجال"],
                        "الحصص": row.get("الحصص الأسبوعية", 1),
                    }
            if new_subjects:
                st.session_state.custom_configs[level]["المواد"] = new_subjects
                st.session_state.template_bytes = None
                st.success(f"✅ تم حفظ {len(new_subjects)} مادة!")

    with col_gen:
        if st.button("🔄 توليد توقيت تلقائي", use_container_width=True):
            cfg2 = get_level_config()
            new_sched = auto_generate_schedule(cfg2["المواد"], cfg2["الأنشطة_الروتينية"])
            st.session_state.custom_configs[level]["التوقيت"] = new_sched
            st.session_state.template_bytes = None
            st.success("✅ تم توليد التوقيت!")

    # ملخص
    total = sum(row.get("الحصص الأسبوعية",0) for row in edited if row.get("المادة"))
    st.info(f"📊 مجموع الحصص: **{total}** حصة/أسبوع (المتاح: 34 حصة)")

    # إضافة مجال جديد
    st.markdown("---")
    with st.expander("➕ إضافة مجال جديد"):
        nc1, nc2 = st.columns(2)
        with nc1:
            new_dom = st.text_input("اسم المجال", key="new_dom")
        with nc2:
            new_col = st.color_picker("اللون", "#1565C0", key="new_col")
        if st.button("إضافة") and new_dom:
            st.session_state.custom_configs[level]["المجالات"][new_dom] = {"اللون": new_col}
            st.success(f"✅ تمت إضافة: {new_dom}")
            st.rerun()


# ──── تبويب 2: الاستخراج ────

with tab2:
    if not st.session_state.file_text:
        st.info("👆 ارفع ملف المذكرات من الشريط الجانبي")
    else:
        st.markdown("### 🎯 استخراج الدروس")

        c_ai, c_re = st.columns(2)
        with c_ai:
            st.markdown('<div class="ai-box"><h3 style="text-align:center;color:#283593;">🧠 ذكاء اصطناعي</h3></div>', unsafe_allow_html=True)
            disabled = not groq_key or not GROQ_AVAILABLE
            if disabled: st.warning("أدخل مفتاح API")
            if st.button("🧠 استخراج بـ AI", use_container_width=True, type="primary", disabled=disabled):
                with st.spinner("🧠 جارٍ..."):
                    db, raw, err = extract_with_ai(st.session_state.file_text, groq_key, ai_model, level)
                    st.session_state.ai_raw = raw
                if err:
                    st.error(f"❌ {err}")
                elif db:
                    dist, rep = distribute_lessons(db)
                    st.session_state.lessons_db = dist
                    st.session_state.dist_report = rep
                    st.session_state.generated_files = {}
                    st.success(f"✅ تم استخراج {sum(len(v) for v in db.values())} درس!")
                    st.rerun()

        with c_re:
            st.markdown('<div style="background:#F5F5F5;border:2px solid #9E9E9E;border-radius:12px;padding:1.2rem;margin:.5rem 0;"><h3 style="text-align:center;color:#616161;">📝 Regex</h3></div>', unsafe_allow_html=True)
            # Regex extraction simplified for space

        # عرض النتائج
        db = st.session_state.lessons_db
        if db:
            st.markdown("---")
            total = sum(len(v) for v in db.values())
            subjects_cfg = get_subjects()
            matched = set(k for k,v in db.items() if v) & set(subjects_cfg.keys())
            missing = set(subjects_cfg.keys()) - set(k for k,v in db.items() if v)

            c1,c2,c3 = st.columns(3)
            for col,title,num,cls in [(c1,"📖 الحصص",total,"card-green"),
                                       (c2,"✅ مغطاة",len(matched),"card-purple"),
                                       (c3,"⚠ ناقصة",len(missing),"card-amber")]:
                with col:
                    st.markdown(f'<div class="card {cls}"><h4>{title}</h4><div class="num">{num}</div></div>',
                                unsafe_allow_html=True)
            if missing: st.warning(f"⚠️ ناقصة: **{' ، '.join(missing)}**")

            for subj in sorted(db.keys()):
                lessons = db[subj]
                if not lessons: continue
                domain = get_domain_for(subj)
                with st.expander(f"✅ {subj} — {len(lessons)} حصة — {domain}"):
                    for j, les in enumerate(lessons, 1):
                        st.markdown(f"**{j}.** 📝 {les.get('موضوع','—')}\n🎯 {les.get('كفاءة','—')}")
                        if j < len(lessons): st.divider()


# ──── تبويب 3: توليد ومعاينة ────

with tab3:
    db = st.session_state.lessons_db
    if not db or not any(db.values()):
        st.info("🧠 استخرج الدروس أولاً")
    else:
        sched = get_schedule()
        days = list(sched.keys())

        st.markdown("### 📅 اختر الأيام")
        cols = st.columns(len(days))
        selected_days = []
        for i,d in enumerate(days):
            routine = get_routine()
            teach = sum(1 for s in sched[d] if s["النشاط"] not in routine)
            with cols[i]:
                if st.checkbox(f"{d} ({teach})", key=f"d_{d}"):
                    selected_days.append(d)
        if st.checkbox("✅ الكل"): selected_days = days

        if selected_days and st.button(f"🚀 توليد {len(selected_days)} كراس",
                                        type="primary", use_container_width=True):
            wdb = copy.deepcopy(db)
            gen = {}
            bar = st.progress(0)
            for idx, d in enumerate(selected_days):
                bar.progress(idx/len(selected_days))
                tmpl = create_template_bytes(d)
                result, info, warns = build_daily_planner(d, tmpl, wdb, week_num, date_str)
                if result:
                    gen[d] = {'bytes':result,'sessions':info,'warnings':warns}
            bar.progress(1.0)
            st.session_state.generated_files = gen
            st.markdown(f'<div class="ok-box"><h3>✅ {len(gen)} كراس!</h3></div>', unsafe_allow_html=True)

        # تحميل + معاينة
        gf = st.session_state.generated_files
        if gf:
            st.markdown("### 📥 التحميل")
            dl_cols = st.columns(min(len(gf),5))
            for i,(d,data) in enumerate(gf.items()):
                with dl_cols[i%5]:
                    st.download_button(f"📄 {d}", data=data['bytes'], file_name=f"كراس_{d}.docx",
                                       mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                       use_container_width=True, key=f"dl_{d}")

            st.markdown("---")
            st.markdown("### 👁️ معاينة")
            dp = st.selectbox("اليوم", list(gf.keys()))
            if dp:
                data = gf[dp]
                for s in data['sessions']:
                    typ = s['نوع']
                    css = {'روتيني':'slot-routine','تعليمي':'slot-teach','ناقص':'slot-warn'}.get(typ,'slot-routine')
                    ic = {'روتيني':'⏰','تعليمي':'📖','ناقص':'⚠️'}.get(typ,'⏰')
                    dom = s.get('المجال','—')
                    bdg = domain_badge(dom) if dom!='—' else ''
                    ext = ''
                    if typ=='تعليمي':
                        ext = f"<br><small>📝 {s['الموضوع']}</small><br><small>🎯 {s['الكفاءة']}</small>"
                    st.markdown(f'<div class="slot {css}"><span style="font-size:1.3rem">{ic}</span>'
                                f'<div style="flex:1"><strong>{s["النشاط"]}</strong> '
                                f'<span style="color:#888">({s["المدة"]})</span>{bdg}{ext}</div></div>',
                                unsafe_allow_html=True)


# ──── تبويب 4: التوقيت ────

with tab4:
    st.markdown(f"### 📊 التوقيت — {level}")
    sched = get_schedule()
    routine = get_routine()
    vd = st.selectbox("اليوم", list(sched.keys()), key="sched_v")
    if vd:
        plan = sched[vd]
        morning = [s for s in plan if s.get('الفترة')=='صباحية']
        evening = [s for s in plan if s.get('الفترة')=='مسائية']
        for nm, sl in [("☀️ صباح",morning),("🌙 مساء",evening)]:
            if not sl: continue
            st.markdown(f"#### {nm}")
            rows = [{"#":j,"النشاط":s['النشاط'],"المدة":s['المدة'],
                     "المجال":get_domain_for(s['النشاط']) if s['النشاط'] not in routine else "—",
                     "النوع":"🔄" if s['النشاط'] in routine else "📖"}
                    for j,s in enumerate(sl,1)]
            st.dataframe(rows, use_container_width=True, hide_index=True)

    st.markdown("---")
    errs, cnts = verify_schedule()
    subjects_cfg = get_subjects()
    for subj, info in subjects_cfg.items():
        exp = info["الحصص"]; act = cnts.get(subj,0)
        ok = "✅" if act==exp else "❌"
        st.markdown(f"{ok} **{subj}** — {act}/{exp} — {domain_badge(get_domain_for(subj))}",
                    unsafe_allow_html=True)


# ──── تبويب 5: المجالات ────

with tab5:
    st.markdown(f"### 🗺️ المجالات — {level}")
    domains = get_domains()
    subjects_cfg = get_subjects()
    doms = {}
    for s, inf in subjects_cfg.items():
        doms.setdefault(inf["المجال"],[]).append(s)
    cols5 = st.columns(2)
    for i,(dom,subjs) in enumerate(doms.items()):
        col = get_domain_color(dom)
        total_h = sum(subjects_cfg[s]["الحصص"] for s in subjs if s in subjects_cfg)
        with cols5[i%2]:
            st.markdown(f'<div style="border:2px solid {col};border-radius:12px;padding:1rem;margin:.5rem 0;">'
                        f'<h4 style="color:{col};text-align:center;">{dom} ({total_h} ح)</h4>',
                        unsafe_allow_html=True)
            for s in subjs:
                cnt = subjects_cfg.get(s,{}).get("الحصص",0)
                st.markdown(f'<div style="display:flex;align-items:center;gap:8px;margin:4px 0;direction:rtl;">'
                            f'<span style="min-width:140px">{s}</span>'
                            f'<div style="background:{col}44;border-radius:4px;height:20px;width:{cnt*14}px;"></div>'
                            f'<span style="color:{col};font-weight:700;">{cnt}</span></div>',
                            unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
    grand = sum(inf["الحصص"] for inf in subjects_cfg.values())
    st.markdown(f'<div class="card card-blue"><h4>المجموع</h4><div class="num">{grand} حصة</div></div>',
                unsafe_allow_html=True)
