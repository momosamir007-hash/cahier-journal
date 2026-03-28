# -*- coding: utf-8 -*-
"""
🎓 الكراس اليومي — جميع المراحل الابتدائية
الإصدار 7.0 — دعم Word + PDF + صور + AI
"""

import streamlit as st
import re, copy, json, base64, io, math
from io import BytesIO
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from PIL import Image

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False


# ╔══════════════════════════════════════════════════════════════╗
# ║     القسم 1: إعدادات المستويات الدراسية                     ║
# ╚══════════════════════════════════════════════════════════════╝

LEVELS_CONFIG = {
    "قسم التحضيري": {
        "الأنشطة_الروتينية": ["الاستقبال","الاستراحة","تهيئة الخروج","نهاية الخروج"],
        "المجالات": {
            "المجال اللغوي":{"اللون":"#1565C0"},"المجال الرياضي":{"اللون":"#C62828"},
            "المجال العلمي":{"اللون":"#2E7D32"},"المجال الاجتماعي":{"اللون":"#F57F17"},
            "المجال الفني":{"اللون":"#6A1B9A"},"المجال البدني والإيقاعي":{"اللون":"#00838F"},
        },
        "المواد": {
            "تعبير شفوي":{"المجال":"المجال اللغوي","الحصص":3},
            "مبادئ القراءة":{"المجال":"المجال اللغوي","الحصص":4},
            "تخطيط":{"المجال":"المجال اللغوي","الحصص":2},
            "رياضيات":{"المجال":"المجال الرياضي","الحصص":5},
            "ت علمية وتكنولوجية":{"المجال":"المجال العلمي","الحصص":4},
            "ت إسلامية":{"المجال":"المجال الاجتماعي","الحصص":2},
            "ت مدنية":{"المجال":"المجال الاجتماعي","الحصص":2},
            "تربية تشكيلية":{"المجال":"المجال الفني","الحص��":2},
            "موسيقى وإنشاد":{"المجال":"المجال الفني","الحصص":2},
            "مسرح وعرائس":{"المجال":"المجال الفني","الحصص":2},
            "ت بدنية":{"المجال":"المجال البدني والإيقاعي","الحصص":4},
            "ت إيقاعية":{"المجال":"المجال البدني والإيقاعي","الحصص":2},
        },
        "التوقيت": {
            "الأحد":[
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
            "الإثنين":[
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
            "الثلاثاء":[
                {"النشاط":"الاستقبال","المدة":"15 د","الفترة":"صباحية"},
                {"النشاط":"تعبير شفوي","المدة":"30 د","الفترة":"صباحية"},
                {"النشاط":"مبادئ القراءة","المدة":"30 د","الفترة":"صباحية"},
                {"النشاط":"رياضيات","المدة":"30 د","الفترة":"صباحية"},
                {"النشاط":"ت إسلامية","المدة":"30 د","الفترة":"صباحية"},
                {"النشاط":"ت بدنية","المدة":"30 د","الفترة":"صباحية"},
                {"النشاط":"تهيئة الخروج","المدة":"15 د","الفترة":"صباحية"},
            ],
            "الأربعاء":[
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
            "الخميس":[
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

    "السنة 1 ابتدائي": {
        "الأنشطة_الروتينية":["الاستقبال","الاستراحة","تهيئة الخروج","نهاية الخروج"],
        "المجالات":{
            "اللغة العربية":{"اللون":"#1565C0"},"الرياضيات":{"اللون":"#C62828"},
            "التربية العلمية":{"اللون":"#2E7D32"},"التربية الاجتماعية":{"اللون":"#F57F17"},
            "التربية الفنية":{"اللون":"#6A1B9A"},"التربية البدنية":{"اللون":"#00838F"},
        },
        "المواد":{
            "قراءة":{"المجال":"اللغة العربية","الحصص":6},
            "تعبير شفوي":{"المجال":"اللغة العربية","الحصص":2},
            "كتابة وخط":{"المجال":"اللغة العربية","الحصص":3},
            "محفوظات":{"المجال":"اللغة العربية","الحصص":1},
            "رياضيات":{"المجال":"الرياضيات","الحصص":5},
            "تربية علمية":{"المجال":"التربية العلمية","الحصص":2},
            "تربية إسلامية":{"المجال":"التربية الاجتماعية","الحصص":2},
            "تربية مدنية":{"المجال":"التربية الاجتماعية","الحصص":1},
            "تربية فنية":{"المجال":"التربية الفنية","الحصص":2},
            "تربية موسيقية":{"المجال":"التربية الفنية","الحصص":1},
            "تربية بدنية":{"المجال":"التربية البدنية","الحصص":2},
        },
        "التوقيت":{},
    },

    "السنة 2 ابتدائي": {
        "الأنشطة_الروتينية":["الاستقبال","الاستراحة","تهيئة الخروج","نهاية الخروج"],
        "المجالات":{
            "اللغة العربية":{"اللون":"#1565C0"},"الرياضيات":{"اللون":"#C62828"},
            "التربية العلمية":{"اللون":"#2E7D32"},"التربية الاجتماعية":{"اللون":"#F57F17"},
            "التربية الفنية":{"اللون":"#6A1B9A"},"التربية البدنية":{"اللون":"#00838F"},
        },
        "المواد":{
            "قراءة":{"المجال":"اللغة العربية","الحصص":5},
            "تعبير شفوي":{"المجال":"اللغة العربية","الحصص":2},
            "كتابة وخط":{"المجال":"اللغة العربية","الحصص":3},
            "إملاء":{"المجال":"اللغة العربية","الحصص":1},
            "محفوظات":{"المجال":"اللغة العربية","الحصص":1},
            "رياضيات":{"المجال":"الرياضيات","الحصص":5},
            "تربية علمية":{"المجال":"التربية العلمية","الحصص":2},
            "تربية إسلامية":{"المجال":"التربية الاجتماعية","الحصص":2},
            "تربية مدنية":{"المجال":"التربية الاجتماعية","الحصص":1},
            "تربية فنية":{"المجال":"التربية الفنية","الحصص":2},
            "تربية موسيقية":{"المجال":"التربية الفنية","الحصص":1},
            "تربية بدنية":{"المجال":"التربية البدنية","الحصص":2},
        },
        "التوقيت":{},
    },

    "السنة 3 ابتدائي": {
        "الأنشطة_الروتينية":["الاستقبال","الاستراحة","تهيئة الخروج","نهاية الخروج"],
        "المجالات":{
            "اللغة العربية":{"اللون":"#1565C0"},"اللغة الفرنسية":{"اللون":"#1976D2"},
            "الرياضيات":{"اللون":"#C62828"},"التربية العلمية":{"اللون":"#2E7D32"},
            "التربية الاجتماعية":{"اللون":"#F57F17"},"التربية الفنية":{"اللون":"#6A1B9A"},
            "التربية البدنية":{"اللون":"#00838F"},
        },
        "المواد":{
            "قراءة":{"المجال":"اللغة العربية","الحصص":4},
            "تعبير شفوي":{"المجال":"اللغة العربية","الحصص":2},
            "كتابة وإملاء":{"المجال":"اللغة العربية","الحصص":2},
            "قواعد":{"المجال":"اللغة العربية","الحصص":1},
            "محفوظات":{"المجال":"اللغة العربية","الحصص":1},
            "فرنسية":{"المجال":"اللغة الفرنسية","الحصص":3},
            "رياضيات":{"المجال":"الرياضيات","الحصص":5},
            "تربية علمية":{"المجال":"التربية العلمية","الحصص":2},
            "تربية إسلامية":{"المجال":"التربية الاجتماعية","الحصص":1},
            "تربية مدنية":{"المجال":"التربية الاجتماعية","الحصص":1},
            "تاريخ وجغرافيا":{"المجال":"التربية الاجتماعية","الحصص":1},
            "تربية فنية":{"المجال":"التربية الفنية","الحصص":1},
            "تربية موسيقية":{"المجال":"التربية الفنية","الحصص":1},
            "تربية بدنية":{"المجال":"التربية البدنية","الحصص":2},
        },
        "التوقيت":{},
    },

    "السنة 4 ابتدائي": {
        "الأنشطة_الروتينية":["الاستقبال","الاستراحة","تهيئة الخروج","نهاية الخروج"],
        "المجالات":{
            "اللغة العربية":{"اللون":"#1565C0"},"اللغة الفرنسية":{"اللون":"#1976D2"},
            "الرياضيات":{"اللون":"#C62828"},"التربية العلمية":{"اللون":"#2E7D32"},
            "التربية الاجتماعية":{"اللون":"#F57F17"},"التربية الفنية":{"اللون":"#6A1B9A"},
            "التربية البدنية":{"اللون":"#00838F"},
        },
        "المواد":{
            "قراءة ودراسة نص":{"المجال":"اللغة العربية","الحصص":3},
            "قواعد صرفية ونحوية":{"المجال":"اللغة العربية","الحصص":2},
            "تعبير كتابي":{"المجال":"اللغة العربية","الحصص":1},
            "تعبير شفوي":{"المجال":"اللغة العربية","الحصص":1},
            "إملاء":{"المجال":"اللغة العربية","الحصص":1},
            "محفوظات":{"المجال":"اللغة العربية","الحصص":1},
            "فرنسية":{"المجال":"اللغة الفرنسية","الحصص":3},
            "رياضيات":{"المجال":"الرياضيات","الحصص":5},
            "تربية علمية":{"المجال":"التربية العلمية","الحصص":2},
            "تربية إسلامية":{"المجال":"التربية الاجتماعية","الحصص":1},
            "تربية مدنية":{"المجال":"التربية الاجتماعية","الحصص":1},
            "تاريخ":{"المجال":"التربية الاجتماعية","الحصص":1},
            "جغرافيا":{"المجال":"التربية الاجتماعية","الحصص":1},
            "تربية فنية":{"المجال":"التربية الفنية","الحصص":1},
            "تربية موسيقية":{"المجال":"التربية الفنية","الحصص":1},
            "تربية بدنية":{"المجال":"التربية البدنية","الحصص":2},
        },
        "التوقيت":{},
    },

    "السنة 5 ابتدائي": {
        "الأنشطة_الروتينية":["الاستقبال","الاستراحة","تهيئة الخروج","نهاية الخروج"],
        "المجالات":{
            "اللغة العربية":{"اللون":"#1565C0"},"اللغة الفرنسية":{"اللون":"#1976D2"},
            "الرياضيات":{"اللون":"#C62828"},"التربية العلمية":{"اللون":"#2E7D32"},
            "التربية الاجتماعية":{"اللون":"#F57F17"},"التربية الفنية":{"اللون":"#6A1B9A"},
            "التربية البدنية":{"اللون":"#00838F"},
        },
        "المواد":{
            "قراءة ودراسة نص":{"المجال":"اللغة العربية","الحصص":3},
            "قواعد صرفية ونحوية":{"المجال":"اللغة العربية","الحصص":2},
            "تعبير كتابي":{"المجال":"اللغة العربية","الحصص":1},
            "تعبير شفوي":{"المجال":"اللغة العربية","الحصص":1},
            "إملاء":{"المجال":"اللغة العربية","الحصص":1},
            "محفوظات":{"المجال":"اللغة العربية","الحصص":1},
            "فرنسية":{"المجال":"اللغة الفرنسية","الحصص":3},
            "رياضيات":{"المجال":"الرياضيات","الحصص":5},
            "تربية علمية":{"المجال":"التربية العلمية","الحصص":2},
            "تربية إسلامية":{"المجال":"التربية الاجتماعية","الحصص":1},
            "تربية مدنية":{"المجال":"التربية الاجتماعية","الحصص":1},
            "تاريخ":{"المجال":"التربية الاجتماعية","الحصص":1},
            "جغرافيا":{"المجال":"التربية الاجتماعية","الحصص":1},
            "تربية فني��":{"المجال":"التربية الفنية","الحصص":1},
            "تربية موسيقية":{"المجال":"التربية الفنية","الحصص":1},
            "تربية بدنية":{"المجال":"التربية البدنية","الحصص":2},
        },
        "التوقيت":{},
    },
}


# ╔══════════════════════════════════════════════════════════════╗
# ║     القسم 2: معالجة الوثائق متعددة الصيغ                    ║
# ╚══════════════════════════════════════════════════════════════╝

SUPPORTED_FORMATS = {
    "docx": "📄 Word",
    "pdf": "📕 PDF",
    "jpg": "🖼️ صورة",
    "jpeg": "🖼️ صورة",
    "png": "🖼️ صورة",
    "bmp": "🖼️ صورة",
    "tiff": "🖼️ صورة",
    "webp": "🖼️ صورة",
}


def get_file_type(filename):
    ext = filename.lower().rsplit('.', 1)[-1] if '.' in filename else ''
    return ext


def compress_image(img_bytes, max_size=1500, quality=85):
    """ضغط الصورة لتناسب API"""
    img = Image.open(BytesIO(img_bytes))
    if img.mode == 'RGBA':
        img = img.convert('RGB')
    w, h = img.size
    if max(w, h) > max_size:
        ratio = max_size / max(w, h)
        img = img.resize((int(w * ratio), int(h * ratio)), Image.LANCZOS)
    buf = BytesIO()
    img.save(buf, format='JPEG', quality=quality)
    return buf.getvalue()


def image_to_base64(img_bytes):
    """تحويل صورة إلى base64"""
    compressed = compress_image(img_bytes)
    return base64.b64encode(compressed).decode('utf-8')


def extract_text_from_docx(file_bytes):
    """استخراج نص من ملف Word"""
    doc = Document(BytesIO(file_bytes))
    lines = []
    for p in doc.paragraphs:
        t = p.text.strip()
        if t:
            lines.append(t)
    for tbl in doc.tables:
        for row in tbl.rows:
            rt = []
            for c in row.cells:
                t = c.text.strip()
                if t:
                    rt.append(t)
            if rt:
                lines.append(" | ".join(rt))
    return "\n".join(lines)


def extract_text_from_pdf(file_bytes):
    """استخراج نص من PDF — نص أو صور"""
    if not PYMUPDF_AVAILABLE:
        return None, [], "مكتبة PyMuPDF غير مثبتة"

    doc = fitz.open(stream=file_bytes, filetype="pdf")
    total_pages = len(doc)
    all_text = []
    page_images = []
    has_text = False

    for page_num in range(total_pages):
        page = doc[page_num]
        text = page.get_text().strip()

        if text and len(text) > 30:
            all_text.append(f"--- صفحة {page_num + 1} ---\n{text}")
            has_text = True
        else:
            # صفحة مسحوبة ضوئياً — تحويل لصورة
            mat = fitz.Matrix(2.0, 2.0)  # دقة مضاعفة
            pix = page.get_pixmap(matrix=mat)
            img_bytes = pix.tobytes("jpeg")
            page_images.append({
                "page": page_num + 1,
                "bytes": img_bytes,
                "base64": base64.b64encode(img_bytes).decode('utf-8')
            })

    doc.close()

    combined_text = "\n".join(all_text) if all_text else ""
    return combined_text, page_images, None


def extract_images_from_pdf(file_bytes):
    """تحويل كل صفحات PDF إلى صور"""
    if not PYMUPDF_AVAILABLE:
        return []

    doc = fitz.open(stream=file_bytes, filetype="pdf")
    images = []
    for i in range(len(doc)):
        page = doc[i]
        mat = fitz.Matrix(2.0, 2.0)
        pix = page.get_pixmap(matrix=mat)
        img_bytes = pix.tobytes("jpeg")
        images.append({
            "page": i + 1,
            "bytes": img_bytes,
            "base64": base64.b64encode(compress_image(img_bytes)).decode('utf-8')
        })
    doc.close()
    return images


# ╔══════════════════════════════════════════════════════════════╗
# ║     القسم 3: الاستخراج بالذكاء الاصطناعي                    ║
# ╚══════════════════════════════════════════════════════════════╝

VISION_MODELS = [
    "llama-3.2-90b-vision-preview",
    "llama-3.2-11b-vision-preview",
]

TEXT_MODELS = [
    "llama-3.3-70b-versatile",
    "llama-3.1-70b-versatile",
    "mixtral-8x7b-32768",
    "gemma2-9b-it",
]


def build_extraction_prompt(level_name, subjects_cfg):
    subj_list = "\n".join([f"- {s}" for s in subjects_cfg.keys()])
    return f"""أنت محلل وثائق تربوية جزائرية متخصص. المستوى: {level_name}

استخرج كل الدروس الموجودة.

المواد المتوقعة (استخدم هذه الأسماء بالضبط):
{subj_list}

لكل درس:
1. "مادة": اسم المادة من القائمة
2. "موضوع": عنوان/موضوع الدرس  
3. "كفاءة": مؤشر الكفاءة (إن لم يوجد: "—")

ملاحظات:
- إذا وجدت نفس المادة بأسماء مختلفة، وحّدها حسب القائمة
- استخرج كل الدروس حتى لو كان هناك أكثر من درس لنفس المادة
- أعد JSON فقط بدون أي نص إضافي

[{{"مادة":"...","موضوع":"...","كفاءة":"..."}}]"""


def build_vision_prompt(level_name, subjects_cfg):
    subj_list = "\n".join([f"- {s}" for s in subjects_cfg.keys()])
    return f"""أنت تقرأ صورة مذكرة تعليمية جزائرية. المستوى: {level_name}

اقرأ كل النص العربي في الصورة واستخرج الدروس.

المواد المتوقعة:
{subj_list}

لكل درس استخرج:
1. "مادة": اسم المادة
2. "موضوع": عنوان الدرس
3. "كفاءة": مؤشر الكفاءة (أو "—")

أعد النتيجة كـ JSON فقط:
[{{"مادة":"...","موضوع":"...","كفاءة":"..."}}]"""


def parse_ai_response(raw):
    """تحليل رد AI لاستخراج JSON"""
    for attempt in [
        lambda: json.loads(raw),
        lambda: json.loads(re.search(r'```(?:json)?\s*([\s\S]*?)```', raw).group(1)),
        lambda: json.loads(re.search(r'\[[\s\S]*?\]', raw).group(0)),
    ]:
        try:
            result = attempt()
            if isinstance(result, list):
                return result
        except:
            pass
    return None


def ai_results_to_db(parsed_list):
    """تحويل نتائج AI إلى قاموس الدروس"""
    db = {}
    if not parsed_list:
        return db
    for item in parsed_list:
        if not isinstance(item, dict):
            continue
        s = item.get("مادة", "").strip()
        t = item.get("موضوع", "—").strip()
        k = item.get("كفاءة", "—").strip()
        if s and t:
            db.setdefault(s, []).append({"موضوع": t, "كفاءة": k})
    return db


def extract_with_text_ai(text, api_key, model, level_name, subjects_cfg):
    """استخراج من نص باستخدام نموذج نصي"""
    if not GROQ_AVAILABLE or not api_key:
        return None, None, "مفتاح API مطلوب"

    prompt = build_extraction_prompt(level_name, subjects_cfg)
    content = prompt + "\n\nالمحتوى:\n---\n" + text[:12000] + "\n---"

    try:
        client = Groq(api_key=api_key)
        comp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "محلل وثائق تربوية. أجب بـ JSON فقط."},
                {"role": "user", "content": content}
            ],
            temperature=0.1, max_tokens=4000,
        )
        raw = comp.choices[0].message.content
        parsed = parse_ai_response(raw)
        if not parsed:
            return None, raw, "فشل تحليل JSON"
        return ai_results_to_db(parsed), raw, None
    except Exception as e:
        return None, None, str(e)


def extract_with_vision_ai(images_b64, api_key, model, level_name, subjects_cfg, progress_callback=None):
    """استخراج من صور باستخدام نموذج بصري"""
    if not GROQ_AVAILABLE or not api_key:
        return None, None, "مفتاح API مطلوب"

    prompt = build_vision_prompt(level_name, subjects_cfg)
    all_results = []
    all_raw = []

    try:
        client = Groq(api_key=api_key)

        for i, img_b64 in enumerate(images_b64):
            if progress_callback:
                progress_callback(i, len(images_b64))

            messages = [{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt + f"\n\n(الصورة {i+1} من {len(images_b64)})"},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{img_b64}"
                        }
                    }
                ]
            }]

            comp = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.1,
                max_tokens=4000,
            )

            raw = comp.choices[0].message.content
            all_raw.append(f"--- صورة {i+1} ---\n{raw}")

            parsed = parse_ai_response(raw)
            if parsed:
                all_results.extend(parsed)

        combined_raw = "\n\n".join(all_raw)
        db = ai_results_to_db(all_results)
        return db, combined_raw, None

    except Exception as e:
        return None, None, str(e)


