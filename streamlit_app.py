# -*- coding: utf-8 -*-
"""
🎓 الكراس اليومي v7.1
Word + PDF + صور + AI
"""

import streamlit as st
import re, copy, json, base64
from io import BytesIO
from PIL import Image

# ── استيراد مكتبات مع معالجة الأخطاء ──

try:
    from docx import Document
    from docx.shared import Pt, Cm, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.enum.table import WD_TABLE_ALIGNMENT
    from docx.oxml.ns import qn
    DOCX_OK = True
except ImportError:
    DOCX_OK = False

try:
    import fitz
    PDF_OK = True
except ImportError:
    try:
        import pymupdf as fitz
        PDF_OK = True
    except ImportError:
        PDF_OK = False

try:
    from groq import Groq
    GROQ_OK = True
except ImportError:
    GROQ_OK = False

FORMATS = ["docx", "pdf", "jpg", "jpeg", "png", "bmp", "webp"]


# ╔══════════════════════════════════════════════════╗
# ║          إعدادات المستويات الدراسية              ║
# ╚══════════════════════════════════════════════════╝

LEVELS = {
    "قسم التحضيري": {
        "روتيني": ["الاستقبال","الاستراحة","تهيئة الخروج","نهاية الخروج"],
        "مجالات": {
            "المجال اللغوي":"#1565C0","المجال الرياضي":"#C62828",
            "المجال العلمي":"#2E7D32","المجال الاجتماعي":"#F57F17",
            "المجال الفني":"#6A1B9A","المجال البدني والإيقاعي":"#00838F",
        },
        "مواد": {
            "تعبير شفوي":{"مجال":"المجال اللغوي","حصص":3},
            "مبادئ القراءة":{"مجال":"المجال اللغوي","حصص":4},
            "تخطيط":{"مجال":"المجال اللغوي","حصص":2},
            "رياضيات":{"مجال":"المجال الرياضي","حصص":5},
            "ت علمية وتكنولوجية":{"مجال":"المجال العلمي","حصص":4},
            "ت إسلامية":{"مجال":"المجال الاجتماعي","حصص":2},
            "ت مدنية":{"مجال":"المجال الاجتماعي","حصص":2},
            "تربية تشكيلية":{"مجال":"المجال الفني","حصص":2},
            "موسيقى وإنشاد":{"مجال":"المجال الفني","حصص":2},
            "مسرح وعرائس":{"مجال":"المجال الفني","حصص":2},
            "ت بدنية":{"مجال":"المجال البدني والإيقاعي","حصص":4},
            "ت إيقاعية":{"مجال":"المجال البدني والإيقاعي","حصص":2},
        },
        "توقيت": {
            "الأحد":[
                {"ن":"الاستقبال","م":"15 د","ف":"ص"},
                {"ن":"تعبير شفوي","م":"30 د","ف":"ص"},
                {"ن":"مبادئ القراءة","م":"30 د","ف":"ص"},
                {"ن":"رياضيات","م":"30 د","ف":"ص"},
                {"ن":"ت علمية وتكنولوجية","م":"30 د","ف":"ص"},
                {"ن":"ت إسلامية","م":"30 د","ف":"ص"},
                {"ن":"تهيئة الخروج","م":"15 د","ف":"ص"},
                {"ن":"الاستقبال","م":"15 د","ف":"م"},
                {"ن":"مسرح وعرائس","م":"30 د","ف":"م"},
                {"ن":"تربية تشكيلية","م":"30 د","ف":"م"},
                {"ن":"ت بدنية","م":"30 د","ف":"م"},
                {"ن":"نهاية الخروج","م":"15 د","ف":"م"},
            ],
            "الإثنين":[
                {"ن":"الاستقبال","م":"15 د","ف":"ص"},
                {"ن":"رياضيات","م":"30 د","ف":"ص"},
                {"ن":"تعبير شفوي","م":"30 د","ف":"ص"},
                {"ن":"تخطيط","م":"30 د","ف":"ص"},
                {"ن":"ت علمية وتكنولوجية","م":"30 د","ف":"ص"},
                {"ن":"ت مدنية","م":"30 د","ف":"ص"},
                {"ن":"تهيئة الخروج","م":"15 د","ف":"ص"},
                {"ن":"الاستقبال","م":"15 د","ف":"م"},
                {"ن":"مسرح وعرائس","م":"30 د","ف":"م"},
                {"ن":"تربية تشكيلية","م":"30 د","ف":"م"},
                {"ن":"ت بدنية","م":"30 د","ف":"م"},
                {"ن":"نهاية الخروج","م":"15 د","ف":"م"},
            ],
            "الثلاثاء":[
                {"ن":"الاستقبال","م":"15 د","ف":"ص"},
                {"ن":"تعبير شفوي","م":"30 د","ف":"ص"},
                {"ن":"مبادئ القراءة","م":"30 د","ف":"ص"},
                {"ن":"رياضيات","م":"30 د","ف":"ص"},
                {"ن":"ت إسلامية","م":"30 د","ف":"ص"},
                {"ن":"ت بدنية","م":"30 د","ف":"ص"},
                {"ن":"تهيئة الخروج","م":"15 د","ف":"ص"},
            ],
            "الأربعاء":[
                {"ن":"الاستقبال","م":"15 د","ف":"ص"},
                {"ن":"رياضيات","م":"30 د","ف":"ص"},
                {"ن":"مبادئ القراءة","م":"30 د","ف":"ص"},
                {"ن":"تخطيط","م":"30 د","ف":"ص"},
                {"ن":"ت علمية وتكنولوجية","م":"30 د","ف":"ص"},
                {"ن":"ت مدنية","م":"30 د","ف":"ص"},
                {"ن":"تهيئة الخروج","م":"15 د","ف":"ص"},
                {"ن":"الاستقبال","م":"15 د","ف":"م"},
                {"ن":"ت إيقاعية","م":"30 د","ف":"م"},
                {"ن":"موسيقى وإنشاد","م":"30 د","ف":"م"},
                {"ن":"ت بدنية","م":"30 د","ف":"م"},
                {"ن":"نهاية الخروج","م":"15 د","ف":"م"},
            ],
            "الخميس":[
                {"ن":"الاستقبال","م":"15 د","ف":"ص"},
                {"ن":"مبادئ القراءة","م":"30 د","ف":"ص"},
                {"ن":"رياضيات","م":"30 د","ف":"ص"},
                {"ن":"ت علمية وتكنولوجية","م":"30 د","ف":"ص"},
                {"ن":"ت إيقاعية","م":"30 د","ف":"ص"},
                {"ن":"موسيقى وإنشاد","م":"30 د","ف":"ص"},
                {"ن":"تهيئة الخروج","م":"15 د","ف":"ص"},
            ],
        },
    },
    "السنة 1 ابتدائي": {
        "روتيني":["الاستقبال","الاستراحة","تهيئة الخروج","نهاية الخروج"],
        "مجالات":{"اللغة العربية":"#1565C0","الرياضيات":"#C62828","التربية العلمية":"#2E7D32",
                   "التربية الاجتماعية":"#F57F17","التربية الفنية":"#6A1B9A","التربية البدنية":"#00838F"},
        "مواد":{
            "قراءة":{"مجال":"اللغة العربية","حصص":6},"تعبير شفوي":{"مجال":"اللغة العربية","حصص":2},
            "كتابة وخط":{"مجال":"اللغة العربية","حصص":3},"محفوظات":{"مجال":"اللغة العربية","حصص":1},
            "رياضيات":{"مجال":"الرياضيات","حصص":5},"تربية علمية":{"مجال":"التربية العلمية","حصص":2},
            "تربية إسلامية":{"مجال":"التربية الاجتماعية","حصص":2},"تربية مدنية":{"مجال":"التربية الاجتماعية","حصص":1},
            "تربية فنية":{"مجال":"التربية الفنية","حصص":2},"تربية موسيقية":{"مجال":"التربية الفنية","حصص":1},
            "تربية بدنية":{"مجال":"التربية البدنية","حصص":2},
        },"توقيت":{},
    },
    "السنة 2 ابتدائي": {
        "روتيني":["الاستقبال","الاستراحة","تهيئة الخروج","نهاية الخروج"],
        "مجالات":{"اللغة العربية":"#1565C0","الرياضيات":"#C62828","التربية العلمية":"#2E7D32",
                   "التربية الاجتماعية":"#F57F17","التربية الفنية":"#6A1B9A","التربية البدنية":"#00838F"},
        "مواد":{
            "قراءة":{"مجال":"اللغة العربية","حصص":5},"تعبير شفوي":{"مجال":"اللغة العربية","حصص":2},
            "كتابة وخط":{"مجال":"اللغة العربية","حصص":3},"إملاء":{"مجال":"اللغة العربية","حصص":1},
            "محفوظات":{"مجال":"اللغة العربية","حصص":1},"رياضيات":{"مجال":"الرياضيات","حصص":5},
            "تربية علمية":{"مجال":"التربية العلمية","حصص":2},"تربية إسلامية":{"مجال":"التربية الاجتماعية","حصص":2},
            "تربية مدنية":{"مجال":"التربية الاجتماعية","حصص":1},"تربية فنية":{"مجال":"التربية الفنية","حصص":2},
            "تربية موسيقية":{"مجال":"التربية الفنية","حصص":1},"تربية بدنية":{"مجال":"التربية البدنية","حصص":2},
        },"توقيت":{},
    },
    "السنة 3 ابتدائي": {
        "روتيني":["الاستقبال","الاستراحة","تهيئة الخروج","نهاية الخروج"],
        "مجالات":{"اللغة العربية":"#1565C0","اللغة الفرنسية":"#1976D2","الرياضيات":"#C62828",
                   "التربية العلمية":"#2E7D32","التربية الاجتماعية":"#F57F17",
                   "التربية الفنية":"#6A1B9A","التربية البدنية":"#00838F"},
        "مواد":{
            "قراءة":{"مجال":"اللغة العربية","حصص":4},"تعبير شفوي":{"مجال":"اللغة العربية","حصص":2},
            "كتابة وإملاء":{"مجال":"اللغة العربية","حصص":2},"قواعد":{"مجال":"اللغة العربية","حصص":1},
            "محفوظات":{"مجال":"اللغة العربية","حصص":1},"فرنسية":{"مجال":"اللغة الفرنسية","حصص":3},
            "رياضيات":{"مجال":"الرياضيات","حصص":5},"تربية علمية":{"مجال":"التربية العلمية","حصص":2},
            "تربية إسلامية":{"مجال":"التربية الاجتماعية","حصص":1},"تربية مدنية":{"مجال":"التربية الاجتماعية","حصص":1},
            "تاريخ وجغرافيا":{"مجال":"التربية الاجتماعية","حصص":1},"تربية فنية":{"مجال":"التربية الفنية","حصص":1},
            "تربية موسيقية":{"مجال":"التربية الفنية","حصص":1},"تربية بدنية":{"مجال":"التربية البدنية","حصص":2},
        },"توقيت":{},
    },
    "السنة 4 ابتدائي": {
        "روتيني":["الاستقبال","الاستراحة","تهيئة الخروج","نهاية الخروج"],
        "مجالات":{"اللغة العربية":"#1565C0","اللغة الفرنسية":"#1976D2","الرياضيات":"#C62828",
                   "التربية العلمية":"#2E7D32","التربية الاجتماعية":"#F57F17",
                   "التربية الفنية":"#6A1B9A","التربية البدنية":"#00838F"},
        "مواد":{
            "قراءة ودراسة نص":{"مجال":"اللغة العربية","حصص":3},"قواعد صرفية ونحوية":{"مجال":"اللغة العربية","حصص":2},
            "تعبير كتابي":{"مجال":"اللغة العربية","حصص":1},"تعبير شفوي":{"مجال":"اللغة العربية","حصص":1},
            "إملاء":{"مجال":"اللغة العربية","حصص":1},"محفوظات":{"مجال":"اللغة العربية","حصص":1},
            "فرنسية":{"مجال":"اللغة الفرنسية","حصص":3},"رياضيات":{"مجال":"الرياضيات","حصص":5},
            "تربية علمية":{"مجال":"التربية العلمية","حصص":2},"تربية إسلامية":{"مجال":"التربية الاجتماعية","حصص":1},
            "تربية مدنية":{"مجال":"التربية الاجتماعية","حصص":1},"تاريخ":{"مجال":"التربية الاجتماعية","حصص":1},
            "جغرافيا":{"مجال":"التربية الاجتماعية","حصص":1},"تربية فنية":{"مجال":"التربية الفنية","حصص":1},
            "تربية موسيقية":{"مجال":"التربية الفنية","حصص":1},"تربية بدنية":{"مجال":"التربية البدنية","حصص":2},
        },"توقيت":{},
    },
    "السنة 5 ابتدائي": {
        "روتيني":["الاستقبال","الاستراحة","تهيئة الخروج","نهاية الخروج"],
        "مجالات":{"اللغة العربية":"#1565C0","اللغة الفرنسية":"#1976D2","الرياضيات":"#C62828",
                   "التربية العلمية":"#2E7D32","التربية الاجتماعية":"#F57F17",
                   "التربية الفنية":"#6A1B9A","التربية البدنية":"#00838F"},
        "مواد":{
            "قراءة ودراسة نص":{"مجال":"اللغة العربية","حصص":3},"قواعد صرفية ونحوية":{"مجال":"اللغة العربية","حصص":2},
            "تعبير كتابي":{"مجال":"اللغة العربية","حصص":1},"تعبير شفوي":{"مجال":"اللغة العربية","حصص":1},
            "إملاء":{"مجال":"اللغة العربية","حصص":1},"محفوظات":{"مجال":"اللغة العربية","حصص":1},
            "فرنسية":{"مجال":"اللغة الفرنسية","حصص":3},"رياضيات":{"مجال":"الرياضيات","حصص":5},
            "تربية علمية":{"مجال":"التربية العلمية","حصص":2},"تربية إسلامية":{"مجال":"التربية الاجتماعية","حصص":1},
            "تربية مدنية":{"مجال":"التربية الاجتماعية","حصص":1},"تاريخ":{"مجال":"التربية الاجتماعية","حصص":1},
            "جغرافيا":{"مجال":"التربية الاجتماعية","حصص":1},"تربية فنية":{"مجال":"التربية الفنية","حصص":1},
            "تربية موسيقية":{"مجال":"التربية الفنية","حصص":1},"تربية بدنية":{"مجال":"التربية البدنية","حصص":2},
        },"توقيت":{},
    },
}


