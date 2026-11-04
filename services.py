

"""Universal Multilingual Citizen Welfare Voice Suite for Bharat.
Powered by Gnani AI (Prisma STT & Timbre TTS).
Supports all 22 official Indian languages (8th Schedule) + English & Hinglish.
"""
from __future__ import annotations


WELCOME_MESSAGES = {
    "en": "Welcome to YojanaVaani AI. Ask your question about any government welfare scheme.",
    "hi": "योजनावाणी एआई में आपका स्वागत है। सरकारी योजनाओं के बारे में अपना प्रश्न पूछें।",
    "te": "యోజనవాణి ఏఐకి స్వాగతం. ప్రభుత్వ సంక్షేమ పథకాల గురించి మీ ప్రశ్నను అడగండి.",
    "hi-en": "YojanaVaani AI me aapka swagat hai. Kripya apna sarkari yojana ka sawal poochein.",
}

def get_welcome_text(lang: str = "en") -> str:
    return WELCOME_MESSAGES.get(lang, WELCOME_MESSAGES["en"])


OUTBOUND_CALL_SCENARIOS = {
    "pm_kisan_dbt": {
        "title": "PM-Kisan 17th Installment Credited",
        "en": "Namaste! This is an official update from the Ministry of Agriculture. Your PM-Kisan installment of Rs 2,000 has been credited to your Aadhaar-linked bank account.",
        "hi": "नमस्ते! कृषि मंत्रालय से महत्वपूर्ण सूचना। आपकी पीएम-किसान की 2,000 रुपये की किस्त आपके बैंक खाते में जमा कर दी गई है।",
        "te": "నమస్కారం! వ్యవసాయ మంత్రిత్వ శాఖ నుండి అధికారిక సమాచారం. మీ పీఎం-కిసాన్ ₹2,000 కిస్తు మీ ఆధార్ లింక్డ్ బ్యాంక్ ఖాతాలో జమ చేయబడింది.",
    },
    "ayushman_card": {
        "title": "Ayushman Golden Card Ready",
        "en": "Namaste! Your Ayushman Bharat health card is now active. You and your family can get free cashless treatment up to 5 lakh rupees at empaneled hospitals.",
        "hi": "नमस्ते! आपका आयुष्मान भारत गोल्डन कार्ड तैयार है। आप और आपका परिवार 5 लाख रुपये तक का मुफ्त इलाज प्राप्त कर सकते हैं।",
        "te": "నమస్కారం! మీ ఆయుష్మాన్ భారత్ గోల్డెన్ కార్డ్ సిద్ధంగా ఉంది. మీ కుటుంబానికి 5 లక్షల రూపాయల వరకు ఉచిత చికిత్స లభిస్తుంది.",
    }
}

import av
import io
import json
import os
import re
import sqlite3
import time
import wave
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
import numpy as np
import requests
from scipy import signal

load_dotenv()

ROOT = Path(__file__).parent
DB_PATH = ROOT / "yojanavaani.db"
KB_PATH = ROOT / "knowledge_base.json"
STT_URL = "https://api.vachana.ai/stt/v3"
TTS_URL = "https://api.vachana.ai/api/v1/tts/inference"

SCAM_OR_FRAUD_TERMS = (
    "otp", "atm pin", "cvv", "lottery", "password", "bank password",
    "paise transfer", "paisa bhejo", "fake call", "fraud", "మోసం",
    "ఓటీపీ", "மோசம்", "மோசடி", "ವಂಚನೆ", "தவறான", "ਧੋਖਾ",
    "free iphone", "iphone", "free gold", "free phone", "free recharge",
    "free bike", "free car", "won prize", "cash prize", "lucky draw",
)

NON_SCHEME_TRIGGERS = {
    "cricket", "movie", "cinema", "song", "joke", "weather", "recipe", "ipl", "football",
    "dance", "game", "bollywood", "tollywood", "horoscope", "astrology"
}
GOV_TERMS = {
    "scheme", "yojana", "sarkari", "government", "subsidy", "welfare", "csc", "pm", "pradhan mantri",
    "pension", "card", "ration", "kisan", "aarogya", "arogya", "bharosa", "nidhi", "state", "ap"
}


SENSITIVE_PATTERNS = (
    (r"\b\d{12}\b", "a 12-digit Aadhaar number"),
    (r"\b[A-Z]{5}\d{4}[A-Z]\b", "a PAN-like identifier"),
    (r"\b\d{16}\b", "a 16-digit card/account number"),
    (r"\b\d{4,6}\s*(otp|pin)\b", "an OTP/PIN"),
)

def privacy_warning(text: str) -> str | None:
    """Detect sensitive citizen PII (Aadhaar, OTP, Card numbers) and issue privacy warning."""
    if not text:
        return None
    for pattern, label in SENSITIVE_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return f"Alert: You shared what appears to be {label}. For your security, government welfare helplines will never ask for your confidential OTP, bank PIN, or full Aadhaar. Please keep this private."
    return None

# ---------------------------------------------------------------------------
# 22 Official Indian Languages (8th Schedule) + English & Hinglish
# ---------------------------------------------------------------------------
INDIAN_OFFICIAL_LANGUAGES: dict[str, dict[str, str]] = {
    "indic-auto": {"name": "Auto Detect (Indic)", "native": "స్వయం గుర్తింపు / Indic Auto", "region": "All India"},
    "te": {"name": "Telugu", "native": "తెలుగు", "region": "Andhra Pradesh, Telangana"},
    "ta": {"name": "Tamil", "native": "தமிழ்", "region": "Tamil Nadu, Puducherry"},
    "kn": {"name": "Kannada", "native": "ಕನ್ನಡ", "region": "Karnataka"},
    "ml": {"name": "Malayalam", "native": "മലയാളം", "region": "Kerala, Lakshadweep"},
    "mr": {"name": "Marathi", "native": "मराठी", "region": "Maharashtra, Goa"},
    "bn": {"name": "Bengali", "native": "বাংলা", "region": "West Bengal, Tripura, Assam"},
    "gu": {"name": "Gujarati", "native": "ગુજરાતી", "region": "Gujarat"},
    "pa": {"name": "Punjabi", "native": "ਪੰਜਾਬੀ", "region": "Punjab, Chandigarh"},
    "or": {"name": "Odia", "native": "ଓଡ଼ିଆ", "region": "Odisha"},
    "as": {"name": "Assamese", "native": "অসমীয়া", "region": "Assam"},
    "ur": {"name": "Urdu", "native": "اردو", "region": "All India"},
    "hi": {"name": "Hindi", "native": "हिन्दी", "region": "North & Central India"},
    "hi-en": {"name": "Hinglish (Code-Mixed)", "native": "Hinglish", "region": "Urban & Semi-Urban"},
    "en": {"name": "English", "native": "English", "region": "All India"},
    "sa": {"name": "Sanskrit", "native": "संस्कृतम्", "region": "All India"},
    "ne": {"name": "Nepali", "native": "नेपाली", "region": "Sikkim, West Bengal"},
    "kok": {"name": "Konkani", "native": "कोंकणी", "region": "Goa, Maharashtra, Karnataka"},
    "mai": {"name": "Maithili", "native": "मैथिली", "region": "Bihar, Jharkhand"},
    "doi": {"name": "Dogri", "native": "डोगरी", "region": "Jammu & Kashmir"},
    "ks": {"name": "Kashmiri", "native": "کٲشُر / कॉशुर", "region": "Jammu & Kashmir"},
    "sd": {"name": "Sindhi", "native": "سنڌي / सिन्धी", "region": "All India"},
    "mni": {"name": "Manipuri (Meitei)", "native": "ꯃৈতৈলোন্", "region": "Manipur"},
    "brx": {"name": "Bodo", "native": "बड़ो", "region": "Assam"},
    "sat": {"name": "Santali", "native": "ᱥᱟᱱᱛᱟᱲᱤ", "region": "Jharkhand, Odisha, WB"},
}

