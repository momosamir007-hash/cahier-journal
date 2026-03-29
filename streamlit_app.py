# -*- coding: utf-8 -*-
"""🎓 الكراس اليومي v9.1 — استخراج مُحسَّن + Groq + HF"""

import streamlit as st
import re
import copy
import json
import base64
import requests
from io import BytesIO
from PIL import Image

try:
    from docx import Document
    from docx.shared import Pt, Cm, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.enum.table import WD_TABLE_ALIGNMENT
    from docx.oxml.ns import qn
    DOCX_OK = True
except Exception:
    DOCX_OK = False

try:
    import fitz
    PDF_OK = True
except Exception:
    PDF_OK = False

# ╔══════════════════════════════════════════════════════╗
# ║ محركات AI عبر API                                    ║
# ╚══════════════════════════════════════════════════════╝

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_TEXT_MODELS = ["llama-3.3-70b-versatile", "mixtral-8x7b-32768", "gemma2-9b-it"]
GROQ_VISION_MODELS = ["llama-3.2-90b-vision-preview", "llama-3.2-11b-vision-preview"]

HF_MODELS = ["mistralai/Mistral-7B-Instruct-v0.3", "meta-llama/Meta-Llama-3-8B-Instruct", "google/gemma-2-2b-it"]


def groq_text_call(api_key, model, system_msg, user_msg):
    try:
        r = requests.post(GROQ_URL,
                          headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                          json={"model": model, "messages": [
                              {"role": "system", "content": system_msg},
                              {"role": "user", "content": user_msg}
                          ], "temperature": 0.1, "max_tokens": 4096},
                          timeout=180)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"], None
    except Exception as e:
        msg = e.response.text[:300] if hasattr(e, 'response') and e.response else str(e)[:300]
        return None, f"Groq: {msg}"


def groq_vision_call(api_key, model, prompt, image_b64):
    try:
        r = requests.post(GROQ_URL,
                          headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                          json={"model": model, "messages": [{"role": "user", "content": [
                              {"type": "text", "text": prompt},
                              {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}}
                          ]}], "temperature": 0.1, "max_tokens": 4096},
                          timeout=180)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"], None
    except Exception as e:
        msg = e.response.text[:300] if hasattr(e, 'response') and e.response else str(e)[:300]
        return None, f"Groq Vision: {msg}"


def hf_text_call(token, model, prompt):
    url = f"https://api-inference.huggingface.co/models/{model}"
    try:
        r = requests.post(url,
                          headers={"Authorization": f"Bearer {token}"},
                          json={"inputs": prompt, "parameters": {"max_new_tokens": 3000, "temperature": 0.1,
                                                                 "return_full_text": False}},
                          timeout=120)
        r.raise_for_status()
        result = r.json()
        if isinstance(result, list) and result:
            return result[0].get("generated_text", ""), None
        return str(result), None
    except Exception as e:
        msg = ""
        if hasattr(e, 'response') and e.response:
            body = e.response.text[:300]
            if "loading" in body.lower():
                return None, "⏳ النموذج يتم تحميله... أعد المحاولة بعد 30 ثانية"
            msg = body
        else:
            msg = str(e)[:300]
        return None, f"HuggingFace: {msg}"


# ╔══════════════════════════════════════════════════════╗
# ║ قراءة الملفات                                        ║
# ╚══════════════════════════════════════════════════════╝

def compress_image(data, max_size=1200, quality=80):
    img = Image.open(BytesIO(data))
    if img.mode == 'RGBA':
        img = img.convert('RGB')
    w, h = img.size
    if max(w, h) > max_size:
        ratio = max_size / max(w, h)
        img = img.resize((int(w * ratio), int(h * ratio)), Image.LANCZOS)
    buf = BytesIO()
    img.save(buf, format='JPEG', quality=quality)
    return buf.getvalue()


def to_base64(data):
    return base64.b64encode(compress_image(data)).decode()


def read_docx_text(file_bytes):
    if not DOCX_OK:
        return ""
    doc = Document(BytesIO(file_bytes))
    lines = []
    for p in doc.paragraphs:
        t = p.text.strip()
        if t:
            lines.append(t)
    for tbl in doc.tables:
        for row in tbl.rows:
            cells = [c.text.strip() for c in row.cells if c.text.strip()]
            if cells:
                lines.append(" | ".join(cells))
    return "\n".join(lines)


def read_pdf_text(file_bytes):
    if not PDF_OK:
        return ""
    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        texts = []
        for page in doc:
            t = page.get_text().strip()
            if t and len(t) > 20:
                texts.append(t)
        doc.close()
        return "\n".join(texts)
    except Exception:
        return ""


def pdf_to_images(file_bytes):
    if not PDF_OK:
        return []
    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        images = []
        for i, page in enumerate(doc):
            mat = fitz.Matrix(2.0, 2.0)
            pix = page.get_pixmap(matrix=mat)
            img_bytes = pix.tobytes("jpeg")
            images.append({"page": i + 1, "bytes": img_bytes, "b64": to_base64(img_bytes)})
        doc.close()
        return images
    except Exception:
        return []


# ╔══════════════════════════════════════════════════════╗
# ║ الاستخراج الذكي — Prompt مُحسَّن                    ║
# ╚══════════════════════════════════════════════════════╝

def build_extraction_prompt(level_name, subjects_dict):
    """بروومبت مُحسَّن يجبر AI على قراءة المذكرات التفصيلية"""
    subjects_list = "\n".join([f"- {s}" for s in subjects_dict.keys()])
    return f"""أنت مفتش تربوي ومحلل وثائق جزائرية دقيق جداً. المستوى: {level_name}

مهمتك استخراج *جميع* الدروس من الملف.

⛔ تحذير هام جداً:
- لا تعتمد فقط على الجداول الإجمالية أو التوزيع الأسبوعي في بداية الملف!
- يجب عليك قراءة "المذكرات التفصيلية" (البطاقات الفنية) الموجودة في باقي الصفحات.
- المذكرات التفصيلية تحتوي على: النشاط/المادة، الموضوع، مؤشر الكفاءة، سير الحصة.
- ابحث عن كلمات مثل: النشاط، المادة، الموضوع، الوحدة، مؤشر الكفاءة، الكفاءة المستهدفة.

المواد المتوقعة (استخدم هذه الأسماء بالضبط):
{subjects_list}

لكل درس تجده في المذكرات التفصيلية، استخرج:
1. "مادة": اسم المادة بالضبط من القائمة أعلاه (وحّد الأسماء المختلفة)
2. "موضوع": عنوان الدرس الحقيقي (ليس اسم المادة!)
3. "كفاءة": مؤشر الكفاءة أو الكفاءة المستهدفة (إن لم يوجد: "—")

شروط صارمة:
- إذا وجدت مادة مكررة بعدة دروس، استخرج كل درس على حدة
- تجاهل الصفوف الفارغة من الجداول الإجمالية
- إذا كان الموضوع فارغاً في الجدول الأول لكنه موجود في المذكرة التفصيلية، استخرجه من المذكرة
- لا تترك أي مادة بدون موضوع إذا كان موجوداً في النص
- أعد JSON Array فقط بدون أي مقدمات أو شرح

[{{"مادة":"...","موضوع":"...","كفاءة":"..."}}]"""


