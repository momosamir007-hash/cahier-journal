# -*- coding: utf-8 -*-
"""🎓 الكراس اليومي — قسم التحضيري"""

import streamlit as st
import copy
from engine import (
    weekly_schedule,
    ROUTINE_ACTIVITIES,
    DOMAIN_MAPPING,
    SUBJECT_WEEKLY_COUNT,
    extract_all_lessons,
    create_template_bytes,
    build_daily_planner_bytes,
    get_all_teaching_subjects,
    get_domain_for,
)
from engine.schedule import verify_schedule

# ═══════════════════════════════════════
#  Page Config
# ═══════════════════════════════════════

st.set_page_config(
    page_title="الكراس اليومي 🎓",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ═══════════════════════════════════════
#  CSS
# ═══════════════════════════════════════

st.markdown("""
<style>
    .main .block-container {
        direction: rtl;
        text-align: right;
    }
    h1, h2, h3 {
        text-align: center !important;
    }

    /* بطاقات ملونة */
    .card {
        padding: 1rem 1.2rem;
        border-radius: 12px;
        text-align: center;
        margin: 0.4rem 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    }
    .card h4 { margin: 0 0 0.3rem 0; font-size: 0.9rem; }
    .card .num { font-size: 2rem; font-weight: 700; }
    .card-blue  { background: linear-gradient(135deg,#1F4E79,#2E75B6); color:#fff; }
    .card-green { background: linear-gradient(135deg,#2E7D32,#43A047); color:#fff; }
    .card-amber { background: linear-gradient(135deg,#E65100,#FF9800); color:#fff; }
    .card-purple{ background: linear-gradient(135deg,#4A148C,#7B1FA2); color:#fff; }

    /* حصة */
    .slot {
        display: flex; align-items: center; gap: 0.8rem;
        padding: 0.7rem 1rem; margin: 0.3rem 0;
        border-radius: 8px; direction: rtl;
    }
    .slot-routine { background:#f5f5f5; border-right:4px solid #9e9e9e; }
    .slot-teach   { background:#e3f2fd; border-right:4px solid #1565c0; }
    .slot-warn    { background:#fff3e0; border-right:4px solid #e65100; }

    /* مجال */
    .domain-badge {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
    }

    .stDownloadButton > button {
        width: 100%;
        background: linear-gradient(135deg,#1F4E79,#2E75B6) !important;
        color: #fff !important; border: none !important;
        border-radius: 8px !important;
    }
    .stDownloadButton > button:hover {
        transform: scale(1.02) !important;
    }

    [data-testid="stSidebar"] { direction: rtl; text-align: right; }
    footer { visibility: hidden; }

    .ok-box {
        background: #e8f5e9; border: 1px solid #4caf50;
        border-radius: 10px; padding: 1rem; text-align: center;
    }
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════
#  ألوان المجالات
# ═══════════════════════════════════════

DOMAIN_COLORS = {
    "المجال اللغوي":                "#1565C0",
    "المجال الرياضي":               "#C62828",
    "المجال العلمي":                "#2E7D32",
    "المجال الاجتماعي":             "#F57F17",
    "المجال الفني":                 "#6A1B9A",
    "المجال البدني والإيقاعي":      "#00838F",
}


def domain_badge(domain):
    color = DOMAIN_COLORS.get(domain, "#666")
    return (
        f'<span class="domain-badge" '
        f'style="background:{color}22;color:{color};'
        f'border:1px solid {color}44;">{domain}</span>'
    )


# ═══════════════════════════════════════
#  Session State
# ═══════════════════════════════════════

if 'lessons_db' not in st.session_state:
    st.session_state.lessons_db = None
if 'template_bytes' not in st.session_state:
    st.session_state.template_bytes = None
if 'generated_files' not in st.session_state:
    st.session_state.generated_files = {}


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
    uploaded = st.file_uploader(
        "اختر ملف .docx",
        type=["docx"],
        help="ارفع ملف المذكرات الأسبوعية",
    )

    st.markdown("---")
    st.markdown("### 📥 القالب")
    if st.button("🔨 إنشاء قالب جديد", use_container_width=True):
        st.session_state.template_bytes = create_template_bytes()
        st.success("✅ تم!")

    if st.session_state.template_bytes:
        st.download_button(
            "📄 تحميل template.docx",
            data=st.session_state.template_bytes,
            file_name="template.docx",
            mime="application/vnd.openxmlformats-officedocument"
                 ".wordprocessingml.document",
            use_container_width=True,
        )

    st.markdown("---")

    # التحقق من التوقيت
    errors, counts = verify_schedule()
    if errors:
        st.error("❌ خلل في التوقيت!")
        for e in errors:
            st.text(e)
    else:
        st.success(f"✅ التوقيت سليم ({sum(counts.values())} حصة)")

    st.caption("🎓 الكراس اليومي v3.0")


# ═══════════════════════════════════════
#  معالجة الرفع
# ═══════════════════════════════════════

if uploaded:
    file_bytes = uploaded.read()
    if st.session_state.get('_last') != uploaded.name:
        with st.spinner("⏳ جارٍ الاستخراج..."):
            db = extract_all_lessons(file_bytes)
            st.session_state.lessons_db = db
            st.session_state._last = uploaded.name
            st.session_state.generated_files = {}
        if db:
            st.toast("✅ تم استخراج الدروس!", icon="📚")
        else:
            st.error("❌ لم يتم العثور على دروس!")

    if not st.session_state.template_bytes:
        st.session_state.template_bytes = create_template_bytes()


# ═══════════════════════════════════════
#  العنوان الرئيسي
# ═══════════════════════════════════════

st.markdown("""
<h1 style="background:linear-gradient(135deg,#1F4E79,#2E75B6);
-webkit-background-clip:text;-webkit-text-fill-color:transparent;
font-size:2.5rem;">🎓 الكراس اليومي</h1>
<p style="text-align:center;color:#888;">
أتمتة إعداد الكراس اليومي — قسم التحضيري
</p>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════
#  التبويبات
# ═══════════════════════════════════════

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📚 الدروس",
    "📅 توليد",
    "👁️ معاينة",
    "📊 التوقيت",
    "🗺️ المجالات",
])