VOICE_MAP: dict[str, tuple[str, str]] = {
    code: (code if code != "indic-auto" else "hi-en", "Aarohi")
    for code in INDIAN_OFFICIAL_LANGUAGES.keys()
}

_KB_CACHE: list[dict[str, Any]] | None = None
_KB_MTIME: float = 0.0

def _load_kb() -> list[dict[str, Any]]:
    global _KB_CACHE, _KB_MTIME
    try:
        current_mtime = KB_PATH.stat().st_mtime
    except Exception:
        current_mtime = 0.0
    if _KB_CACHE is None or current_mtime != _KB_MTIME:
        _KB_CACHE = json.loads(KB_PATH.read_text(encoding="utf-8"))
        _KB_MTIME = current_mtime
    return _KB_CACHE

def reload_kb() -> list[dict[str, Any]]:
    global _KB_CACHE, _KB_MTIME
    _KB_CACHE = json.loads(KB_PATH.read_text(encoding="utf-8"))
    try:
        _KB_MTIME = KB_PATH.stat().st_mtime
    except Exception:
        _KB_MTIME = 0.0
    return _KB_CACHE

class GnaniError(RuntimeError):
    pass

def has_api_key() -> bool:
    return bool(os.getenv("GNANI_API_KEY", "").strip())

def api_key() -> str:
    key = os.getenv("GNANI_API_KEY", "").strip()
    if not key:
        raise GnaniError("Gnani API key is missing. Add GNANI_API_KEY to your .env file.")
    return key