def parse_ai_json(raw_text):
    if not raw_text:
        return None
    for parser in [
        lambda: json.loads(raw_text),
        lambda: json.loads(re.search(r'```(?:json)?\s*([\s\S]*?)```', raw_text).group(1)),
        lambda: json.loads(re.search(r'\[[\s\S]*?\]', raw_text).group(0)),
    ]:
        try:
            result = parser()
            if isinstance(result, list):
                return result
        except Exception:
            pass
    return None


def ai_results_to_db(parsed_list):
    """تحويل نتائج AI إلى قاموس مع تجاهل النتائج الفارغة"""
    db = {}
    if not parsed_list:
        return db
    for item in parsed_list:
        if not isinstance(item, dict):
            continue
        subject = item.get("مادة", "").strip()
        topic = item.get("موضوع", "").strip()
        indicator = item.get("كفاءة", "").strip()

        # تنظيف علامات الفراغ
        empty_markers = ["", "-", "—", "–", "لا يوجد", "غير محدد", "...", "None", "null"]
        if topic in empty_markers:
            topic = "—"
        if indicator in empty_markers:
            indicator = "—"

        # تجاهل إذا الموضوع هو نفسه اسم المادة (خطأ شائع)
        if topic == subject:
            topic = "—"

        if subject:
            if subject not in db:
                db[subject] = []
            is_empty = (topic == "—" and indicator == "—")
            if not is_empty:  # درس حقيقي — نضيفه
                db[subject].append({"موضوع": topic, "كفاءة": indicator})
            elif len(db[subject]) == 0:  # نحتفظ به مؤقتاً إذا لم نجد شيئاً أفضل
                db[subject].append({"موضوع": topic, "كفاءة": indicator})

    # تنظيف نهائي: إزالة الفارغة إذا وُجدت دروس حقيقية
    for subj in db:
        valid = [l for l in db[subj] if l["موضوع"] != "—" or l["كفاءة"] != "—"]
        if valid:
            db[subj] = valid
    return db


# ╔══════════════════════════════════════════════════════╗
# ║ دوال الاستخراج حسب نوع الملف                         ║
# ╚══════════════════════════════════════════════════════╝

# حدود النص حسب المحرك
GROQ_TEXT_LIMIT = 25000  # Groq يدعم سياق طويل
HF_TEXT_LIMIT = 15000    # HF أقل


def extract_from_text_groq(text, api_key, model, level, subjects):
    prompt = build_extraction_prompt(level, subjects)
    full = prompt + "\n\nالمحتوى الكامل للمذكرات:\n---\n" + text[:GROQ_TEXT_LIMIT] + "\n---"
    raw, err = groq_text_call(api_key, model, "أنت محلل وثائق تربوية خبير. أجب بـ JSON فقط.", full)
    if err:
        return None, raw, err
    parsed = parse_ai_json(raw)
    if not parsed:
        return None, raw, "فشل تحليل رد AI — تأكد أن الملف يحتوي على مذكرات تفصيلية"
    return ai_results_to_db(parsed), raw, None


def extract_from_text_hf(text, token, model, level, subjects):
    prompt = build_extraction_prompt(level, subjects)
    full = prompt + "\n\nالمحتوى:\n---\n" + text[:HF_TEXT_LIMIT] + "\n---"
    raw, err = hf_text_call(token, model, full)
    if err:
        return None, raw, err
    parsed = parse_ai_json(raw)
    if not parsed:
        return None, raw, "فشل تحليل رد AI"
    return ai_results_to_db(parsed), raw, None


def extract_from_images_groq(images_b64, api_key, model, level, subjects, progress_cb=None):
    prompt = build_extraction_prompt(level, subjects)
    prompt += "\n\nاقرأ كل النص العربي من الصورة واستخرج الدروس من المذكرات التفصيلية."
    all_results = []
    all_raws = []
    for i, b64 in enumerate(images_b64):
        if progress_cb:
            progress_cb(i, len(images_b64))
        raw, err = groq_vision_call(api_key, model, prompt + f"\n(الصفحة {i+1} من {len(images_b64)})", b64)
        if err:
            all_raws.append(f"--- صفحة {i+1}: خطأ ---\n{err}")
            continue
        all_raws.append(f"--- صفحة {i+1} ---\n{raw}")
        parsed = parse_ai_json(raw)
        if parsed:
            all_results.extend(parsed)
    combined = "\n\n".join(all_raws)
    if not all_results:
        return None, combined, "لم يتم استخراج أي درس من الصور"
    return ai_results_to_db(all_results), combined, None