# ╔══════════════════════════════════════════════════╗
# ║              دوال مساعدة                         ║
# ╚══════════════════════════════════════════════════╝

DAYS = ["الأحد","الإثنين","الثلاثاء","الأربعاء","الخميس"]
HALF = {"الثلاثاء","الخميس"}

def cfg():
    lv = st.session_state.get('lv','قسم التحضيري')
    if 'cfgs' in st.session_state and lv in st.session_state.cfgs:
        return st.session_state.cfgs[lv]
    return LEVELS.get(lv, LEVELS['قسم التحضيري'])

def auto_sched(mats, rtn):
    sessions = []
    for s,i in mats.items():
        sessions.extend([s]*i["حصص"])
    sch = {}; idx = 0
    for day in DAYS:
        plan = []; full = day not in HALF
        plan.append({"ن":rtn[0] if rtn else "الاستقبال","م":"15 د","ف":"ص"})
        for _ in range(5):
            if idx < len(sessions):
                plan.append({"ن":sessions[idx],"م":"45 د","ف":"ص"}); idx+=1
        plan.append({"ن":"تهيئة الخروج","م":"15 د","ف":"ص"})
        if full:
            plan.append({"ن":rtn[0] if rtn else "الاستقبال","م":"15 د","ف":"م"})
            for _ in range(3):
                if idx < len(sessions):
                    plan.append({"ن":sessions[idx],"م":"45 د","ف":"م"}); idx+=1
            plan.append({"ن":"نهاية الخروج","م":"15 د","ف":"م"})
        sch[day] = plan
    return sch