# ╔══════════════════════════════════════════════════════════════╗
# ║     القسم 4: معالج الملفات الموحد                            ║
# ╚══════════════════════════════════════════════════════════════╝

def process_file(file_bytes, filename, api_key, text_model, vision_model,
                 level_name, subjects_cfg, progress_bar=None, status_text=None):
    """
    المعالج الموحد — يتعامل مع أي صيغة ملف
    
    المسار:
    DOCX → نص → AI نصي
    PDF (نصي) → نص → AI نصي
    PDF (صور) → صور → AI بصري
    صورة → AI بصري مباشرة
    """
    ext = get_file_type(filename)
    results = {"db": None, "raw": None, "error": None,
               "method": "", "text": "", "images": []}

    # ═══ DOCX ═══
    if ext == "docx":
        if status_text:
            status_text.text("📄 جارٍ قراءة ملف Word...")
        text = extract_text_from_docx(file_bytes)
        results["text"] = text
        results["method"] = "📄 Word → 🧠 AI نصي"

        if status_text:
            status_text.text("🧠 الذكاء الاصطناعي يحلل النص...")
        db, raw, err = extract_with_text_ai(
            text, api_key, text_model, level_name, subjects_cfg
        )
        results["db"] = db
        results["raw"] = raw
        results["error"] = err

    # ═══ PDF ═══
    elif ext == "pdf":
        if not PYMUPDF_AVAILABLE:
            results["error"] = "مكتبة PyMuPDF غير مثبتة"
            return results

        if status_text:
            status_text.text("📕 جارٍ قراءة ملف PDF...")

        text, page_images, pdf_err = extract_text_from_pdf(file_bytes)

        if pdf_err:
            results["error"] = pdf_err
            return results

        # هل يوجد نص كافٍ؟
        if text and len(text) > 100:
            # PDF نصي
            results["text"] = text
            results["method"] = "📕 PDF نصي → 🧠 AI نصي"

            if status_text:
                status_text.text("🧠 الذكاء الاصطناعي يحلل النص...")
            db, raw, err = extract_with_text_ai(
                text, api_key, text_model, level_name, subjects_cfg
            )
            results["db"] = db
            results["raw"] = raw
            results["error"] = err

        elif page_images:
            # PDF مسحوب ضوئياً — إرسال الصور للـ AI البصري
            results["images"] = page_images
            results["method"] = f"📕 PDF صور ({len(page_images)} صفحة) → 👁️ AI بصري"

            if status_text:
                status_text.text(f"👁️ AI يقرأ {len(page_images)} صفحة...")

            images_b64 = [img["base64"] for img in page_images]

            def prog(i, total):
                if progress_bar:
                    progress_bar.progress((i + 1) / total)
                if status_text:
                    status_text.text(f"👁️ صفحة {i+1}/{total}...")

            db, raw, err = extract_with_vision_ai(
                images_b64, api_key, vision_model,
                level_name, subjects_cfg, prog
            )
            results["db"] = db
            results["raw"] = raw
            results["error"] = err

        else:
            # PDF فارغ تماماً — نحاول كصور
            all_images = extract_images_from_pdf(file_bytes)
            if all_images:
                results["images"] = all_images
                results["method"] = f"📕 PDF → صور ({len(all_images)} صفحة) → 👁️ AI بصري"
                images_b64 = [img["base64"] for img in all_images]

                db, raw, err = extract_with_vision_ai(
                    images_b64, api_key, vision_model,
                    level_name, subjects_cfg
                )
                results["db"] = db
                results["raw"] = raw
                results["error"] = err
            else:
                results["error"] = "ملف PDF فارغ"

    # ═══ صورة ═══
    elif ext in ("jpg", "jpeg", "png", "bmp", "tiff", "webp"):
        results["method"] = "🖼️ صورة → 👁️ AI بصري"

        if status_text:
            status_text.text("👁️ الذكاء الاصطناعي يقرأ الصورة...")

        img_b64 = image_to_base64(file_bytes)
        results["images"] = [{"page": 1, "bytes": file_bytes, "base64": img_b64}]

        db, raw, err = extract_with_vision_ai(
            [img_b64], api_key, vision_model,
            level_name, subjects_cfg
        )
        results["db"] = db
        results["raw"] = raw
        results["error"] = err

    else:
        results["error"] = f"صيغة غير مدعومة: {ext}"

    return results