def smart_process_file(file_bytes, filename, groq_key, hf_key, groq_tmodel, groq_vmodel, hf_model, level, subjects,
                       progress_bar=None, status_text=None):
    ext = filename.lower().rsplit('.', 1)[-1] if '.' in filename else ''
    result = {"db": None, "raw": None, "err": None, "method": ""}

    has_groq = bool(groq_key)
    has_hf = bool(hf_key)

    if not has_groq and not has_hf:
        result["err"] = "🔑 أدخل مفتاح API واحد على الأقل (Groq أو HuggingFace)"
        return result

    if ext == "docx":
        if status_text:
            status_text.text("📄 قراءة Word...")
        text = read_docx_text(file_bytes)
        if not text:
            result["err"] = "ملف Word فارغ"
            return result
        if status_text:
            status_text.text(f"📄 تم قراءة {len(text)} حرف")
        if has_groq:
            result["method"] = "📄 Word → 🟢 Groq"
            if status_text:
                status_text.text("🟢 Groq يحلل المذكرات...")
            db, raw, err = extract_from_text_groq(text, groq_key, groq_tmodel, level, subjects)
        else:
            result["method"] = "📄 Word → 🟡 HuggingFace"
            if status_text:
                status_text.text("🟡 HuggingFace يحلل...")
            db, raw, err = extract_from_text_hf(text, hf_key, hf_model, level, subjects)
        result["db"] = db
        result["raw"] = raw
        result["err"] = err

    elif ext == "pdf":
        if status_text:
            status_text.text("📕 قراءة PDF...")
        text = read_pdf_text(file_bytes)
        if text and len(text) > 100:
            if status_text:
                status_text.text(f"📕 PDF نصي — {len(text)} حرف")
            if has_groq:
                result["method"] = "📕 PDF نصي → 🟢 Groq"
                if status_text:
                    status_text.text("🟢 Groq يحلل المذكرات...")
                db, raw, err = extract_from_text_groq(text, groq_key, groq_tmodel, level, subjects)
            else:
                result["method"] = "📕 PDF نصي → 🟡 HuggingFace"
                if status_text:
                    status_text.text("🟡 HuggingFace يحلل...")
                db, raw, err = extract_from_text_hf(text, hf_key, hf_model, level, subjects)
            result["db"] = db
            result["raw"] = raw
            result["err"] = err
        else:  # PDF مسحوب ضوئياً
            if not has_groq:
                result["err"] = ("📕 هذا PDF مسحوب ضوئياً (صور).\n\n"
                                 "الحلول:\n"
                                 "1. أدخل مفتاح Groq API (يدعم قراءة الصور)\n"
                                 "2. أو صوّر الصفحات بالهاتف 📱 وارفعها كصور")
                return result
            if not PDF_OK:
                result["err"] = "مكتبة pymupdf مطلوبة لتحويل PDF"
                return result
            if status_text:
                status_text.text("📸 تحويل PDF إلى صور...")
            images = pdf_to_images(file_bytes)
            if not images:
                result["err"] = "فشل تحويل PDF"
                return result
            result["method"] = f"📕 PDF ({len(images)} صفحة) → 📸 → 👁️ Groq Vision"
            if status_text:
                status_text.text(f"👁️ قراءة {len(images)} صفحة بصرياً...")

            def on_progress(i, total):
                if progress_bar:
                    progress_bar.progress((i + 1) / total)
                if status_text:
                    status_text.text(f"👁️ صفحة {i+1}/{total}...")

            db, raw, err = extract_from_images_groq(
                [img["b64"] for img in images],
                groq_key, groq_vmodel, level, subjects, on_progress)
            result["db"] = db
            result["raw"] = raw
            result["err"] = err

    elif ext in ("jpg", "jpeg", "png", "bmp", "webp", "tiff"):
        if not has_groq:
            result["err"] = "🖼️ قراءة الصور تحتاج مفتاح Groq (يدعم Vision)"
            return result
        result["method"] = "🖼️ صورة → 👁️ Groq Vision"
        if status_text:
            status_text.text("👁️ قراءة الصورة...")
        db, raw, err = extract_from_images_groq(
            [to_base64(file_bytes)],
            groq_key, groq_vmodel, level, subjects)
        result["db"] = db
        result["raw"] = raw
        result["err"] = err

    else:
        result["err"] = f"صيغة غير مدعومة: .{ext}"

    return result


# ╔══════════════════════════════════════════════════════╗
# ║ المستويات الدراسية                                   ║
# ╚══════════════════════════════════════════════════════╝