def sched():
    c = cfg(); s = c.get("توقيت",{})
    return s if s else auto_sched(c["مواد"], c["روتيني"])

def mats(): return cfg().get("مواد",{})
def doms(): return cfg().get("مجالات",{})
def rtn(): return cfg().get("روتيني",[])
def dom4(a):
    m = mats()
    return m[a]["مجال"] if a in m else "—"
def dcol(d):
    dm = doms()
    return dm.get(d,"#666")
def dbdg(d):
    c=dcol(d)
    return f'<span style="display:inline-block;padding:2px 8px;border-radius:10px;font-size:.7rem;font-weight:600;background:{c}22;color:{c};border:1px solid {c}33;">{d}</span>'


# ╔══════════════════════════════════════════════════╗
# ║           معالجة الملفات                         ║
# ╚══════════════════════════════════════════════════╝

def compress_img(data, maxsz=1500, q=85):
    img = Image.open(BytesIO(data))
    if img.mode=='RGBA': img=img.convert('RGB')
    w,h=img.size
    if max(w,h)>maxsz:
        r=maxsz/max(w,h); img=img.resize((int(w*r),int(h*r)),Image.LANCZOS)
    buf=BytesIO(); img.save(buf,format='JPEG',quality=q); return buf.getvalue()

def img_b64(data):
    return base64.b64encode(compress_img(data)).decode()

