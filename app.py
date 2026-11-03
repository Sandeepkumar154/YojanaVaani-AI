import base64
import hashlib
import os

import streamlit as st
from audio_recorder_streamlit import audio_recorder
from dotenv import load_dotenv

from services import (
    INDIAN_OFFICIAL_LANGUAGES,
    OUTBOUND_CALL_SCENARIOS,
    GnaniError,
    _load_kb,
    create_scheme_request,
    enhance_audio,
    get_sample_prompts,
    get_scheme_stats,
    get_voice_for_language,
    get_welcome_text,
    has_api_key,
    has_gemini_key,
    init_db,
    privacy_warning,
    process_voice_turn,
    reload_kb,
    simulate_telephony_channel,
    synthesize,
    transcribe,
    verify_gemini_connection,
    verify_gnani_connection,
)

load_dotenv(override=True)
init_db()

def update_gemini_key_in_env(new_key: str):
    env_file = ".env"
    existing = []
    if os.path.exists(env_file):
        with open(env_file, "r", encoding="utf-8") as f:
            existing = f.readlines()
    updated = False
    new_lines = []
    for line in existing:
        if line.strip().startswith("GEMINI_API_KEY="):
            if not updated:
                new_lines.append(f"GEMINI_API_KEY={new_key}\n")
                updated = True
        else:
            new_lines.append(line)
    if not updated:
        new_lines.append(f"GEMINI_API_KEY={new_key}\n")
    with open(env_file, "w", encoding="utf-8") as f:
        f.writelines(new_lines)
    os.environ["GEMINI_API_KEY"] = new_key
    load_dotenv(override=True)

# ---------------------------------------------------------------------------
# Language-Specified Indic National Tricolor Brand Emblem Generator
# ---------------------------------------------------------------------------
LANGUAGE_EMBLEM_GLYPHS: dict[str, str] = {
    "indic-auto": "भा",
    "hi": "हि",
    "hi-en": "भा",
    "te": "తె",
    "ta": "த",
    "kn": "ಕ",
    "ml": "മ",
    "mr": "म",
    "bn": "বা",
    "gu": "ગુ",
    "pa": "ਪੰ",
    "or": "ଓ",
    "as": "অ",
    "ur": "اردو",
    "en": "EN",
    "sa": "सं",
    "ne": "ने",
    "kok": "कों",
    "mai": "मै",
    "doi": "डो",
    "ks": "कॉ",
    "sd": "सि",
    "mni": "ꯃৈ",
    "brx": "ब",
    "sat": "ᱥ",
}

def generate_emblem_svg(lang_code: str | None, size: int = 56) -> str:
    """Generate a futuristic Indic Acoustic Chakra emblem subtly echoing the national flag colors."""
    glyph = LANGUAGE_EMBLEM_GLYPHS.get(lang_code or "indic-auto", "भा")
    font_size = 23 if len(glyph) <= 2 else 15
    svg_uid = f"emb_{lang_code}_{size}".replace("-", "_")
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="{size}" height="{size}" style="vertical-align: middle; filter: drop-shadow(0 4px 10px rgba(0,0,0,0.5));">
  <defs>
    <linearGradient id="bgGrad_{svg_uid}" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0a1128" />
      <stop offset="50%" stop-color="#1c2541" />
      <stop offset="100%" stop-color="#0b132b" />
    </linearGradient>
    <!-- Subtle National Tricolor Ambient Ring (Saffron -> White -> Emerald) -->
    <linearGradient id="tricolorArc_{svg_uid}" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#FF7700" />
      <stop offset="30%" stop-color="#FF9933" />
      <stop offset="50%" stop-color="#FFFFFF" />
      <stop offset="70%" stop-color="#10B981" />
      <stop offset="100%" stop-color="#047857" />
    </linearGradient>
    <radialGradient id="chakraCore_{svg_uid}" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#38bdf8" stop-opacity="0.95" />
      <stop offset="55%" stop-color="#1d4ed8" stop-opacity="0.75" />
      <stop offset="100%" stop-color="#0b132b" stop-opacity="0.9" />
    </radialGradient>
  </defs>

  <!-- Outer Glass Badge Base -->
  <circle cx="50" cy="50" r="47" fill="url(#bgGrad_{svg_uid})" stroke="rgba(255,255,255,0.12)" stroke-width="1.5" />

  <!-- Subtle Indian Tricolor Ambient Ring -->
  <circle cx="50" cy="50" r="42" fill="none" stroke="url(#tricolorArc_{svg_uid})" stroke-width="3" stroke-dasharray="9 3" opacity="0.95" />

  <!-- Acoustic Voice Wave Ripples -->
  <circle cx="50" cy="50" r="34" fill="none" stroke="#38bdf8" stroke-width="1.2" stroke-opacity="0.45" stroke-dasharray="4 3" />
  <circle cx="50" cy="50" r="28" fill="url(#chakraCore_{svg_uid})" />

  <!-- Celestial Tricolor Cardinal Accent Dots -->
  <circle cx="50" cy="9" r="3.2" fill="#FF7700" />
  <circle cx="50" cy="91" r="3.2" fill="#10B981" />
  <circle cx="9" cy="50" r="2.2" fill="#FFFFFF" opacity="0.85" />
  <circle cx="91" cy="50" r="2.2" fill="#38BDF8" opacity="0.85" />

  <!-- Language-Specified Native Script Character -->
  <text x="50" y="58" font-family="'Plus Jakarta Sans', 'Noto Sans Devanagari', 'Noto Sans Telugu', 'Noto Sans Tamil', -apple-system, sans-serif" 
        font-size="{font_size}" font-weight="800" fill="#FFFFFF" text-anchor="middle">{glyph}</text>
</svg>"""

def update_browser_favicon(lang_code: str):
    """Dynamically set browser favicon to the language-specified tricolor acoustic emblem."""
    svg_raw = generate_emblem_svg(lang_code, size=64)
    b64_svg = base64.b64encode(svg_raw.encode("utf-8")).decode("utf-8")
    favicon_script = f"""
    <script>
        (function() {{
            let link = document.querySelector("link[rel*='icon']") || document.createElement('link');
            link.type = 'image/svg+xml';
            link.rel = 'shortcut icon';
            link.href = 'data:image/svg+xml;base64,{b64_svg}';
            document.getElementsByTagName('head')[0].appendChild(link);
        }})();
    </script>
    """
    st.markdown(favicon_script, unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Page Config & Luxury Theme
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="YojanaVaani AI — Bharat's Citizen Voice AI",
    page_icon="🇮🇳",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Custom CSS: Modern Glassmorphism & Luxury Aesthetics
# ---------------------------------------------------------------------------
CUSTOM_CSS = """
<style>
/* Global Font & Smoothness */
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', -apple-system, sans-serif;
}

/* Background gradient styling */
.stApp {
    background: radial-gradient(circle at 10% 20%, rgba(16, 24, 40, 0.95), rgba(8, 12, 22, 1));
    color: #e2e8f0;
}

/* Luxury Hero Banner */
.hero-container {
    background: linear-gradient(135deg, rgba(255, 153, 51, 0.12) 0%, rgba(255, 255, 255, 0.05) 50%, rgba(19, 136, 8, 0.12) 100%);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 20px;
    padding: 24px 32px;
    margin-bottom: 24px;
    backdrop-filter: blur(16px);
    box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.5);
    position: relative;
    overflow: hidden;
}

.hero-container::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; height: 3px;
    background: linear-gradient(90deg, #FF9933 0%, #FFFFFF 50%, #138808 100%);
}

.hero-pill {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 4px 14px;
    background: rgba(255, 255, 255, 0.08);
    border: 1px solid rgba(255, 255, 255, 0.15);
    border-radius: 9999px;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    color: #38bdf8;
    margin-bottom: 12px;
}