LEVELS = {
    "قسم التحضيري": {
        "رت": ["الاستقبال", "الاستراحة", "تهيئة الخروج", "نهاية الخروج"],
        "مج": {"المجال اللغوي": "#1565C0", "المجال الرياضي": "#C62828", "المجال العلمي": "#2E7D32",
               "المجال الاجتماعي": "#F57F17", "المجال الفني": "#6A1B9A", "المجال البدني والإيقاعي": "#00838F"},
        "مو": {
            "تعبير شفوي": {"ج": "المجال اللغوي", "ح": 3},
            "مبادئ القراءة": {"ج": "المجال اللغوي", "ح": 4},
            "تخطيط": {"ج": "المجال اللغوي", "ح": 2},
            "رياضيات": {"ج": "المجال الرياضي", "ح": 5},
            "ت علمية وتكنولوجية": {"ج": "المجال العلمي", "ح": 4},
            "ت إسلامية": {"ج": "المجال الاجتماعي", "ح": 2},
            "ت مدنية": {"ج": "المجال الاجتماعي", "ح": 2},
            "تربية تشكيلية": {"ج": "المجال الفني", "ح": 2},
            "موسيقى وإنشاد": {"ج": "المجال الفني", "ح": 2},
            "مسرح وعرائس": {"ج": "المجال الفني", "ح": 2},
            "ت بدنية": {"ج": "المجال البدني والإيقاعي", "ح": 4},
            "ت إيقاعية": {"ج": "المجال البدني والإيقاعي", "ح": 2},
        },
        "تو": {
            "الأحد": [{"ن": "الاستقبال", "م": "15 د", "ف": "ص"},
                      {"ن": "تعبير شفوي", "م": "30 د", "ف": "ص"},
                      {"ن": "مبادئ القراءة", "م": "30 د", "ف": "ص"},
                      {"ن": "رياضيات", "م": "30 د", "ف": "ص"},
                      {"ن": "ت علمية وتكنولوجية", "م": "30 د", "ف": "ص"},
                      {"ن": "ت إسلامية", "م": "30 د", "ف": "ص"},
                      {"ن": "تهيئة الخروج", "م": "15 د", "ف": "ص"},
                      {"ن": "الاستقبال", "م": "15 د", "ف": "م"},
                      {"ن": "مسرح وعرائس", "م": "30 د", "ف": "م"},
                      {"ن": "تربية تشكيلية", "م": "30 د", "ف": "م"},
                      {"ن": "ت بدنية", "م": "30 د", "ف": "م"},
                      {"ن": "نهاية الخروج", "م": "15 د", "ف": "م"}],
            "الإثنين": [{"ن": "الاستقبال", "م": "15 د", "ف": "ص"},
                        {"ن": "رياضيات", "م": "30 د", "ف": "ص"},
                        {"ن": "تعبير شفوي", "م": "30 د", "ف": "ص"},
                        {"ن": "تخطيط", "م": "30 د", "ف": "ص"},
                        {"ن": "ت علمية وتكنولوجية", "م": "30 د", "ف": "ص"},
                        {"ن": "ت مدنية", "م": "30 د", "ف": "ص"},
                        {"ن": "تهيئة الخروج", "م": "15 د", "ف": "ص"},
                        {"ن": "الاستقبال", "م": "15 د", "ف": "م"},
                        {"ن": "مسرح وعرائس", "م": "30 د", "ف": "م"},
                        {"ن": "تربية تشكيلية", "م": "30 د", "ف": "م"},
                        {"ن": "ت بدنية", "م": "30 د", "ف": "م"},
                        {"ن": "نهاية الخروج", "م": "15 د", "ف": "م"}],
            "الثلاثاء": [{"ن": "الاستقبال", "م": "15 د", "ف": "ص"},
                         {"ن": "تعبير شفوي", "م": "30 د", "ف": "ص"},
                         {"ن": "مبادئ القراءة", "م": "30 د", "ف": "ص"},
                         {"ن": "رياضيات", "م": "30 د", "ف": "ص"},
                         {"ن": "ت إسلامية", "م": "30 د", "ف": "ص"},
                         {"ن": "ت بدنية", "م": "30 د", "ف": "ص"},
                         {"ن": "تهيئة الخروج", "م": "15 د", "ف": "ص"}],
            "الأربعاء": [{"ن": "الاستقبال", "م": "15 د", "ف": "ص"},
                         {"ن": "رياضيات", "م": "30 د", "ف": "ص"},
                         {"ن": "مبادئ القراءة", "م": "30 د", "ف": "ص"},
                         {"ن": "تخطيط", "م": "30 د", "ف": "ص"},
                         {"ن": "ت علمية وتكنولوجية", "م": "30 د", "ف": "ص"},
                         {"ن": "ت مدنية", "م": "30 د", "ف": "ص"},
                         {"ن": "تهيئة الخروج", "م": "15 د", "ف": "ص"},
                         {"ن": "الاستقبال", "م": "15 د", "ف": "م"},
                         {"ن": "ت إيقاعية", "م": "30 د", "ف": "م"},
                         {"ن": "موسيقى وإنشاد", "م": "30 د", "ف": "م"},
                         {"ن": "ت بدنية", "م": "30 د", "ف": "م"},
                         {"ن": "نهاية الخروج", "م": "15 د", "ف": "م"}],
            "الخميس": [{"ن": "الاستقبال", "م": "15 د", "ف": "ص"},
                       {"ن": "مبادئ القراءة", "م": "30 د", "ف": "ص"},
                       {"ن": "رياضيات", "م": "30 د", "ف": "ص"},
                       {"ن": "ت علمية وتكنولوجية", "م": "30 د", "ف": "ص"},
                       {"ن": "ت إيقاعية", "م": "30 د", "ف": "ص"},
                       {"ن": "موسيقى وإنشاد", "م": "30 د", "ف": "ص"},
                       {"ن": "تهيئة الخروج", "م": "15 د", "ف": "ص"}],
        },
    },
    "السنة 1 ابتدائي": {
        "رت": ["الاستقبال", "الاستراحة", "تهيئة الخروج", "نهاية الخروج"],
        "مج": {"اللغة العربية": "#1565C0", "الرياضيات": "#C62828", "التربية العلمية": "#2E7D32",
               "التربية الاجتماعية": "#F57F17", "التربية الفنية": "#6A1B9A", "التربية البدنية": "#00838F"},
        "مو": {"قراءة": {"ج": "اللغة العربية", "ح": 6}, "تعبير شفوي": {"ج": "اللغة العربية", "ح": 2},
               "كتابة وخط": {"ج": "اللغة العربية", "ح": 3}, "محفوظات": {"ج": "اللغة العربية", "ح": 1},
               "رياضيات": {"ج": "الرياضيات", "ح": 5}, "تربية علمية": {"ج": "التربية العلمية", "ح": 2},
               "تربية إسلامية": {"ج": "التربية الاجتماعية", "ح": 2}, "تربية مدنية": {"ج": "التربية الاجتماعية", "ح": 1},
               "تربية فنية": {"ج": "التربية الفنية", "ح": 2}, "تربية موسيقية": {"ج": "التربية الفنية", "ح": 1},
               "تربية بدنية": {"ج": "التربية البدنية", "ح": 2}},
        "تو": {},
    },
    "السنة 2 ابتدائي": {
        "رت": ["الاستقبال", "الاستراحة", "تهيئة الخروج", "نهاية الخروج"],
        "مج": {"اللغة العربية": "#1565C0", "الرياضيات": "#C62828", "التربية العلمية": "#2E7D32",
               "التربية الاجتماعية": "#F57F17", "التربية الفنية": "#6A1B9A", "التربية البدنية": "#00838F"},
        "مو": {"قراءة": {"ج": "اللغة العربية", "ح": 5}, "تعبير شفوي": {"ج": "اللغة العربية", "ح": 2},
               "كتابة وخط": {"ج": "اللغة العربية", "ح": 3}, "إملاء": {"ج": "اللغة العربية", "ح": 1},
               "محفوظات": {"ج": "اللغة العربية", "ح": 1}, "رياضيات": {"ج": "الرياضيات", "ح": 5},
               "تربية علمية": {"ج": "التربية العلمية", "ح": 2}, "تربية إسلامية": {"ج": "التربية الاجتماعية", "ح": 2},
               "تربية مدنية": {"ج": "التربية الاجتماعية", "ح": 1}, "تربية فنية": {"ج": "التربية الفنية", "ح": 2},
               "تربية موسيقية": {"ج": "التربية الفنية", "ح": 1}, "تربية بدنية": {"ج": "التربية البدنية", "ح": 2}},
        "تو": {},
    },
    "السنة 3 ابتدائي": {
        "رت": ["الاستقبال", "الاستراحة", "تهيئة الخروج", "نهاية الخروج"],
        "مج": {"اللغة العربية": "#1565C0", "اللغة الفرنسية": "#1976D2", "الرياضيات": "#C62828",
               "التربية العلمية": "#2E7D32", "التربية الاجتماعية": "#F57F17", "التربية الفنية": "#6A1B9A",
               "التربية البدنية": "#00838F"},
        "مو": {"قراءة": {"ج": "اللغة العربية", "ح": 4}, "تعبير شفوي": {"ج": "اللغة العربية", "ح": 2},
               "كتابة وإملاء": {"ج": "اللغة العربية", "ح": 2}, "قواعد": {"ج": "اللغة العربية", "ح": 1},
               "محفوظات": {"ج": "اللغة العربية", "ح": 1}, "فرنسية": {"ج": "اللغة الفرنسية", "ح": 3},
               "رياضيات": {"ج": "الرياضيات", "ح": 5}, "تربية علمية": {"ج": "التربية العلمية", "ح": 2},
               "تربية إسلامية": {"ج": "التربية الاجتماعية", "ح": 1}, "تربية مدنية": {"ج": "التربية الاجتماعية", "ح": 1},
               "تاريخ وجغرافيا": {"ج": "التربية الاجتماعية", "ح": 1}, "تربية فنية": {"ج": "التربية الفنية", "ح": 1},
               "تربية موسيقية": {"ج": "التربية الفنية", "ح": 1}, "تربية بدنية": {"ج": "التربية البدنية", "ح": 2}},
        "تو": {},
    },
    "السنة 4 ابتدائي": {
        "رت": ["الاستقبال", "الاستراحة", "تهيئة الخروج", "نهاية الخروج"],
        "مج": {"اللغة العربية": "#1565C0", "اللغة الفرنسية": "#1976D2", "الرياضيات": "#C62828",
               "التربية العلمية": "#2E7D32", "التربية الاجتماعية": "#F57F17", "التربية الفنية": "#6A1B9A",
               "التربية البدنية": "#00838F"},
        "مو": {"قراءة ودراسة نص": {"ج": "اللغة العربية", "ح": 3},
               "قواعد صرفية ونحوية": {"ج": "اللغة العربية", "ح": 2},
               "تعبير كتابي": {"ج": "اللغة العربية", "ح": 1}, "تعبير شفوي": {"ج": "اللغة العربية", "ح": 1},
               "إملاء": {"ج": "اللغة العربية", "ح": 1}, "محفوظات": {"ج": "اللغة العربية", "ح": 1},
               "فرنسية": {"ج": "اللغة الفرنسية", "ح": 3}, "رياضيات": {"ج": "الرياضيات", "ح": 5},
               "تربية علمية": {"ج": "التربية العلمية", "ح": 2}, "تربية إسلامية": {"ج": "التربية الاجتماعية", "ح": 1},
               "تربية مدنية": {"ج": "التربية الاجتماعية", "ح": 1}, "تاريخ": {"ج": "التربية الاجتماعية", "ح": 1},
               "جغرافيا": {"ج": "التربية الاجتماعية", "ح": 1}, "تربية فنية": {"ج": "التربية الفنية", "ح": 1},
               "تربية موسيقية": {"ج": "التربية الفنية", "ح": 1}, "تربية بدنية": {"ج": "التربية البدنية", "ح": 2}},
        "تو": {},
    },
    "السنة 5 ابتدائي": {
        "رت": ["الاستقبال", "الاستراحة", "تهيئة الخروج", "نهاية الخروج"],
        "مج": {"اللغة العربية": "#1565C0", "اللغة الفرنسية": "#1976D2", "الرياضيات": "#C62828",
               "التربية العلمية": "#2E7D32", "التربية الاجتماعية": "#F57F17", "التربية الفنية": "#6A1B9A",
               "التربية البدنية": "#00838F"},
        "مو": {"قراءة ودراسة نص": {"ج": "اللغة العربية", "ح": 3},
               "قواعد صرفية ونحوية": {"ج": "اللغة العربية", "ح": 2},
               "تعبير كتابي": {"ج": "اللغة العربية", "ح": 1}, "تعبير شفوي": {"ج": "اللغة العربية", "ح": 1},
               "إملاء": {"ج": "اللغة العربية", "ح": 1}, "محفوظات": {"ج": "اللغة العربية", "ح": 1},
               "فرنسية": {"ج": "اللغة الفرنسية", "ح": 3}, "رياضيات": {"ج": "الرياضيات", "ح": 5},
               "تربية علمية": {"ج": "التربية العلمية", "ح": 2}, "تربية إسلامية": {"ج": "التربية الاجتماعية", "ح": 1},
               "تربية مدنية": {"ج": "التربية الاجتماعية", "ح": 1}, "تاريخ": {"ج": "التربية الاجتماعية", "ح": 1},
               "جغرافيا": {"ج": "التربية الاجتماعية", "ح": 1}, "تربية فنية": {"ج": "التربية الفنية", "ح": 1},
               "تربية موسيقية": {"ج": "التربية الفنية", "ح": 1}, "تربية بدنية": {"ج": "التربية البدنية", "ح": 2}},
        "تو": {},
    },
}


