import os
from datetime import datetime

import plotly.graph_objects as go
import streamlit as st

from ai_logic import detect_priority, get_crop_rotation, get_irrigation_plan, route_department
from database import (
    adopt_scheme,
    create_complaint,
    get_complaints_by_farmer,
    get_farmer_by_id,
    get_matching_schemes,
    update_farmer_profile,
)
from i18n_utils import (
    language_options,
    localize_department,
    localize_free_text,
    localize_priority,
    localize_scheme_text,
    localize_status,
    localize_term,
    t,
)
from translations import CROPS, FARMER_CATEGORIES, SOIL_TYPES, STATES, WATER_SOURCES, get_text

# ── Nav configuration ──────────────────────────────────────────────────────────
NAV_ICONS = {
    "tutorial":   "📚",
    "profile":    "👤",
    "irrigation": "💧",
    "rotation":   "🔄",
    "schemes":    "🏛️",
    "complaints": "📋",
}


def show():
    lang   = st.session_state.get("language", "en")
    farmer = get_farmer_by_id(st.session_state.user_data["id"])
    st.session_state.user_data = farmer

    # ── Sidebar ────────────────────────────────────────────────────────────────
    with st.sidebar:
        state_txt    = farmer.get("state", "")    or t("state_not_set",    lang)
        district_txt = farmer.get("district", "") or t("district_not_set", lang)
        st.markdown(
            f"""
            <div style='text-align:center; padding:1.2rem 0 0.8rem;'>
                <div style='font-size:2.8rem; line-height:1.1;'>👨‍🌾</div>
                <div style='font-size:1.05rem; font-weight:700; color:#163a2f;
                    margin-top:0.4rem;'>{farmer['name']}</div>
                <div style='font-size:0.78rem; color:#4a7a5a; margin-top:0.15rem;'>
                    📍 {state_txt} · {district_txt}</div>
                <div style='font-size:0.75rem; color:#2e7d32; margin-top:0.2rem;
                    background:#eef9f1; border-radius:20px; padding:0.15rem 0.6rem;
                    display:inline-block; border:1px solid #c8e3cf;'>
                    📱 {farmer['phone']}</div>
            </div>
            <hr style='border:1px solid #c8e3cf; margin:0.5rem 0 0.8rem;'>
            """,
            unsafe_allow_html=True,
        )

        if farmer.get("crop_type"):
            st.markdown(
                f"""
                <div class='kisan-card' style='padding:0.75rem; margin-bottom:0.6rem;'>
                    <div style='font-size:0.72rem; font-weight:600; color:#4a7a5a;
                        text-transform:uppercase; letter-spacing:0.4px;'>
                        🌾 {t('current_profile', lang)}</div>
                    <div style='font-size:0.85rem; color:#163a2f; margin-top:0.4rem;
                        line-height:1.7;'>
                        🌱 {farmer.get('crop_type','')}<br>
                        📐 {farmer.get('area_size') or '-'} acres<br>
                        🪨 {localize_term('soil', farmer.get('soil_type','-'), lang)}<br>
                        💧 {localize_term('water', farmer.get('water_source','-'), lang)}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("<br>", unsafe_allow_html=True)
        options  = language_options()
        keys     = list(options.keys())
        new_lang = st.selectbox(
            f"🌐 {t('language', lang)}",
            keys,
            format_func=lambda x: options[x],
            index=keys.index(lang) if lang in keys else 0,
        )
        if new_lang != lang:
            st.session_state.language = new_lang
            st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button(f"🚪 {get_text('logout')}", use_container_width=True):
            for key in ["logged_in", "user_type", "user_data"]:
                st.session_state[key] = None
            st.session_state.logged_in = False
            st.session_state.page = "login"
            st.rerun()

    # ── Page header ────────────────────────────────────────────────────────────
    st.markdown(
        f"""
        <div style='display:flex; align-items:center; gap:1rem; margin-bottom:1.5rem;
            background:#ffffff; border:1px solid #c8e3cf; border-radius:14px;
            padding:1rem 1.4rem; box-shadow:0 4px 16px rgba(30,90,50,0.09);'>
            <div style='font-size:2rem;'>👨‍🌾</div>
            <div>
                <div style='font-size:1.4rem; font-weight:700; color:#2e7d32;'>
                    {get_text('dashboard')}</div>
                <div style='color:#4a7a5a; font-size:0.88rem;'>
                    {get_text('welcome_farmer')}, <b>{farmer['name']}</b>! 🙏</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Navigation ─────────────────────────────────────────────────────────────
    # FIX: 'rotation' tab was missing from nav_items — added here
    nav_items = [
        ("tutorial",   _show_tutorial),
        ("profile",    lambda x: _show_profile(farmer, x)),
        ("irrigation", lambda x: _show_irrigation(farmer, x)),
        ("rotation",   lambda x: _show_rotation(farmer, x)),   # ← was missing
        ("schemes",    lambda x: _show_schemes(farmer, x)),
        ("complaints", lambda x: _show_complaints(farmer, x)),
    ]
    nav_keys = [k for k, _ in nav_items]

    if ("farmer_active_tab" not in st.session_state
            or st.session_state.farmer_active_tab not in nav_keys):
        st.session_state.farmer_active_tab = "tutorial"

    nav_cols = st.columns(len(nav_items))
    for idx, (key, _) in enumerate(nav_items):
        icon  = NAV_ICONS.get(key, "")
        label = f"{icon} {get_text(key)}"
        with nav_cols[idx]:
            is_active = st.session_state.farmer_active_tab == key
            if is_active:
                st.markdown(
                    f"<div style='background:#2e7d32;border-radius:10px;padding:0.5rem;"
                    f"text-align:center;color:#fff;font-weight:700;font-size:0.85rem;"
                    f"margin-bottom:0.25rem;'>{label}</div>",
                    unsafe_allow_html=True,
                )
                # invisible button to keep click logic working
                if st.button(label, key=f"farmer_nav_{key}", use_container_width=True):
                    st.session_state.farmer_active_tab = key
            else:
                if st.button(label, key=f"farmer_nav_{key}", use_container_width=True):
                    st.session_state.farmer_active_tab = key

    st.markdown("<div class='green-divider'></div>", unsafe_allow_html=True)

    active_key = st.session_state.farmer_active_tab
    for key, renderer in nav_items:
        if key == active_key:
            renderer(lang)
            break


# ── Tutorial ───────────────────────────────────────────────────────────────────

def _show_tutorial(lang):
    st.markdown(
        f"<div style='font-size:1.4rem; font-weight:700; color:#2e7d32;"
        f"margin-bottom:1.2rem;'>📚 {get_text('tutorial_title')}</div>",
        unsafe_allow_html=True,
    )

    steps = [
        ("👤", get_text("tut_step1"), t("tutorial_desc_1", lang)),
        ("💧", get_text("tut_step2"), t("tutorial_desc_2", lang)),
        ("🏛️",get_text("tut_step3"), t("tutorial_desc_3", lang)),
        ("🔄", get_text("tut_step4"), t("tutorial_desc_4", lang)),
        ("📋", get_text("tut_step5"), t("tutorial_desc_5", lang)),
    ]
    for icon, title, desc in steps:
        st.markdown(
            f"""
            <div class='kisan-card' style='display:flex; gap:1rem; align-items:flex-start;
                margin-bottom:0.75rem;'>
                <div style='font-size:1.6rem; min-width:44px; text-align:center;
                    padding-top:0.1rem;'>{icon}</div>
                <div>
                    <div style='font-weight:700; color:#163a2f; margin-bottom:0.25rem;
                        font-size:0.95rem;'>{title}</div>
                    <div style='color:#4a7a5a; font-size:0.88rem;'>{desc}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        f"<div class='alert-success'>💡 <b>{t('quick_start', lang)}</b></div>",
        unsafe_allow_html=True,
    )

    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    demo_stats = [
        ("🌾", "20+",    t("crops_supported",     lang)),
        ("🏛️", "10+",   t("govt_schemes",         lang)),
        ("💧", "Smart",  t("irrigation_ai",        lang)),
        ("🔄", "Instant",t("crop_rotation_label",  lang)),
    ]
    for col, (icon, val, label) in zip([col1, col2, col3, col4], demo_stats):
        with col:
            st.markdown(
                f"""
                <div class='metric-card'>
                    <div style='font-size:1.6rem;'>{icon}</div>
                    <div class='metric-value'>{val}</div>
                    <div class='metric-label'>{label}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # ── Tips banner ────────────────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    tips = [
        "🌱 Fill your profile first to unlock all personalised features.",
        "📱 Your data is saved securely — login anytime on any device.",
        "💬 Use the Complaints tab to report water, pest or damage issues quickly.",
        "🏛️ Check Schemes regularly — new government schemes are added often.",
    ]
    tips_html = "".join(
        f"<div style='padding:0.3rem 0; border-left:3px solid #43a047; padding-left:0.7rem;"
        f"margin:0.4rem 0; color:#163a2f; font-size:0.88rem;'>{tip}</div>"
        for tip in tips
    )
    st.markdown(
        f"""
        <div class='kisan-card'>
            <div style='font-weight:700; color:#2e7d32; margin-bottom:0.6rem;'>
                💡 Pro Tips</div>
            {tips_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


# ── Profile ────────────────────────────────────────────────────────────────────

def _show_profile(farmer, lang):
    st.markdown(
        f"<div style='font-size:1.4rem; font-weight:700; color:#2e7d32;"
        f"margin-bottom:1.2rem;'>👤 {get_text('profile')}</div>",
        unsafe_allow_html=True,
    )

    # Completeness indicator
    fields      = ["crop_type", "soil_type", "water_source", "area_size",
                   "farmer_category", "state", "district"]
    filled      = sum(1 for f in fields if farmer.get(f))
    pct         = int(filled / len(fields) * 100)
    bar_color   = "#2e7d32" if pct == 100 else "#fb8c00" if pct >= 50 else "#e53935"
    st.markdown(
        f"""
        <div style='background:#ffffff;border:1px solid #c8e3cf;border-radius:12px;
            padding:1rem 1.2rem;margin-bottom:1.2rem;'>
            <div style='display:flex;justify-content:space-between;
                align-items:center;margin-bottom:0.5rem;'>
                <div style='font-weight:600;color:#163a2f;font-size:0.9rem;'>
                    📊 Profile Completeness</div>
                <div style='font-weight:700;color:{bar_color};'>{pct}%</div>
            </div>
            <div style='background:#e7f6ea;border-radius:20px;height:8px;overflow:hidden;'>
                <div style='width:{pct}%;background:{bar_color};height:100%;
                    border-radius:20px;transition:width 0.4s;'></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("profile_form"):
        col1, col2 = st.columns(2)
        with col1:
            state = st.selectbox(
                f"🗺️ {get_text('state')}",
                STATES,
                index=STATES.index(farmer["state"]) if farmer.get("state") in STATES else 0,
                format_func=lambda x: localize_term("states", x, lang),
            )
            crop = st.selectbox(
                f"🌾 {get_text('crop_type')}",
                CROPS,
                index=CROPS.index(farmer["crop_type"]) if farmer.get("crop_type") in CROPS else 0,
                format_func=lambda x: localize_term("crops", x, lang),
            )
            soil = st.selectbox(
                f"🪨 {get_text('soil_type')}",
                SOIL_TYPES,
                index=SOIL_TYPES.index(farmer["soil_type"]) if farmer.get("soil_type") in SOIL_TYPES else 0,
                format_func=lambda x: localize_term("soil", x, lang),
            )
        with col2:
            district = st.text_input(
                f"📍 {get_text('district')}", value=farmer.get("district") or ""
            )
            area = st.number_input(
                f"📐 {get_text('area_size')}",
                min_value=0.1, max_value=1000.0,
                value=float(farmer.get("area_size") or 1.0), step=0.5,
            )
            water = st.selectbox(
                f"💧 {get_text('water_source')}",
                WATER_SOURCES,
                index=WATER_SOURCES.index(farmer["water_source"])
                      if farmer.get("water_source") in WATER_SOURCES else 0,
                format_func=lambda x: localize_term("water", x, lang),
            )
            category = st.selectbox(
                f"👥 {get_text('farmer_category')}",
                FARMER_CATEGORIES,
                index=FARMER_CATEGORIES.index(farmer["farmer_category"])
                      if farmer.get("farmer_category") in FARMER_CATEGORIES else 0,
                format_func=lambda x: localize_term("farmer_category", x, lang),
            )

        if st.form_submit_button(
            f"💾 {get_text('save_profile')}", use_container_width=True
        ):
            update_farmer_profile(
                farmer["id"],
                {
                    "crop_type":       crop,
                    "area_size":       area,
                    "soil_type":       soil,
                    "water_source":    water,
                    "farmer_category": category,
                    "state":           state,
                    "district":        district,
                },
            )
            st.session_state.user_data = get_farmer_by_id(farmer["id"])
            st.success(f"✅ {get_text('profile_saved')}")
            st.rerun()


# ── Irrigation Planner ─────────────────────────────────────────────────────────

def _show_irrigation(farmer, lang):
    st.markdown(
        f"<div style='font-size:1.4rem; font-weight:700; color:#2e7d32;"
        f"margin-bottom:1rem;'>💧 {get_text('irrigation')}</div>",
        unsafe_allow_html=True,
    )

    if not farmer.get("crop_type"):
        st.markdown(
            f"<div class='alert-warning'>⚠️ {t('fill_profile_first_irrigation', lang)}</div>",
            unsafe_allow_html=True,
        )
        return

    crop  = farmer.get("crop_type", "Default")
    soil  = farmer.get("soil_type", "Default")
    water = farmer.get("water_source", "Canal")
    area  = float(farmer.get("area_size") or 1.0)

    # Info strip
    st.markdown(
        f"""
        <div style='background:#eef9f1;border:1px solid #c8e3cf;border-radius:10px;
            padding:0.75rem 1rem;margin-bottom:1rem;display:flex;gap:1.5rem;
            flex-wrap:wrap;font-size:0.88rem;color:#163a2f;'>
            <div>🌾 <b>{localize_term('crops', crop, lang)}</b></div>
            <div>🪨 <b>{localize_term('soil', soil, lang)}</b></div>
            <div>💧 <b>{localize_term('water', water, lang)}</b></div>
            <div>📐 <b>{area} acres</b></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button(f"🚀 {get_text('get_plan')}", use_container_width=True):
        st.session_state["irr_plan"] = get_irrigation_plan(crop, soil, water, area, lang=lang)

    if "irr_plan" not in st.session_state:
        st.markdown(
            f"<div class='alert-info'>ℹ️ "
            f"{localize_free_text('Click Generate Irrigation Plan to get your personalised schedule.', lang)}"
            f"</div>",
            unsafe_allow_html=True,
        )
        return

    plan = st.session_state["irr_plan"]

    st.markdown(
        f"<div style='font-size:1.05rem; font-weight:700; color:#163a2f; margin:1rem 0 0.8rem;'>"
        f"📋 {get_text('irrigation_plan')} <span style='color:#2e7d32;'>{crop}</span></div>",
        unsafe_allow_html=True,
    )

    # Metric cards
    col1, col2, col3, col4 = st.columns(4)
    metrics = [
        ("💧", get_text("water_required"), plan["water_per_acre"]),
        ("📅", get_text("frequency"),       plan["frequency"]),
        ("🌾", get_text("est_yield"),        plan["estimated_yield"]),
        ("⏰", t("best_time", lang),         plan["best_time"]),
    ]
    for col, (icon, label, value) in zip([col1, col2, col3, col4], metrics):
        with col:
            st.markdown(
                f"""
                <div class='metric-card'>
                    <div style='font-size:1.5rem;'>{icon}</div>
                    <div style='font-size:0.92rem; font-weight:700; color:#2e7d32;
                        margin:0.3rem 0;'>{value}</div>
                    <div class='metric-label'>{label}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    if plan["efficiency_tip"]:
        st.markdown(
            f"<div class='alert-info'>💡 {plan['efficiency_tip']}</div>",
            unsafe_allow_html=True,
        )

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(
            f"<div style='font-weight:600;color:#163a2f;margin-bottom:0.5rem;'>"
            f"📅 {t('irrigation_schedule_next_5', lang)}</div>",
            unsafe_allow_html=True,
        )
        for s in plan["schedule"]:
            st.markdown(
                f"<div style='padding:0.4rem 0.6rem; border-left:3px solid #2e7d32;"
                f"margin:0.3rem 0; color:#163a2f; font-size:0.88rem;"
                f"background:#f8fdf9; border-radius:0 6px 6px 0;'>{s}</div>",
                unsafe_allow_html=True,
            )

    with col2:
        st.markdown(
            f"<div style='font-weight:600;color:#163a2f;margin-bottom:0.5rem;'>"
            f"🌱 {t('crop_growth_stage_guide', lang)}</div>",
            unsafe_allow_html=True,
        )
        for stage in plan["stages"]:
            st.markdown(
                f"<div style='padding:0.4rem 0.6rem; border-left:3px solid #43a047;"
                f"margin:0.3rem 0; color:#4a7a5a; font-size:0.83rem;"
                f"background:#f8fdf9; border-radius:0 6px 6px 0;'>{stage}</div>",
                unsafe_allow_html=True,
            )

    # Chart
    days       = [i * int(plan["freq_days"]) for i in range(1, 8)]
    water_vals = [int(plan["water_per_acre_num"]) * 0.2 for _ in days]
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=[f"Day {d}" for d in days], y=water_vals,
            marker_color="#43a047", name="Water (L)",
            text=[f"{int(v):,}L" for v in water_vals],
            textposition="outside",
        )
    )
    fig.update_layout(
        title=f"📊 {t('irrigation_schedule_for', lang)} {crop}",
        plot_bgcolor="#ffffff", paper_bgcolor="#f8fdf9",
        font_color="#163a2f", title_font_color="#2e7d32",
        xaxis=dict(gridcolor="#e0ede3"),
        yaxis=dict(gridcolor="#e0ede3", title="Water (L)"),
        height=300, margin=dict(t=48, b=12, l=12, r=12),
    )
    st.plotly_chart(fig, use_container_width=True)


# ── Crop Rotation Advisor ──────────────────────────────────────────────────────

def _show_rotation(farmer, lang):
    st.markdown(
        f"<div style='font-size:1.4rem; font-weight:700; color:#2e7d32;"
        f"margin-bottom:1rem;'>🔄 {get_text('rotation')}</div>",
        unsafe_allow_html=True,
    )

    if not farmer.get("crop_type"):
        st.markdown(
            f"<div class='alert-warning'>⚠️ {t('fill_profile_first', lang)}</div>",
            unsafe_allow_html=True,
        )
        return

    crop = farmer.get("crop_type", "Default")
    soil = farmer.get("soil_type", "Default")

    st.markdown(
        f"""
        <div style='background:#eef9f1;border:1px solid #c8e3cf;border-radius:10px;
            padding:0.75rem 1rem;margin-bottom:1rem;font-size:0.88rem;color:#163a2f;
            display:flex;gap:1.5rem;flex-wrap:wrap;'>
            <div>🌾 <b>{t('current_crop_soil', lang)}:</b> {crop}</div>
            <div>🪨 <b>{t('soil_label', lang)}:</b> {soil}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button(f"🔍 {get_text('get_rotation')}", use_container_width=True):
        st.session_state["rotation_result"] = get_crop_rotation(crop, soil, lang=lang)

    if "rotation_result" not in st.session_state:
        st.markdown(
            "<div class='alert-info'>ℹ️ Click the button above to get your personalised crop rotation recommendation.</div>",
            unsafe_allow_html=True,
        )
        return

    r = st.session_state["rotation_result"]

    # Main result card
    st.markdown(
        f"""
        <div class='kisan-card' style='border-left:4px solid #2e7d32;
            background:linear-gradient(135deg,#f7fff8,#edf9f0);'>
            <div style='font-size:1.15rem; font-weight:700; color:#2e7d32;
                margin-bottom:1rem;'>
                🌾 {crop} &nbsp;→&nbsp; 🌱 {r['next_crop']}
            </div>
            <div style='display:grid; grid-template-columns:1fr 1fr; gap:1rem;'>
                <div style='background:#ffffff;border:1px solid #c8e3cf;border-radius:10px;padding:0.9rem;'>
                    <div style='color:#4a7a5a; font-size:0.78rem; font-weight:600;
                        text-transform:uppercase; letter-spacing:0.4px;'>
                        {get_text('next_crop')}</div>
                    <div style='color:#163a2f; font-size:1.1rem; font-weight:700;
                        margin-top:0.3rem;'>🌱 {r['next_crop']}</div>
                </div>
                <div style='background:#ffffff;border:1px solid #c8e3cf;border-radius:10px;padding:0.9rem;'>
                    <div style='color:#4a7a5a; font-size:0.78rem; font-weight:600;
                        text-transform:uppercase; letter-spacing:0.4px;'>
                        {get_text('soil_impact')}</div>
                    <div style='color:#2e7d32; font-size:0.92rem; font-weight:600;
                        margin-top:0.3rem;'>📈 {r['soil_impact']}</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(
            f"""
            <div class='kisan-card'>
                <div style='color:#4a7a5a; font-size:0.8rem; font-weight:600;
                    margin-bottom:0.4rem;'>❓ {get_text('rotation_reason')}</div>
                <div style='color:#163a2f; font-size:0.9rem;'>🔬 {r['reason']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            f"""
            <div class='kisan-card'>
                <div style='color:#4a7a5a; font-size:0.8rem; font-weight:600;
                    margin-bottom:0.4rem;'>🪨 {t('soil_specific_tip', lang)}</div>
                <div style='color:#163a2f; font-size:0.9rem;'>💡 {r['soil_tip']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        f"<div class='alert-info'>🌿 {r['fallow_option']}</div>",
        unsafe_allow_html=True,
    )

    # Visual timeline
    _render_rotation_timeline(crop, r['next_crop'], lang)


def _render_rotation_timeline(current_crop, next_crop, lang):
    """Simple visual crop cycle timeline."""
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class='kisan-card'>
            <div style='font-weight:700;color:#2e7d32;margin-bottom:0.8rem;'>
                📅 Crop Cycle Timeline</div>
            <div style='display:flex;align-items:center;gap:0;flex-wrap:nowrap;
                overflow-x:auto;padding-bottom:0.5rem;'>
                <div style='text-align:center;min-width:100px;'>
                    <div style='background:#2e7d32;color:#fff;border-radius:50%;
                        width:48px;height:48px;line-height:48px;font-size:1.2rem;
                        margin:0 auto;'>🌾</div>
                    <div style='font-size:0.75rem;color:#163a2f;font-weight:600;
                        margin-top:0.3rem;'>{current_crop}</div>
                    <div style='font-size:0.68rem;color:#4a7a5a;'>Current</div>
                </div>
                <div style='flex:1;height:2px;background:linear-gradient(90deg,#2e7d32,#43a047);
                    min-width:30px;'></div>
                <div style='text-align:center;min-width:100px;'>
                    <div style='background:#f3fbf4;border:2px dashed #43a047;border-radius:50%;
                        width:48px;height:48px;line-height:44px;font-size:1.2rem;
                        margin:0 auto;'>🌱</div>
                    <div style='font-size:0.75rem;color:#163a2f;font-weight:600;
                        margin-top:0.3rem;'>{next_crop}</div>
                    <div style='font-size:0.68rem;color:#4a7a5a;'>Next Season</div>
                </div>
                <div style='flex:1;height:2px;background:linear-gradient(90deg,#43a047,#c8e3cf);
                    min-width:30px;border-style:dashed;'></div>
                <div style='text-align:center;min-width:100px;'>
                    <div style='background:#f3fbf4;border:2px dashed #c8e3cf;border-radius:50%;
                        width:48px;height:48px;line-height:44px;font-size:1.2rem;
                        margin:0 auto;'>🔄</div>
                    <div style='font-size:0.75rem;color:#4a7a5a;font-weight:600;
                        margin-top:0.3rem;'>Repeat / Fallow</div>
                    <div style='font-size:0.68rem;color:#4a7a5a;'>Season 3</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ── Government Schemes ─────────────────────────────────────────────────────────

def _show_schemes(farmer, lang):
    st.markdown(
        f"<div style='font-size:1.4rem; font-weight:700; color:#2e7d32;"
        f"margin-bottom:1rem;'>🏛️ {get_text('schemes')}</div>",
        unsafe_allow_html=True,
    )

    state        = farmer.get("state") or "All"
    crop         = farmer.get("crop_type") or "All"
    category_raw = farmer.get("farmer_category") or "All"
    category     = category_raw.split("(")[0].strip() if "(" in category_raw else category_raw

    schemes = get_matching_schemes(state, crop, category)
    if not schemes:
        st.markdown(
            f"<div class='alert-warning'>⚠️ {get_text('no_schemes')}</div>",
            unsafe_allow_html=True,
        )
        return

    st.markdown(
        f"<div class='alert-success'>✅ "
        f"{t('schemes_found', lang)} <b>{len(schemes)}</b> "
        f"{t('schemes_matching_profile', lang)} "
        f"({state} · {crop} · {category})</div>",
        unsafe_allow_html=True,
    )

    for s in schemes:
        display_name    = localize_scheme_text(s["name"],        lang)
        display_desc    = localize_scheme_text(s["description"], lang)
        display_benefits= localize_scheme_text(s["benefits"],    lang)
        display_dept    = localize_department(s["department"],   lang)
        stars           = "⭐" * int(round(s["rating"]))

        with st.expander(
            f"🏛️ {display_name}  ·  👥 {s['adoption_count']:,} {t('farmers', lang)}"
            f"  ·  ⭐ {s['rating']}"
        ):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**📝 {get_text('description')}:** {display_desc}")
                st.markdown(f"**💰 {get_text('benefits')}:** {display_benefits}")
                st.markdown(f"**🏢 {get_text('department')}:** {display_dept}")
                st.markdown(
                    f"**🗺️ {t('eligible_states_label', lang)}:** {s['eligible_states']}  |  "
                    f"**🌾 {t('eligible_crops_label', lang)}:** {s['eligible_crops']}"
                )
            with col2:
                st.markdown(
                    f"""
                    <div class='metric-card'>
                        <div style='font-size:1.3rem; color:#2e7d32; font-weight:700;'>
                            {s['rating']}</div>
                        <div style='font-size:0.85rem;'>{stars}</div>
                        <div style='font-size:0.72rem; color:#4a7a5a; margin-top:0.4rem;'>
                            {s['adoption_count']:,} {t('adoptions', lang)}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            if st.button(
                f"✋ {get_text('apply_scheme')}",
                key=f"adopt_{s['id']}",
                use_container_width=True,
            ):
                adopt_scheme(s["id"], farmer["id"])
                st.success(
                    f"✅ {t('interest_registered', lang)} **{display_name}**. "
                    f"{t('department_will_contact', lang)}"
                )


# ── Complaints ─────────────────────────────────────────────────────────────────

def _show_complaints(farmer, lang):
    st.markdown(
        f"<div style='font-size:1.4rem; font-weight:700; color:#2e7d32;"
        f"margin-bottom:1rem;'>📋 {get_text('complaints')}</div>",
        unsafe_allow_html=True,
    )

    tab1, tab2 = st.tabs([
        f"📝 {get_text('submit_complaint')}",
        f"📁 {get_text('my_complaints')}",
    ])

    with tab1:
        with st.form("complaint_form"):
            title = st.text_input(
                f"📌 {get_text('complaint_title')}",
                placeholder=t("brief_issue_title", lang),
            )
            desc = st.text_area(
                f"📝 {get_text('complaint_desc')}",
                placeholder=t("issue_detail_placeholder", lang),
                height=120,
            )
            image = st.file_uploader(
                f"📷 {get_text('upload_image')}", type=["jpg", "jpeg", "png"]
            )

            if st.form_submit_button(f"📤 {get_text('submit_complaint')}", use_container_width=True):
                if not (title and desc):
                    st.warning(f"⚠️ {get_text('fill_all')}")
                else:
                    priority   = detect_priority(title, desc)
                    department = route_department(title, desc)
                    image_path = None
                    if image:
                        os.makedirs("complaint_images", exist_ok=True)
                        image_path = (
                            f"complaint_images/{farmer['id']}_"
                            f"{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
                        )
                        with open(image_path, "wb") as f:
                            f.write(image.read())

                    cid = create_complaint(
                        farmer_id=farmer["id"],
                        farmer_name=farmer["name"],
                        state=farmer.get("state", ""),
                        district=farmer.get("district", ""),
                        title=title,
                        description=desc,
                        priority=priority,
                        department=department,
                        image_path=image_path,
                    )
                    priority_badge = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}
                    st.success(f"✅ {get_text('complaint_submitted')}")
                    st.markdown(
                        f"""
                        <div class='kisan-card' style='border-left:4px solid #2e7d32;'>
                            <div><b>🔖 {get_text('complaint_id')}:</b>
                                <code style='color:#2e7d32; font-size:1rem;'>{cid}</code></div>
                            <div style='margin-top:0.5rem;'>
                                <b>⚡ {get_text('priority')}:</b>
                                {priority_badge.get(priority,'⚪')}
                                {localize_priority(priority, lang)}</div>
                            <div><b>🏢 {t('routed_to', lang)}:</b> {department}</div>
                            <div style='color:#4a7a5a; font-size:0.83rem; margin-top:0.5rem;'>
                                📌 {t('track_complaint_hint', lang)}</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

    with tab2:
        complaints = get_complaints_by_farmer(farmer["id"])
        if not complaints:
            st.markdown(
                f"<div class='alert-info'>ℹ️ {get_text('no_complaints')}</div>",
                unsafe_allow_html=True,
            )
            return

        # Stats row
        total    = len(complaints)
        resolved = sum(1 for c in complaints if c["status"] == "Resolved")
        pending  = total - resolved

        c1, c2, c3 = st.columns(3)
        for col, icon, label, val, color in [
            (c1, "📋", "Total",    total,    "#2e7d32"),
            (c2, "✅", "Resolved", resolved, "#388e3c"),
            (c3, "⏳", "Pending",  pending,  "#fb8c00"),
        ]:
            with col:
                st.markdown(
                    f"<div class='metric-card'><div style='font-size:1.3rem;'>{icon}</div>"
                    f"<div style='font-size:1.4rem;font-weight:700;color:{color};'>{val}</div>"
                    f"<div class='metric-label'>{label}</div></div>",
                    unsafe_allow_html=True,
                )
        st.markdown("<br>", unsafe_allow_html=True)

        for c in complaints:
            priority_colors = {"High": "#e53935", "Medium": "#fb8c00", "Low": "#43a047"}
            priority_bg     = {"High": "#fff5f5",  "Medium": "#fff8f0", "Low": "#f1fdf2"}
            status_icons    = {"Submitted": "📨", "In Progress": "⚙️", "Resolved": "✅"}
            pcolor = priority_colors.get(c["priority"], "#2e7d32")
            pbg    = priority_bg.get(c["priority"], "#f1fdf2")
            sicon  = status_icons.get(c["status"], "📨")

            st.markdown(
                f"""
                <div class='kisan-card' style='border-left:3px solid {pcolor};'>
                    <div style='display:flex; justify-content:space-between;
                        align-items:flex-start;'>
                        <div>
                            <div style='font-weight:700; color:#163a2f;
                                font-size:0.95rem;'>{c['title']}</div>
                            <code style='font-size:0.78rem; color:#2e7d32;'>
                                {c['complaint_id']}</code>
                        </div>
                        <div style='background:{pbg};border:1px solid {pcolor}55;
                            color:{pcolor};border-radius:20px;padding:0.2rem 0.7rem;
                            font-size:0.72rem;font-weight:700;white-space:nowrap;'>
                            {localize_priority(c['priority'], lang)}</div>
                    </div>
                    <div style='color:#4a7a5a; font-size:0.85rem;
                        margin:0.5rem 0;'>
                        {c['description'][:140]}{'…' if len(c['description']) > 140 else ''}
                    </div>
                    <div style='display:flex; justify-content:space-between;
                        font-size:0.78rem; color:#4a7a5a; flex-wrap:wrap; gap:0.4rem;'>
                        <div>{sicon} <b style='color:#163a2f;'>
                            {localize_status(c['status'], lang)}</b></div>
                        <div>🏢 {c['department']}</div>
                        <div>📅 {c['created_at'][:10]}</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