def read_docx(fb):
    if not DOCX_OK: return ""
    doc=Document(BytesIO(fb)); lines=[]
    for p in doc.paragraphs:
        t=p.text.strip()
        if t: lines.append(t)
    for tbl in doc.tables:
        for row in tbl.rows:
            rt=[c.text.strip() for c in row.cells if c.text.strip()]
            if rt: lines.append(" | ".join(rt))
    return "\n".join(lines)

def read_pdf(fb):
    if not PDF_OK: return "", []
    doc=fitz.open(stream=fb,filetype="pdf")
    txt=[]; imgs=[]
    for i in range(len(doc)):
        pg=doc[i]; t=pg.get_text().strip()
        if t and len(t)>30:
            txt.append(t)
        else:
            pix=pg.get_pixmap(matrix=fitz.Matrix(2,2))
            ib=pix.tobytes("jpeg")
            imgs.append({"p":i+1,"b":ib,"b64":base64.b64encode(compress_img(ib)).decode()})
    doc.close()
    return "\n".join(txt), imgs

def pdf_to_imgs(fb):
    if not PDF_OK: return []
    doc=fitz.open(stream=fb,filetype="pdf"); imgs=[]
    for i in range(len(doc)):
        pix=doc[i].get_pixmap(matrix=fitz.Matrix(2,2))
        ib=pix.tobytes("jpeg")
        imgs.append({"p":i+1,"b":ib,"b64":base64.b64encode(compress_img(ib)).decode()})
    doc.close(); return imgs


# ╔══════════════════════════════════════════════════╗
# ║           الذكاء الاصطناعي                       ║
# ╚══════════════════════════════════════════════════╝

VMODELS = ["llama-3.2-90b-vision-preview","llama-3.2-11b-vision-preview"]
TMODELS = ["llama-3.3-70b-versatile","llama-3.1-70b-versatile","mixtral-8x7b-32768","gemma2-9b-it"]

def ai_prompt(lv, mats_cfg):
    sl = "\n".join([f"- {s}" for s in mats_cfg.keys()])
    return f"""أنت محلل وثائق تربوية جزائرية. المستوى: {lv}

استخرج كل الدروس. المواد المتوقعة (استخدم هذه الأسماء بالضبط):
{sl}

لكل درس: "مادة", "موضوع", "كفاءة" (أو "—")

أعد JSON فقط: [{{"مادة":"...","موضوع":"...","كفاءة":"..."}}]"""

def parse_json(raw):
    for fn in [
        lambda: json.loads(raw),
        lambda: json.loads(re.search(r'```(?:json)?\s*([\s\S]*?)```',raw).group(1)),
        lambda: json.loads(re.search(r'\[[\s\S]*?\]',raw).group(0)),
    ]:
        try:
            r=fn()
            if isinstance(r,list): return r
        except: pass
    return None

def to_db(parsed):
    db={}
    if not parsed: return db
    for it in parsed:
        if not isinstance(it,dict): continue
        s=it.get("مادة","").strip(); t=it.get("موضوع","—").strip(); k=it.get("كفاءة","—").strip()
        if s and t: db.setdefault(s,[]).append({"موضوع":t,"كفاءة":k})
    return db

def ai_text(text, key, model, lv, mc):
    if not GROQ_OK or not key: return None,None,"مفتاح API مطلوب"
    prompt = ai_prompt(lv, mc)
    try:
        c=Groq(api_key=key)
        r=c.chat.completions.create(model=model,messages=[
            {"role":"system","content":"محلل وثائق. أجب بـ JSON فقط."},
            {"role":"user","content":prompt+"\n\nالمحتوى:\n---\n"+text[:12000]+"\n---"}
        ],temperature=0.1,max_tokens=4000)
        raw=r.choices[0].message.content; p=parse_json(raw)
        if not p: return None,raw,"فشل تحليل JSON"
        return to_db(p),raw,None
    except Exception as e: return None,None,str(e)

def ai_vision(imgs_b64, key, model, lv, mc, prog=None):
    if not GROQ_OK or not key: return None,None,"مفتاح API مطلوب"
    prompt = ai_prompt(lv, mc) + "\n\nاقرأ النص العربي من الصورة."
    results=[]; raws=[]
    try:
        c=Groq(api_key=key)
        for i,b64 in enumerate(imgs_b64):
            if prog: prog(i,len(imgs_b64))
            r=c.chat.completions.create(model=model,messages=[{
                "role":"user","content":[
                    {"type":"text","text":prompt+f"\n(صورة {i+1}/{len(imgs_b64)})"},
                    {"type":"image_url","image_url":{"url":f"data:image/jpeg;base64,{b64}"}}
                ]
            }],temperature=0.1,max_tokens=4000)
            raw=r.choices[0].message.content; raws.append(raw)
            p=parse_json(raw)
            if p: results.extend(p)
        return to_db(results),"\n---\n".join(raws),None
    except Exception as e: return None,None,str(e)