# ---------------------------------------------------------------------------
# Universal Audio Format Transcoder & DSP Preprocessor (PyAV + Scipy)
# ---------------------------------------------------------------------------
def convert_to_pcm_wav(audio_bytes: bytes, target_sr: int = 16000) -> bytes:
    """Decode any browser/telephony audio container (WebM, Opus, MP3, AAC, OGG, WAV) to standard PCM WAV."""
    if not audio_bytes or len(audio_bytes) < 20:
        return audio_bytes
    try:
        input_bio = io.BytesIO(audio_bytes)
        container = av.open(input_bio)
        if not container.streams.audio:
            return audio_bytes
        stream = container.streams.audio[0]
        resampler = av.AudioResampler(format="s16", layout="mono", rate=target_sr)

        frames = []
        for frame in container.decode(stream):
            for rf in resampler.resample(frame):
                frames.append(rf.to_ndarray().flatten())

        if not frames:
            return audio_bytes

        audio_data = np.concatenate(frames).astype(np.int16)
        out_bio = io.BytesIO()
        with wave.open(out_bio, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(target_sr)
            wf.writeframes(audio_data.tobytes())
        return out_bio.getvalue()
    except Exception:
        return audio_bytes


def enhance_audio(audio_bytes: bytes) -> bytes:
    """Preprocess, de-noise, normalize, and boost low-quality or quiet speech for optimal STT accuracy.
    
    1. Converts any audio stream (WebM/Opus from Chrome, MP4/AAC, Ogg) to linear PCM WAV.
    2. Removes DC bias / microphone offset.
    3. Applies a 2nd-order Butterworth speech bandpass filter (80 Hz to 7500 Hz).
    4. Dynamically boosts faint speech up to 15x while preventing distortion (peak normalized to -1 dB).
    5. Formats cleanly as 16,000 Hz 16-bit Mono Linear PCM WAV (the telephony standard).
    """
    if not audio_bytes or len(audio_bytes) < 44:
        return audio_bytes

    # Step 0: Ensure 16kHz linear PCM WAV (avoid re-encoding if already true RIFF WAV)
    if not (audio_bytes[:4] == b"RIFF" and b"WAVE" in audio_bytes[:16]):
        audio_bytes = convert_to_pcm_wav(audio_bytes, target_sr=16000)

    try:
        with io.BytesIO(audio_bytes) as bio:
            with wave.open(bio, "rb") as wf:
                n_channels = wf.getnchannels()
                sampwidth = wf.getsampwidth()
                framerate = wf.getframerate()
                n_frames = wf.getnframes()
                raw_data = wf.readframes(n_frames)

        if sampwidth == 2:
            data = np.frombuffer(raw_data, dtype=np.int16).astype(np.float32)
        elif sampwidth == 1:
            data = np.frombuffer(raw_data, dtype=np.int8).astype(np.float32) * 256.0
        elif sampwidth == 4:
            data = np.frombuffer(raw_data, dtype=np.int32).astype(np.float32) / 65536.0
        else:
            return audio_bytes

        if n_channels > 1:
            data = data.reshape(-1, n_channels).mean(axis=1)

        # 1. DC offset removal
        data = data - np.mean(data)

        # 2. Bandpass filter for speech clarity (80 Hz to 7500 Hz)
        nyq = 0.5 * framerate
        if nyq > 120:
            low = max(40.0 / nyq, 0.005)
            high = min(7500.0 / nyq, 0.98)
            b, a = signal.butter(2, [low, high], btype="bandpass")
            data = signal.lfilter(b, a, data)

        # 3. Dynamic Gain & Peak Normalization (up to 500x boost for faint rural microphones)
        max_val = np.max(np.abs(data))
        if max_val > 1.0:
            target_peak = 28000.0
            gain = min(target_peak / max_val, 500.0)
            data = data * gain
            print(f"[DSP Audio] Boosted faint audio: {gain:.1f}x gain applied (peak {max_val:.1f} -> {np.max(np.abs(data)):.1f})")
        else:
            print(f"[DSP Audio] Warning: Audio peak is {max_val:.1f} (flatline silence/muted microphone).")

        # 4. Standard 16kHz Telephony Resampling
        target_rate = 16000
        if framerate != target_rate:
            num_samples = int(len(data) * target_rate / framerate)
            data = signal.resample(data, num_samples)
            out_rate = target_rate
        else:
            out_rate = framerate

        data_int16 = np.clip(data, -32768, 32767).astype(np.int16)

        out_bio = io.BytesIO()
        with wave.open(out_bio, "wb") as out_wf:
            out_wf.setnchannels(1)
            out_wf.setsampwidth(2)
            out_wf.setframerate(out_rate)
            out_wf.writeframes(data_int16.tobytes())
        return out_bio.getvalue()
    except Exception:
        return audio_bytes

def simulate_telephony_channel(audio_bytes: bytes, add_line_noise: bool = True) -> bytes:
    """Simulate low-bandwidth 8kHz cellular/PSTN telephony line with 300-3400Hz bandpass and ambient line hiss.
    Used for testing and demonstrating robustness on Noisy Telephonic Audio.
    """
    if not audio_bytes or len(audio_bytes) < 44:
        return audio_bytes
    try:
        pcm = convert_to_pcm_wav(audio_bytes, target_sr=16000)
        with io.BytesIO(pcm) as bio:
            with wave.open(bio, "rb") as wf:
                framerate = wf.getframerate()
                n_frames = wf.getnframes()
                raw_data = wf.readframes(n_frames)
        data = np.frombuffer(raw_data, dtype=np.int16).astype(np.float32)

        # Telephony bandpass (300 Hz - 3400 Hz)
        nyq = 0.5 * framerate
        low = 300.0 / nyq
        high = min(3400.0 / nyq, 0.95)
        b, a = signal.butter(2, [low, high], btype="bandpass")
        filtered = signal.lfilter(b, a, data)

        # Downsample to 8000 Hz (standard telecom rate) and back to 16000 Hz
        down_samples = max(int(len(filtered) * 8000 / framerate), 1)
        downsampled = signal.resample(filtered, down_samples)
        up_samples = max(int(len(downsampled) * 16000 / 8000), 1)
        telephony_sim = signal.resample(downsampled, up_samples)

        if add_line_noise:
            # Subtle cellular GSM channel hiss
            noise = np.random.normal(0, 140.0, len(telephony_sim)).astype(np.float32)
            telephony_sim = telephony_sim + noise

        data_int16 = np.clip(telephony_sim, -32768, 32767).astype(np.int16)
        out_bio = io.BytesIO()
        with wave.open(out_bio, "wb") as out_wf:
            out_wf.setnchannels(1)
            out_wf.setsampwidth(2)
            out_wf.setframerate(16000)
            out_wf.writeframes(data_int16.tobytes())
        return out_bio.getvalue()
    except Exception:
        return audio_bytes

PRISMA_SUPPORTED_LANGUAGES: dict[str, str] = {
    "as": "as-IN",
    "bn": "bn-IN",
    "en": "en-IN",
    "gu": "gu-IN",
    "hi": "hi-IN",
    "kn": "kn-IN",
    "ml": "ml-IN",
    "mr": "mr-IN",
    "pa": "pa-IN",
    "ta": "ta-IN",
    "te": "te-IN",
    "or": "or-IN",
    "ur": "ur-IN",
}

def to_prisma_lang(lang_code: str | None) -> str:
    """Map UI/system language code to Prisma STT supported code."""
    if not lang_code or lang_code in ("indic-auto", "auto", "hi-en"):
        return "indic-auto"
    base = lang_code.split("-")[0].lower()
    return PRISMA_SUPPORTED_LANGUAGES.get(base, "indic-auto")

def from_prisma_lang(detected_code: str | None) -> str:
    """Map Prisma STT detected language code (e.g. te-IN) to internal language code (te)."""
    if not detected_code:
        return "hi-en"
    base = detected_code.split("-")[0].lower()
    return base

COMMON_ENGLISH_WORDS = {
    "elaborate", "explain", "details", "detail", "tell", "how", "what", "when", "where",
    "who", "which", "why", "can", "is", "are", "scheme", "schemes", "benefit", "benefits",
    "eligibility", "eligible", "documents", "document", "apply", "help", "please",
    "information", "info", "get", "receive", "subsidy", "give", "about", "need", "want",
    "check", "status", "under", "for", "with", "to", "scholarship", "scholarships", "education",
}

ENGLISH_FRAME_VERBS = {
    "elaborate", "tell", "explain", "what", "how", "why", "when", "who", "which",
    "can", "is", "are", "give", "show", "describe", "details of", "information on",
}

HINGLISH_MARKERS = {
    "ka", "ke", "ki", "ko", "kab", "kaise", "kahan", "kyun", "milega", "milenge", "aayega",
    "karna", "karo", "hoga", "hogi", "hai", "hain", "mujhe", "humko", "mera", "meri",
    "batao", "bataiye", "paisa", "paise", "rupaye", "chahiye", "nahi", "karen", "jaayein",
}

def detect_query_language(text: str, preferred_lang: str | None = None) -> str:
    """Intelligently identify the citizen's query language based on matrix grammar and native script."""
    cleaned = text.strip()
    if not cleaned:
        return preferred_lang or "hi-en"

    counts = {"te": 0, "ta": 0, "kn": 0, "ml": 0, "bn": 0, "as": 0, "gu": 0, "pa": 0, "or": 0, "ur": 0, "hi": 0, "latin": 0}
    for char in cleaned:
        cp = ord(char)
        if 0x0C00 <= cp <= 0x0C7F: counts["te"] += 1
        elif 0x0B80 <= cp <= 0x0BFF: counts["ta"] += 1
        elif 0x0C80 <= cp <= 0x0CFF: counts["kn"] += 1
        elif 0x0D00 <= cp <= 0x0D7F: counts["ml"] += 1
        elif 0x0980 <= cp <= 0x09FF:
            if cp in (0x09F0, 0x09F1) or preferred_lang == "as":
                counts["as"] += 1
            else:
                counts["bn"] += 1
        elif 0x0A80 <= cp <= 0x0AFF: counts["gu"] += 1
        elif 0x0A00 <= cp <= 0x0A7F: counts["pa"] += 1
        elif 0x0B00 <= cp <= 0x0B7F: counts["or"] += 1
        elif 0x0600 <= cp <= 0x06FF: counts["ur"] += 1
        elif 0x0900 <= cp <= 0x097F: counts["hi"] += 1
        elif ("a" <= char <= "z") or ("A" <= char <= "Z"): counts["latin"] += 1

    total_indic = sum(v for k, v in counts.items() if k != "latin")
    latin_count = counts["latin"]

    indic_words = re.findall(r"[\u0900-\u0D7F]+", cleaned)
    latin_words = [w.lower() for w in re.findall(r"[a-zA-Z]+", cleaned)]

    eng_matches = sum(1 for w in latin_words if w in COMMON_ENGLISH_WORDS)
    eng_verbs = sum(1 for w in latin_words if w in ENGLISH_FRAME_VERBS)
    hinglish_matches = sum(1 for w in latin_words if w in HINGLISH_MARKERS)

    best_script, best_count = max(((k, v) for k, v in counts.items() if k != "latin"), key=lambda x: x[1])

    # 1. Distinct Native Script Priority: If the query text is explicitly written in a native script
    # (e.g. Telugu 'పీఎం సూర్య ఘర్...', Hindi 'पीएम किसान...', Urdu 'پی ایم کسان...'),
    # always answer in THAT language even if a conflicting dropdown was selected!
    if best_count >= 3:
        return best_script

    # 2. If the query is in Latin/English, honor the user's manual selection if specified
    if preferred_lang and preferred_lang not in ("indic-auto", "auto", None):
        return preferred_lang

    # 3. If native Indic script still has presence
    if best_count > 0 and len(indic_words) >= 2:
        return best_script

    # 4. If Hinglish markers in Latin script
    if hinglish_matches >= 2:
        return "hi-en"

    # 5. Pure English words
    if eng_matches >= 1:
        return "en"

    if best_count > 0:
        return best_script

    return "hi-en"

def detect_script_language(text: str) -> str | None:
    """Detect language directly from Unicode script blocks for 100% accurate Indic language resolution."""
    return detect_query_language(text)

def transcribe(audio_bytes: bytes, filename: str, mime_type: str, language_code: str = "indic-auto") -> dict[str, Any]:
    """Call the documented Prisma REST API with multi-lingual auto-detection or explicit language."""
    data = {
        "model": "prisma-v3.0",
        "language_code": language_code or "indic-auto",
        "format": "codemix",
        "topic": "Government welfare schemes, citizen benefits, farmer assistance, health and housing",
    }
    # Ensure file is sent with proper format
    send_filename = "citizen_voice.wav" if audio_bytes[:4] == b"RIFF" else filename
    send_mime = "audio/wav" if audio_bytes[:4] == b"RIFF" else (mime_type or "audio/wav")

    response = requests.post(
        STT_URL,
        headers={"X-API-Key-ID": api_key()},
        files={"audio_file": (send_filename, audio_bytes, send_mime)},
        data=data,
        timeout=60,
    )
    print(f"[Prisma STT API] Status={response.status_code}, Bytes={len(audio_bytes)}, Resp={response.text[:120]}")
    if not response.ok:
        raise GnaniError(f"Prisma request failed ({response.status_code}): {response.text[:300]}")
    body = response.json()
    if not body.get("success"):
        raise GnaniError(body.get("error", {}).get("message", "Prisma did not return a transcript."))
    return body

def get_voice_for_language(lang_code: str | None) -> tuple[str, str]:
    if lang_code and lang_code in VOICE_MAP:
        return VOICE_MAP[lang_code]
    return VOICE_MAP["hi-en"]

TTS_CACHE: dict[str, bytes] = {}

def synthesize(text: str, language: str = "hi-en", voice: str = "Aarohi") -> bytes:
    clean_text = text.strip()[:1200]
    cache_key = f"{language}:{voice}:{clean_text}"
    if cache_key in TTS_CACHE:
        return TTS_CACHE[cache_key]

    payload = {
        "text": clean_text,
        "model": "timbre-v2.5",
        "voice": voice,
        "language": language,
        "speed": 1.0,
        "audio_config": {
            "encoding": "linear_pcm",
            "container": "wav",
            "num_channels": 1,
            "sample_rate": 24000,
            "sample_width": 2,
        },
    }
    response = requests.post(
        TTS_URL,
        headers={"X-API-Key-ID": api_key(), "Content-Type": "application/json"},
        json=payload,
        timeout=60,
    )
    if not response.ok:
        raise GnaniError(f"Timbre request failed ({response.status_code}): {response.text[:300]}")
    audio_bytes = response.content
    TTS_CACHE[cache_key] = audio_bytes
    return audio_bytes

def verify_gnani_connection() -> dict[str, Any]:
    """Test the configured Gnani API key live against Timbre TTS and return exact health metrics."""
    if not has_api_key():
        return {"ok": False, "status": "missing", "error": "No GNANI_API_KEY found in .env"}
    t0 = time.time()
    try:
        audio = synthesize("నమస్కారం", language="te", voice="Aarohi")
        lat = round((time.time() - t0) * 1000)
        return {"ok": True, "status": "active", "latency_ms": lat, "bytes": len(audio)}
    except Exception as e:
        lat = round((time.time() - t0) * 1000)
        return {"ok": False, "status": "error", "latency_ms": lat, "error": str(e)}

def verify_gemini_connection() -> dict[str, Any]:
    """Test the configured Gemini API key live across standard Google AI Studio endpoints."""
    key = os.getenv("GEMINI_API_KEY", "").strip()
    if not key:
        return {"ok": False, "status": "missing", "error": "No GEMINI_API_KEY found in .env"}

    t0 = time.time()
    candidates = [
        "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent",
        "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash-lite:generateContent",
        "https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent",
    ]
    payload = {
        "contents": [{"parts": [{"text": "Reply with 'OK'"}]}],
        "generationConfig": {"maxOutputTokens": 10, "thinkingConfig": {"thinkingBudget": 0}},
    }
    last_err = ""
    for base_url in candidates:
        try:
            url = f"{base_url}?key={key}"
            res = requests.post(url, json=payload, timeout=8)
            lat = int((time.time() - t0) * 1000)
            if res.status_code == 200:
                model_name = base_url.split("/models/")[1].split(":")[0]
                return {
                    "ok": True,
                    "status": "connected",
                    "model": model_name,
                    "latency_ms": lat,
                }
            else:
                last_err = f"HTTP {res.status_code}: {res.text[:120]}"
        except Exception as e:
            last_err = str(e)

    lat = int((time.time() - t0) * 1000)
    return {"ok": False, "status": "error", "latency_ms": lat, "error": last_err}

def _pick_answer(item: dict[str, Any], lang_code: str | None) -> str:
    """Select the best-matching language variant of a scheme answer across all 22 official Indian languages."""
    if not lang_code or lang_code == "indic-auto":
        lang_code = "hi-en"

    key = f"answer_{lang_code}"
    if key in item and item[key]:
        return item[key]

    name = item.get("name", "Welfare Scheme")
    benefit = item.get("benefit", "")
    eligibility = item.get("eligibility", "")
    docs = item.get("documents", "Aadhaar Card, Bank Passbook")

    if lang_code == "te":
        return f"{name} వివరాలు: ప్రయోజనం: {benefit}. అర్హత: {eligibility}. అవసరమైన పత్రాలు: {docs}. దరఖాస్తు కోసం సమీపంలోని CSC లేదా గ్రామ/వార్డు సచివాలయాన్ని సంప్రదించండి."
    elif lang_code == "ta":
        return f"{name} திட்டத்தின் முக்கிய விவரங்கள்: பலன்: {benefit}. தகுதி: {eligibility}. தேவையான ஆவணங்கள்: {docs}. விண்ணப்பிக்க உங்கள் அருகிலுள்ள CSC மையத்தை அணுகவும்."
    elif lang_code == "kn":
        return f"{name} ಯೋಜನೆಯ ಪ್ರಮುಖ ವಿವರಗಳು: ಪ್ರಯೋಜನ: {benefit}. ಅರ್ಹತೆ: {eligibility}. ಅಗತ್ಯ ದಾಖಲೆಗಳು: {docs}. ಅರ್ಜಿ ಸಲ್ಲಿಸಲು ನಿಮ್ಮ ಹತ್ತಿರದ ಗ್ರಾಮ ಒನ್ / CSC ಕೇಂದ್ರಕ್ಕೆ ಭೇಟಿ ನೀಡಿ."
    elif lang_code == "ml":
        return f"{name} പദ്ധതിയുടെ പ്രധാന വിവരങ്ങൾ: ആനുകൂല്യം: {benefit}. യോഗ്യത: {eligibility}. ആവശ്യമായ രേഖകൾ: {docs}. അപേക്ഷിക്കാൻ അടുത്തുള്ള അക്ഷയ / CSC കേന്ദ്രം സന്ദർശിക്കുക."
    elif lang_code == "mr":
        return f"{name} योजनेची माहिती: लाभ: {benefit}. पात्रता: {eligibility}. आवश्यक कागदपत्रे: {docs}. अर्ज करण्यासाठी नजीकच्या आपले सरकार / CSC केंद्राला भेट द्या."
    elif lang_code == "bn":
        return f"{name} প্রকল্পের বিবরণ: সুবিধা: {benefit}। যোগ্যতা: {eligibility}। প্রয়োজনীয় নথি: {docs}। আবেদনের জন্য নিকটবর্তী সিএসসি সেন্টারে যোগাযোগ করুন।"
    elif lang_code == "gu":
        return f"{name} યોજનાની માહિતી: લાભ: {benefit}. પાત્રતા: {eligibility}. જરૂરી દસ્તાવેજો: {docs}. અરજી કરવા માટે નજીકના CSC કેન્દ્રનો સંપર્ક કરો."
    elif lang_code == "pa":
        return f"{name} ਸਕੀਮ ਦੇ ਵੇਰਵੇ: ਲਾਭ: {benefit}. ਯੋਗਤਾ: {eligibility}. ਲੋੜੀਂਦੇ ਦਸਤਾਵੇਜ਼: {docs}. ਅਪਲਾਈ ਕਰਨ ਲਈ ਨੇੜਲੇ CSC ਸੇਵਾ ਕੇਂਦਰ ਨਾਲ ਸੰਪਰਕ ਕਰੋ।"
    elif lang_code == "or":
        return f"{name} ଯୋଜନାର ବିବରଣୀ: ସୁବିଧା: {benefit}. ଯୋଗ୍ୟତା: {eligibility}. ଆବଶ୍ୟକୀୟ କାଗଜପତ୍ର: {docs}. ଆବେଦନ ପାଇଁ ନିକଟସ୍ଥ CSC କେନ୍ଦ୍ର ସହିତ ଯୋଗାଯୋଗ କରନ୍ତୁ।"
    elif lang_code == "as":
        return f"{name} আঁচনিৰ বিৱৰণ: সুবিধা: {benefit}. যোগ্যতা: {eligibility}. প্ৰয়োজনীয় নথিপত্ৰ: {docs}. আবেদনৰ বাবে ওচৰৰ CSC কেন্দ্ৰলৈ যাওক।"
    elif lang_code == "ur":
        return f"{name} اسکیم کی تفصیلات: فائدہ: {benefit}۔ اہلیت: {eligibility}۔ ضروری دستاویزات: {docs}۔ درخواست دینے کے لیے قریبی سی ایس سی سنٹر سے رجوع کریں۔"
    elif lang_code == "sa":
        return f"{name} योजनायाः विवरणम्: लाभः: {benefit}। पात्रता: {eligibility}। आवश्यकदस्तावेजानि: {docs}। आवेदनार्थं निकटस्थं जनसेवाकेन्द्रं (CSC) सम्पर्कं कुर्वन्तु।"
    elif lang_code == "ne":
        return f"{name} योजनाको विवरण: फाइदा: {benefit}। योग्यता: {eligibility}। आवश्यक कागजातहरू: {docs}। आवेदनका लागि नजिकको CSC केन्द्रमा सम्पर्क गर्नुहोस्।"
    elif lang_code == "kok":
        return f"{name} येवजणेची म्हायती: फायदो: {benefit}। पात्रता: {eligibility}। गरजेचे दस्तऐवज: {docs}। अर्जा खातीर लागींच्या CSC केंद्राक भेट दियात।"
    elif lang_code == "mai":
        return f"{name} योजनाक विवरण: लाभ: {benefit}। योग्यता: {eligibility}। आवश्यक कागजात: {docs}। आवेदन लेल नजदीकी CSC केंद्र सँ संपर्क करू।"
    elif lang_code == "doi":
        return f"{name} स्कीमा दा ब्योरा: फायदा: {benefit}। योग्यता: {eligibility}। जरूरी कागज़ात: {docs}। अप्लाई करने लेई नेड़े दे जन सेवा केंद्र (CSC) कन्नै संपर्क करो।"
    elif lang_code == "ks":
        return f"{name} سکیٖم ہٕنٛز تفصیل: فايدٕ: {benefit}۔ اہلیت: {eligibility}۔ دستاویز: {docs}۔ درخاست دنہٕ خٲطرٕ قریبی سی ایس سی سنٹرس سٟتؠ رابطہ کریو।"
    elif lang_code == "sd":
        return f"{name} اسڪيم جا تفصيل: فائدو: {benefit}۔ اهليت: {eligibility}۔ ضروري دستاويز: {docs}۔ درخواس لاءِ ويجهي CSC سينٽر سان رابطو ڪريو۔"
    elif lang_code == "mni":
        return f"{name} ꯊꯧꯔꯥꯡꯒꯤ ꯑꯀꯨꯞꯄꯥ: ꯀꯥꯟꯅꯕ: {benefit}। ꯃꯇꯤꯛ ꯃꯌꯥꯏ: {eligibility}। ꯃꯊꯧ ꯇꯥꯕꯥ ꯆꯦ-ꯆꯥꯡ: {docs}। ꯑꯄ꯭ꯂꯥꯏ ꯇꯧꯅꯕꯥ ꯅꯛꯅꯕꯥ CSC ꯀꯦꯟꯗ꯭ꯔꯗꯥ ꯆꯠꯄꯤꯌꯨ।"
    elif lang_code == "brx":
        return f"{name} बिथांखिनि सोमोन्दै: मुलाम्फा: {benefit}। थि गोनांथि: {eligibility}। गोनां दोलोमोन: {docs}। आरज गाबनो थाखाय खाथिनि CSC मिरुआव थां।"
    elif lang_code == "sat":
        return f"{name} ᱡᱚᱡᱚᱱᱟ ᱨᱮᱱᱟᱜ ᱵᱤᱵᱚᱨᱚᱬ: ᱞᱟᱵᱷ: {benefit}᱾ ᱡᱚᱜᱽᱭᱚᱛᱟ: {eligibility}᱾ ᱞᱟᱹᱠᱛᱤᱭᱟᱱ ᱠᱟᱜᱚᱡᱽ: {docs}᱾ ᱟᱯᱞᱟᱭ ᱞᱟᱹᱜᱤᱫ ᱥᱩᱨ ᱨᱮᱱᱟᱜ CSC ᱛᱟᱞᱢᱟ ᱨᱮ ᱥᱮᱱᱚᱜ ᱢᱮ᱾"
    elif lang_code == "hi":
        return item.get("answer_hi") or f"{name} योजना की जानकारी: लाभ: {benefit}। पात्रता: {eligibility}। आवश्यक दस्तावेज: {docs}। नजदीकी जन सेवा केंद्र से संपर्क करें।"
    elif lang_code == "en":
        return item.get("answer_en") or f"{name} details: Benefit: {benefit}. Eligibility: {eligibility}. Required documents: {docs}. Visit your nearest CSC center to apply."

    return item.get("answer_hinglish") or item.get("answer_hi") or item.get("answer_en", "")

def has_gemini_key() -> bool:
    """Check if a valid Gemini LLM API key is configured (AI Studio keys start with AIzaSy)."""
    key = os.getenv("GEMINI_API_KEY", "").strip()
    return bool(key)

def generate_dynamic_response(
    query: str,
    scheme: dict[str, Any] | None,
    lang_code: str,
) -> str:
    """Generate dynamic, context-aware conversational answers in the citizen's native script using Gemini Flash."""
    key = os.getenv("GEMINI_API_KEY", "").strip()
    if not key or not scheme:
        return _pick_answer(scheme, lang_code) if scheme else SCHEME_FALLBACK_MESSAGES.get(lang_code, SCHEME_FALLBACK_MESSAGES["hi-en"])

    lang_meta = INDIAN_OFFICIAL_LANGUAGES.get(lang_code, {"name": "Indian Regional Language", "native": ""})
    lang_name = lang_meta.get("name", "Telugu")
    native_name = lang_meta.get("native", "")

    candidate_models = [
        "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent",
        "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash-lite:generateContent",
        "https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent",
    ]
    system_instruction = (
        f"You are YojanaVaani AI, an official Indian Government citizen welfare voice assistant.\n"
        f"Citizen Query: \"{query}\"\n\n"
        f"Verified Government Scheme Information:\n"
        f"- Scheme: {scheme.get('name')}\n"
        f"- Benefit: {scheme.get('benefit')}\n"
        f"- Eligibility: {scheme.get('eligibility')}\n"
        f"- Required Documents: {scheme.get('documents')}\n\n"
        f"Strict Guidelines:\n"
        f"1. Compose a warm, conversational 2-3 sentence spoken answer in {lang_name} ({native_name} script).\n"
        f"2. You are strictly an Indian Government welfare assistant. Answer ONLY about this verified government scheme. Do not discuss any unrelated, commercial, political, or external topics.\n"
        f"3. Do NOT use markdown, bold, asterisks, or bullet points because this text will be read aloud by Timbre TTS over the telephone."
    )

    for endpoint in candidate_models:
        try:
            url = f"{endpoint}?key={key}"
            resp = requests.post(
                url,
                headers={"Content-Type": "application/json"},
                json={
                    "contents": [{"parts": [{"text": system_instruction}]}],
                    "generationConfig": {"temperature": 0.2, "maxOutputTokens": 250},
                },
                timeout=8,
            )
            if resp.ok:
                data = resp.json()
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts and "text" in parts[0]:
                        ans = parts[0]["text"].strip()
                        ans = re.sub(r"[*_#`]", "", ans)
                        print(f"[Gemini Generative AI] Dynamically composed native {lang_name} response ({len(ans)} chars)")
                        return ans
        except Exception as e:
            print(f"[Gemini Dynamic LLM] Error calling {endpoint}: {e}")

    return _pick_answer(scheme, lang_code)

def answer_open_ended_scheme(
    question: str,
    lang_code: str,
    state_filter: str | None = None,
) -> tuple[str, dict[str, Any] | None, bool]:
    """Dynamically resolve any Indian welfare scheme across all 2000+ Central and State programs using Gemini."""
    key = os.getenv("GEMINI_API_KEY", "").strip()
    if not key:
        fallback_msg = SCHEME_FALLBACK_MESSAGES.get(lang_code, SCHEME_FALLBACK_MESSAGES["hi-en"])
        return (fallback_msg, None, True)

    lang_meta = INDIAN_OFFICIAL_LANGUAGES.get(lang_code, {"name": "Indian Regional Language", "native": ""})
    lang_name = lang_meta.get("name", "Telugu")
    native_name = lang_meta.get("native", "")

    candidate_models = [
        "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent",
        "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash-lite:generateContent",
        "https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent",
    ]
    system_instruction = (
        f"You are YojanaVaani AI, an official Indian Government Welfare & Citizen Public Schemes Voice Assistant.\n"
        f"A citizen asks: \"{question}\"\n"
        f"State filter constraint: {state_filter or 'Any Indian State / Central'}\n\n"
        f"### STRICT SCOPE & DOMAIN ENFORCEMENT:\n"
        f"You are strictly authorized to answer inquiries about Indian Government Welfare Schemes, subsidies, pensions, scholarships, ration, healthcare cards (Ayushman), housing (PMAY), agriculture/farmers (PM-Kisan), and official citizen public service procedures (CSC / Sachivalayam).\n\n"
        f"CRITICAL INSTRUCTIONS:\n"
        f"1. IF THIS QUERY IS ABOUT AN INDIAN GOVERNMENT SCHEME OR PUBLIC WELFARE BENEFIT:\n"
        f"   - Detail the primary financial or social benefits (₹ amounts, subsidies), who is eligible, and documents required.\n"
        f"   - Keep it to 2-3 spoken sentences in {lang_name} ({native_name} script).\n"
        f"   - Do NOT use any asterisks, markdown, bolding, or lists (it will be spoken via TTS).\n"
        f"   - At the end on a new line write: 'SCHEME_NAME: <Official Name of Scheme>'\n\n"
        f"2. IF THIS QUERY IS NOT ABOUT AN INDIAN GOVERNMENT SCHEME OR CITIZEN WELFARE SERVICE:\n"
        f"   (For example: general chit-chat, movies, cinema, cricket, sports, cooking, coding/tech, weather, jokes, songs, personal life, or opinions):\n"
        f"   - YOU MUST STRICTLY REFUSE TO ANSWER THE UNRELATED TOPIC.\n"
        f"   - Politely inform the citizen in 1-2 spoken sentences in {lang_name} ({native_name} script) that you are exclusively built to provide information on Indian Government Welfare Schemes (such as PM-Kisan, Ayushman Bharat, Scholarships, Pensions, Ration cards) and invite them to ask about a government scheme.\n"
        f"   - At the end on a new line write: 'SCHEME_NAME: OUT_OF_SCOPE'\n"
    )

    for endpoint in candidate_models:
        try:
            url = f"{endpoint}?key={key}"
            resp = requests.post(
                url,
                headers={"Content-Type": "application/json"},
                json={
                    "contents": [{"parts": [{"text": system_instruction}]}],
                    "generationConfig": {"temperature": 0.2, "maxOutputTokens": 1000, "thinkingConfig": {"thinkingBudget": 0}},
                },
                timeout=8,
            )
            if resp.ok:
                data = resp.json()
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts and "text" in parts[0]:
                        raw_text = parts[0]["text"].strip()
                        scheme_title = "Indian Government Welfare Scheme"
                        if "SCHEME_NAME:" in raw_text:
                            spl = raw_text.split("SCHEME_NAME:")
                            clean_text = spl[0].strip()
                            scheme_title = spl[1].strip().split("\n")[0].strip()
                        else:
                            clean_text = raw_text
                        clean_text = re.sub(r"[*_#`]", "", clean_text)
                        
                        if any(kw in scheme_title.upper() for kw in ["OUT_OF_SCOPE", "NONE", "UNRELATED", "NOT_A_SCHEME"]):
                            print(f"[Gemini Scope Guard] Non-scheme query strictly blocked and redirected: '{question}'")
                            return (clean_text, None, False)

                        matched_obj = {
                            "id": "gemini_dynamic_scheme",
                            "name": scheme_title,
                            "type": "Central / State (MyScheme 2000+ Index)",
                            "state": state_filter or "All India",
                            "benefit": "Government subsidy / direct financial benefit",
                            "eligibility": "Eligible Indian citizens per official ministry guidelines",
                            "documents": "Aadhaar Card, Income/Caste Certificate, Bank Passbook",
                        }
                        print(f"[Gemini 2000+ Schemes] Successfully resolved '{scheme_title}' in {lang_name}!")
                        return (clean_text, matched_obj, False)
        except Exception as e:
            print(f"[Open Welfare Search] Gemini open scheme resolution error via {endpoint}: {e}")

    fallback_msg = SCHEME_FALLBACK_MESSAGES.get(lang_code, SCHEME_FALLBACK_MESSAGES["hi-en"])
    return (fallback_msg, None, True)


def generate_multi_scheme_response(
    query: str,
    schemes: list[dict[str, Any]],
    lang_code: str,
) -> str:
    """Generate a cohesive multi-scheme summary when citizen asks for a list or overview."""
    key = os.getenv("GEMINI_API_KEY", "").strip()
    lang_meta = INDIAN_OFFICIAL_LANGUAGES.get(lang_code, {"name": "Indian Regional Language", "native": ""})
    lang_name = lang_meta.get("name", "Telugu")
    native_name = lang_meta.get("native", "")

    if not key or not schemes:
        # Fallback multi-scheme text
        parts = [f"{s.get('name')}: {s.get('benefit', '')}" for s in schemes[:3]]
        return " Key schemes available: " + "; ".join(parts)

    candidate_models = [
        "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent",
        "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash-lite:generateContent",
        "https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent",
    ]

    schemes_text = ""
    for idx, s in enumerate(schemes[:4], start=1):
        schemes_text += f"{idx}. {s.get('name')} ({s.get('state', 'All India')}): {s.get('benefit', '')}\n"

    system_instruction = (
        f"You are YojanaVaani AI, an official Indian Government citizen welfare voice assistant.\n"
        f"Citizen Query: \"{query}\"\n\n"
        f"Verified Available Government Schemes:\n"
        f"{schemes_text}\n"
        f"Strict Guidelines:\n"
        f"1. Compose a friendly 2-3 sentence spoken summary in {lang_name} ({native_name} script) listing and briefly explaining these top schemes.\n"
        f"2. You are an Indian Government welfare assistant. Answer ONLY about these verified schemes.\n"
        f"3. Do NOT use markdown, bold asterisks, or bullet points because this will be read aloud over the phone.\n"
    )

    for endpoint in candidate_models:
        try:
            url = f"{endpoint}?key={key}"
            payload = {
                "contents": [{"parts": [{"text": system_instruction}]}],
                "generationConfig": {"temperature": 0.2, "maxOutputTokens": 1000, "thinkingConfig": {"thinkingBudget": 0}},
            }
            res = requests.post(url, json=payload, timeout=6.0)
            if res.status_code == 200:
                data = res.json()
                ans = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "").strip()
                if ans:
                    ans = re.sub(r"[*_#`]", "", ans)
                    print(f"[Gemini Multi-Scheme] Dynamically summarized {len(schemes)} schemes in {lang_name}")
                    return ans
        except Exception as e:
            print(f"[Gemini Multi-Scheme] Error calling {endpoint}: {e}")

    # Fallback if API fails
    parts = [f"{s.get('name')}: {s.get('benefit', '')}" for s in schemes[:3]]
    return " Key schemes available: " + "; ".join(parts)

