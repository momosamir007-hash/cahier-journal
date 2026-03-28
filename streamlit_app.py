# -*- coding: utf-8 -*-
"""
🎓 الكراس اليومي - قسم التحضيري
تطبيق Streamlit لأتمتة إعداد الكراس اليومي
"""

import streamlit as st
import copy
from engine import (
    weekly_schedule,
    ROUTINE_ACTIVITIES,
    extract_all_lessons,
    create_template_bytes,
    build_daily_planner_bytes,
)
from engine.schedule import get_all_teaching_subjects

# ═══════════════════════════════════════
#  إعدادات الصفحة
# ═══════════════════════════════════════

st.set_page_config(
    page_title="الكراس اليومي 🎓",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ═══════════════════════════════════════
#  CSS مخصص للعربية
# ═══════════════════════════════════════

st.markdown("""
<style>
    /* اتجاه عربي */
    .main .block-container {
        direction: rtl;
        text-align: right;
    }

    /* العناوين */
    h1, h2, h3 {
        text-align: center !important;
        font-family: 'Sakkal Majalla', 'Arial', sans-serif !important;
    }

    /* بطاقات */
    .metric-card {
        background: linear-gradient(135deg, #1F4E79, #2E75B6);
        color: white;
        padding: 1.2rem;
        border-radius: 12px;
        text-align: center;
        margin: 0.5rem 0;
        box-shadow: 0 4px 15px rgba(31, 78, 121, 0.3);
    }
    .metric-card h3 {
        color: white !important;
        margin: 0;
        font-size: 1rem;
    }
    .metric-card .number {
        font-size: 2.2rem;
        font-weight: bold;
        margin: 0.3rem 0;
    }

    /* جدول الحصص */
    .session-row {
        display: flex;
        align-items: center;
        padding: 0.6rem 1rem;
        margin: 0.3rem 0;
        border-radius: 8px;
        direction: rtl;
        gap: 1rem;
    }
    .session-routine {
        background: #f0f2f6;
        border-right: 4px solid #9e9e9e;
    }
    .session-teach {
        background: #e8f4fd;
        border-right: 4px solid #1F4E79;
    }
    .session-warn {
        background: #fff3e0;
        border-right: 4px solid #ff9800;
    }

    /* الشريط الجانبي */
    .css-1d391kg, [data-testid="stSidebar"] {
        direction: rtl;
        text-align: right;
    }

    /* أزرار التحميل */
    .stDownloadButton > button {
        width: 100%;
        background: linear-gradient(135deg, #1F4E79, #2E75B6) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.7rem !important;
        font-size: 1rem !important;
        transition: transform 0.2s !important;
    }
    .stDownloadButton > button:hover {
        transform: scale(1.02) !important;
    }

    /* الـ Expander */
    .streamlit-expanderHeader {
        direction: rtl;
        text-align: right;
        font-size: 1.1rem;
    }

    /* تحسين المظهر العام */
    .success-box {
        background: #e8f5e9;
        border: 1px solid #4caf50;
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
        margin: 1rem 0;
    }

    /* إخفاء footer */
    footer {visibility: hidden;}

    /* تنسيق الـ tabs */
    .stTabs [data-baseweb="tab-list"] {
        direction: rtl;
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        font-size: 1rem;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════
#  الحالة (Session State)
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

    # رقم الأسبوع
    week_num = st.text_input(
        "📅 رقم الأسبوع",
        placeholder="مثال: 10",
        key="week_num"
    )

    # التاريخ
    date_str = st.text_input(
        "📆 التاريخ",
        placeholder="مثال: 2024/12/01",
        key="date_str"
    )

    st.markdown("---")

    # رفع ملف المذكرات
    st.markdown("### 📤 رفع ملف المذكرات")
    uploaded = st.file_uploader(
        "اختر ملف المذكرات (.docx)",
        type=["docx"],
        help="ارفع ملف المذكرات الأسبوعية بصيغة Word",
        key="memo_upload"
    )

    st.markdown("---")

    # تحميل القالب الفارغ
    st.markdown("### 📥 تحميل القالب")
    if st.button("🔨 إنشاء القالب", use_container_width=True):
        st.session_state.template_bytes = create_template_bytes()
        st.success("✅ تم إنشاء القالب!")

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
    st.markdown("""
    <div style="text-align:center; color:#666; font-size:0.85rem;">
        🎓 الكراس اليومي v2.0<br>
        قسم التحضيري
    </div>
    """, unsafe_allow_html=True)


# ═══════════════════════════════════════
#  المحتوى الرئيسي
# ═══════════════════════════════════════

st.markdown("""
<h1 style="
    background: linear-gradient(135deg, #1F4E79, #2E75B6);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 2.5rem;
    margin-bottom: 0;
">🎓 الكراس اليومي</h1>
<p style="text-align:center; color:#666; font-size:1.1rem;">
    أتمتة إعداد الكراس اليومي لقسم التحضيري
</p>
""", unsafe_allow_html=True)


# ── معالجة رفع الملف ──
if uploaded:
    file_bytes = uploaded.read()

    # استخراج تلقائي عند رفع ملف جديد
    if (st.session_state.get('_last_file') != uploaded.name):
        with st.spinner("⏳ جارٍ استخراج الدروس..."):
            db = extract_all_lessons(file_bytes)
            st.session_state.lessons_db = db
            st.session_state._last_file = uploaded.name
            st.session_state.generated_files = {}

        if db:
            st.toast("✅ تم استخراج الدروس بنجاح!", icon="📚")
        else:
            st.error("❌ لم يتم العثور على دروس في الملف!")

    # إنشاء القالب تلقائياً إذا لم يكن موجوداً
    if not st.session_state.template_bytes:
        st.session_state.template_bytes = create_template_bytes()


# ═══════════════════════════════════════
#  التبويبات الرئيسية
# ═══════════════════════════════════════

tab1, tab2, tab3, tab4 = st.tabs([
    "📚 الدروس المستخرجة",
    "📅 توليد الكراسات",
    "👁️ المعاينة",
    "📊 التوقيت الأسبوعي",
])


# ══════════════════════════════════════════════
#  التبويب 1: عرض الدروس المستخرجة
# ══════════════════════════════════════════════

with tab1:
    db = st.session_state.lessons_db

    if not db:
        st.info("👆 ارفع ملف المذكرات من الشريط الجانبي للبدء")

        # عرض تعليمات
        with st.expander("📖 كيف يعمل التطبيق؟"):
            st.markdown("""
            ### خطوات الاستخدام:
            1. **ارفع** ملف المذكرات الأسبوعية من الشريط الجانبي
            2. **راجع** الدروس المستخرجة في هذا التبويب
            3. **اختر** الأيام المطلوبة من تبويب "توليد الكراسات"
            4. **حمّل** الملفات الجاهزة

            ### الأنماط المطلوبة في المذكرات:
            ```
            النشاط : تعبير شفوي
            الموضوع : الصفات
            مؤشر الكفاءة : يستعمل الصفات في جمل
            ```
            """)
    else:
        # إحصائيات
        total_lessons = sum(len(v) for v in db.values())
        total_subjects = len(db)
        schedule_subjects = get_all_teaching_subjects()
        matched = schedule_subjects & set(db.keys())
        missing = schedule_subjects - set(db.keys())

        # بطاقات الإحصائيات
        c1, c2, c3, c4 = st.columns(4)

        with c1:
            st.markdown(f"""
            <div class="metric-card">
                <h3>📘 المواد</h3>
                <div class="number">{total_subjects}</div>
            </div>
            """, unsafe_allow_html=True)

        with c2:
            st.markdown(f"""
            <div class="metric-card">
                <h3>📖 الدروس</h3>
                <div class="number">{total_lessons}</div>
            </div>
            """, unsafe_allow_html=True)

        with c3:
            st.markdown(f"""
            <div class="metric-card">
                <h3>✅ متطابقة</h3>
                <div class="number">{len(matched)}</div>
            </div>
            """, unsafe_allow_html=True)

        with c4:
            color = "#ff9800" if missing else "#4caf50"
            st.markdown(f"""
            <div class="metric-card"
                 style="background:linear-gradient(135deg,
                        {color}, {color}dd);">
                <h3>⚠ ناقصة</h3>
                <div class="number">{len(missing)}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")

        # تحذير المواد الناقصة
        if missing:
            st.warning(
                f"⚠️ مواد في التوقيت لم توجد في المذكرات: "
                f"**{' ، '.join(missing)}**"
            )

        # عرض الدروس حسب المادة
        for subject in sorted(db.keys()):
            lessons = db[subject]
            icon = "✅" if subject in schedule_subjects else "ℹ️"

            with st.expander(
                f"{icon} {subject} — {len(lessons)} درس",
                expanded=False
            ):
                for j, lesson in enumerate(lessons, 1):
                    topic = lesson.get('موضوع', '—')
                    indic = lesson.get('كفاءة', '—')

                    st.markdown(f"""
                    **الدرس {j}:**
                    - 📝 الموضوع: `{topic}`
                    - 🎯 الكفاءة: `{indic}`
                    """)
                    if j < len(lessons):
                        st.divider()


# ══════════════════════════════════════════════
#  التبويب 2: توليد الكراسات
# ══════════════════════════════════════════════

with tab2:
    db = st.session_state.lessons_db

    if not db:
        st.info("👆 ارفع ملف المذكرات أولاً")
    else:
        st.markdown("### 📅 اختر الأيام لتوليد الكراسات")

        days = list(weekly_schedule.keys())

        col_days = st.columns(len(days))
        selected_days = []
        for i, day in enumerate(days):
            with col_days[i]:
                count = len(weekly_schedule[day])
                if st.checkbox(
                    f"{day}\n({count} حصة)",
                    key=f"day_{day}"
                ):
                    selected_days.append(day)

        # زر تحديد الكل
        if st.checkbox("✅ تحديد الكل", key="select_all"):
            selected_days = days

        st.markdown("---")

        if selected_days:
            if st.button(
                f"🚀 توليد {len(selected_days)} كراس",
                type="primary",
                use_container_width=True,
            ):
                template = st.session_state.template_bytes
                if not template:
                    template = create_template_bytes()
                    st.session_state.template_bytes = template

                working_db = copy.deepcopy(db)
                generated = {}
                progress = st.progress(0)
                status = st.empty()

                for idx, day in enumerate(selected_days):
                    status.text(f"⏳ جارٍ توليد كراس {day}...")
                    progress.progress(
                        (idx) / len(selected_days)
                    )

                    result, sessions, warns = build_daily_planner_bytes(
                        day=day,
                        template_bytes=template,
                        schedule=weekly_schedule,
                        lessons_db=working_db,
                        week_num=week_num,
                        date_str=date_str,
                    )

                    if result:
                        generated[day] = {
                            'bytes': result,
                            'sessions': sessions,
                            'warnings': warns,
                        }

                progress.progress(1.0)
                status.empty()

                st.session_state.generated_files = generated

                st.markdown(f"""
                <div class="success-box">
                    <h3>✅ تم بنجاح!</h3>
                    <p>تم توليد {len(generated)} كراس جاهز للتحميل</p>
                </div>
                """, unsafe_allow_html=True)

        # عرض أزرار التحميل
        if st.session_state.generated_files:
            st.markdown("### 📥 تحميل الكراسات")

            cols = st.columns(
                min(len(st.session_state.generated_files), 3)
            )

            for i, (day, data) in enumerate(
                st.session_state.generated_files.items()
            ):
                with cols[i % 3]:
                    warns = data.get('warnings', [])
                    icon = "⚠️" if warns else "📄"

                    st.download_button(
                        f"{icon} كراس {day}",
                        data=data['bytes'],
                        file_name=f"كراس_{day}.docx",
                        mime=(
                            "application/vnd.openxmlformats-"
                            "officedocument.wordprocessingml.document"
                        ),
                        use_container_width=True,
                        key=f"dl_{day}",
                    )

                    if warns:
                        st.caption(
                            f"⚠ بدون مذكرة: {', '.join(set(warns))}"
                        )


# ══════════════════════════════════════════════
#  التبويب 3: المعاينة
# ══════════════════════════════════════════════

with tab3:
    gen = st.session_state.generated_files

    if not gen:
        st.info("📅 قم بتوليد الكراسات أولاً من التبويب السابق")
    else:
        day_choice = st.selectbox(
            "اختر اليوم للمعاينة",
            list(gen.keys()),
            key="preview_day"
        )

        if day_choice:
            data = gen[day_choice]
            sessions = data['sessions']
            warnings = data.get('warnings', [])

            st.markdown(f"## 📋 كراس يوم {day_choice}")

            if warnings:
                st.warning(
                    f"⚠️ مواد بدون مذكرة: "
                    f"**{', '.join(set(warnings))}**"
                )

            # فصل الفترات
            morning = [s for s in sessions if s['الفترة'] == 'صباحية']
            evening = [s for s in sessions if s['الفترة'] == 'مسائية']

            for period_name, period_sessions in [
                ("☀️ الفترة الصباحية", morning),
                ("🌙 الفترة المسائية", evening),
            ]:
                if not period_sessions:
                    continue

                st.markdown(f"### {period_name}")

                for s in period_sessions:
                    typ = s['نوع']

                    if typ == 'روتيني':
                        css = "session-routine"
                        icon = "⏰"
                    elif typ == 'ناقص':
                        css = "session-warn"
                        icon = "⚠️"
                    else:
                        css = "session-teach"
                        icon = "📖"

                    topic = s.get('الموضوع', '—')
                    indic = s.get('الكفاءة', '—')

                    st.markdown(f"""
                    <div class="session-row {css}">
                        <span style="font-size:1.3rem">{icon}</span>
                        <div style="flex:1">
                            <strong>{s['النشاط']}</strong>
                            <span style="color:#888;">({s['المدة']})</span>
                            {f'<br><small>📝 {topic}</small>' if typ == 'تعليمي' else ''}
                            {f'<br><small>🎯 {indic}</small>' if typ == 'تعليمي' else ''}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown("")


# ══════════════════════════════════════════════
#  التبويب 4: التوقيت الأسبوعي
# ══════════════════════════════════════════════

with tab4:
    st.markdown("### 📊 التوقيت الأسبوعي للتحضيري")

    view_day = st.selectbox(
        "اختر اليوم",
        list(weekly_schedule.keys()),
        key="schedule_view"
    )

    if view_day:
        plan = weekly_schedule[view_day]

        morning = [s for s in plan if s.get('الفترة') == 'صباحية']
        evening = [s for s in plan if s.get('الفترة') == 'مسائية']

        for name, sessions in [
            ("☀️ الصباح", morning),
            ("🌙 المساء", evening),
        ]:
            if not sessions:
                continue

            st.markdown(f"#### {name}")

            # جدول بسيط
            table_data = []
            for i, s in enumerate(sessions, 1):
                act = s['النشاط']
                is_routine = act in ROUTINE_ACTIVITIES
                table_data.append({
                    "الرقم": i,
                    "النشاط": act,
                    "المدة": s['المدة'],
                    "النوع": "🔄 روتيني" if is_routine else "📖 تعليمي",
                })

            st.dataframe(
                table_data,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "الرقم": st.column_config.NumberColumn(width="small"),
                    "النشاط": st.column_config.TextColumn(width="medium"),
                    "المدة": st.column_config.TextColumn(width="small"),
                    "النوع": st.column_config.TextColumn(width="small"),
                },
            )

    # إحصائيات عامة
    st.markdown("---")
    st.markdown("#### 📈 إحصائيات عامة")

    total_by_day = {
        d: len([s for s in p if s['النشاط'] not in ROUTINE_ACTIVITIES])
        for d, p in weekly_schedule.items()
    }

    cols = st.columns(len(total_by_day))
    for i, (d, c) in enumerate(total_by_day.items()):
        with cols[i]:
            st.metric(d, f"{c} حصة")