def process_file(fb, fname, key, tmod, vmod, lv, mc, bar=None, msg=None):
    ext=fname.lower().rsplit('.',1)[-1] if '.' in fname else ''
    res={"db":None,"raw":None,"err":None,"method":"","imgs":[]}

    if ext=="docx":
        if msg: msg.text("📄 قراءة Word...")
        txt=read_docx(fb)
        if not txt:
            res["err"]="ملف فارغ أو python-docx غير متوفر"; return res
        res["method"]="📄 Word → 🧠 AI نصي"
        if msg: msg.text("🧠 تحليل...")
        db,raw,err=ai_text(txt,key,tmod,lv,mc)
        res["db"]=db;res["raw"]=raw;res["err"]=err

    elif ext=="pdf":
        if not PDF_OK:
            # بدون PyMuPDF → تحويل لصورة عبر Pillow
            res["err"]="مكتبة PDF غير متوفرة. ارفع الملف كصور بدلاً من ذلك."
            return res
        if msg: msg.text("📕 قراءة PDF...")
        txt,imgs=read_pdf(fb)
        if txt and len(txt)>100:
            res["method"]="📕 PDF نصي → 🧠 AI نصي"
            if msg: msg.text("🧠 تحليل نص...")
            db,raw,err=ai_text(txt,key,tmod,lv,mc)
            res["db"]=db;res["raw"]=raw;res["err"]=err
        elif imgs:
            res["imgs"]=imgs
            res["method"]=f"📕 PDF صور ({len(imgs)} ص) → 👁️ AI بصري"
            if msg: msg.text(f"👁️ قراءة {len(imgs)} صفحة...")
            def pg(i,t):
                if bar: bar.progress((i+1)/t)
                if msg: msg.text(f"👁️ صفحة {i+1}/{t}...")
            b64s=[im["b64"] for im in imgs]
            db,raw,err=ai_vision(b64s,key,vmod,lv,mc,pg)
            res["db"]=db;res["raw"]=raw;res["err"]=err
        else:
            aimgs=pdf_to_imgs(fb)
            if aimgs:
                res["imgs"]=aimgs; res["method"]=f"📕 PDF → صور ({len(aimgs)} ص)"
                b64s=[im["b64"] for im in aimgs]
                db,raw,err=ai_vision(b64s,key,vmod,lv,mc)
                res["db"]=db;res["raw"]=raw;res["err"]=err
            else:
                res["err"]="PDF فارغ"

    elif ext in ("jpg","jpeg","png","bmp","webp","tiff"):
        res["method"]="🖼️ صورة → 👁️ AI بصري"
        if msg: msg.text("👁️ قراءة الصورة...")
        b64=img_b64(fb)
        res["imgs"]=[{"p":1,"b":fb,"b64":b64}]
        db,raw,err=ai_vision([b64],key,vmod,lv,mc)
        res["db"]=db;res["raw"]=raw;res["err"]=err
    else:
        res["err"]=f"صيغة غير مدعومة: {ext}"
    return res


# ╔══════════════════════════════════════════════════╗
# ║           التوزيع + القالب + الحقن               ║
# ╚══════════════════════════════════════════════════╝

def distribute(raw_db):
    mc=mats(); dist={}; rep={}
    for s,info in mc.items():
        req=info["حصص"]; av=raw_db.get(s,[]); cnt=len(av)
        if cnt==0: dist[s]=[]; rep[s]={"req":req,"av":0,"ok":False}; continue
        result=[]
        if cnt>=req: result=[l.copy() for l in av[:req]]
        else:
            pp=req/cnt
            for i,les in enumerate(av):
                for _ in range(round((i+1)*pp)-round(i*pp)):
                    result.append(les.copy())
        dist[s]=result; rep[s]={"req":req,"av":cnt,"ok":bool(result)}
    return dist,rep

def _rtl(p):
    pPr=p._p.get_or_add_pPr(); pPr.append(pPr.makeelement(qn('w:bidi'),{}))

def _cell(c,t,bold=False,sz=10,col=None):
    c.text=""; p=c.paragraphs[0]; p.alignment=WD_ALIGN_PARAGRAPH.CENTER; _rtl(p)
    r=p.add_run(t); r.bold=bold; r.font.size=Pt(sz); r.font.name="Sakkal Majalla"
    if col: r.font.color.rgb=col
    rPr=r._r.get_or_add_rPr()
    rPr.append(rPr.makeelement(qn('w:rFonts'),{qn('w:cs'):'Sakkal Majalla'}))

def _shade(row,hx):
    for c in row.cells:
        tc=c._tc.get_or_add_tcPr()
        tc.append(tc.makeelement(qn('w:shd'),{qn('w:fill'):hx,qn('w:val'):'clear'}))

def _ptbl(doc,title,start,cnt):
    h=doc.add_paragraph(); h.alignment=WD_ALIGN_PARAGRAPH.CENTER; _rtl(h)
    r=h.add_run(title); r.bold=True; r.font.size=Pt(13); r.font.color.rgb=RGBColor(0,51,102)
    hdrs=['مؤشرات الكفاءة','عنوان الدرس','الميدان','النشاط','المدة']
    tbl=doc.add_table(rows=1+cnt,cols=5); tbl.style='Table Grid'; tbl.alignment=WD_TABLE_ALIGNMENT.CENTER
    ws=[Cm(5.5),Cm(5),Cm(3.5),Cm(3.5),Cm(2)]
    for row in tbl.rows:
        for i,w in enumerate(ws): row.cells[i].width=w
    hdr=tbl.rows[0]; _shade(hdr,"1F4E79")
    for i,t in enumerate(hdrs): _cell(hdr.cells[i],t,True,11,RGBColor(255,255,255))
    for j in range(cnt):
        n=start+j; dr=tbl.rows[1+j]
        if j%2==0: _shade(dr,"EDF2F9")
        for i,ph in enumerate([f'{{{{k_{n}}}}}',f'{{{{t_{n}}}}}',f'{{{{d_{n}}}}}',f'{{{{n_{n}}}}}',f'{{{{m_{n}}}}}']):
            _cell(dr.cells[i],ph,sz=9)