# ──────────────────────────────────────
#  تبويب 1: الدروس المستخرجة
# ──────────────────────────────────────

with tab1:
    db = st.session_state.lessons_db

    if not db:
        st.info("👆 ارفع ملف المذكرات من الشريط الجانبي")
        with st.expander("📖 تعليمات"):
            st.markdown("""
            **الأنماط المطلوبة في ملف المذكرات:**
            ```
            النشاط : تعبير شفوي
            الموضوع : الصفات
            مؤشر الكفاءة : يستعمل الصفات في جمل
            ```
            """)
    else:
        total = sum(len(v) for v in db.values())
        subjects = get_all_teaching_subjects()
        matched = subjects & set(db.keys())
        missing = subjects - set(db.keys())

        c1, c2, c3, c4 = st.columns(4)
        cards = [
            (c1, "📘 المواد", len(db), "card-blue"),
            (c2, "📖 الدروس", total, "card-green"),
            (c3, "✅ متطابقة", len(matched), "card-purple"),
            (c4, "⚠ ناقصة", len(missing), "card-amber"),
        ]
        for col, title, num, cls in cards:
            with col:
                st.markdown(
                    f'<div class="card {cls}">'
                    f'<h4>{title}</h4>'
                    f'<div class="num">{num}</div></div>',
                    unsafe_allow_html=True,
                )

        if missing:
            st.warning(
                f"⚠️ مواد ناقصة: **{' ، '.join(missing)}**\n\n"
                "عدّل NAME_MAPPING أو أضفها للمذكرات"
            )

        st.markdown("---")

        for subj in sorted(db.keys()):
            lessons = db[subj]
            domain = get_domain_for(subj)
            icon = "✅" if subj in subjects else "ℹ️"

            with st.expander(
                f"{icon} {subj} — {len(lessons)} درس — {domain}"
            ):
                for j, les in enumerate(lessons, 1):
                    st.markdown(
                        f"**{j}.** 📝 {les.get('موضوع','—')}\n\n"
                        f"🎯 {les.get('كفاءة','—')}"
                    )
                    if j < len(lessons):
                        st.divider()