# ╔══════════════════════════════════════════════════════════════╗
# ║     القسم 5: دوال مساعدة                                    ║
# ╚══════════════════════════════════════════════════════════════╝

WEEKDAYS = ["الأحد","الإثنين","الثلاثاء","الأربعاء","الخميس"]
HALF_DAYS = {"الثلاثاء","الخميس"}

def auto_schedule(subjects_cfg, routine):
    full = [d for d in WEEKDAYS if d not in HALF_DAYS]
    half = [d for d in WEEKDAYS if d in HALF_DAYS]
    sessions = []
    for s, i in subjects_cfg.items():
        sessions.extend([s] * i["الحصص"])
    sched = {}; idx = 0
    for day in WEEKDAYS:
        plan = []; is_full = day not in HALF_DAYS
        plan.append({"النشاط":routine[0] if routine else "الاستقبال","المدة":"15 د","الفترة":"صباحية"})
        for _ in range(5):
            if idx < len(sessions):
                plan.append({"النشاط":sessions[idx],"المدة":"45 د","الفترة":"صباحية"}); idx+=1
        plan.append({"النشاط":"تهيئة الخروج","المدة":"15 د","الفترة":"صباحية"})
        if is_full:
            plan.append({"النشاط":routine[0] if routine else "الاستقبال","المدة":"15 د","الفترة":"مسائية"})
            for _ in range(3):
                if idx < len(sessions):
                    plan.append({"النشاط":sessions[idx],"المدة":"45 د","الفترة":"مسائية"}); idx+=1
            plan.append({"النشاط":"نهاية الخروج","المدة":"15 د","الفترة":"مسائية"})
        sched[day] = plan
    return sched