# ╔══════════════════════════════════════════════════════╗
# ║ دوال المستوى والتوقيت والتوزيع والقالب               ║
# ╚══════════════════════════════════════════════════════╝

DAYS = ["الأحد", "الإثنين", "الثلاثاء", "الأربعاء", "الخميس"]
HALF = {"الثلاثاء", "الخميس"}


def gc():
    return st.session_state.get('cfgs', LEVELS).get(st.session_state.get('lv', 'قسم التحضيري'), LEVELS['قسم التحضيري'])


def auto_s(mo, rt):
    ss = []
    [ss.extend([s] * i["ح"]) for s, i in mo.items()]
    sc = {}
    ix = 0
    for d in DAYS:
        p = []
        f = d not in HALF
        p.append({"ن": rt[0] if rt else "الاستقبال", "م": "15 د", "ف": "ص"})
        for _ in range(5):
            if ix < len(ss):
                p.append({"ن": ss[ix], "م": "45 د", "ف": "ص"})
                ix += 1
        p.append({"ن": "تهيئة الخروج", "م": "15 د", "ف": "ص"})
        if f:
            p.append({"ن": rt[0] if rt else "الاستقبال", "م": "15 د", "ف": "م"})
            for _ in range(3):
                if ix < len(ss):
                    p.append({"ن": ss[ix], "م": "45 د", "ف": "م"})
                    ix += 1
            p.append({"ن": "نهاية الخروج", "م": "15 د", "ف": "م"})
        sc[d] = p
    return sc


def gs():
    c = gc()
    s = c.get("تو", {})
    return s if s else auto_s(c["مو"], c["رت"])


def gm():
    return gc().get("مو", {})


def gd():
    return gc().get("مج", {})


def gr():
    return gc().get("رت", [])


def d4(a):
    m = gm()
    return m[a]["ج"] if a in m else "—"


def dc(d):
    return gd().get(d, "#666")


def dbg(d):
    c = dc(d)
    return (f'<span style="display:inline-block;padding:2px 8px;border-radius:10px;'
            f'font-size:.7rem;font-weight:600;background:{c}22;color:{c};'
            f'border:1px solid {c}33;">{d}</span>')


def distribute(raw_db):
    mc = gm()
    dist = {}
    rep = {}
    for s, i in mc.items():
        rq = i["ح"]
        av = raw_db.get(s, [])
        cn = len(av)
        if cn == 0:
            dist[s] = []
            rep[s] = {"r": rq, "a": 0, "ok": False}
            continue
        result = []
        if cn >= rq:
            result = [l.copy() for l in av[:rq]]
        else:
            pp = rq / cn
            for i2, les in enumerate(av):
                for _ in range(round((i2 + 1) * pp) - round(i2 * pp)):
                    result.append(les.copy())
        dist[s] = result
        rep[s] = {"r": rq, "a": cn, "ok": bool(result)}
    return dist, rep


def _rtl(p):
    pPr = p._p.get_or_add_pPr()
    pPr.append(pPr.makeelement(qn('w:bidi'), {}))


def _cl(c, t, b=False, s=10, co=None):
    c.text = ""
    p = c.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _rtl(p)
    r = p.add_run(t)
    r.bold = b
    r.font.size = Pt(s)
    r.font.name = "Sakkal Majalla"
    if co:
        r.font.color.rgb = co
    rPr = r._r.get_or_add_rPr()
    rPr.append(rPr.makeelement(qn('w:rFonts'), {qn('w:cs'): 'Sakkal Majalla'}))


def _sh(row, hx):
    for c in row.cells:
        tc = c._tc.get_or_add_tcPr()
        tc.append(tc.makeelement(qn('w:shd'), {qn('w:fill'): hx, qn('w:val'): 'clear'}))