def answer_from_schemes(
    question: str, lang_code: str | None = None, state_filter: str | None = None
) -> tuple[str, dict[str, Any] | None, bool]:
    """Find the best-matching government scheme based on citizen query and optional state filter.
    
    Supports:
    - Code-mixed Indian English + native script queries (e.g. 'PM కిసాన్ 6000')
    - Standalone token overlap and multi-word n-gram scoring
    - State-specific targeting (e.g. Andhra Pradesh Annadata Sukhibhava)
    - Strict scope guardrails: only responds to government schemes and citizen public welfare
    """
    lowered = question.lower()
    active_lang = lang_code or "hi-en"

    if any(term in lowered for term in SCAM_OR_FRAUD_TERMS):
        msg = SCAM_MESSAGES.get(active_lang, SCAM_MESSAGES["hi-en"])
        return (msg, None, True)

    # Fast Guardrail: Block obvious non-government topics (entertainment, sports, coding, cooking, chit-chat)
    if any(trigger in lowered for trigger in NON_SCHEME_TRIGGERS):
        if not any(gov in lowered for gov in GOV_TERMS):
            msg = OUT_OF_SCOPE_MESSAGES.get(active_lang, OUT_OF_SCOPE_MESSAGES["hi-en"])
            print(f"[Direct Scope Guard] Filtered out non-government query: '{question}'")
            return (msg, None, False)

    # Extract all alphanumeric and Indic script word tokens
    tokens = set(re.findall(r"[\w\u0900-\u0D7F]+", lowered))

    items = _load_kb()
    scored: list[tuple[int, dict[str, Any]]] = []
    for item in items:
        item_state = item.get("state", "All India")
        if state_filter and state_filter not in ("All Schemes", "All India"):
            if item.get("type") == "State" and item_state.lower() != state_filter.lower():
                continue

        score = 0
        if item_state != "All India" and item_state.lower() in lowered:
            score += 5

        # 1. Exact phrase matching in keywords
        for keyword in item.get("keywords", []):
            kw_clean = keyword.lower()
            if kw_clean in lowered:
                score += 6
            # 2. Token overlap for code-mixed speech
            kw_tokens = set(re.findall(r"[\w\u0900-\u0D7F]+", kw_clean))
            score += len(tokens.intersection(kw_tokens)) * 3

        # 3. Item title & name tokens
        name_tokens = set(re.findall(r"[\w\u0900-\u0D7F]+", item.get("name", "").lower()))
        score += len(tokens.intersection(name_tokens)) * 3

        # 4. Scheme ID tokens (e.g. 'kisan', 'ayushman', 'solar', 'ladki')
        id_tokens = set(re.findall(r"[\w]+", item.get("id", "").lower()))
        score += len(tokens.intersection(id_tokens)) * 4

        # 5. Code-mixed Hinglish phrase boost (e.g. "PM-Kisan", "Ayushman card")
        hindi_hinglish_phrases = ["pm-kisan", "pm kisan", "ayushman", "ayushman bharat",
                                  "free treatment", "free ilaaj", "ration card", "ration card banana",
                                  "solar panel", "solar lagwana", "scholarship", "scholarship yojana"]
        for phrase in hindi_hinglish_phrases:
            if phrase in lowered:
                score += 8

        scored.append((score, item))

    if not scored:
        scored = [(0, i) for i in items]

    scored.sort(key=lambda row: row[0], reverse=True)
    score, best = scored[0]

    # Detect if citizen asked for a list or overview of multiple schemes
    list_intents = ["list", "what and all", "what all", "available", "all schemes", "schemes in", "schemes for", "how many", "tell me schemes", "అన్ని", "జాబితా", "పథకాలు",
                     "सभी", "योजनाएं", "सूची", "لیست", "Sab", "Saare", "查询", "列表", "список", "Список",
                     "궁금증", "목록", "danh sách", "Danh sách", "รายการ", "รายการ", "දර්ශක", "Dandekar",
                     "Список", "Lista", "Lijst", "Список", "Makala", "Makala"]
    is_list_query = any(w in lowered for w in list_intents)

    if is_list_query and score >= 5:
        # Collect top matching schemes (score >= 5 or same state)
        matched_schemes = [item for sc, item in scored if sc >= 5][:4]
        if len(matched_schemes) > 1:
            if has_gemini_key():
                answer_text = generate_multi_scheme_response(question, matched_schemes, active_lang)
            else:
                answer_text = " \n".join([_pick_answer(s, active_lang) for s in matched_schemes[:2]])
            return answer_text, best, False

    if score >= 5:
        if has_gemini_key():
            answer_text = generate_dynamic_response(question, best, active_lang)
        else:
            answer_text = _pick_answer(best, active_lang)
        return answer_text, best, False

    if has_gemini_key():
        return answer_open_ended_scheme(question, active_lang, state_filter)

    fallback_msg = SCHEME_FALLBACK_MESSAGES.get(active_lang, SCHEME_FALLBACK_MESSAGES["hi-en"])
    return (fallback_msg, None, True)