.hero-title {
    font-size: 32px;
    font-weight: 800;
    letter-spacing: -0.5px;
    background: linear-gradient(180deg, #FFFFFF 0%, #94a3b8 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0 0 6px 0;
}

.hero-subtitle {
    font-size: 14px;
    color: #94a3b8;
    margin: 0;
}

/* Glassmorphic Cards */
.glass-card {
    background: rgba(17, 24, 39, 0.7);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 16px;
    padding: 20px;
    backdrop-filter: blur(12px);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
    transition: transform 0.2s ease, border-color 0.2s ease;
}

.glass-card:hover {
    border-color: rgba(56, 189, 248, 0.3);
    transform: translateY(-2px);
}

/* Voice Wave Visualizer Animation */
.visualizer-container {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
    height: 48px;
    margin: 12px 0;
}

.wave-bar {
    width: 5px;
    background: linear-gradient(180deg, #38bdf8, #818cf8);
    border-radius: 9999px;
    animation: wavePulse 1.2s ease-in-out infinite alternate;
}

.wave-bar:nth-child(1) { height: 18px; animation-delay: 0.1s; }
.wave-bar:nth-child(2) { height: 32px; animation-delay: 0.3s; }
.wave-bar:nth-child(3) { height: 44px; animation-delay: 0.2s; }
.wave-bar:nth-child(4) { height: 26px; animation-delay: 0.4s; }
.wave-bar:nth-child(5) { height: 36px; animation-delay: 0.15s; }
.wave-bar:nth-child(6) { height: 20px; animation-delay: 0.35s; }

@keyframes wavePulse {
    0% { transform: scaleY(0.4); opacity: 0.5; }
    100% { transform: scaleY(1.1); opacity: 1; }
}

/* Phone Simulator Chassis */
.phone-chassis {
    max-width: 380px;
    margin: 0 auto;
    background: #090d16;
    border: 4px solid #1e293b;
    border-radius: 40px;
    padding: 24px 20px;
    box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.7), 0 0 40px rgba(56, 189, 248, 0.15);
    position: relative;
}

.phone-notch {
    width: 120px;
    height: 18px;
    background: #1e293b;
    border-radius: 0 0 12px 12px;
    margin: -24px auto 16px auto;
}

/* Streamlit Tabs Customization */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    background: rgba(15, 23, 42, 0.6);
    padding: 6px;
    border-radius: 14px;
    border: 1px solid rgba(255, 255, 255, 0.06);
}

.stTabs [data-baseweb="tab"] {
    height: 44px;
    border-radius: 10px;
    color: #94a3b8;
    font-weight: 600;
    font-size: 13px;
    padding: 0 18px;
    border: none;
    transition: all 0.2s ease;
}

.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, rgba(56, 189, 248, 0.15), rgba(99, 102, 241, 0.2)) !important;
    color: #38bdf8 !important;
    border: 1px solid rgba(56, 189, 248, 0.3) !important;
}