def _pt(doc, ti, st2, cn):
    h = doc.add_paragraph()
    h.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _rtl(h)
    r = h.add_run(ti)
    r.bold = True
    r.font.size = Pt(13)
    r.font.color.rgb = RGBColor(0, 51, 102)

    hd = ['مؤشرات الكفاءة', 'عنوان الدرس', 'الميدان', 'النشاط', 'المدة']
    tbl = doc.add_table(rows=1 + cn, cols=5)
    tbl.style = 'Table Grid'
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER

    ws = [Cm(5.5), Cm(5), Cm(3.5), Cm(3.5), Cm(2)]
    for row in tbl.rows:
        for i, w in enumerate(ws):
            row.cells[i].width = w

    hr = tbl.rows[0]
    _sh(hr, "1F4E79")
    for i, t in enumerate(hd):
        _cl(hr.cells[i], t, True, 11, RGBColor(255, 255, 255))

    for j in range(cn):
        n = st2 + j
        dr = tbl.rows[1 + j]
        if j % 2 == 0:
            _sh(dr, "EDF2F9")
        for i, ph in enumerate([f'{{{{k_{n}}}}}', f'{{{{t_{n}}}}}', f'{{{{d_{n}}}}}', f'{{{{n_{n}}}}}', f'{{{{m_{n}}}}}']):
            _cl(dr.cells[i], ph, s=9)


def mkt(day=None):
    if not DOCX_OK:
        return None
    lv = st.session_state.get('lv', '')
    sc = gs()
    mt = 7
    et = 5
    if day and day in sc:
        pl = sc[day]
        mt = sum(1 for s in pl if s['ف'] == 'ص')
        et = sum(1 for s in pl if s['ف'] == 'م')
    doc = Document()
    for sec in doc.sections:
        sec._sectPr.append(sec._sectPr.makeelement(qn('w:bidi'), {}))
    for t, sz, b in [('الجمهورية الجزائرية الديمقراطية الشعبية', 12, True),
                     ('وزارة التربية الوطنية', 11, False)]:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        _rtl(p)
        r = p.add_run(t)
        r.bold = b
        r.font.size = Pt(sz)
    tp = doc.add_paragraph()
    tp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _rtl(tp)
    tr = tp.add_run(f'الكراس اليومي — {lv}')
    tr.bold = True
    tr.font.size = Pt(16)
    tr.font.color.rgb = RGBColor(0, 51, 102)
    inf = doc.add_table(rows=1, cols=3)
    inf.alignment = WD_TABLE_ALIGNMENT.CENTER
    _cl(inf.rows[0].cells[2], 'اليوم:{{day}}', True, 12)
    _cl(inf.rows[0].cells[1], 'التاريخ:{{date}}', s=11)
    _cl(inf.rows[0].cells[0], 'الأسبوع:{{week}}', s=11)
    doc.add_paragraph('')
    _pt(doc, '☀ الفترة الصباحية', 1, mt)
    if et > 0:
        doc.add_paragraph('')
        _pt(doc, '🌙 الفترة المسائية', mt + 1, et)
    doc.add_paragraph('')
    np2 = doc.add_paragraph()
    np2.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    _rtl(np2)
    np2.add_run('ملاحظات:' + '.' * 80).font.size = Pt(10)
    buf = BytesIO()
    doc.save(buf)
    return buf.getvalue()


def _sr(pa, o, n):
    if o not in pa.text:
        return
    for run in pa.runs:
        if o in run.text:
            run.text = run.text.replace(o, n)
            return
    f = pa.text.replace(o, n)
    if pa.runs:
        for run in pa.runs:
            run.text = ""
        pa.runs[0].text = f


def bld(day, tmpl, dd, wn="", ds=""):
    if not DOCX_OK:
        return None, [], []
    sc = gs()
    pl = sc.get(day, [])
    if not pl:
        return None, [], []
    rt = gr()
    doc = Document(BytesIO(tmpl))
    rp = {"{{day}}": day, "{{date}}": ds, "{{week}}": wn}
    si = []
    wa = []
    for i, s in enumerate(pl, 1):
        a = s["ن"]
        du = s["م"]
        pe = "صباحية" if s["ف"] == "ص" else "مسائية"
        dm = d4(a)
        rp[f"{{{{m_{i}}}}}"] = du
        rp[f"{{{{n_{i}}}}}"] = a
        info = {"رقم": i, "النشاط": a, "المدة": du, "الفترة": pe, "المجال": dm,
                "نوع": "روتيني", "الموضوع": "—", "الكفاءة": "—"}
        if a in rt:
            rp[f"{{{{t_{i}}}}}"] = rp[f"{{{{k_{i}}}}}"] = rp[f"{{{{d_{i}}}}}"] = "—"
        elif a in dd and dd[a]:
            le = dd[a].pop(0)
            t = le.get('موضوع', '—')
            k = le.get('كفاءة', '—')
            rp[f"{{{{t_{i}}}}}"] = t
            rp[f"{{{{k_{i}}}}}"] = k
            rp[f"{{{{d_{i}}}}}"] = dm
            info.update({"نوع": "تعليمي", "الموضوع": t, "الكفاءة": k})
        else:
            rp[f"{{{{t_{i}}}}}"] = "⚠ لا توجد مذكرة"
            rp[f"{{{{k_{i}}}}}"] = "⚠"
            rp[f"{{{{d_{i}}}}}"] = dm
            info["نوع"] = "ناقص"
            wa.append(a)
        si.append(info)

    for tbl in doc.tables:
        for row in tbl.rows:
            for cell in row.cells:
                for pa in cell.paragraphs:
                    for k2, v in rp.items():
                        if k2 in pa.text:
                            _sr(pa, k2, str(v))
    for pa in doc.paragraphs:
        for k2, v in rp.items():
            if k2 in pa.text:
                _sr(pa, k2, str(v))

    buf = BytesIO()
    doc.save(buf)
    return buf.getvalue(), si, wa


# ╔══════════════════════════════════════════════════════╗
# ║ واجهة Streamlit                                      ║
# ╚══════════════════════════════════════════════════════╝