def get_cfg():
    lv = st.session_state.get('selected_level','قسم التحضيري')
    if 'custom_configs' in st.session_state and lv in st.session_state.custom_configs:
        return st.session_state.custom_configs[lv]
    return LEVELS_CONFIG.get(lv, LEVELS_CONFIG['قسم التحضيري'])

def get_sched():
    c = get_cfg(); s = c.get("التوقيت",{})
    return s if s else auto_schedule(c["المواد"], c["الأنشطة_الروتينية"])

def get_subj(): return get_cfg().get("المواد",{})
def get_dom(): return get_cfg().get("المجالات",{})
def get_rtn(): return get_cfg().get("الأنشطة_الروتينية",[])
def dom_for(a):
    s = get_subj()
    return s[a]["المجال"] if a in s else "—"
def dom_color(d):
    dm = get_dom()
    return dm[d]["اللون"] if d in dm else "#666"
def dom_badge(d):
    c = dom_color(d)
    return f'<span style="display:inline-block;padding:2px 10px;border-radius:12px;font-size:.75rem;font-weight:600;background:{c}22;color:{c};border:1px solid {c}44;">{d}</span>'

def distribute(raw_db):
    subj = get_subj(); dist = {}; rep = {}
    for s, info in subj.items():
        req = info["الحصص"]; av = raw_db.get(s,[]); cnt = len(av)
        if cnt == 0:
            dist[s]=[]; rep[s]={"مطلوب":req,"متوفر":0,"حالة":"❌","توزيع":[]}; continue
        result = []; dd = []
        if cnt >= req:
            result = [l.copy() for l in av[:req]]; dd = [f"درس {i+1}" for i in range(req)]
        else:
            pp = req/cnt
            for i, les in enumerate(av):
                ss = round(i*pp); ee = round((i+1)*pp)
                for _ in range(ee-ss):
                    en = les.copy(); en["_n"]=len(result)+1; en["_t"]=req
                    result.append(en); dd.append(f"درس {i+1}")
        dist[s]=result; rep[s]={"مطلوب":req,"متوفر":cnt,"حالة":"✅" if result else "❌","توزيع":dd}
    return dist, rep