def mk_tmpl(day=None):
    if not DOCX_OK: return None
    lv=st.session_state.get('lv','')
    sc=sched()
    if day and day in sc:
        plan=sc[day]; mt=sum(1 for s in plan if s['ف']=='ص'); et=sum(1 for s in plan if s['ف']=='م')
    else: mt=7; et=5
    doc=Document()
    for sec in doc.sections: sec._sectPr.append(sec._sectPr.makeelement(qn('w:bidi'),{}))
    for t,sz,b in [('الجمهورية الجزائرية الديمقراطية الشعبية',12,True),('وزارة التربية الوطنية',11,False)]:
        p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; _rtl(p)
        r=p.add_run(t); r.bold=b; r.font.size=Pt(sz)
    tp=doc.add_paragraph(); tp.alignment=WD_ALIGN_PARAGRAPH.CENTER; _rtl(tp)
    tr=tp.add_run(f'الكراس اليومي — {lv}'); tr.bold=True; tr.font.size=Pt(16); tr.font.color.rgb=RGBColor(0,51,102)
    info=doc.add_table(rows=1,cols=3); info.alignment=WD_TABLE_ALIGNMENT.CENTER
    _cell(info.rows[0].cells[2],'اليوم : {{day}}',True,12)
    _cell(info.rows[0].cells[1],'التاريخ : {{date}}',sz=11)
    _cell(info.rows[0].cells[0],'الأسبوع : {{week}}',sz=11)
    doc.add_paragraph(''); _ptbl(doc,'☀ الفترة الصباحية',1,mt)
    if et>0: doc.add_paragraph(''); _ptbl(doc,'🌙 الفترة المسائية',mt+1,et)
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

def build(day,tmpl,dist_db,wn="",ds=""):
    if not DOCX_OK: return None,[],[]
    sc=sched(); plan=sc.get(day,[])
    if not plan: return None,[],[]
    rt=rtn(); doc=Document(BytesIO(tmpl))
    reps={"{{day}}":day,"{{date}}":ds,"{{week}}":wn}
    si=[]; warns=[]
    for i,s in enumerate(plan,1):
        act=s["ن"]; dur=s["م"]; per="صباحية" if s["ف"]=="ص" else "مسائية"
        dm=dom4(act)
        reps[f"{{{{m_{i}}}}}"]=dur; reps[f"{{{{n_{i}}}}}"]=act
        info={"رقم":i,"النشاط":act,"المدة":dur,"الفترة":per,"المجال":dm,"نوع":"روتيني","الموضوع":"—","الكفاءة":"—"}
        if act in rt:
            reps[f"{{{{t_{i}}}}}"]=reps[f"{{{{k_{i}}}}}"]=reps[f"{{{{d_{i}}}}}"]="—"
        elif act in dist_db and dist_db[act]:
            les=dist_db[act].pop(0); t=les.get('موضوع','—'); k=les.get('كفاءة','—')
            reps[f"{{{{t_{i}}}}}"]=t; reps[f"{{{{k_{i}}}}}"]=k; reps[f"{{{{d_{i}}}}}"]=dm
            info.update({"نوع":"تعليمي","الموضوع":t,"الكفاءة":k})
        else:
            reps[f"{{{{t_{i}}}}}"]="⚠ لا توجد مذكرة"; reps[f"{{{{k_{i}}}}}"]="⚠"
            reps[f"{{{{d_{i}}}}}"]=dm; info["نوع"]="ناقص"; warns.append(act)
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
    return buf.getvalue(),si,warns


# ╔══════════════════════════════════════════════════╗
# ║              واجهة Streamlit                     ║
# ╚══════════════════════════════════════════════════╝

st.set_page_config(page_title="الكراس اليومي 🎓",page_icon="🎓",layout="wide",initial_sidebar_state="expanded")

st.markdown("""<style>
.main .block-container{direction:rtl;text-align:right}
h1,h2,h3{text-align:center!important}
.card{padding:1rem;border-radius:12px;text-align:center;margin:.4rem 0;box-shadow:0 2px 8px rgba(0,0,0,.08)}
.card h4{margin:0 0 .3rem 0;font-size:.9rem}.card .num{font-size:2rem;font-weight:700}
.card-blue{background:linear-gradient(135deg,#1F4E79,#2E75B6);color:#fff}
.card-green{background:linear-gradient(135deg,#2E7D32,#43A047);color:#fff}
.card-amber{background:linear-gradient(135deg,#E65100,#FF9800);color:#fff}
.card-purple{background:linear-gradient(135deg,#4A148C,#7B1FA2);color:#fff}
.slot{display:flex;align-items:center;gap:.8rem;padding:.6rem 1rem;margin:.2rem 0;border-radius:8px;direction:rtl}
.slot-r{background:#f5f5f5;border-right:4px solid #9e9e9e}
.slot-t{background:#e3f2fd;border-right:4px solid #1565c0}
.slot-w{background:#fff3e0;border-right:4px solid #e65100}
.stDownloadButton>button{width:100%;background:linear-gradient(135deg,#1F4E79,#2E75B6)!important;color:#fff!important;border:none!important;border-radius:8px!important}
[data-testid="stSidebar"]{direction:rtl;text-align:right}
footer{visibility:hidden}
.ok-box{background:#e8f5e9;border:1px solid #4caf50;border-radius:10px;padding:1rem;text-align:center}
</style>""",unsafe_allow_html=True)

for k in ['db','gen','rep','raw','lv','cfgs','method']:
    if k not in st.session_state:
        if k=='gen': st.session_state[k]={}
        elif k=='lv': st.session_state[k]='قسم التحضيري'
        elif k=='cfgs': st.session_state[k]=copy.deepcopy(LEVELS)
        else: st.session_state[k]=None


# ══════════ الشريط الجانبي ══════════