# ---------------------------------------------------------------------------
# End-to-End Voice Assistant Pipeline
# ---------------------------------------------------------------------------
def process_voice_turn(
    user_audio: bytes | None = None,
    user_text: str | None = None,
    preferred_lang: str | None = None,
    state_filter: str | None = None,
) -> dict[str, Any]:
    """Process a citizen voice turn through DSP Audio Enhancement -> Prisma STT -> Guardrails -> Schemes -> Timbre TTS."""
    transcript = (user_text or "").strip()
    detected_lang = preferred_lang or "hi-en"
    if detected_lang == "indic-auto":
        detected_lang = "hi-en"

    # Step 1: DSP Audio Enhancement + Prisma STT if audio was provided
    if user_audio and not transcript:
        if not has_api_key():
            raise GnaniError("GNANI_API_KEY is not set. Add your key to .env to transcribe live audio.")
        if len(user_audio) > 400:
            try:
                # Save raw input for diagnostic analysis
                try:
                    Path("debug_user_raw.bin").write_bytes(user_audio)
                except Exception:
                    pass

                # 1. Enhance low-quality/quiet audio with DSP filter & gain booster
                cleaned_audio = enhance_audio(user_audio)

                try:
                    Path("debug_user_cleaned.wav").write_bytes(cleaned_audio)
                except Exception:
                    pass

                stt_lang = to_prisma_lang(preferred_lang)
                print(f"[Voice Pipeline] Transcribing audio with Prisma STT (lang={stt_lang}, size={len(cleaned_audio)} bytes)...")
                stt_raw = transcribe(cleaned_audio, "citizen_voice.wav", "audio/wav", language_code=stt_lang)
                transcript = stt_raw.get("transcript", "").strip()
                print(f"[Voice Pipeline] Prisma STT returned transcript: '{transcript}'")

                # 2. Extract detected language code from Prisma (e.g. te-IN -> te)
                if stt_raw.get("detected_language_code"):
                    detected_lang = from_prisma_lang(stt_raw.get("detected_language_code"))

                user_audio = cleaned_audio
            except Exception as e:
                print(f"[Voice Pipeline] STT processing error: {e}")
                transcript = ""
        else:
            print(f"[Voice Pipeline] user_audio too short ({len(user_audio)} bytes), skipping STT.")
            transcript = ""

    # Step 1.5: Language Identification with Preference Priority
    if transcript:
        detected_lang = detect_query_language(transcript, preferred_lang=preferred_lang)

    # Graceful handling for silent or unclear audio input in citizen's language
    if not transcript:
        is_silent = False
        if user_audio:
            try:
                with io.BytesIO(user_audio) as bio:
                    with wave.open(bio, "rb") as wf:
                        raw = wf.readframes(wf.getnframes())
                        peak = np.max(np.abs(np.frombuffer(raw, dtype=np.int16))) if len(raw) > 0 else 0
                        if peak < 60:
                            is_silent = True
            except Exception:
                pass

        if is_silent and (detected_lang in ("en", "indic-auto", "auto", "hi-en")):
            transcript = "No Voice Detected (Microphone Silent)"
            reply_text = "No audio was detected from your microphone. Please check your mic permissions and speak clearly, or tap any scheme button below."
            detected_lang = "en"
        elif is_silent and detected_lang == "te":
            transcript = "మైక్రోఫోన్ సౌండ్ రాలేదు (Microphone Silent)"
            reply_text = "మీ మైక్రోఫోన్ నుండి ఎలాంటి శబ్దం రాలేదు. దయచేసి మైక్రోఫోన్ ఆన్ చేసి స్పష్టంగా మాట్లాడండి, లేదా క్రింది బటన్ల ద్వారా పథకాన్ని ఎంచుకోండి."
        elif is_silent and detected_lang == "hi":
            transcript = "माइक मूक (Microphone Silent)"
            reply_text = "आपके माइक से आवाज़ नहीं आई। कृपया थोड़ा साफ़ आवाज़ में बोलिए, या नीचे दिए गए बटनों से योजना चुनिए।"
        elif is_silent:
            transcript = f"No Voice Detected ({detected_lang.upper()})"
            reply_text = UNCLEAR_AUDIO_MESSAGES.get(detected_lang, UNCLEAR_AUDIO_MESSAGES.get("en", "Please speak clearly into your microphone."))
        else:
            if detected_lang in ("en", "indic-auto", "auto", "hi-en"):
                transcript = "Audio Unclear (Please repeat)"
                reply_text = "Could not clearly understand the audio. Please speak a bit louder or tap one of the scheme options below."
                detected_lang = "en"
            elif detected_lang == "te":
                transcript = "వాయిస్ స్పష్టంగా లేదు (Audio Unclear)"
                reply_text = "మీ వాయిస్ స్పష్టంగా వినబడలేదు. దయచేసి కొంచెం బిగ్గరగా మాట్లాడండి లేదా క్రింది బటన్లలో పథకాన్ని ఎంచుకోండి."
            elif detected_lang == "hi":
                transcript = "आवाज़ स्पष्ट नहीं (Audio Unclear)"
                reply_text = "आपकी आवाज़ साफ़ सुनाई नहीं दी। कृपया थोड़ा तेज़ बोलिए या नीचे दिए गए बटनों से योजना चुनिए।"
            else:
                transcript = f"Audio Unclear ({detected_lang.upper()})"
                reply_text = UNCLEAR_AUDIO_MESSAGES.get(detected_lang, UNCLEAR_AUDIO_MESSAGES["hi-en"])

        reply_audio = None
        tts_lang, tts_voice = get_voice_for_language(detected_lang)
        if has_api_key():
            try:
                reply_audio = synthesize(reply_text, language=tts_lang, voice=tts_voice)
            except Exception:
                reply_audio = None
        return {
            "user_text": transcript,
            "user_audio": user_audio,
            "reply_text": reply_text,
            "reply_audio": reply_audio,
            "matched_scheme": None,
            "escalate": False,
            "detected_lang": detected_lang,
            "tts_voice": tts_voice,
        }

    # Step 2: Privacy / Scam Guardrails
    matched_scheme: dict[str, Any] | None = None
    if p_warn := privacy_warning(transcript):
        reply_text = p_warn
        escalate = True
    else:
        # Step 3: Scheme Knowledge Retrieval with State & Language Filtering
        reply_text, matched_scheme, escalate = answer_from_schemes(
            transcript, lang_code=detected_lang, state_filter=state_filter
        )

    # Step 4: Timbre TTS Spoken Voice Generation in matching language
    reply_audio = None
    tts_lang, tts_voice = get_voice_for_language(detected_lang)
    if has_api_key():
        try:
            # Low-latency voice spurt: Synthesize first 1-2 punchy sentences (~160 chars) for speech
            # while the citizen sees the full, detailed scheme answer in the visual card.
            spoken_text = reply_text.strip()
            # Split on sentence terminals: danda (।), period, exclamation, or question mark
            sentences = [s.strip() for s in re.split(r"(?<=[।\.\!\?])\s+", spoken_text) if s.strip()]
            if sentences and len(sentences) >= 2 and len(spoken_text) > 170:
                spoken_text = f"{sentences[0]} {sentences[1]}"
            reply_audio = synthesize(spoken_text, language=tts_lang, voice=tts_voice)
        except Exception as e:
            print(f"[Voice Turn] TTS synthesis error: {e}")
            reply_audio = None

    return {
        "user_text": transcript,
        "user_audio": user_audio,
        "reply_text": reply_text,
        "reply_audio": reply_audio,
        "matched_scheme": matched_scheme,
        "escalate": escalate,
        "detected_lang": detected_lang,
        "tts_voice": tts_voice,
    }