# ╔══════════════════════════════════════════════════════════════╗
# ║     القسم 6: القالب والحقن                                   ║
# ╚══════════════════════════════════════════════════════════════╝

def _rtl(p):
    pPr=p._p.get_or_add_pPr(); pPr.append(pPr.makeelement(qn('w:bidi'),{}))
def _cell(c,t,bold=False,size=10,color=None):
    c.text=""; p=c.paragraphs[0]; p.alignment=WD_ALIGN_PARAGRAPH.CENTER; _rtl(p)
    r=p.add_run(t); r.bold=bold; r.font.size=Pt(size); r.font.name="Sakkal Majalla"
    if color: r.font.color.rgb=color
    rPr=r._r.get_or_add_rPr()
    rPr.append(rPr.makeelement(qn('w:rFonts'),{qn('w:cs'):'Sakkal Majalla'}))
def _shade(row,hx):
    for c in row.cells:
        tc=c._tc.get_or_add_tcPr()
        tc.append(tc.makeelement(qn('w:shd'),{qn('w:fill'):hx,qn('w:val'):'clear'}))
def _ptable(doc,title,start,count):
    h=doc.add_paragraph(); h.alignment=WD_ALIGN_PARAGRAPH.CENTER; _rtl(h)
    r=h.add_run(title); r.bold=True; r.font.size=Pt(13); r.font.color.rgb=RGBColor(0,51,102)
    hdrs=['مؤشرات الكفاءة','عنوان الدرس','الميدان','النشاط','المدة']
    tbl=doc.add_table(rows=1+count,cols=5); tbl.style='Table Grid'; tbl.alignment=WD_TABLE_ALIGNMENT.CENTER
    ws=[Cm(5.5),Cm(5),Cm(3.5),Cm(3.5),Cm(2)]
    for row in tbl.rows:
        for i,w in enumerate(ws): row.cells[i].width=w
    hdr=tbl.rows[0]; _shade(hdr,"1F4E79")
    for i,t in enumerate(hdrs): _cell(hdr.cells[i],t,True,11,RGBColor(255,255,255))
    for j in range(count):
        n=start+j; dr=tbl.rows[1+j]
        if j%2==0: _shade(dr,"EDF2F9")
        for i,ph in enumerate([f'{{{{كفاءة_{n}}}}}',f'{{{{موضوع_{n}}}}}',f'{{{{ميدان_{n}}}}}',f'{{{{نشاط_{n}}}}}',f'{{{{مدة_{n}}}}}']):
            _cell(dr.cells[i],ph,size=9)

def create_tmpl(day=None):
    lv = st.session_state.get('selected_level','')
    sched = get_sched()
    if day and day in sched:
        plan=sched[day]; rtn=get_rtn()
        mt=sum(1 for s in plan if s['الفترة']=='صباحية')
        et=sum(1 for s in plan if s.get('الفترة')=='مسائية')
    else: mt=7; et=5
    doc=Document()
    for sec in doc.sections: sec._sectPr.append(sec._sectPr.makeelement(qn('w:bidi'),{}))
    for t,sz,b in [('الجمهورية الجزائرية الديمقراطية الشعبية',12,True),('وزارة التربية الوطنية',11,False)]:
        p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; _rtl(p)
        r=p.add_run(t); r.bold=b; r.font.size=Pt(sz)
    tp=doc.add_paragraph(); tp.alignment=WD_ALIGN_PARAGRAPH.CENTER; _rtl(tp)
    tr=tp.add_run(f'الكراس اليومي — {lv}'); tr.bold=True; tr.font.size=Pt(16); tr.font.color.rgb=RGBColor(0,51,102)
    info=doc.add_table(rows=1,cols=3); info.alignment=WD_TABLE_ALIGNMENT.CENTER
    _cell(info.rows[0].cells[2],'اليوم : {{اليوم}}',True,12)
    _cell(info.rows[0].cells[1],'التاريخ : {{التاريخ}}',size=11)
    _cell(info.rows[0].cells[0],'الأسبوع : {{الأسبوع}}',size=11)
    doc.add_paragraph(''); _ptable(doc,'☀ الفترة الصباحية',1,mt)
    if et>0: doc.add_paragraph(''); _ptable(doc,'🌙 الفترة المسائية',mt+1,et)
    doc.add_paragraph('')
    np2=doc.add_paragraph(); np2.alignment=WD_ALIGN_PARAGRAPH.RIGHT; _rtl(np2)
    np2.add_run('ملاحظات : '+'.'*80).font.size=Pt(10)
    buf=BytesIO(); doc.save(buf); return buf.getvalue()