with st.sidebar:
    st.markdown("## 🎓 المستوى")
    lvls=list(LEVELS.keys())
    sel=st.selectbox("المستوى",lvls,index=lvls.index(st.session_state.lv))
    if sel!=st.session_state.lv:
        st.session_state.lv=sel; st.session_state.db=None; st.session_state.gen={}
        st.rerun()

    c=cfg(); ts=sum(i["حصص"] for i in c["مواد"].values())
    st.info(f"📘 {len(c['مواد'])} مادة | 📖 {ts} حصة/أسبوع")

    st.markdown("---")
    wn=st.text_input("📅 الأسبوع",placeholder="10")
    ds=st.text_input("📆 التاريخ",placeholder="2024/12/01")

    st.markdown("---")
    st.markdown("### 🧠 Groq AI")
    gk=st.text_input("🔑 API Key",type="password")
    tm=st.selectbox("📝 نموذج نصي",TMODELS)
    vm=st.selectbox("👁️ نموذج بصري",VMODELS)

    st.markdown("---")

    # عرض حالة المكتبات
    st.markdown("### 📦 المكتبات")
    st.markdown(f"{'✅' if DOCX_OK else '❌'} python-docx")
    st.markdown(f"{'✅' if PDF_OK else '❌'} PyMuPDF (PDF)")
    st.markdown(f"{'✅' if GROQ_OK else '❌'} Groq AI")

    st.markdown("---")
    uploaded=st.file_uploader("📤 ملف المذكرات",type=FORMATS)
    st.caption("🎓 v7.1")


# معالجة الرفع
if uploaded:
    fb=uploaded.read()
    if st.session_state.get('_l')!=uploaded.name:
        st.session_state._fb=fb; st.session_state._l=uploaded.name
        st.session_state.db=None; st.session_state.gen={}
        st.session_state.raw=None; st.session_state.method=None

# العنوان
lv=st.session_state.lv
st.markdown(f"""<h1 style="background:linear-gradient(135deg,#1F4E79,#2E75B6);
-webkit-background-clip:text;-webkit-text-fill-color:transparent;
font-size:2.2rem;">🎓 الكراس اليومي — {lv}</h1>
<p style="text-align:center;color:#888;">📄 Word • 📕 PDF • 🖼️ صور • 🧠 AI</p>""",unsafe_allow_html=True)


# ══════════ التبويبات ══════════

tab1,tab2,tab3,tab4=st.tabs(["🧠 استخراج","📅 توليد","⚙️ إعداد","🗺️ مجالات"])

# ──── تبويب 1 ────
with tab1:
    if not uploaded:
        st.info("👆 ارفع ملف المذكرات (Word أو PDF أو صورة)")
    else:
        ext=uploaded.name.lower().rsplit('.',1)[-1]
        st.markdown(f"**📁 {uploaded.name}** ({len(st.session_state._fb)//1024} KB)")

        if ext in ('jpg','jpeg','png','bmp','webp'):
            st.image(st.session_state._fb,use_container_width=True)

        can=gk and GROQ_OK
        if not can: st.warning("🔑 أدخل مفتاح Groq API")

        if st.button("🧠 استخراج تلقائي",type="primary",use_container_width=True,disabled=not can):
            bar=st.progress(0); msg=st.empty()
            res=process_file(st.session_state._fb,uploaded.name,gk,tm,vm,lv,mats(),bar,msg)
            bar.progress(1.0); msg.empty()
            st.session_state.raw=res["raw"]; st.session_state.method=res["method"]
            if res["err"]:
                st.error(f"❌ {res['err']}")
            elif res["db"]:
                d,r=distribute(res["db"])
                st.session_state.db=d; st.session_state.rep=r; st.session_state.gen={}
                total=sum(len(v) for v in res["db"].values())
                st.success(f"✅ {total} درس!"); st.rerun()
            else:
                st.error("❌ لم يتم العثور على دروس")

        db=st.session_state.db
        if db:
            if st.session_state.method:
                st.caption(f"المسار: {st.session_state.method}")
            total=sum(len(v) for v in db.values())
            mc=mats(); matched=set(k for k,v in db.items() if v)&set(mc.keys())
            miss=set(mc.keys())-set(k for k,v in db.items() if v)
            c1,c2,c3=st.columns(3)
            for col,tl,nm,cl in [(c1,"📖",total,"card-green"),(c2,"✅",len(matched),"card-purple"),(c3,"⚠",len(miss),"card-amber")]:
                with col: st.markdown(f'<div class="card {cl}"><h4>{tl}</h4><div class="num">{nm}</div></div>',unsafe_allow_html=True)
            if miss: st.warning(f"⚠️ ناقصة: **{' ، '.join(miss)}**")
            for subj in sorted(db.keys()):
                les=db[subj]
                if not les: continue
                with st.expander(f"✅ {subj} — {len(les)} حصة"):
                    for j,l in enumerate(les,1):
                        st.markdown(f"**{j}.** 📝 {l.get('موضوع','—')}\n🎯 {l.get('كفاءة','—')}")
                        if j<len(les): st.divider()
            if st.session_state.raw:
                with st.expander("🧠 رد AI"): st.code(st.session_state.raw,language="json")