# ──────────────────────────────────────
#  تبويب 2: توليد الكراسات
# ──────────────────────────────────────

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
            teach_count = sum(
                1 for s in plan if s["النشاط"] not in ROUTINE_ACTIVITIES
            )
            has_evening = any(
                s.get("الفترة") == "مسائية" for s in plan
            )
            label = f"{d}\n({teach_count} حصة)"
            if not has_evening:
                label += "\n☀ صباح فقط"

            with cols[i]:
                if st.checkbox(label, key=f"d_{d}"):
                    selected.append(d)

        all_check = st.checkbox("✅ الكل")
        if all_check:
            selected = days

        st.markdown("---")

        if selected and st.button(
            f"🚀 توليد {len(selected)} كراس",
            type="primary",
            use_container_width=True,
        ):
            tmpl = st.session_state.template_bytes
            if not tmpl:
                tmpl = create_template_bytes()
                st.session_state.template_bytes = tmpl

            wdb = copy.deepcopy(db)
            gen = {}
            bar = st.progress(0)
            msg = st.empty()

            for idx, d in enumerate(selected):
                msg.text(f"⏳ {d}...")
                bar.progress(idx / len(selected))

                result, info, warns = build_daily_planner_bytes(
                    day=d,
                    template_bytes=tmpl,
                    schedule=weekly_schedule,
                    lessons_db=wdb,
                    week_num=week_num,
                    date_str=date_str,
                )
                if result:
                    gen[d] = {
                        'bytes': result,
                        'sessions': info,
                        'warnings': warns,
                    }

            bar.progress(1.0)
            msg.empty()
            st.session_state.generated_files = gen

            st.markdown(
                f'<div class="ok-box"><h3>✅ تم توليد '
                f'{len(gen)} كراس!</h3></div>',
                unsafe_allow_html=True,
            )

        # أزرار التحميل
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
                        mime="application/vnd.openxmlformats-"
                             "officedocument.wordprocessingml.document",
                        use_container_width=True,
                        key=f"dl_{d}",
                    )
                    if w:
                        st.caption(f"⚠ {', '.join(set(w))}")


# ──────────────────────────────────────
#  تبويب 3: معاينة
# ──────────────────────────────────────