def _sr(para,old,new):
    if old not in para.text: return
    for run in para.runs:
        if old in run.text: run.text=run.text.replace(old,new); return
    f=para.text.replace(old,new)
    if para.runs:
        for run in para.runs: run.text=""
        para.runs[0].text=f

def build_planner(day,tmpl_bytes,dist_db,wn="",ds=""):
    sched=get_sched(); plan=sched.get(day,[])
    if not plan: return None,[],[]
    rtn=get_rtn(); doc=Document(BytesIO(tmpl_bytes))
    reps={"{{اليوم}}":day,"{{التاريخ}}":ds,"{{الأسبوع}}":wn}
    si=[]; warns=[]
    for i,session in enumerate(plan,1):
        act=session["النشاط"]; dur=session["المدة"]; per=session.get("الفترة","")
        domain=dom_for(act)
        reps[f"{{{{مدة_{i}}}}}"]=dur; reps[f"{{{{نشاط_{i}}}}}"]=act
        info={"رقم":i,"النشاط":act,"المدة":dur,"الفترة":per,"المجال":domain,"نوع":"روتيني","الموضوع":"—","الكفاءة":"—"}
        if act in rtn:
            reps[f"{{{{موضوع_{i}}}}}"]=reps[f"{{{{كفاءة_{i}}}}}"]=reps[f"{{{{ميدان_{i}}}}}"]="—"
        elif act in dist_db and dist_db[act]:
            les=dist_db[act].pop(0); t=les.get('موضوع','—'); k=les.get('كفاءة','—')
            reps[f"{{{{موضوع_{i}}}}}"]=t; reps[f"{{{{كفاءة_{i}}}}}"]=k; reps[f"{{{{ميدان_{i}}}}}"]=domain
            info.update({"نوع":"تعليمي","الموضوع":t,"الكفاءة":k})
        else:
            reps[f"{{{{موضوع_{i}}}}}"]="⚠ لا توجد مذكرة"; reps[f"{{{{كفاءة_{i}}}}}"]="⚠ لا توجد مذكرة"
            reps[f"{{{{ميدان_{i}}}}}"]=domain; info["نوع"]="ناقص"; warns.append(act)
        si.append(info)
    for tbl in doc.tables:
        for row in tbl.rows:
            for cell in row.cells:
                for para in cell.paragraphs:
                    for k,v in reps.items():
                        if k in para.text: _sr(para,k,str(v))
    for para in doc.paragraphs:
        for k,v in reps.items():
            if k in para.text: _sr(para,k,str(v))
    buf=BytesIO(); doc.save(buf)
    return buf.getvalue(), si, warns


# ╔══════════════════════════════════════════════════════════════╗
# ║                  القسم 7: واجهة Streamlit                   ║
# ╚══════════════════════════════════════════════════════════════╝