# ──── تبويب 2 ────
with tab2:
    db=st.session_state.db
    if not db or not any(db.values()):
        st.info("🧠 استخرج الدروس أولاً")
    elif not DOCX_OK:
        st.error("❌ مكتبة python-docx غير متوفرة")
    else:
        sc=sched(); days=list(sc.keys())
        st.markdown("### 📅 اختر الأيام")
        cols=st.columns(len(days)); sd=[]
        for i,d in enumerate(days):
            rt2=rtn(); tc=sum(1 for s in sc[d] if s["ن"] not in rt2)
            with cols[i]:
                if st.checkbox(f"{d} ({tc})",key=f"d_{d}"): sd.append(d)
        if st.checkbox("✅ الكل"): sd=days

        if sd and st.button(f"🚀 توليد {len(sd)} كراس",type="primary",use_container_width=True):
            wdb=copy.deepcopy(db); gen={}; bar=st.progress(0)
            for idx,d in enumerate(sd):
                bar.progress(idx/len(sd))
                tmpl=mk_tmpl(d)
                if tmpl:
                    result,info,warns=build(d,tmpl,wdb,wn,ds)
                    if result: gen[d]={'b':result,'s':info,'w':warns}
            bar.progress(1.0)
            st.session_state.gen=gen
            st.markdown(f'<div class="ok-box"><h3>✅ {len(gen)} كراس!</h3></div>',unsafe_allow_html=True)

        gf=st.session_state.gen
        if gf:
            st.markdown("### 📥 التحميل")
            dlc=st.columns(min(len(gf),5))
            for i,(d,data) in enumerate(gf.items()):
                with dlc[i%5]:
                    st.download_button(f"📄 {d}",data=data['b'],file_name=f"كراس_{d}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        use_container_width=True,key=f"dl_{d}")

            st.markdown("---\n### 👁️ معاينة")
            dp=st.selectbox("اليوم",list(gf.keys()))
            if dp:
                for s in gf[dp]['s']:
                    typ=s['نوع']
                    css={'روتيني':'slot-r','تعليمي':'slot-t','ناقص':'slot-w'}.get(typ,'slot-r')
                    ic={'روتيني':'⏰','تعليمي':'📖','ناقص':'⚠️'}.get(typ,'⏰')
                    dm=s.get('المجال','—'); bdg=dbdg(dm) if dm!='—' else ''
                    ext2=''
                    if typ=='تعليمي': ext2=f"<br><small>📝 {s['الموضوع']}</small><br><small>🎯 {s['الكفاءة']}</small>"
                    st.markdown(f'<div class="slot {css}"><span style="font-size:1.2rem">{ic}</span>'
                        f'<div style="flex:1"><strong>{s["النشاط"]}</strong> '
                        f'<span style="color:#888">({s["المدة"]})</span>{bdg}{ext2}</div></div>',
                        unsafe_allow_html=True)

# ──── تبويب 3 ────
with tab3:
    st.markdown(f"### ⚙️ {lv}")
    c2=cfg(); mc2=c2["مواد"]; dm2=c2["مجالات"]
    sd2=[{"المادة":n,"المجال":i["مجال"],"الحصص":i["حصص"]} for n,i in mc2.items()]
    edited=st.data_editor(sd2,num_rows="dynamic",column_config={
        "المادة":st.column_config.TextColumn("المادة",width="medium"),
        "المجال":st.column_config.SelectboxColumn("المجال",options=list(dm2.keys()),width="medium"),
        "الحصص":st.column_config.NumberColumn("الحصص",min_value=1,max_value=10,width="small"),
    },use_container_width=True,key="ed")

    ec1,ec2=st.columns(2)
    with ec1:
        if st.button("💾 حفظ",use_container_width=True,type="primary"):
            ns={}
            for r in edited:
                if r.get("المادة") and r.get("المجال"):
                    ns[r["المادة"]]={"مجال":r["المجال"],"حصص":r.get("الحصص",1)}
            if ns: st.session_state.cfgs[lv]["مواد"]=ns; st.success("✅")
    with ec2:
        if st.button("🔄 توليد توقيت",use_container_width=True):
            c3=cfg(); ns2=auto_sched(c3["مواد"],c3["روتيني"])
            st.session_state.cfgs[lv]["توقيت"]=ns2; st.success("✅")

    tot=sum(r.get("الحصص",0) for r in edited if r.get("المادة"))
    st.info(f"المجموع: **{tot}** حصة (المتاح: 34)")

# ──── تبويب 4 ────
with tab4:
    ca,cb=st.columns(2)
    with ca:
        st.markdown(f"### 🗺️ المجالات")
        mc3=mats(); dms2={}
        for s,i in mc3.items(): dms2.setdefault(i["مجال"],[]).append(s)
        for dm,subs in dms2.items():
            cl=dcol(dm); th=sum(mc3[s]["حصص"] for s in subs)
            st.markdown(f'<div style="border:2px solid {cl};border-radius:12px;padding:.8rem;margin:.4rem 0;">'
                f'<h4 style="color:{cl};text-align:center;">{dm} ({th}ح)</h4>',unsafe_allow_html=True)
            for s in subs:
                cnt=mc3[s]["حصص"]
                st.markdown(f'<div style="display:flex;align-items:center;gap:6px;margin:3px 0;direction:rtl;">'
                    f'<span style="min-width:130px;font-size:.85rem">{s}</span>'
                    f'<div style="background:{cl}44;border-radius:3px;height:16px;width:{cnt*14}px;"></div>'
                    f'<span style="color:{cl};font-weight:700;font-size:.85rem">{cnt}</span></div>',
                    unsafe_allow_html=True)
            st.markdown('</div>',unsafe_allow_html=True)
    with cb:
        st.markdown(f"### 📊 التوقيت")
        sc2=sched()
        if sc2:
            vd=st.selectbox("اليوم",list(sc2.keys()),key="sv")
            if vd:
                rt2=rtn()
                for pn,pv in [("☀️ صباح","ص"),("🌙 مساء","م")]:
                    sl=[s for s in sc2[vd] if s["ف"]==pv]
                    if not sl: continue
                    st.markdown(f"**{pn}**")
                    rows=[{"#":j,"النشاط":s['ن'],"المدة":s['م'],
                           "المجال":dom4(s['ن']) if s['ن'] not in rt2 else "—"}
                          for j,s in enumerate(sl,1)]
                    st.dataframe(rows,use_container_width=True,hide_index=True)
        else:
            st.warning("اضغط 'توليد توقيت' في تبويب الإعداد")