/* Metric styling */
[data-testid="stMetricValue"] {
    font-size: 26px !important;
    font-weight: 800 !important;
    background: linear-gradient(180deg, #ffffff 0%, #cbd5e1 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

/* Quick Prompt Buttons */
.stButton > button {
    border-radius: 10px;
    font-weight: 600;
    font-size: 12.5px;
    transition: all 0.2s ease;
}

.stButton > button:hover {
    border-color: #38bdf8 !important;
    box-shadow: 0 0 15px rgba(56, 189, 248, 0.25);
    transform: translateY(-1px);
}

/* Sidebar Nav Radio Drawer Styling */
[data-testid="stSidebar"] div[role="radiogroup"] > label {
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 12px;
    padding: 10px 14px;
    margin-bottom: 6px;
    cursor: pointer;
    transition: all 0.2s ease;
}

[data-testid="stSidebar"] div[role="radiogroup"] > label:hover {
    background: rgba(56, 189, 248, 0.12);
    border-color: rgba(56, 189, 248, 0.35);
}

[data-testid="stSidebar"] div[role="radiogroup"] > label[data-checked="true"],
[data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked) {
    background: linear-gradient(135deg, rgba(56, 189, 248, 0.22), rgba(99, 102, 241, 0.28)) !important;
    border-color: #38bdf8 !important;
    box-shadow: 0 0 14px rgba(56, 189, 248, 0.25);
}

/* Executive Voice Orb */
.orb-container {
    display: flex;
    justify-content: center;
    align-items: center;
    margin: 14px 0 10px 0;
}

.voice-orb {
    width: 84px;
    height: 84px;
    border-radius: 50%;
    background: radial-gradient(circle, #38bdf8 0%, rgba(56, 189, 248, 0.35) 45%, rgba(16, 185, 129, 0.2) 75%, transparent 100%);
    box-shadow: 0 0 32px rgba(56, 189, 248, 0.55), inset 0 0 22px rgba(255, 153, 51, 0.35);
    animation: orbGlow 3s ease-in-out infinite alternate;
    display: flex;
    align-items: center;
    justify-content: center;
}

.voice-orb-inner {
    width: 38px;
    height: 38px;
    border-radius: 50%;
    background: linear-gradient(135deg, #ffffff, #38bdf8);
    box-shadow: 0 0 16px #38bdf8;
    animation: orbInnerPulse 1.8s ease-in-out infinite alternate;
}

@keyframes orbGlow {
    0% { transform: scale(0.95); box-shadow: 0 0 22px rgba(56, 189, 248, 0.4); }
    100% { transform: scale(1.08); box-shadow: 0 0 42px rgba(56, 189, 248, 0.75), 0 0 55px rgba(16, 185, 129, 0.3); }
}

@keyframes orbInnerPulse {
    0% { transform: scale(0.9); opacity: 0.85; }
    100% { transform: scale(1.15); opacity: 1; }
}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Session State
# ---------------------------------------------------------------------------
if "current_lang" not in st.session_state:
    st.session_state["current_lang"] = None

if "conversation" not in st.session_state:
    st.session_state["conversation"] = []

if "last_audio_hash" not in st.session_state:
    st.session_state["last_audio_hash"] = None

if "call_active" not in st.session_state:
    st.session_state["call_active"] = False

if "call_history" not in st.session_state:
    st.session_state["call_history"] = []

if "call_telecom_sim" not in st.session_state:
    st.session_state["call_telecom_sim"] = False

if "outbound_call_active" not in st.session_state:
    st.session_state["outbound_call_active"] = False

if "outbound_call_scenario" not in st.session_state:
    st.session_state["outbound_call_scenario"] = "pm_kisan_dbt"

if "last_call_audio_hash" not in st.session_state:
    st.session_state["last_call_audio_hash"] = None

NAV_MODES = [
    "🎙️ Voice Assistant Studio",
    "📞 1800-YOJANA Telephony Agent",
    "📚 Schemes Directory",
    "📊 Citizen CSC Desk",
]

if "nav_mode" not in st.session_state:
    st.session_state["nav_mode"] = NAV_MODES[0]

# ---------------------------------------------------------------------------
# Sidebar: Navigation Drawer, Engine Status, Language, and Scope Filter
# ---------------------------------------------------------------------------
with st.sidebar:
    active_lang_code = st.session_state.get("current_lang") or "indic-auto"
    side_emblem_svg = generate_emblem_svg(active_lang_code, size=46)
    st.markdown(
        f"""
        <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 8px;">
            <div style="flex-shrink: 0;">{side_emblem_svg}</div>
            <div>
                <h3 style="margin: 0; font-weight: 800; font-size: 18px; letter-spacing: -0.5px;">YojanaVaani AI</h3>
                <div style="font-size: 11px; color: #38bdf8; font-weight: 600;">CITIZEN VOICE SUITE • GNANI AI</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("---")

    st.markdown("<div style='font-size: 11px; font-weight: 700; color: #38bdf8; letter-spacing: 1.2px; margin-bottom: 8px;'>NAVIGATION DRAWER</div>", unsafe_allow_html=True)
    selected_nav = st.radio(
        "Navigation Drawer",
        NAV_MODES,
        index=NAV_MODES.index(st.session_state["nav_mode"]) if st.session_state["nav_mode"] in NAV_MODES else 0,
        label_visibility="collapsed",
        key="sidebar_nav_mode",
    )
    st.session_state["nav_mode"] = selected_nav
    st.markdown("---")

    # Engine Status Badge
    key_configured = has_api_key()
    if key_configured:
        st.markdown(
            """
            <div style="background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.3); padding: 10px 14px; border-radius: 10px; margin-bottom: 8px;">
                <div style="display: flex; align-items: center; gap: 8px;">
                    <div style="width: 8px; height: 8px; border-radius: 9999px; background: #10b981; box-shadow: 0 0 8px #10b981;"></div>
                    <span style="font-weight: 700; font-size: 12px; color: #10b981;">GNANI AI CLOUD: ACTIVE</span>
                </div>
                <div style="font-size: 11px; color: #94a3b8; margin-top: 4px;">• Prisma v3.0 (Indic STT)<br>• Timbre v2.5 (Indic TTS)</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.warning("🟡 Gnani API Key Not Detected in .env")

    # Dynamic Reasoning Engine Status
    gemini_active = has_gemini_key()
    if gemini_active:
        st.markdown(
            """
            <div style="background: rgba(56, 189, 248, 0.1); border: 1px solid rgba(56, 189, 248, 0.3); padding: 8px 12px; border-radius: 10px; margin-bottom: 12px;">
                <div style="display: flex; align-items: center; gap: 6px;">
                    <span style="font-size: 13px;">🧠</span>
                    <span style="font-weight: 700; font-size: 11.5px; color: #38bdf8;">GEMINI 1.5 FLASH: ACTIVE</span>
                </div>
                <div style="font-size: 10.5px; color: #94a3b8; margin-top: 2px;">Dynamic Generative Multilingual Answers</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
            <div style="background: rgba(148, 163, 184, 0.08); border: 1px solid rgba(148, 163, 184, 0.2); padding: 8px 12px; border-radius: 10px; margin-bottom: 12px;">
                <div style="display: flex; align-items: center; gap: 6px;">
                    <span style="font-size: 13px;">📚</span>
                    <span style="font-weight: 700; font-size: 11.5px; color: #94a3b8;">GROUNDED SCHEMES RAG: ACTIVE</span>
                </div>
                <div style="font-size: 10.5px; color: #64748b; margin-top: 2px;">27+ Central/State Schemes Verified Facts</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with st.expander("✨ Enable Gemini Generative AI (Optional)", expanded=not gemini_active):
        st.caption("💡 Completely optional. YojanaVaani AI already has 29+ Central/State schemes built-in via Gnani AI.")
        current_saved_key = os.getenv("GEMINI_API_KEY", "").strip()
        if "gemini_key_input" not in st.session_state:
            st.session_state["gemini_key_input"] = current_saved_key

        g_key_in = st.text_input(
            "Gemini API Key",
            value=st.session_state.get("gemini_key_input", current_saved_key),
            type="password",
            placeholder="Paste AIzaSy... key",
            help="Saved permanently in your .env file so it is never forgotten across reloads.",
            key="gemini_key_box",
        )
        if current_saved_key:
            masked = current_saved_key[:6] + "••••••••" + (current_saved_key[-4:] if len(current_saved_key) > 10 else "")
            st.markdown(
                f"<div style='font-size:11px;color:#10b981;margin-bottom:8px;'>🔒 <b>Key Stored in .env:</b> {masked}</div>",
                unsafe_allow_html=True,
            )

        c_g1, c_g2, c_g3 = st.columns([1, 1, 0.8])
        with c_g1:
            if st.button("Save & Activate", use_container_width=True, key="btn_save_gemini"):
                if g_key_in.strip():
                    update_gemini_key_in_env(g_key_in.strip())
                    st.session_state["gemini_key_input"] = g_key_in.strip()
                    st.success("✅ Gemini Key saved permanently!")
                    st.rerun()
        with c_g2:
            if st.button("Test Key", use_container_width=True, key="btn_test_gemini"):
                test_target = g_key_in.strip() or current_saved_key
                if test_target:
                    os.environ["GEMINI_API_KEY"] = test_target
                with st.spinner("Pinging Google Generative AI..."):
                    gem_res = verify_gemini_connection()
                    if gem_res["ok"]:
                        st.success(f"✅ Gemini Brain Active! (Latency: {gem_res['latency_ms']}ms)")
                    else:
                        st.error(f"❌ {gem_res.get('error')}")
        with c_g3:
            if st.button("Clear", use_container_width=True, key="btn_clear_gemini"):
                update_gemini_key_in_env("")
                st.session_state["gemini_key_input"] = ""
                st.info("Key cleared.")
                st.rerun()

    with st.expander("🔍 Test Gnani Cloud Connection", expanded=False):
        st.caption("Live handshake ping to Gnani Cloud servers (api.vachana.ai):")
        if st.button("Ping Gnani Cloud (Timbre + Prisma)", use_container_width=True, key="btn_test_gnani"):
            with st.spinner("Pinging api.vachana.ai..."):
                gnani_res = verify_gnani_connection()
                if gnani_res["ok"]:
                    st.success(f"✅ Gnani Cloud 100% Active! (Latency: {gnani_res['latency_ms']}ms • Received {gnani_res['bytes']:,} bytes audio)")
                else:
                    st.error(f"❌ Gnani Connection Error: {gnani_res.get('error')}")

    st.markdown("##### 🗣️ Preferred Language")
    lang_options = list(INDIAN_OFFICIAL_LANGUAGES.keys())
    lang_labels = [
        f"{INDIAN_OFFICIAL_LANGUAGES[k]['native']} ({INDIAN_OFFICIAL_LANGUAGES[k]['name']})"
        for k in lang_options
    ]
    selected_lang_idx = st.selectbox(
        "Auto-Detect / Select from 22 Languages",
        range(len(lang_options)),
        format_func=lambda i: lang_labels[i],
        index=0,
    )
    selected_lang_code = lang_options[selected_lang_idx]
    update_browser_favicon(selected_lang_code)

    # Dynamically update conversation welcome message when language changes
    if st.session_state["current_lang"] != selected_lang_code:
        st.session_state["current_lang"] = selected_lang_code
        if selected_lang_code == "te":
            wel_text = "నమస్కారం! పైన ఉన్న మైక్ బటన్ నొక్కి మీ ప్రశ్నను అడగండి (ఉదా: పీఎం-కిసాన్ లేదా ఆయుష్మాన్ భారత్ సహాయం ఎలా పొందాలి?)."
        elif selected_lang_code == "hi":
            wel_text = "नमस्ते! ऊपर दिए गए माइक बटन को दबाकर अपना सवाल पूछिए (जैसे: पीएम-किसान या आयुष्मान भारत कार्ड कैसे बनेगा?)।"
        elif selected_lang_code == "en":
            wel_text = "Welcome! Tap the mic button above and ask your question about any government scheme."
        else:
            wel_text = get_welcome_text(selected_lang_code)

        st.session_state["conversation"] = [
            {
                "role": "assistant",
                "text": wel_text,
                "audio": None,  # Do not speak automatically on page load/language switch
                "lang": selected_lang_code,
                "scheme": None,
                "escalate": False,
                "is_welcome": True,
            }
        ]
        st.session_state["last_audio_hash"] = None

    st.markdown("##### 📍 Scope / State Filter")
    all_schemes_raw = _load_kb()
    states_list = sorted(list(set(
        s.get("state", "All India") for s in all_schemes_raw if s.get("state") != "All India"
    )))
    state_filter = st.selectbox(
        "Target Scheme Domain",
        ["All Schemes (Central + State)", "Central Schemes Only"] + states_list,
        index=0,
    )
    clean_state_filter = None
    if state_filter == "Central Schemes Only":
        clean_state_filter = "All India"
    elif state_filter != "All Schemes (Central + State)":
        clean_state_filter = state_filter

    with st.expander("🌐 22 Official Languages Reference", expanded=False):
        for code, info in INDIAN_OFFICIAL_LANGUAGES.items():
            if code != "indic-auto":
                st.markdown(f"**{info['native']}** ({info['name']})<br><span style='font-size:11px;color:#94a3b8;'>{info['region']}</span>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown(
        """
        <div style="font-size: 11px; color: #64748b; line-height: 1.6;">
            <b>Challenge Target Badges:</b><br>
            ✓ 22 Official Languages Covered<br>
            ✓ Central + All State Schemes<br>
            ✓ Noisy Telephonic Audio Ready<br>
            ✓ Anti-Fraud Scam Shield<br>
            ✓ Gram Panchayat & CSC Desk
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🗑️ Reset Chat", use_container_width=True):
        if selected_lang_code == "te":
            wel_text = "నమస్కారం! పైన ఉన్న మైక్ బటన్ నొక్కి మీ ప్రశ్నను అడగండి (ఉదా: పీఎం-కిసాన్ లేదా ఆయుష్మాన్ భారత్ సహాయం ఎలా పొందాలి?)."
        elif selected_lang_code == "hi":
            wel_text = "नमस्ते! ऊपर दिए गए माइक बटन को दबाकर अपना सवाल पूछिए (जैसे: पीएम-किसान या आयुष्मान भारत कार्ड कैसे बनेगा?)।"
        elif selected_lang_code == "en":
            wel_text = "Welcome! Tap the mic button above and ask your question about any government scheme."
        else:
            wel_text = get_welcome_text(selected_lang_code)

        st.session_state["conversation"] = [
            {
                "role": "assistant",
                "text": wel_text,
                "audio": None,
                "lang": selected_lang_code,
                "scheme": None,
                "escalate": False,
                "is_welcome": True,
            }
        ]
        st.session_state["last_audio_hash"] = None
        st.rerun()

# ---------------------------------------------------------------------------
# Navigation Dispatcher: Main Dashboard contains ONLY the Active View
# When '🎙️ Voice Assistant Studio' is selected, the screen is 100% focused on Voice AI
# ---------------------------------------------------------------------------
if st.session_state["nav_mode"] == "🎙️ Voice Assistant Studio":
    hero_emblem = generate_emblem_svg(selected_lang_code, size=68)
    st.markdown(
        f"""
        <div class="hero-container">
            <div style="display: flex; align-items: center; gap: 18px;">
                <div style="flex-shrink: 0;">{hero_emblem}</div>
                <div>
                    <div class="hero-pill">⚡ BHARAT'S NEXT-GEN CITIZEN WELFARE AI • POWERED BY GNANI AI</div>
                    <h1 class="hero-title">YojanaVaani AI — Citizen Voice Studio</h1>
                    <p class="hero-subtitle">
                        Voice-first access to 2,000+ Central and State welfare benefits across 22 official Indian languages.
                        Speak in your mother tongue, listen to live synthesized responses, and navigate schemes seamlessly.
                    </p>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c_mic_box, c_prompts_box = st.columns([1.1, 2])

    with c_mic_box:
        orb_emblem = generate_emblem_svg(selected_lang_code, size=46)
        st.markdown(
            f"""
            <div class="glass-card" style="text-align: center;">
                <div style="font-size: 11px; font-weight: 700; color: #38bdf8; letter-spacing: 1.2px; margin-bottom: 4px;">LIVE AUDIO INTERACTION</div>
                <div class="orb-container">
                    <div class="voice-orb">
                        {orb_emblem}
                    </div>
                </div>
                <h3 style="margin: 0 0 4px 0; font-size: 17px;">Speak in Your Mother Tongue</h3>
                <p style="font-size: 11px; color: #94a3b8; margin-bottom: 8px;">Auto-detected via Prisma STT (indic-auto)</p>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            <div style="background: rgba(56, 189, 248, 0.08); border: 1px solid rgba(56, 189, 248, 0.25); border-radius: 8px; padding: 6px 10px; margin-bottom: 10px; font-size: 11px; color: #a5f3fc; line-height: 1.4;">
                ⚡ <b>Smart Auto-Cutoff (VAD)</b>: Tap mic, speak your question, and the mic will <b>automatically turn off</b> 1.8s after you stop talking!
            </div>
            """,
            unsafe_allow_html=True,
        )

        vad_key = f"vad_mic_{st.session_state.get('mic_counter', 0)}"
        vad_audio = audio_recorder(
            text="Tap to Speak (Auto-Off)",
            recording_color="#ef4444",
            neutral_color="#38bdf8",
            icon_name="microphone",
            icon_size="2x",
            pause_threshold=1.2,
            sample_rate=16000,
            key=vad_key,
        )

        with st.expander("Or use Manual Push-to-Talk Mic", expanded=False):
            mic_key = f"citizen_mic_{st.session_state.get('mic_counter', 0)}"
            native_audio = st.audio_input("Record Voice (Manual Stop)", key=mic_key)

        recorded_audio = None
        if vad_audio is not None and len(vad_audio) > 400:
            recorded_audio = vad_audio
        elif native_audio is not None:
            recorded_audio = native_audio.getvalue()

        audio_to_run = None
        query_to_run = None

        st.markdown(
            """
                <div class="visualizer-container">
                    <div class="wave-bar"></div>
                    <div class="wave-bar"></div>
                    <div class="wave-bar"></div>
                    <div class="wave-bar"></div>
                    <div class="wave-bar"></div>
                    <div class="wave-bar"></div>
                </div>
                <div style="font-size: 11px; color: #64748b;">Prisma 16kHz Model • Timbre Regional TTS • Zero-Trust Shield</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c_prompts_box:
        st.markdown(
            """
            <div class="glass-card">
                <div style="font-size: 12px; font-weight: 700; color: #818cf8; letter-spacing: 1px; margin-bottom: 8px;">ONE-CLICK CITIZEN DEMO PROMPTS</div>
            """,
            unsafe_allow_html=True,
        )

        prompts = get_sample_prompts(selected_lang_code)

        lbl_map = {
            "te": {
                "pm_kisan": "🌾 పీఎం-కిసాన్ ₹6000", "ayushman": "🏥 ఆయుష్మాన్ ₹5L", "surya_ghar": "☀️ సూర్య ఘర్ సోలార్", "vishwakarma": "🔨 పీఎం విశ్వకర్మ",
                "ladki_bahin": "👸 లడ్కీ బహిన్ (MH)", "gruha_lakshmi": "🏠 గృహ లక్ష్మి (KA)", "magalir_urimai": "🌸 మగళిర్ ఉరిమై (TN)", "kanya_sumangala": "👧 కన్యా సుమంగళ (UP)",
                "scam_test": "🚨 మోసపూరిత కాల్ OTP అలర్ట్",
            },
            "ta": {
                "pm_kisan": "🌾 பிஎம்-கிசான் ₹6000", "ayushman": "🏥 ஆயுஷ்மான் ₹5L", "surya_ghar": "☀️ சூர்யா கர் சோலார்", "vishwakarma": "🔨 பிஎம் விஸ்வகர்மா",
                "ladki_bahin": "👸 லட்கி பஹின் (MH)", "gruha_lakshmi": "🏠 கிருக லட்சுமி (KA)", "magalir_urimai": "🌸 மகளிர் உரிமை (TN)", "kanya_sumangala": "👧 கன்யா சுமங்கலா (UP)",
                "scam_test": "🚨 மோசடி அழைப்பு OTP எச்சரிக்கை",
            },
            "kn": {
                "pm_kisan": "🌾 ಪಿಎಂ-ಕಿಸಾನ್ ₹6000", "ayushman": "🏥 ಆಯುಷ್ಮಾನ್ ₹5L", "surya_ghar": "☀️ ಸೂರ್ಯ ಘರ್ ಸೋಲಾರ್", "vishwakarma": "🔨 ಪಿಎಂ ವಿಶ್ವಕರ್ಮ",
                "ladki_bahin": "👸 ಲಾಡ್ಕಿ ಬಹಿನ್ (MH)", "gruha_lakshmi": "🏠 ಗೃಹ ಲಕ್ಷ್ಮಿ (KA)", "magalir_urimai": "🌸 ಮಗಳಿರ್ ಉರಿಮೈ (TN)", "kanya_sumangala": "👧 ಕನ್ಯಾ ಸುಮಂಗಲಾ (UP)",
                "scam_test": "🚨 ವಂಚನೆ ಕರೆ OTP ಎಚ್ಚರಿಕೆ",
            },
            "hi": {
                "pm_kisan": "🌾 पीएम-किसान ₹6000", "ayushman": "🏥 आयुष्मान ₹5 लाख", "surya_ghar": "☀️ सूर्य घर सोलर", "vishwakarma": "🔨 पीएम विश्वकर्मा",
                "ladki_bahin": "👸 लाड़की बहिन (MH)", "gruha_lakshmi": "🏠 गृह लक्ष्मी (KA)", "magalir_urimai": "🌸 मगलिर उरीमई (TN)", "kanya_sumangala": "👧 कन्या सुमंगला (UP)",
                "scam_test": "🚨 फ्रॉड अलर्ट: OTP मांगना",
            },
        }
        btn_l = lbl_map.get(selected_lang_code, {
            "pm_kisan": "🌾 PM-Kisan ₹6000", "ayushman": "🏥 Ayushman ₹5L", "surya_ghar": "☀️ Surya Ghar Solar", "vishwakarma": "🔨 PM Vishwakarma",
            "ladki_bahin": "👸 Ladki Bahin (MH ₹1500)", "gruha_lakshmi": "🏠 Gruha Lakshmi (KA ₹2000)", "magalir_urimai": "🌸 Magalir Urimai (TN ₹1000)", "kanya_sumangala": "👧 Kanya Sumangala (UP)",
            "scam_test": "🚨 Scam Test: Fraud caller asking for OTP",
        })

        st.caption("🇮🇳 **Central Welfare Schemes:**")
        c1, c2, c3, c4 = st.columns(4)
        sample_query = None
        if c1.button(btn_l["pm_kisan"], use_container_width=True):
            sample_query = prompts["pm_kisan"]
        if c2.button(btn_l["ayushman"], use_container_width=True):
            sample_query = prompts["ayushman"]
        if c3.button(btn_l["surya_ghar"], use_container_width=True):
            sample_query = prompts["surya_ghar"]
        if c4.button(btn_l["vishwakarma"], use_container_width=True):
            sample_query = prompts["vishwakarma"]

        st.caption("📍 **State Government Welfare Schemes:**")
        s1, s2, s3, s4 = st.columns(4)
        if s1.button(btn_l["ladki_bahin"], use_container_width=True):
            sample_query = prompts["ladki_bahin"]
        if s2.button(btn_l["gruha_lakshmi"], use_container_width=True):
            sample_query = prompts["gruha_lakshmi"]
        if s3.button(btn_l["magalir_urimai"], use_container_width=True):
            sample_query = prompts["magalir_urimai"]
        if s4.button(btn_l["kanya_sumangala"], use_container_width=True):
            sample_query = prompts["kanya_sumangala"]

        st.caption("🛡️ **Security & Anti-Fraud Guardrail:**")
        if st.button(btn_l["scam_test"], use_container_width=True):
            sample_query = prompts["scam_test"]

        st.markdown("</div>", unsafe_allow_html=True)

    with st.expander("⌨️ Or type your question in any Indian script / English"):
        text_input = st.text_input("Type inquiry here", placeholder="e.g. Free ration card kaise milega? / റേഷൻ കാർഡ്", key="manual_scheme_input")
        send_btn = st.button("Submit Inquiry", key="btn_send_scheme")

    # -----------------------------------------------------------------------
    # Process Input: Priority to button clicks & text inputs
    # -----------------------------------------------------------------------
    if audio_to_run:
        # Handled from direct voice sample button
        pass
    elif sample_query:
        query_to_run = sample_query
    elif send_btn and text_input.strip():
        query_to_run = text_input.strip()
    elif recorded_audio and len(recorded_audio) > 400:
        h = hashlib.md5(recorded_audio).hexdigest()
        if st.session_state.get("last_audio_hash") != h:
            st.session_state["last_audio_hash"] = h
            audio_to_run = recorded_audio
            st.session_state["mic_counter"] = st.session_state.get("mic_counter", 0) + 1

    if audio_to_run or query_to_run:
        with st.spinner("⚡ YojanaVaani AI analyzing with Gnani Voice Engine..."):
            try:
                turn = process_voice_turn(
                    user_audio=audio_to_run,
                    user_text=query_to_run,
                    preferred_lang=selected_lang_code,
                    state_filter=clean_state_filter,
                )

                st.session_state["conversation"].append({
                    "role": "user",
                    "text": turn["user_text"],
                    "audio": turn["user_audio"],
                })

                st.session_state["conversation"].append({
                    "role": "assistant",
                    "text": turn["reply_text"],
                    "audio": turn["reply_audio"],
                    "lang": turn["detected_lang"],
                    "scheme": turn["matched_scheme"],
                    "escalate": turn["escalate"],
                })

                st.rerun()

            except GnaniError as e:
                st.error(f"Gnani Engine Notice: {e}")
            except Exception as e:
                st.error(f"Error processing inquiry: {e}")

    # -----------------------------------------------------------------------
    # Conversation Stream
    # -----------------------------------------------------------------------
    st.markdown("---")
    st.markdown("### 💬 Live Interaction Timeline")

    for idx, msg in enumerate(st.session_state["conversation"]):
        is_latest = (idx == len(st.session_state["conversation"]) - 1)
        if msg["role"] == "user":
            with st.chat_message("user", avatar="👤"):
                st.markdown(f"**Citizen**: {msg['text']}")
        else:
            with st.chat_message("assistant", avatar="🇮🇳"):
                st.markdown(f"**YojanaVaani**: {msg['text']}")

                # Directly auto-play spoken voice response so villagers don't need to manually click play!
                if msg.get("audio"):
                    b64_a = base64.b64encode(msg["audio"]).decode("utf-8")
                    auto_flag = "autoplay" if (is_latest and not msg.get("is_welcome", False)) else ""
                    st.markdown(
                        f"""
                        <div style="display: flex; align-items: center; gap: 8px; margin: 6px 0 2px 0;">
                            <span style="font-size: 11px; color: #10b981; font-weight: 700;">🔊 Spoken Voice (Direct Audio):</span>
                        </div>
                        <audio {auto_flag} controls style="width: 100%; height: 38px; border-radius: 8px;">
                            <source src="data:audio/wav;base64,{b64_a}" type="audio/wav">
                        </audio>
                        """,
                        unsafe_allow_html=True,
                    )
                elif key_configured:
                    st.caption("🔊 Spoken audio rendered via Gnani Timbre TTS")

                # Tags / Grounding Badges
                badges = []
                if msg.get("lang"):
                    lang_meta = INDIAN_OFFICIAL_LANGUAGES.get(msg['lang'], {})
                    lang_name = lang_meta.get('name', msg['lang'])
                    badges.append(f"🌐 `{lang_name}`")
                if msg.get("scheme"):
                    s = msg["scheme"]
                    scope_type = "🏛️ Central" if s.get("type") == "Central" else f"📍 State: {s.get('state')}"
                    badges.append(f"{scope_type} — **{s['name']}**")
                if msg.get("escalate"):
                    badges.append("🚨 **Special Triage / Security Alert**")
                if badges:
                    st.caption(" • ".join(badges))

                # Quick link to slide drawer CSC desk for assistance
                if msg.get("scheme"):
                    sch = msg["scheme"]
                    if st.button(f"📋 Need Help with {sch.get('name', 'Scheme')}? Open CSC Desk in Slide Drawer →", key=f"btn_chat_csc_{idx}"):
                        st.session_state["nav_mode"] = "📊 Citizen CSC Desk"
                        st.rerun()

# ===========================================================================
# VIEW 2: FULL TELEPHONY CALLING AGENT CONSOLE (INBOUND & OUTBOUND)
# ===========================================================================
elif st.session_state["nav_mode"] == "📞 1800-YOJANA Telephony Agent":
    st.markdown(
        """
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
            <div>
                <h3 style="margin: 0; font-size: 22px; font-weight: 800;">📞 1800-YOJANA Telephony Voice Agent</h3>
                <div style="font-size: 13px; color: #94a3b8; margin-top: 4px;">
                    Cellular phone agent for 500M+ rural citizens with ₹1,000 keypad feature phones (No Internet / No Smartphone required).
                </div>
            </div>
            <div style="background: rgba(16, 185, 129, 0.12); border: 1px solid rgba(16, 185, 129, 0.4); padding: 6px 14px; border-radius: 9999px; font-size: 11.5px; color: #10b981; font-weight: 700;">
                ● GATEWAY PORT 8000 ACTIVE
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    call_tabs = st.tabs([
        "📥 Inbound Call (1800-200-9652)",
        "📤 Outbound Proactive Call Simulation",
        "📡 Cloud Telephony Gateway & Webhooks",
    ])

    # -----------------------------------------------------------------------
    # TAB 1: INBOUND CALL (CITIZEN CALLS AI)
    # -----------------------------------------------------------------------
    with call_tabs[0]:
        col_phone, col_telephony_guide = st.columns([1, 1.2])

        with col_phone:
            st.markdown(
                """
                <div class="phone-chassis">
                    <div class="phone-notch"></div>
                    <div style="text-align: center; padding: 6px 0 10px 0;">
                        <div style="font-size: 10px; letter-spacing: 2px; color: #94a3b8; font-weight: 700;">BHARAT SEVA TOLL-FREE CALL</div>
                        <div style="font-size: 24px; font-weight: 800; color: #ffffff; font-family: monospace; margin: 3px 0;">1800-200-9652</div>
                        <div style="display: inline-block; padding: 2px 10px; background: rgba(56, 189, 248, 0.15); border: 1px solid rgba(56, 189, 248, 0.3); border-radius: 9999px; font-size: 10px; color: #38bdf8; font-weight: 700;">TOLL-FREE HELPLINE</div>
                        <div style="font-size: 11px; color: #10b981; font-weight: 700; margin-top: 6px;">
                            📱 Live Carrier Number: <span style="font-family: monospace; color: #ffffff;">+1 737 250 8034</span>
                        </div>
                    </div>
                """,
                unsafe_allow_html=True,
            )

            # Telecom simulation mode toggle
            sim_noise = st.checkbox(
                "📻 Simulate 8kHz Telecom Line Noise (Cellular Simulation)",
                value=st.session_state.get("call_telecom_sim", False),
                key="chk_telecom_noise_sim",
                help="Applies narrowband 300Hz-3400Hz telephone filter and cellular channel hiss to demonstrate noise robustness.",
            )
            st.session_state["call_telecom_sim"] = sim_noise

            btn_c1, btn_c2 = st.columns(2)
            with btn_c1:
                if not st.session_state["call_active"]:
                    if st.button("🟢 Dial 1800-200-9652", use_container_width=True, type="primary"):
                        st.session_state["call_active"] = True
                        if selected_lang_code == "te":
                            call_wel = "నమస్కారం! యోజనవాణి ప్రభుత్వ సంక్షేమ కాల్ సెంటర్‌కు స్వాగతం. పీఎం-కిసాన్, ఆయుష్మాన్ భారత్, స్కాలర్‌షిప్‌లు లేదా ఇతర సంక్షేమ పథకాల గురించి మీ ప్రశ్నను అడగండి."
                        elif selected_lang_code == "hi":
                            call_wel = "नमस्ते! योजनावाणी सरकारी कल्याण कॉल सेंटर में आपका स्वागत है। पीएम-किसान, आयुष्मान भारत, छात्रवृत्ति या अन्य योजनाओं के बारे में अपना सवाल पूछें।"
                        else:
                            call_wel = get_welcome_text(selected_lang_code)

                        call_audio = None
                        if has_api_key():
                            try:
                                tts_lang, tts_voice = get_voice_for_language(selected_lang_code)
                                call_audio = synthesize(call_wel, language=tts_lang, voice=tts_voice)
                            except Exception:
                                call_audio = None
                        st.session_state["call_history"] = [
                            {
                                "speaker": "Agent",
                                "text": call_wel,
                                "audio": call_audio,
                            }
                        ]
                        st.rerun()
            with btn_c2:
                if st.session_state["call_active"]:
                    if st.button("🔴 Hang Up Call", use_container_width=True):
                        st.session_state["call_active"] = False
                        st.rerun()

            if st.session_state["call_active"]:
                st.markdown(
                    """
                    <div style="background: rgba(16, 185, 129, 0.15); border: 1px solid rgba(16, 185, 129, 0.4); border-radius: 12px; padding: 10px; text-align: center; margin: 10px 0;">
                        <span style="color: #10b981; font-weight: 800; font-size: 13px;">● CALL IN PROGRESS (Carrier: Jio 4G / BSNL)</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                st.caption("🎙️ **Speak into your phone mic (Auto stops after silence):**")
                call_voice_input = audio_recorder(
                    text="Tap to Speak (Auto-Off Mic)",
                    recording_color="#e53935",
                    neutral_color="#10b981",
                    icon_name="microphone",
                    icon_size="2x",
                    pause_threshold=1.6,
                    energy_threshold=0.001,
                    key="inbound_call_mic",
                )

                # Process spoken telephone audio
                if call_voice_input and len(call_voice_input) > 400:
                    h = hashlib.md5(call_voice_input).hexdigest()
                    if st.session_state.get("last_call_audio_hash") != h:
                        st.session_state["last_call_audio_hash"] = h
                        try:
                            # Apply telephone simulation if enabled
                            processed_audio = call_voice_input
                            if st.session_state.get("call_telecom_sim"):
                                processed_audio = simulate_telephony_channel(call_voice_input)

                            turn = process_voice_turn(
                                user_audio=processed_audio,
                                preferred_lang=selected_lang_code,
                                state_filter=clean_state_filter,
                            )
                            st.session_state["call_history"].append({"speaker": "Caller", "text": turn["user_text"]})
                            st.session_state["call_history"].append({"speaker": "Agent", "text": turn["reply_text"], "audio": turn["reply_audio"]})
                            st.rerun()
                        except Exception as err:
                            st.error(str(err))

                st.markdown("---")
                st.caption("🔢 **Or Tap Dialpad / DTMF Keypad:**")
                d_c1, d_c2, d_c3 = st.columns(3)
                dtmf_triggered = None
                if d_c1.button("1️⃣ PM-Kisan", use_container_width=True, key="dtmf_1"):
                    dtmf_triggered = "పీఎం-కిసాన్ సమ్మాన్ నిధి పథకం వివరాలు చెప్పండి"
                if d_c2.button("2️⃣ Ayushman", use_container_width=True, key="dtmf_2"):
                    dtmf_triggered = "ఆయుష్మాన్ భారత్ ఉచిత వైద్యం పథకం కార్డు వివరాలు చెప్పండి"
                if d_c3.button("3️⃣ Scholarships", use_container_width=True, key="dtmf_3"):
                    dtmf_triggered = "నేషనల్ స్కాలర్‌షిప్ పోర్టల్ మరియు విద్యా దీవెన వివరాలు చెప్పండి"

                d_c4, d_c5, d_c6 = st.columns(3)
                if d_c4.button("4️⃣ Surya Ghar", use_container_width=True, key="dtmf_4"):
                    dtmf_triggered = "పీఎం సూర్య ఘర్ ఉచిత సౌర విద్యుత్ పథకం వివరాలు"
                if d_c5.button("5️⃣ Mudra Loan", use_container_width=True, key="dtmf_5"):
                    dtmf_triggered = "పీఎం ముద్రా వ్యాపార రుణం పథకం వివరాలు"
                if d_c6.button("9️⃣ Sachivalayam", use_container_width=True, key="dtmf_9"):
                    dtmf_triggered = "గ్రామ సచివాలయం మరియు కామన్ సర్వీస్ సెంటర్ సహాయం"

                if dtmf_triggered:
                    turn = process_voice_turn(
                        user_text=dtmf_triggered,
                        preferred_lang=selected_lang_code,
                        state_filter=clean_state_filter,
                    )
                    st.session_state["call_history"].append({"speaker": "Caller (Keypad)", "text": dtmf_triggered})
                    st.session_state["call_history"].append({"speaker": "Agent", "text": turn["reply_text"], "audio": turn["reply_audio"]})
                    st.rerun()

                st.markdown("---")
                st.markdown("##### 📱 Real-Time Audio Earpiece Feed:")
                for c_idx, c_msg in enumerate(st.session_state["call_history"]):
                    is_c_latest = (c_idx == len(st.session_state["call_history"]) - 1)
                    if c_msg["speaker"].startswith("Caller"):
                        st.markdown(f"👤 **{c_msg['speaker']}**: *\"{c_msg['text']}\"*")
                    else:
                        st.markdown(f"🤖 **YojanaVaani Agent**: *\"{c_msg['text']}\"*")
                        if c_msg.get("audio"):
                            b64_c = base64.b64encode(c_msg["audio"]).decode("utf-8")
                            c_auto = "autoplay" if is_c_latest else ""
                            st.markdown(
                                f'<audio {c_auto} controls style="width:100%;height:36px;margin:4px 0;"><source src="data:audio/wav;base64,{b64_c}" type="audio/wav"></audio>',
                                unsafe_allow_html=True,
                            )
            else:
                st.markdown(
                    """
                    <div style="background: rgba(255, 255, 255, 0.03); border: 1px dashed rgba(255, 255, 255, 0.1); border-radius: 12px; padding: 24px; text-align: center; margin: 12px 0;">
                        <div style="font-size: 32px; margin-bottom: 8px;">📞</div>
                        <div style="font-size: 14px; font-weight: 700; color: #ffffff;">Toll-Free Calling Line Idle</div>
                        <div style="font-size: 12px; color: #94a3b8; margin-top: 4px;">Click <b>Dial 1800-200-9652</b> above to simulate an incoming citizen telephone call.</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            st.markdown("</div>", unsafe_allow_html=True)

        with col_telephony_guide:
            st.markdown(
                """
                <div class="glass-card">
                    <div style="font-size: 12px; font-weight: 700; color: #38bdf8; letter-spacing: 1px; margin-bottom: 8px;">TELECOM NETWORK ARCHITECTURE</div>
                    <h3 style="margin: 0 0 10px 0; font-size: 20px;">Dialing from Any Physical Phone</h3>
                    <p style="font-size: 13px; color: #94a3b8; line-height: 1.6;">
                        YojanaVaani AI is designed so that a rural citizen with a ₹1,000 keypad phone (no internet, no smartphone) can dial an ordinary phone number and converse with our AI in their native dialect.
                    </p>
                    
                    <div style="background: rgba(0,0,0,0.3); border-radius: 12px; padding: 14px; margin: 14px 0; font-family: monospace; font-size: 12px; line-height: 1.8; color: #a5f3fc;">
                        📱 Physical Feature Phone (Jio / Airtel / BSNL)<br>
                        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;│ (Cellular Call over Telecom Tower)<br>
                        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;▼<br>
                        🏢 Cloud Telephony Gateway (Exotel / Twilio / Tata Tele)<br>
                        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;│ (TwiML / XML Webhook & Audio Stream)<br>
                        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;▼<br>
                        🚀 YojanaVaani Server (<code>telephony_server.py:8000</code>)<br>
                        &nbsp;&nbsp;&nbsp;&nbsp;├── 🎙️ DSP Telephony Filter (300-3400Hz speech boost)<br>
                        &nbsp;&nbsp;&nbsp;&nbsp;├── 🗣️ Prisma STT (indic-auto: dialect & accent robust)<br>
                        &nbsp;&nbsp;&nbsp;&nbsp;├── 🧠 Welfare Grounding (29+ Central/State schemes)<br>
                        &nbsp;&nbsp;&nbsp;&nbsp;└── 🔊 Timbre TTS (Low-latency regional stream)
                    </div>

                    <div style="background: rgba(56, 189, 248, 0.08); border-left: 3px solid #38bdf8; padding: 10px 14px; border-radius: 0 8px 8px 0; font-size: 12.5px; color: #cbd5e1;">
                        <b>Challenge Category Target:</b> Directly fulfills the <b>"Noisy Telephonic Audio"</b> track (₹50,000) by demonstrating end-to-end voice handling over real 8kHz/16kHz telephone audio.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # -----------------------------------------------------------------------
    # TAB 2: OUTBOUND PROACTIVE CALL SIMULATION
    # -----------------------------------------------------------------------
    with call_tabs[1]:
        col_out_phone, col_out_info = st.columns([1, 1.2])

        with col_out_phone:
            st.markdown(
                """
                <div class="phone-chassis">
                    <div class="phone-notch"></div>
                    <div style="text-align: center; padding: 6px 0 10px 0;">
                        <div style="font-size: 10px; letter-spacing: 2px; color: #10b981; font-weight: 700;">PROACTIVE OUTBOUND CALL</div>
                        <div style="font-size: 20px; font-weight: 800; color: #ffffff; margin: 3px 0;">GOVT HELPLINE ALERT</div>
                        <div style="font-size: 11px; color: #94a3b8;">+91 1800-200-9652</div>
                    </div>
                """,
                unsafe_allow_html=True,
            )

            out_scenario_key = st.selectbox(
                "Select Government Notification Scenario",
                list(OUTBOUND_CALL_SCENARIOS.keys()),
                format_func=lambda k: OUTBOUND_CALL_SCENARIOS[k]["title"],
                key="sel_outbound_scenario",
            )
            scenario_meta = OUTBOUND_CALL_SCENARIOS[out_scenario_key]

            if not st.session_state.get("outbound_call_active"):
                st.markdown(
                    f"""
                    <div style="background: rgba(56, 189, 248, 0.08); border: 1px dashed rgba(56, 189, 248, 0.3); border-radius: 12px; padding: 14px; text-align: center; margin: 12px 0;">
                        <div style="font-size: 11px; color: #38bdf8; font-weight: 700;">{scenario_meta['agency'].upper()}</div>
                        <div style="font-size: 14px; font-weight: 700; color: #ffffff; margin-top: 4px;">{scenario_meta['title']}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                if st.button("📲 Simulate Incoming Government Call", use_container_width=True, type="primary"):
                    st.session_state["outbound_call_active"] = True
                    out_text = scenario_meta.get(selected_lang_code, scenario_meta.get("en", ""))
                    out_audio = None
                    if has_api_key():
                        try:
                            tts_lang, tts_voice = get_voice_for_language(selected_lang_code)
                            out_audio = synthesize(out_text, language=tts_lang, voice=tts_voice)
                        except Exception:
                            out_audio = None
                    st.session_state["outbound_history"] = [
                        {
                            "speaker": "Govt Agent (Outbound)",
                            "text": out_text,
                            "audio": out_audio,
                        }
                    ]
                    st.rerun()

            else:
                st.markdown(
                    """
                    <div style="background: rgba(16, 185, 129, 0.15); border: 1px solid rgba(16, 185, 129, 0.4); border-radius: 12px; padding: 10px; text-align: center; margin: 10px 0;">
                        <span style="color: #10b981; font-weight: 800; font-size: 13px;">● OUTBOUND CALL CONNECTED (Listening to Citizen)</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                if st.button("🔴 Hang Up Call", use_container_width=True, key="btn_hangup_outbound"):
                    st.session_state["outbound_call_active"] = False
                    st.rerun()

                st.caption("🎙️ **Citizen reply (Speak to ask questions or verify status):**")
                out_reply_voice = audio_recorder(
                    text="Speak your reply...",
                    recording_color="#e53935",
                    neutral_color="#10b981",
                    icon_name="microphone",
                    icon_size="2x",
                    pause_threshold=1.6,
                    energy_threshold=0.001,
                    key="outbound_reply_mic",
                )

                if out_reply_voice and len(out_reply_voice) > 400:
                    turn = process_voice_turn(
                        user_audio=out_reply_voice,
                        preferred_lang=selected_lang_code,
                        state_filter=clean_state_filter,
                    )
                    st.session_state["outbound_history"].append({"speaker": "Citizen", "text": turn["user_text"]})
                    st.session_state["outbound_history"].append({"speaker": "Govt Agent", "text": turn["reply_text"], "audio": turn["reply_audio"]})
                    st.rerun()

                st.markdown("---")
                st.markdown("##### 📱 Real-Time Call Audio:")
                for o_idx, o_msg in enumerate(st.session_state.get("outbound_history", [])):
                    is_o_latest = (o_idx == len(st.session_state["outbound_history"]) - 1)
                    if o_msg["speaker"] == "Citizen":
                        st.markdown(f"👤 **{o_msg['speaker']}**: *\"{o_msg['text']}\"*")
                    else:
                        st.markdown(f"🤖 **{o_msg['speaker']}**: *\"{o_msg['text']}\"*")
                        if o_msg.get("audio"):
                            b64_o = base64.b64encode(o_msg["audio"]).decode("utf-8")
                            o_auto = "autoplay" if is_o_latest else ""
                            st.markdown(
                                f'<audio {o_auto} controls style="width:100%;height:36px;margin:4px 0;"><source src="data:audio/wav;base64,{b64_o}" type="audio/wav"></audio>',
                                unsafe_allow_html=True,
                            )

            st.markdown("</div>", unsafe_allow_html=True)

        with col_out_info:
            st.markdown(
                """
                <div class="glass-card">
                    <div style="font-size: 12px; font-weight: 700; color: #10b981; letter-spacing: 1px; margin-bottom: 8px;">GOVERNMENT OUTBOUND DISPATCH</div>
                    <h3 style="margin: 0 0 10px 0; font-size: 20px;">Proactive Welfare Voice Notifications</h3>
                    <p style="font-size: 13px; color: #94a3b8; line-height: 1.6;">
                        Instead of waiting for rural citizens to find out about scheme deadlines, departments can trigger automated voice calls that notify beneficiaries in their native dialect and answer their follow-up questions immediately.
                    </p>
                    
                    <div style="background: rgba(0,0,0,0.3); border-radius: 12px; padding: 14px; margin: 14px 0; font-size: 12.5px; line-height: 1.8; color: #cbd5e1;">
                        <b>Key Use Cases:</b><br>
                        • 🌾 <b>PM-Kisan</b>: Payment credit confirmation and biometric e-KYC reminders.<br>
                        • 🎓 <b>Scholarships</b>: Application deadline alerts for SC/ST/OBC students.<br>
                        • 🏥 <b>Ayushman Bharat</b>: Golden Card distribution alerts in rural wards.<br>
                        • ⚡ <b>Surya Ghar</b>: Solar rooftop subsidy status notifications.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # -----------------------------------------------------------------------
    # TAB 3: CARRIER INTEGRATION (EXOTEL / TWILIO / TATA TELE)
    # -----------------------------------------------------------------------
    with call_tabs[2]:
        st.markdown("### 📡 Live Telecom Gateway Integration (Exotel / Twilio / Tata Tele)")
        st.caption("How to point a real 10-digit Indian virtual phone number to YojanaVaani AI:")

        g_col1, g_col2 = st.columns(2)
        with g_col1:
            st.markdown(
                """
                <div class="glass-card">
                    <h4 style="margin: 0 0 8px 0; color: #38bdf8;">1. Exotel / Twilio Webhook Endpoints</h4>
                    <p style="font-size: 12.5px; color: #94a3b8;">
                        Configure these URLs in your Cloud Telephony dashboard:
                    </p>
                    <div style="background: #0f172a; padding: 10px; border-radius: 8px; font-family: monospace; font-size: 12px; margin-bottom: 8px;">
                        <b>Incoming Call URL (HTTP POST):</b><br>
                        <code>https://&lt;your-public-url&gt;/call/incoming</code>
                    </div>
                    <div style="background: #0f172a; padding: 10px; border-radius: 8px; font-family: monospace; font-size: 12px; margin-bottom: 8px;">
                        <b>Speech Process URL (HTTP POST):</b><br>
                        <code>https://&lt;your-public-url&gt;/call/process</code>
                    </div>
                    <div style="background: #0f172a; padding: 10px; border-radius: 8px; font-family: monospace; font-size: 12px;">
                        <b>DTMF Keypad URL (HTTP POST):</b><br>
                        <code>https://&lt;your-public-url&gt;/call/dtmf</code>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with g_col2:
            st.markdown(
                """
                <div class="glass-card">
                    <h4 style="margin: 0 0 8px 0; color: #10b981;">2. Trigger Outbound Call via REST API</h4>
                    <p style="font-size: 12.5px; color: #94a3b8;">
                        Government departments can dispatch calls programmatically:
                    </p>
                    <div style="background: #0f172a; padding: 10px; border-radius: 8px; font-family: monospace; font-size: 11.5px; line-height: 1.6;">
                        curl -X POST "http://127.0.0.1:8000/call/outbound" \\<br>
                        &nbsp;&nbsp;-H "Content-Type: application/json" \\<br>
                        &nbsp;&nbsp;-d '{"phone_number": "+919876543210", "scenario_id": "pm_kisan_dbt", "language": "te"}'
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

# ===========================================================================
# VIEW 3: CENTRAL & STATE SCHEMES DIRECTORY
# ===========================================================================
elif st.session_state["nav_mode"] == "📚 Schemes Directory":
    st.markdown("### 📚 Comprehensive Government Schemes Repository")
    st.caption("Explore verified Central and State welfare programs across 28 States & UTs.")

    all_schemes = _load_kb()

    f1, f2, f3 = st.columns(3)
    with f1:
        type_options = ["All Types (Central + State)", "Central", "State"]
        sel_type = st.selectbox("Filter Scheme Level", type_options)

    with f2:
        states_in_db = sorted(list(set(s.get("state", "All India") for s in all_schemes)))
        sel_state = st.selectbox("Filter State / Territory", ["All States / UTs"] + states_in_db)

    with f3:
        categories = sorted(list(set(s.get("category", "General") for s in all_schemes)))
        sel_cat = st.selectbox("Filter Welfare Domain", ["All Categories"] + categories)

    # Filter schemes
    filtered = all_schemes
    if sel_type == "Central":
        filtered = [s for s in filtered if s.get("type") == "Central"]
    elif sel_type == "State":
        filtered = [s for s in filtered if s.get("type") == "State"]

    if sel_state != "All States / UTs":
        filtered = [s for s in filtered if s.get("state") == sel_state]

    if sel_cat != "All Categories":
        filtered = [s for s in filtered if s.get("category") == sel_cat]

    st.markdown(f"**Displaying {len(filtered)} Verified Schemes:**")

    for item in filtered:
        with st.container():
            st_badge = "🇮🇳 Central Scheme" if item.get("type") == "Central" else f"📍 State Scheme ({item.get('state')})"
            st.markdown(
                f"""
                <div class="glass-card" style="margin-bottom: 14px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                        <h3 style="margin: 0; font-size: 18px; color: #ffffff;">{item['name']}</h3>
                        <span style="background: rgba(56, 189, 248, 0.15); border: 1px solid rgba(56, 189, 248, 0.3); padding: 3px 10px; border-radius: 9999px; font-size: 11px; color: #38bdf8; font-weight: 700;">{st_badge}</span>
                    </div>
                    <div style="font-size: 12px; color: #94a3b8; margin-bottom: 12px;">📁 Domain: <b>{item.get('category', 'General')}</b></div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            d1, d2, d3 = st.columns(3)
            with d1:
                st.markdown("**💰 Key Financial Benefit:**")
                st.info(item.get("benefit", "Government assistance"))
            with d2:
                st.markdown("**🎯 Eligibility Criteria:**")
                st.write(item.get("eligibility", "As per guidelines"))
            with d3:
                st.markdown("**📑 Required Documents:**")
                st.write(item.get("documents", "Identity & Income proofs"))

            with st.expander(f"Multilingual Explanations for {item['name']}"):
                st.markdown(f"**Hinglish:** {item.get('answer_hinglish', '')}")
                st.markdown(f"**Hindi:** {item.get('answer_hi', '')}")
                st.markdown(f"**English:** {item.get('answer_en', '')}")
            st.markdown("---")

# ===========================================================================
# VIEW 4: CITIZEN CSC & GRAM PANCHAYAT DESK
# ===========================================================================
elif st.session_state["nav_mode"] == "📊 Citizen CSC Desk":
    st.markdown("### 📊 Citizen CSC & Gram Panchayat Desk")
    st.caption("Citizen assistance ticket registry and live service demand telemetry.")

    with st.expander("📝 Register New Citizen Assistance Follow-up", expanded=True):
        all_schemes = _load_kb()
        scheme_titles = [f"{s['name']} ({s.get('state', 'Central')})" for s in all_schemes]
        
        with st.form("desk_citizen_apply_form"):
            cf1, cf2 = st.columns(2)
            with cf1:
                citizen_name = st.text_input("Citizen Full Name", placeholder="e.g. Ramesh Kumar / రైతు పేరు")
            with cf2:
                village = st.text_input("Village / Town & District", placeholder="e.g. Rampur, Varanasi / ఊరు లేదా జిల్లా")
            
            selected_scheme_str = st.selectbox("Select Target Welfare Program", scheme_titles)
            matched_s = next((s for s in all_schemes if f"{s['name']} ({s.get('state', 'Central')})" == selected_scheme_str), all_schemes[0])
            
            notes = st.text_input("Assistance Required", placeholder="e.g. Biometric eKYC, land record linking, payment status check")
            
            submit_req = st.form_submit_button("Submit Assistance Ticket", type="primary")
            if submit_req:
                try:
                    if privacy_warning(notes):
                        raise ValueError("Do not include sensitive OTPs or card numbers.")
                    req_id = create_scheme_request(
                        citizen_name=citizen_name,
                        village_or_town=village,
                        scheme_id=matched_s["id"],
                        scheme_name=matched_s["name"],
                        notes=notes,
                    )
                    st.success(f"✅ Assistance Request #{req_id} logged for {citizen_name}! Assigned to local CSC / Panchayat officer.")
                    st.rerun()
                except Exception as err:
                    st.error(str(err))

    st.markdown("---")
    st.markdown("#### 📈 Real-Time Field Telemetry & Registered Tickets")

    stats = get_scheme_stats()
    m1, m2, m3 = st.columns(3)
    m1.metric("Total Citizen Consultations", stats["total"])
    m2.metric("Distinct Welfare Programs", len(stats["by_scheme"]))
    m3.metric("Pending Field Follow-ups", stats["total"])

    if stats["by_scheme"]:
        st.markdown("##### Citizen Inquiries by Welfare Domain")
        st.bar_chart(stats["by_scheme"])

    st.markdown("##### Live Field Assistance Registry (SQLite Database)")
    if stats["recent"]:
        st.table([
            {
                "Ticket #": r[0],
                "Citizen Name": r[1],
                "Village / District": r[2],
                "Scheme Requested": r[3],
                "Citizen Notes": r[4],
                "Status": r[5],
                "Logged At (UTC)": r[6][:19],
            }
            for r in stats["recent"]
        ])
    else:
        st.info("No field assistance requests logged yet. Inquiries with follow-up requests will appear here.")