st.set_page_config(page_title="الكراس اليومي 🎓",page_icon="🎓",layout="wide",initial_sidebar_state="expanded")

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
.format-card{border:2px solid #ddd;border-radius:10px;padding:.8rem;text-align:center;margin:.3rem}
.format-active{border-color:#1F4E79;background:#E3F2FD}
</style>""", unsafe_allow_html=True)

for k in ['lessons_db','generated_files','dist_report','ai_raw','file_text',
          'selected_level','custom_configs','proc_images','proc_method']:
    if k not in st.session_state:
        if k=='generated_files': st.session_state[k]={}
        elif k=='selected_level': st.session_state[k]='قسم التحضيري'
        elif k=='custom_configs': st.session_state[k]=copy.deepcopy(LEVELS_CONFIG)
        elif k=='proc_images': st.session_state[k]=[]
        else: st.session_state[k]=None


# ═══════════════ الشريط الجانبي ═══════════════

with st.sidebar:
    st.markdown("## 🎓 المستوى")
    lvls = list(LEVELS_CONFIG.keys())
    sel = st.selectbox("المستوى الدراسي", lvls,
                        index=lvls.index(st.session_state.selected_level))
    if sel != st.session_state.selected_level:
        st.session_state.selected_level = sel
        st.session_state.lessons_db = None
        st.session_state.generated_files = {}
        st.rerun()

    cfg = get_cfg()
    ts = sum(i["الحصص"] for i in cfg["المواد"].values())
    st.info(f"📘 {len(cfg['المواد'])} مادة | 📖 {ts} حصة/أسبوع")

    st.markdown("---")
    week_num = st.text_input("📅 الأسبوع", placeholder="10")
    date_str = st.text_input("📆 التاريخ", placeholder="2024/12/01")

    st.markdown("---")
    st.markdown("### 🧠 Groq AI")
    groq_key = st.text_input("🔑 API Key", type="password",
                              help="console.groq.com")
    txt_model = st.selectbox("📝 نموذج نصي", TEXT_MODELS)
    vis_model = st.selectbox("👁️ نموذج بصري", VISION_MODELS)

    st.markdown("---")
    st.markdown("### 📤 رفع الملف")
    st.markdown(f"""
    الصيغ المدعومة:
    - 📄 Word (.docx)
    - 📕 PDF (.pdf)
    - 🖼️ صور (.jpg .png .bmp)
    """)

    uploaded = st.file_uploader(
        "اختر ملفاً",
        type=list(SUPPORTED_FORMATS.keys()),
        help="Word أو PDF أو صورة"
    )

    st.caption("🎓 v7.0 — Word + PDF + صور + AI")


# ═══════════════ معالجة الرفع ═══════════════

if uploaded:
    file_bytes = uploaded.read()
    if st.session_state.get('_last') != uploaded.name:
        st.session_state._fb = file_bytes
        st.session_state._last = uploaded.name
        st.session_state.lessons_db = None
        st.session_state.generated_files = {}
        st.session_state.proc_images = []
        st.session_state.proc_method = None
        st.session_state.ai_raw = None

        ext = get_file_type(uploaded.name)
        fmt = SUPPORTED_FORMATS.get(ext, "❓")
        st.toast(f"📁 تم رفع: {uploaded.name} ({fmt})", icon="📁")


# ═══════════════ العنوان ═══════════════

lv = st.session_state.selected_level
st.markdown(f"""
<h1 style="background:linear-gradient(135deg,#1F4E79,#2E75B6);
-webkit-background-clip:text;-webkit-text-fill-color:transparent;
font-size:2.2rem;">🎓 الكراس اليومي — {lv}</h1>
<p style="text-align:center;color:#888;">
📄 Word  •  📕 PDF  •  🖼️ صور  •  🧠 ذكاء اصطناعي
</p>
""", unsafe_allow_html=True)


# ═══════════════ التبويبات ═══════════════

tab1, tab2, tab3, tab4 = st.tabs([
    "🧠 استخراج الدروس", "📅 توليد ومعاينة",
    "⚙️ إعداد المستوى", "🗺️ المجالات والتوقيت"
])


# ──── تبويب 1: الاستخراج ────

with tab1:
    if not uploaded:
        st.info("👆 ارفع ملف المذكرات من الشريط الجانبي")

        st.markdown("### 📁 الصيغ المدعومة")
        fc = st.columns(3)
        with fc[0]:
            st.markdown("""
            <div class="format-card">
                <h3>📄 Word</h3>
                <p>.docx</p>
                <small>يُقرأ النص مباشرة<br>ثم يُرسل لـ AI نصي</small>
            </div>""", unsafe_allow_html=True)
        with fc[1]:
            st.markdown("""
            <div class="format-card">
                <h3>📕 PDF</h3>
                <p>.pdf</p>
                <small>نصي → AI نصي<br>صور → AI بصري</small>
            </div>""", unsafe_allow_html=True)
        with fc[2]:
            st.markdown("""
            <div class="format-card">
                <h3>🖼️ صورة</h3>
                <p>.jpg .png .bmp</p>
                <small>تُرسل مباشرة<br>لـ AI بصري (OCR)</small>
            </div>""", unsafe_allow_html=True)

    else:
        ext = get_file_type(uploaded.name)
        fmt = SUPPORTED_FORMATS.get(ext, "❓")

        st.markdown(f"""
        <div class="format-card format-active">
            <strong>{fmt} {uploaded.name}</strong>
            <small>({len(st.session_state._fb) / 1024:.0f} KB)</small>
        </div>""", unsafe_allow_html=True)

        # معاينة الصورة/PDF
        if ext in ('jpg','jpeg','png','bmp','webp'):
            st.image(st.session_state._fb, caption="الصورة المرفوعة", use_container_width=True)
        elif ext == 'pdf' and PYMUPDF_AVAILABLE:
            with st.expander("👁️ معاينة صفحات PDF"):
                doc = fitz.open(stream=st.session_state._fb, filetype="pdf")
                cols = st.columns(min(len(doc), 3))
                for i in range(min(len(doc), 6)):
                    pix = doc[i].get_pixmap(matrix=fitz.Matrix(1,1))
                    with cols[i % 3]:
                        st.image(pix.tobytes("jpeg"), caption=f"صفحة {i+1}")
                doc.close()

        # زر الاستخراج
        can_extract = groq_key and GROQ_AVAILABLE
        if not can_extract:
            st.warning("🔑 أدخل مفتاح Groq API في الشريط الجانبي")

        if st.button("🧠 استخراج الدروس تلقائياً", type="primary",
                     use_container_width=True, disabled=not can_extract):

            bar = st.progress(0)
            status = st.empty()

            results = process_file(
                file_bytes=st.session_state._fb,
                filename=uploaded.name,
                api_key=groq_key,
                text_model=txt_model,
                vision_model=vis_model,
                level_name=lv,
                subjects_cfg=get_subj(),
                progress_bar=bar,
                status_text=status,
            )

            bar.progress(1.0)
            status.empty()

            st.session_state.ai_raw = results["raw"]
            st.session_state.proc_method = results["method"]
            st.session_state.proc_images = results.get("images", [])

            if results["error"]:
                st.error(f"❌ {results['error']}")
            elif results["db"]:
                dist, rep = distribute(results["db"])
                st.session_state.lessons_db = dist
                st.session_state.dist_report = rep
                st.session_state.generated_files = {}
                total = sum(len(v) for v in results["db"].values())
                st.success(f"✅ تم استخراج {total} درس!")
                st.rerun()
            else:
                st.error("❌ لم يتم العثور على دروس")

        # عرض النتائج
        db = st.session_state.lessons_db
        if db:
            method = st.session_state.proc_method or ""
            st.markdown(f"---\n**المسار:** {method}")

            total = sum(len(v) for v in db.values())
            scfg = get_subj()
            matched = set(k for k,v in db.items() if v) & set(scfg.keys())
            missing = set(scfg.keys()) - set(k for k,v in db.items() if v)

            c1,c2,c3 = st.columns(3)
            for col,title,num,cls in [(c1,"📖 حصص",total,"card-green"),
                                       (c2,"✅ مغطاة",len(matched),"card-purple"),
                                       (c3,"⚠ ناقصة",len(missing),"card-amber")]:
                with col:
                    st.markdown(f'<div class="card {cls}"><h4>{title}</h4><div class="num">{num}</div></div>',
                                unsafe_allow_html=True)

            if missing: st.warning(f"⚠️ ناقصة: **{' ، '.join(missing)}**")

            for subj in sorted(db.keys()):
                lessons = db[subj]
                if not lessons: continue
                d = dom_for(subj)
                with st.expander(f"✅ {subj} — {len(lessons)} حصة — {d}"):
                    for j,les in enumerate(lessons,1):
                        st.markdown(f"**{j}.** 📝 {les.get('موضوع','—')}\n🎯 {les.get('كفاءة','—')}")
                        if j < len(lessons): st.divider()

        # رد AI
        if st.session_state.ai_raw:
            with st.expander("🧠 رد AI الخام"):
                st.code(st.session_state.ai_raw, language="json")


# ──── تبويب 2: توليد ────

with tab2:
    db = st.session_state.lessons_db
    if not db or not any(db.values()):
        st.info("🧠 استخرج الدروس أولاً")
    else:
        sched = get_sched(); days = list(sched.keys())
        st.markdown("### 📅 اختر الأيام")
        cols = st.columns(len(days)); sel_days = []
        for i,d in enumerate(days):
            rtn = get_rtn()
            tc = sum(1 for s in sched[d] if s["النشاط"] not in rtn)
            with cols[i]:
                if st.checkbox(f"{d} ({tc})", key=f"d_{d}"): sel_days.append(d)
        if st.checkbox("✅ الكل"): sel_days = days

        if sel_days and st.button(f"🚀 توليد {len(sel_days)} كراس",
                                   type="primary", use_container_width=True):
            wdb = copy.deepcopy(db); gen = {}; bar = st.progress(0)
            for idx,d in enumerate(sel_days):
                bar.progress(idx/len(sel_days))
                tmpl = create_tmpl(d)
                result,info,warns = build_planner(d,tmpl,wdb,week_num,date_str)
                if result: gen[d] = {'bytes':result,'sessions':info,'warnings':warns}
            bar.progress(1.0)
            st.session_state.generated_files = gen
            st.markdown(f'<div class="ok-box"><h3>✅ {len(gen)} كراس!</h3></div>',
                        unsafe_allow_html=True)

        gf = st.session_state.generated_files
        if gf:
            st.markdown("### 📥 التحميل")
            dlc = st.columns(min(len(gf),5))
            for i,(d,data) in enumerate(gf.items()):
                with dlc[i%5]:
                    st.download_button(f"📄 {d}", data=data['bytes'], file_name=f"كراس_{d}.docx",
                                       mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                       use_container_width=True, key=f"dl_{d}")

            st.markdown("---\n### 👁️ معاينة")
            dp = st.selectbox("اليوم", list(gf.keys()))
            if dp:
                for s in gf[dp]['sessions']:
                    typ=s['نوع']
                    css={'روتيني':'slot-routine','تعليمي':'slot-teach','ناقص':'slot-warn'}.get(typ,'slot-routine')
                    ic={'روتيني':'⏰','تعليمي':'📖','ناقص':'⚠️'}.get(typ,'⏰')
                    dm=s.get('المجال','—'); bdg=dom_badge(dm) if dm!='—' else ''
                    ext=''
                    if typ=='تعليمي': ext=f"<br><small>📝 {s['الموضوع']}</small><br><small>🎯 {s['الكفاءة']}</small>"
                    st.markdown(f'<div class="slot {css}"><span style="font-size:1.3rem">{ic}</span>'
                                f'<div style="flex:1"><strong>{s["النشاط"]}</strong> '
                                f'<span style="color:#888">({s["المدة"]})</span>{bdg}{ext}</div></div>',
                                unsafe_allow_html=True)


# ──── تبويب 3: إعداد المستوى ────

with tab3:
    st.markdown(f"### ⚙️ تخصيص مواد {lv}")
    cfg = get_cfg(); subj = cfg["المواد"]; doms = cfg["المجالات"]
    sd = [{"المادة":n,"المجال":i["المجال"],"الحصص":i["الحصص"]} for n,i in subj.items()]

    edited = st.data_editor(sd, num_rows="dynamic",
        column_config={
            "المادة":st.column_config.TextColumn("المادة",width="medium"),
            "المجال":st.column_config.SelectboxColumn("المجال",options=list(doms.keys()),width="medium"),
            "الحصص":st.column_config.NumberColumn("الحصص",min_value=1,max_value=10,width="small"),
        }, use_container_width=True, key="subj_ed")

    c1,c2 = st.columns(2)
    with c1:
        if st.button("💾 حفظ", use_container_width=True, type="primary"):
            ns = {}
            for r in edited:
                if r.get("المادة") and r.get("المجال"):
                    ns[r["المادة"]]={"المجال":r["المجال"],"الحصص":r.get("الحصص",1)}
            if ns:
                st.session_state.custom_configs[lv]["المواد"]=ns
                st.success(f"✅ {len(ns)} مادة!")
    with c2:
        if st.button("🔄 توليد توقيت تلقائي", use_container_width=True):
            c2 = get_cfg()
            ns = auto_schedule(c2["المواد"],c2["الأنشطة_الروتينية"])
            st.session_state.custom_configs[lv]["التوقيت"]=ns
            st.success("✅ تم!")

    tot = sum(r.get("الحصص",0) for r in edited if r.get("المادة"))
    st.info(f"📊 المجموع: **{tot}** حصة (المتاح: 34)")


# ──── تبويب 4: المجالات والتوقيت ────

with tab4:
    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown(f"### 🗺️ المجالات — {lv}")
        scfg = get_subj(); dms = {}
        for s,i in scfg.items(): dms.setdefault(i["المجال"],[]).append(s)
        for dm,subs in dms.items():
            cl = dom_color(dm)
            th = sum(scfg[s]["الحصص"] for s in subs if s in scfg)
            st.markdown(f'<div style="border:2px solid {cl};border-radius:12px;padding:.8rem;margin:.5rem 0;">'
                        f'<h4 style="color:{cl};text-align:center;">{dm} ({th} ح)</h4>', unsafe_allow_html=True)
            for s in subs:
                cnt = scfg.get(s,{}).get("الحصص",0)
                st.markdown(f'<div style="display:flex;align-items:center;gap:8px;margin:4px 0;direction:rtl;">'
                            f'<span style="min-width:130px;font-size:.9rem">{s}</span>'
                            f'<div style="background:{cl}44;border-radius:4px;height:18px;width:{cnt*14}px;"></div>'
                            f'<span style="color:{cl};font-weight:700;">{cnt}</span></div>',
                            unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

    with col_b:
        st.markdown(f"### 📊 التوقيت — {lv}")
        sched = get_sched()
        if sched:
            vd = st.selectbox("اليوم", list(sched.keys()), key="sv")
            if vd:
                plan = sched[vd]; rtn = get_rtn()
                for per_name, per_val in [("☀️ صباح","صباحية"),("🌙 مساء","مسائية")]:
                    sl = [s for s in plan if s.get("الفترة")==per_val]
                    if not sl: continue
                    st.markdown(f"**{per_name}**")
                    rows = [{"#":j,"النشاط":s['النشاط'],"المدة":s['المدة'],
                             "المجال":dom_for(s['النشاط']) if s['النشاط'] not in rtn else "—"}
                            for j,s in enumerate(sl,1)]
                    st.dataframe(rows, use_container_width=True, hide_index=True)
        else:
            st.warning("اضغط 'توليد توقيت تلقائي' في تبويب الإعداد")