st.set_page_config(page_title="الكراس اليومي 🎓", page_icon="🎓", layout="wide", initial_sidebar_state="expanded")

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
.slot{display:flex;align-items:center;gap:.8rem;padding:.6rem 1rem;margin:.2rem 0;border-radius:8px;direction:rtl}
.slot-r{background:#f5f5f5;border-right:4px solid #9e9e9e}.slot-t{background:#e3f2fd;border-right:4px solid #1565c0}.slot-w{background:#fff3e0;border-right:4px solid #e65100}
.stDownloadButton>button{width:100%;background:linear-gradient(135deg,#1F4E79,#2E75B6)!important;color:#fff!important;border:none!important;border-radius:8px!important}
[data-testid="stSidebar"]{direction:rtl;text-align:right}footer{visibility:hidden}
.ok-box{background:#e8f5e9;border:1px solid #4caf50;border-radius:10px;padding:1rem;text-align:center}
.tip{background:#E3F2FD;border:1px solid #1565C0;border-radius:8px;padding:.8rem;margin:.5rem 0;direction:rtl}
</style>
""", unsafe_allow_html=True)

for k in ['db', 'gen', 'raw', 'lv', 'cfgs', 'method']:
    if k not in st.session_state:
        if k == 'gen':
            st.session_state[k] = {}
        elif k == 'lv':
            st.session_state[k] = 'قسم التحضيري'
        elif k == 'cfgs':
            st.session_state[k] = copy.deepcopy(LEVELS)
        else:
            st.session_state[k] = None

with st.sidebar:
    st.markdown("## 🎓 المستوى")
    lvl = list(LEVELS.keys())
    sel = st.selectbox("المستوى", lvl, index=lvl.index(st.session_state.lv))
    if sel != st.session_state.lv:
        st.session_state.lv = sel
        st.session_state.db = None
        st.session_state.gen = {}
        st.rerun()

    c = gc()
    ts = sum(i["ح"] for i in c["مو"].values())
    st.info(f"📘 {len(c['مو'])} مادة | 📖 {ts} حصة")

    st.markdown("---")
    wn = st.text_input("📅 الأسبوع", placeholder="10")
    ds = st.text_input("📆 التاريخ", placeholder="2024/12/01")

    st.markdown("---")
    st.markdown("### 🔑 مفاتيح AI")
    st.markdown("**🟢 Groq** (نصوص + صور)")
    gk = st.text_input("مفتاح Groq", type="password", help="console.groq.com", key="gk")
    gtm = st.selectbox("نموذج نصي", GROQ_TEXT_MODELS, key="gtm")
    gvm = st.selectbox("نموذج بصري", GROQ_VISION_MODELS, key="gvm")
    st.markdown("**🟡 HuggingFace** (نصوص فقط)")
    hk = st.text_input("مفتاح HF", type="password", help="huggingface.co/settings/tokens", key="hk")
    hm = st.selectbox("نموذج HF", HF_MODELS, key="hm")

    st.markdown("---")
    st.markdown(f"{'✅' if DOCX_OK else '❌'} Word | {'✅' if PDF_OK else '❌'} PDF")
    st.markdown(f"{'🟢' if gk else '⬜'} Groq | {'🟡' if hk else '⬜'} HF")
    st.markdown("---")
    up = st.file_uploader("📤 المذكرات", type=["docx", "pdf", "jpg", "jpeg", "png", "bmp", "webp"])
    st.caption("🎓 v9.1")

if up:
    fb = up.read()
    if st.session_state.get('_l') != up.name:
        st.session_state._fb = fb
        st.session_state._l = up.name
        st.session_state.db = None
        st.session_state.gen = {}
        st.session_state.raw = None

lv = st.session_state.lv
st.markdown(f'<h1 style="background:linear-gradient(135deg,#1F4E79,#2E75B6);-webkit-background-clip:text;-webkit-text-fill-color:transparent;font-size:2.2rem;">🎓 الكراس اليومي — {lv}</h1><p style="text-align:center;color:#888;">📄Word•📕PDF•🖼️صور•🟢Groq•🟡HuggingFace</p>', unsafe_allow_html=True)

t1, t2, t3, t4 = st.tabs(["🧠 استخراج", "📅 توليد", "⚙️ إعداد", "🗺️ مجالات"])

with t1:
    if not up:
        st.info("👆 ارفع ملف المذكرات من الشريط الجانبي")
        st.markdown("""
        ### 📁 الصيغ المدعومة
        | الصيغة | 🟢 Groq | 🟡 HuggingFace |
        |--------|---------|----------------|
        | 📄 Word | ✅ نصي | ✅ نصي |
        | 📕 PDF نصي | ✅ نصي | ✅ نصي |
        | 📕 PDF صور | ✅ بصري | ❌ |
        | 🖼️ صورة | ✅ بصري | ❌ |
        """)
        st.markdown('<div class="tip">💡 <strong>للحصول على أفضل النتائج:</strong> ارفع ملف المذكرات التفصيلية (البطاقات الفنية) وليس جدول التوزيع الأسبوعي فقط.</div>', unsafe_allow_html=True)
    else:
        ext = up.name.lower().rsplit('.', 1)[-1]
        sz = len(st.session_state._fb) // 1024
        st.markdown(f"### 📁 {up.name} ({sz} KB)")
        if ext in ('jpg', 'jpeg', 'png', 'bmp', 'webp'):
            st.image(st.session_state._fb, use_container_width=True)
        elif ext == 'pdf' and PDF_OK:
            with st.expander("👁️ معاينة الصفحات"):
                imgs = pdf_to_images(st.session_state._fb)
                if imgs:
                    cols = st.columns(min(len(imgs), 3))
                    for ix, im in enumerate(imgs[:6]):
                        with cols[ix % 3]:
                            st.image(im["bytes"], caption=f"صفحة {im['page']}")

        has_key = bool(gk) or bool(hk)
        if not has_key:
            st.warning("🔑 أدخل مفتاح API واحد على الأقل")
        st.markdown('<div class="tip">💡 ارفع <strong>المذكرات التفصيلية</strong> (تحتوي بطاقات الدروس) وليس الجداول الإجمالية الفارغة فقط.</div>', unsafe_allow_html=True)

        if st.button("🧠 استخراج الدروس", type="primary", use_container_width=True, disabled=not has_key):
            bar = st.progress(0)
            msg = st.empty()
            res = smart_process_file(st.session_state._fb, up.name, gk, hk, gtm, gvm, hm, lv, gm(), bar, msg)
            bar.progress(1.0)
            msg.empty()
            st.session_state.raw = res["raw"]
            st.session_state.method = res["method"]
            if res["err"]:
                st.error(f"❌ {res['err']}")
            elif res["db"]:
                d, r = distribute(res["db"])
                st.session_state.db = d
                st.session_state.gen = {}
                total = sum(len(v) for v in res["db"].values())
                st.success(f"✅ تم استخراج {total} درس!")
                st.rerun()
            else:
                st.error("❌ لم يتم العثور على دروس — تأكد أن الملف يحتوي على مذكرات تفصيلية")

        db = st.session_state.db
        if db:
            if st.session_state.get('method'):
                st.caption(f"🔄 {st.session_state.method}")
            total = sum(len(v) for v in db.values())
            mc = gm()
            matched = set(k2 for k2, v in db.items() if v) & set(mc.keys())
            miss = set(mc.keys()) - set(k2 for k2, v in db.items() if v)
            c1, c2, c3 = st.columns(3)
            for col, tl, nm, cl in [(c1, "📖 حصص", total, "card-green"),
                                     (c2, "✅ مغطاة", len(matched), "card-purple"),
                                     (c3, "⚠ ناقصة", len(miss), "card-amber")]:
                with col:
                    st.markdown(f'<div class="card {cl}"><h4>{tl}</h4><div class="num">{nm}</div></div>', unsafe_allow_html=True)
            if miss:
                st.warning(f"⚠️ مواد ناقصة: **{' ، '.join(miss)}**")
            for su in sorted(db.keys()):
                le = db[su]
                if not le:
                    continue
                dm = d4(su)
                with st.expander(f"✅ {su} — {len(le)} حصة — {dm}"):
                    for j, l in enumerate(le, 1):
                        st.markdown(f"**{j}.** 📝 {l.get('موضوع', '—')}\n\n🎯 {l.get('كفاءة', '—')}")
                        if j < len(le):
                            st.divider()
            if st.session_state.raw:
                with st.expander("🧠 رد AI الخام"):
                    st.code(st.session_state.raw, language="json")

with t2:
    db = st.session_state.db
    if not db or not any(db.values()):
        st.info("🧠 استخرج الدروس أولاً")
    elif not DOCX_OK:
        st.error("❌ python-docx مطلوب")
    else:
        sc = gs()
        days = list(sc.keys())
        st.markdown("### 📅 اختر الأيام")
        cols = st.columns(len(days))
        sd = []
        for i, d in enumerate(days):
            rt2 = gr()
            tc = sum(1 for s in sc[d] if s["ن"] not in rt2)
            with cols[i]:
                if st.checkbox(f"{d}({tc})", key=f"d_{d}"):
                    sd.append(d)
        if st.checkbox("✅ الكل"):
            sd = days

        if sd and st.button(f"🚀 توليد {len(sd)} كراس", type="primary", use_container_width=True):
            wdb = copy.deepcopy(db)
            gen = {}
            bar = st.progress(0)
            for ix, d in enumerate(sd):
                bar.progress(ix / len(sd))
                tp = mkt(d)
                if tp:
                    res, inf, wa = bld(d, tp, wdb, wn, ds)
                    if res:
                        gen[d] = {'b': res, 's': inf, 'w': wa}
            bar.progress(1.0)
            st.session_state.gen = gen
            st.markdown(f'<div class="ok-box"><h3>✅ {len(gen)} كراس!</h3></div>', unsafe_allow_html=True)

        gf = st.session_state.gen
        if gf:
            st.markdown("### 📥 التحميل")
            dlc = st.columns(min(len(gf), 5))
            for i, (d, data) in enumerate(gf.items()):
                with dlc[i % 5]:
                    st.download_button(f"📄{d}", data=data['b'], file_name=f"كراس_{d}.docx",
                                       mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                       use_container_width=True, key=f"dl_{d}")
            st.markdown("---\n### 👁️ معاينة")
            dp = st.selectbox("اليوم", list(gf.keys()))
            if dp:
                for s in gf[dp]['s']:
                    ty = s['نوع']
                    css = {'روتيني': 'slot-r', 'تعليمي': 'slot-t', 'ناقص': 'slot-w'}.get(ty, 'slot-r')
                    ic = {'روتيني': '⏰', 'تعليمي': '📖', 'ناقص': '⚠️'}.get(ty, '⏰')
                    dm = s.get('المجال', '—')
                    bd = dbg(dm) if dm != '—' else ''
                    ex = ''
                    if ty == 'تعليمي':
                        ex = f"<br><small>📝{s['الموضوع']}</small><br><small>🎯{s['الكفاءة']}</small>"
                    st.markdown(f'<div class="slot {css}"><span style="font-size:1.2rem">{ic}</span><div style="flex:1"><strong>{s["النشاط"]}</strong> <span style="color:#888">({s["المدة"]})</span>{bd}{ex}</div></div>', unsafe_allow_html=True)

with t3:
    st.markdown(f"### ⚙️ {lv}")
    c2 = gc()
    mc2 = c2["مو"]
    dm2 = c2["مج"]
    sd2 = [{"المادة": n, "المجال": i["ج"], "الحصص": i["ح"]} for n, i in mc2.items()]
    ed = st.data_editor(sd2, num_rows="dynamic", column_config={
        "المادة": st.column_config.TextColumn("المادة", width="medium"),
        "المجال": st.column_config.SelectboxColumn("المجال", options=list(dm2.keys()), width="medium"),
        "الحصص": st.column_config.NumberColumn("الحصص", min_value=1, max_value=10, width="small"),
    }, use_container_width=True, key="ed")

    e1, e2 = st.columns(2)
    with e1:
        if st.button("💾 حفظ", use_container_width=True, type="primary"):
            ns = {r["المادة"]: {"ج": r["المجال"], "ح": r.get("الحصص", 1)} for r in ed if
                  r.get("المادة") and r.get("المجال")}
            if ns:
                st.session_state.cfgs[lv]["مو"] = ns
                st.success("✅")
    with e2:
        if st.button("🔄 توقيت تلقائي", use_container_width=True):
            c3 = gc()
            st.session_state.cfgs[lv]["تو"] = auto_s(c3["مو"], c3["رت"])
            st.success("✅")
    st.info(f"المجموع: **{sum(r.get('الحصص', 0) for r in ed if r.get('المادة'))}** حصة")

with t4:
    ca, cb = st.columns(2)
    with ca:
        st.markdown("### 🗺️ المجالات")
        mc3 = gm()
        dm3 = {}
        for s, i in mc3.items():
            dm3.setdefault(i["ج"], []).append(s)
        for dm, su in dm3.items():
            cl = dc(dm)
            th = sum(mc3[s]["ح"] for s in su)
            st.markdown(f'<div style="border:2px solid {cl};border-radius:12px;padding:.8rem;margin:.4rem 0;"><h4 style="color:{cl};text-align:center;">{dm}({th}ح)</h4>', unsafe_allow_html=True)
            for s in su:
                cn = mc3[s]["ح"]
                st.markdown(f'<div style="display:flex;align-items:center;gap:6px;margin:3px 0;direction:rtl;"><span style="min-width:130px;font-size:.85rem">{s}</span><div style="background:{cl}44;border-radius:3px;height:16px;width:{cn * 14}px;"></div><span style="color:{cl};font-weight:700;font-size:.85rem">{cn}</span></div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
    with cb:
        st.markdown("### 📊 التوقيت")
        sc2 = gs()
        if sc2:
            vd = st.selectbox("اليوم", list(sc2.keys()), key="sv")
            if vd:
                rt2 = gr()
                for pn, pv in [("☀️ صباح", "ص"), ("🌙 مساء", "م")]:
                    sl = [s for s in sc2[vd] if s["ف"] == pv]
                    if not sl:
                        continue
                    st.markdown(f"**{pn}**")
                    st.dataframe([{"#": j, "النشاط": s['ن'], "المدة": s['م'],
                                   "المجال": d4(s['ن']) if s['ن'] not in rt2 else "—"} for j, s in enumerate(sl, 1)],
                                 use_container_width=True, hide_index=True)
        else:
            st.warning("اضغط 'توقيت تلقائي' في تبويب الإعداد")