with tab3:
    gf = st.session_state.generated_files

    if not gf:
        st.info("📅 ولّد الكراسات أولاً")
    else:
        day_pick = st.selectbox("اختر اليوم", list(gf.keys()))

        if day_pick:
            data = gf[day_pick]
            sessions = data['sessions']

            st.markdown(f"## 📋 كراس يوم {day_pick}")

            if data.get('warnings'):
                st.warning(
                    f"⚠️ بدون مذكرة: "
                    f"**{', '.join(set(data['warnings']))}**"
                )

            morning = [s for s in sessions if s['الفترة'] == 'صباحية']
            evening = [s for s in sessions if s['الفترة'] == 'مسائية']

            for pname, plist in [
                ("☀️ الفترة الصباحية", morning),
                ("🌙 الفترة المسائية", evening),
            ]:
                if not plist:
                    continue

                st.markdown(f"### {pname}")

                for s in plist:
                    typ = s['نوع']
                    css = {
                        'روتيني': 'slot-routine',
                        'تعليمي': 'slot-teach',
                        'ناقص':   'slot-warn',
                    }.get(typ, 'slot-routine')

                    icon = {'روتيني':'⏰','تعليمي':'📖','ناقص':'⚠️'}.get(typ,'⏰')

                    domain = s.get('المجال', '—')
                    badge = domain_badge(domain) if domain != '—' else ''

                    extra = ''
                    if typ == 'تعليمي':
                        extra = (
                            f"<br><small>📝 {s['الموضوع']}</small>"
                            f"<br><small>🎯 {s['الكفاءة']}</small>"
                        )
                    elif typ == 'ناقص':
                        extra = "<br><small>⚠ لا توجد مذكرة</small>"

                    st.markdown(f"""
                    <div class="slot {css}">
                        <span style="font-size:1.3rem">{icon}</span>
                        <div style="flex:1">
                            <strong>{s['النشاط']}</strong>
                            <span style="color:#888">({s['المدة']})</span>
                            {badge}
                            {extra}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)


# ──────────────────────────────────────
#  تبويب 4: التوقيت الأسبوعي
# ──────────────────────────────────────

with tab4:
    st.markdown("### 📊 التوقيت الأسبوعي")

    view_day = st.selectbox(
        "اختر اليوم",
        list(weekly_schedule.keys()),
        key="sched_day",
    )

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
                domain = get_domain_for(act) if not is_r else "—"
                rows.append({
                    "#": j,
                    "النشاط": act,
                    "المدة": s['المدة'],
                    "المجال": domain,
                    "النوع": "🔄" if is_r else "📖",
                })

            st.dataframe(
                rows,
                use_container_width=True,
                hide_index=True,
            )

    # إحصائيات
    st.markdown("---")
    st.markdown("#### 📈 توزيع الحصص")

    _, counts = verify_schedule()
    for subj, expected in SUBJECT_WEEKLY_COUNT.items():
        actual = counts.get(subj, 0)
        ok = "✅" if actual == expected else "❌"
        domain = get_domain_for(subj)
        st.markdown(
            f"{ok} **{subj}** — "
            f"{actual}/{expected} حصة — "
            f"{domain_badge(domain)}",
            unsafe_allow_html=True,
        )


# ──────────────────────────────────────
#  تبويب 5: خريطة المجالات
# ──────────────────────────────────────

with tab5:
    st.markdown("### 🗺️ المجالات التعليمية")

    # تجميع المواد حسب المجال
    domains = {}
    for subj, dom in DOMAIN_MAPPING.items():
        domains.setdefault(dom, []).append(subj)

    cols5 = st.columns(2)

    for i, (dom, subjects) in enumerate(domains.items()):
        color = DOMAIN_COLORS.get(dom, "#666")
        total_h = sum(SUBJECT_WEEKLY_COUNT.get(s, 0) for s in subjects)

        with cols5[i % 2]:
            st.markdown(
                f'<div style="border:2px solid {color};'
                f'border-radius:12px;padding:1rem;margin:0.5rem 0;">'
                f'<h4 style="color:{color};text-align:center;">'
                f'{dom} ({total_h} حصة/أسبوع)</h4>',
                unsafe_allow_html=True,
            )

            for s in subjects:
                cnt = SUBJECT_WEEKLY_COUNT.get(s, 0)
                bar_width = cnt * 12
                st.markdown(
                    f'<div style="display:flex;align-items:center;'
                    f'gap:8px;margin:4px 0;direction:rtl;">'
                    f'<span style="min-width:140px">{s}</span>'
                    f'<div style="background:{color}44;'
                    f'border-radius:4px;height:20px;'
                    f'width:{bar_width}px;"></div>'
                    f'<span style="color:{color};font-weight:700;">'
                    f'{cnt}</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

            st.markdown('</div>', unsafe_allow_html=True)

    # ملخص كلي
    st.markdown("---")
    grand = sum(SUBJECT_WEEKLY_COUNT.values())
    st.markdown(
        f'<div class="card card-blue">'
        f'<h4>المجموع الأسبوعي</h4>'
        f'<div class="num">{grand} حصة تعليمية</div>'
        f'<small>{len(SUBJECT_WEEKLY_COUNT)} مادة في '
        f'{len(domains)} مجالات</small></div>',
        unsafe_allow_html=True,
    )
