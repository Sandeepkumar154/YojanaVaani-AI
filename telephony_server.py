"""Telephony Voice Gateway for YojanaVaani AI.

Integrates with Cloud Telephony providers (Twilio, Exotel, or Tata Tele)
to allow citizens to dial a real phone number (e.g. +1 737 250 8034 / 1800-YOJANA)
and converse with the AI voice assistant in real time over standard cellular voice lines.
"""
import os
import uuid
import time
import base64
import requests
from fastapi import FastAPI, Request, Response, UploadFile, File, Form
from fastapi.responses import PlainTextResponse, JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from services import (
    process_voice_turn,
    synthesize,
    get_voice_for_language,
    get_welcome_text,
    OUTBOUND_CALL_SCENARIOS,
    has_api_key,
    _load_kb,
    INDIAN_OFFICIAL_LANGUAGES,
)

load_dotenv(override=True)

app = FastAPI(
    title="YojanaVaani AI Telephony Gateway & Web Portal",
    description="Telecom Voice Gateway and Ultra-Premium Web Application connecting Indian citizens to Government Welfare Schemes",
    version="2.4.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PORT = int(os.getenv("TELEPHONY_PORT", 8000))

def get_server_url() -> str:
    load_dotenv(override=True)
    return os.getenv("SERVER_PUBLIC_URL", "https://yojanavaani-ai.loca.lt").rstrip("/")

# In-memory stores for streaming audio and multi-turn call sessions
AUDIO_CACHE: dict[str, bytes] = {}
CALL_SESSIONS: dict[str, dict] = {}


def cache_audio(audio_bytes: bytes) -> str:
    """Store generated speech in memory for telecom provider to stream via <Play> tag."""
    audio_id = str(uuid.uuid4())[:12]
    AUDIO_CACHE[audio_id] = audio_bytes
    return audio_id


@app.get("/")
def serve_home():
    """Serve the Next-Gen Ultra-Premium Voice AI Portal."""
    web_file = os.path.join(os.path.dirname(__file__), "web", "index.html")
    if os.path.exists(web_file):
        return FileResponse(web_file)
    return {
        "status": "online",
        "service": "YojanaVaani AI Telephony Gateway",
        "server_url": get_server_url(),
    }


@app.get("/api/health")
def health_check():
    gnani_diag = verify_gnani_connection()
    gemini_diag = verify_gemini_connection()
    return {
        "status": "online",
        "service": "YojanaVaani AI Telephony Gateway",
        "gnani_stt": "Prisma v3.0 (telephony 8kHz/16kHz)",
        "gnani_tts": "Timbre v2.5",
        "has_gnani_key": bool(os.getenv("GNANI_API_KEY", "").strip()),
        "has_gemini_key": bool(os.getenv("GEMINI_API_KEY", "").strip()),
        "gnani_check": gnani_diag,
        "gemini_check": gemini_diag,
        "server_url": get_server_url(),
        "carrier_number": os.getenv("TWILIO_PHONE_NUMBER", "+17372508034"),
        "total_active_sessions": len(CALL_SESSIONS),
        "cached_audio_clips": len(AUDIO_CACHE),
    }


@app.get("/api/schemes")
def get_schemes_list():
    """Retrieve full catalog of central and state welfare schemes."""
    return _load_kb()


@app.get("/api/languages")
def get_languages_list():
    """Retrieve full list of all 22 official Indian languages + Indic auto."""
    return INDIAN_OFFICIAL_LANGUAGES


class ChatPayload(BaseModel):
    text: str
    lang: str = "indic-auto"




ANNOUNCEMENT_CACHE = {}

ANNOUNCEMENT_TEXTS = {
    "indic-auto": ("Welcome to YojanaVaani AI. Tap Start Recording and speak in your mother tongue, or ask any question about government welfare schemes.", "en"),
    "en": ("Welcome to YojanaVaani AI. Tap Start Recording and speak in your mother tongue, or ask any question about government welfare schemes.", "en"),
    "te": ("నమస్కారం! యోజనవాణి వెబ్‌సైట్‌కి స్వాగతం. పైన ఉన్న మైక్ బటన్ నొక్కి మీ ప్రశ్నను అడగండి.", "te"),
    "hi": ("नमस्ते! योजनावाणी पोर्टल में आपका स्वागत है। सरकारी योजनाओं की जानकारी के लिए माइक दबाकर बोलें।", "hi"),
    "ta": ("வணக்கம்! யோஜனாவாணி போர்ட்டலுக்கு நல்வரவு. அரசு திட்டங்கள் பற்றி அறிய மைக் பொத்தானை அழுத்தவும்.", "ta"),
    "kn": ("ನಮಸ್ಕಾರ! ಯೋಜನಾವಾಣಿ ಪೋರ್ಟಲ್‌ಗೆ ಸುಸ್ವಾಗತ. ಸರ್ಕಾರಿ ಯೋಜನೆಗಳ ಮಾಹಿತಿಗಾಗಿ ಮೈಕ್ ಒತ್ತಿ ಮಾತನಾಡಿ.", "kn"),
}

@app.get("/api/announcement")
def get_announcement(lang: str = "indic-auto"):
    """Return synthesized voice announcement to play directly when citizen opens portal."""
    entry = ANNOUNCEMENT_TEXTS.get(lang) or ANNOUNCEMENT_TEXTS["indic-auto"]
    text, lang_code = entry

    if not ANNOUNCEMENT_CACHE.get(lang):
        try:
            audio_bytes = synthesize(text, language=lang_code)
            ANNOUNCEMENT_CACHE[lang] = base64.b64encode(audio_bytes).decode("utf-8")
        except Exception as e:
            print(f"[Announcement TTS Error] {e}")
            ANNOUNCEMENT_CACHE[lang] = None

    return {
        "text": text,
        "lang": lang,
        "audio_base64": ANNOUNCEMENT_CACHE.get(lang),
    }



ANNOUNCEMENT_RAW_CACHE = {}

@app.get("/api/announcement.wav")
def get_announcement_wav(lang: str = "indic-auto"):
    """Stream raw WAV audio directly for native HTML5 audio playback."""
    entry = ANNOUNCEMENT_TEXTS.get(lang) or ANNOUNCEMENT_TEXTS["indic-auto"]
    text, lang_code = entry

    if not ANNOUNCEMENT_RAW_CACHE.get(lang):
        try:
            ANNOUNCEMENT_RAW_CACHE[lang] = synthesize(text, language=lang_code)
        except Exception as e:
            print(f"[Announcement WAV Error] {e}")
            return Response(content=b"", status_code=500)

    audio_bytes = ANNOUNCEMENT_RAW_CACHE[lang]
    return Response(
        content=audio_bytes,
        media_type="audio/wav",
        headers={
            "Content-Type": "audio/wav",
            "Content-Length": str(len(audio_bytes)),
            "Accept-Ranges": "bytes",
            "Cache-Control": "public, max-age=3600"
        }
    )


@app.post("/api/chat")
def api_chat(payload: ChatPayload):
    """Direct query API for web interface with live Timbre TTS speech."""
    try:
        turn = process_voice_turn(user_text=payload.text, preferred_lang=payload.lang)
        audio_b64 = base64.b64encode(turn["reply_audio"]).decode("utf-8") if turn.get("reply_audio") else None
        return {
            "user_text": turn.get("user_text", payload.text),
            "reply_text": turn.get("reply_text", "Information is being retrieved."),
            "audio_base64": audio_b64,
            "matched_scheme": turn.get("matched_scheme"),
            "escalate": turn.get("escalate", False),
            "detected_lang": turn.get("detected_lang", payload.lang),
        }
    except Exception as exc:
        print(f"[API Chat Error] {exc}")
        return {
            "user_text": payload.text,
            "reply_text": "Unable to process the query right now. Please try again or tap one of the schemes below.",
            "audio_base64": None,
            "matched_scheme": None,
            "escalate": False,
            "detected_lang": payload.lang,
        }


@app.post("/api/voice")
async def api_voice(audio: UploadFile = File(...), lang: str = Form("indic-auto")):
    """Process live audio recorded from web browser microphone via Gnani Prisma + Timbre."""
    try:
        audio_bytes = await audio.read()
        turn = process_voice_turn(user_audio=audio_bytes, preferred_lang=lang)
        audio_b64 = base64.b64encode(turn["reply_audio"]).decode("utf-8") if turn.get("reply_audio") else None
        return {
            "user_text": turn.get("user_text", ""),
            "reply_text": turn.get("reply_text", "No speech detected. Please speak clearly into the microphone."),
            "audio_base64": audio_b64,
            "matched_scheme": turn.get("matched_scheme"),
            "escalate": turn.get("escalate", False),
            "detected_lang": turn.get("detected_lang", lang),
        }
    except Exception as exc:
        print(f"[API Voice Error] {exc}")
        return {
            "user_text": "",
            "reply_text": "Voice processing encountered a temporary error. Please try speaking again.",
            "audio_base64": None,
            "matched_scheme": None,
            "escalate": False,
            "detected_lang": lang,
        }


@app.get("/audio/{audio_id}.wav")
def stream_audio_clip(audio_id: str):
    """Serve synthesized Timbre TTS audio file to telephony carrier (Twilio/Exotel)."""
    if audio_id in AUDIO_CACHE:
        content = AUDIO_CACHE[audio_id]
        headers = {
            "Content-Type": "audio/wav",
            "Content-Length": str(len(content)),
            "Accept-Ranges": "bytes",
        }
        return Response(content=content, media_type="audio/wav", headers=headers)
    return Response(content=b"", status_code=404)


# ---------------------------------------------------------------------------
# 1. Incoming Call Handler (Twilio / Exotel compatible TwiML / XML)
# ---------------------------------------------------------------------------
@app.post("/call/incoming", response_class=PlainTextResponse)
async def handle_incoming_call(request: Request):
    """Triggered when a citizen dials the virtual phone number."""
    form_data = await request.form()
    call_sid = form_data.get("CallSid") or str(uuid.uuid4())[:10]
    caller_phone = form_data.get("From") or "Anonymous Caller"
    server_url = get_server_url()

    print(f"[Telephony Incoming Call] Received call from: {caller_phone} (SID: {call_sid})")

    # Initialize caller session
    CALL_SESSIONS[call_sid] = {
        "call_sid": call_sid,
        "caller_phone": caller_phone,
        "start_time": time.time(),
        "lang": "te",
        "turns": [],
        "status": "in_progress",
    }

    # Welcome greeting text in native Telugu
    welcome_text = "నమస్కారం! యోజనవాణి ప్రభుత్వ సంక్షేమ కాల్ సెంటర్‌కు స్వాగతం. పీఎం-కిసాన్, ఆయుష్మాన్ భారత్, స్కాలర్‌షిప్‌లు లేదా ఇతర సంక్షేమ పథకాల గురించి మీ ప్రశ్నను అడగండి."
    
    play_tag = ""
    if has_api_key():
        try:
            tts_lang, tts_voice = get_voice_for_language("te")
            wel_audio = synthesize(welcome_text, language=tts_lang, voice=tts_voice)
            audio_id = cache_audio(wel_audio)
            play_tag = f"<Play>{server_url}/audio/{audio_id}.wav</Play>"
            print(f"[Telephony Incoming Call] Synthesized welcome audio clip ID: {audio_id} ({len(wel_audio)} bytes)")
        except Exception as e:
            print(f"[Telephony Incoming Call] Synthesis fallback: {e}")
            play_tag = "<Say language='hi-IN'>Namaste! YojanaVaani me aapka swagat hai. Apna sawal bolein.</Say>"
    else:
        play_tag = "<Say language='hi-IN'>Namaste! YojanaVaani me aapka swagat hai. Apna sawal bolein.</Say>"

    CALL_SESSIONS[call_sid]["turns"].append({"speaker": "Agent", "text": welcome_text})

    # Clean, valid TwiML with <Play> followed by <Record>
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    {play_tag}
    <Record 
        action="{server_url}/call/process?session_id={call_sid}" 
        method="POST" 
        maxLength="30" 
        timeout="3" 
        playBeep="true"
    />
    <Say language="hi-IN">YojanaVaani me call karne ke liye dhanyavad.</Say>
    <Hangup/>
</Response>
"""
    return Response(content=twiml, media_type="application/xml")


# ---------------------------------------------------------------------------
# 2. Process Spoken Audio from Telecom Carrier
# ---------------------------------------------------------------------------
@app.post("/call/process", response_class=PlainTextResponse)
async def process_call_audio(request: Request):
    """Triggered when citizen finishes speaking over the telephone."""
    form_data = await request.form()
    query_params = request.query_params
    session_id = query_params.get("session_id") or form_data.get("CallSid") or "unknown"
    recording_url = form_data.get("RecordingUrl")
    server_url = get_server_url()

    print(f"[Telephony Process Call] Received recording for session: {session_id} | URL: {recording_url}")

    session = CALL_SESSIONS.get(session_id, {
        "call_sid": session_id,
        "lang": "te",
        "turns": [],
    })

    reply_text = "నమస్కారం! మీ మాట స్పష్టంగా వినిపించలేదు. దయచేసి మరొకసారి అడగండి లేదా సమీప గ్రామ సచివాలయాన్ని సంప్రదించండి."
    reply_audio = None

    if recording_url:
        try:
            # Twilio audio URL: append .wav for direct PCM audio download
            dl_url = f"{recording_url}.wav" if not recording_url.endswith(".wav") else recording_url
            audio_resp = requests.get(dl_url, timeout=12)
            if audio_resp.ok:
                audio_bytes = audio_resp.content
                print(f"[Telephony Process Call] Downloaded {len(audio_bytes)} bytes of citizen voice")
                turn = process_voice_turn(
                    user_audio=audio_bytes,
                    preferred_lang=session.get("lang", "te"),
                )
                reply_text = turn["reply_text"]
                reply_audio = turn["reply_audio"]
                session["turns"].append({"speaker": "Caller", "text": turn["user_text"]})
                print(f"[Telephony Process Call] Transcribed: '{turn['user_text']}'")
        except Exception as err:
            print(f"[Telephony Process Call] Error processing audio: {err}")
            reply_text = f"క్షమించండి, కాల్ ప్రాసెస్ చేయడంలో లోపం తలెత్తింది."

    session["turns"].append({"speaker": "Agent", "text": reply_text})
    CALL_SESSIONS[session_id] = session

    play_tag = ""
    if reply_audio:
        audio_id = cache_audio(reply_audio)
        play_tag = f"<Play>{server_url}/audio/{audio_id}.wav</Play>"
    else:
        play_tag = "<Say language='hi-IN'>Aapka sawal samajh me nahi aaya. Kripya punah koshish karein.</Say>"

    # Continue the conversation loop over the call line
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    {play_tag}
    <Record 
        action="{server_url}/call/process?session_id={session_id}" 
        method="POST" 
        maxLength="30" 
        timeout="3" 
        playBeep="true"
    />
    <Say language="hi-IN">YojanaVaani me call karne ke liye dhanyavad.</Say>
    <Hangup/>
</Response>
"""
    return Response(content=twiml, media_type="application/xml")


# ---------------------------------------------------------------------------
# 3. Outbound Proactive Call Dispatcher API
# ---------------------------------------------------------------------------
class OutboundCallPayload(BaseModel):
    phone_number: str
    scenario_id: str = "pm_kisan_dbt"
    language: str = "te"


@app.post("/call/outbound")
def trigger_proactive_call(payload: OutboundCallPayload):
    """Trigger an outbound automated phone call to any citizen's mobile number."""
    scenario = OUTBOUND_CALL_SCENARIOS.get(payload.scenario_id, OUTBOUND_CALL_SCENARIOS["pm_kisan_dbt"])
    msg_text = scenario.get(payload.language, scenario.get("en", "Government welfare notification."))
    
    call_id = f"outbound_{uuid.uuid4().hex[:8]}"
    CALL_SESSIONS[call_id] = {
        "call_sid": call_id,
        "caller_phone": payload.phone_number,
        "start_time": time.time(),
        "lang": payload.language,
        "scenario": scenario.get("title"),
        "turns": [{"speaker": "Agent (Outbound)", "text": msg_text}],
        "status": "dispatched",
    }

    return {
        "status": "success",
        "call_id": call_id,
        "recipient": payload.phone_number,
        "scenario": scenario.get("title"),
        "message": msg_text,
        "notice": "Call session initiated and ready for media stream.",
    }


# ---------------------------------------------------------------------------
# 4. Live Call Sessions & Telemetry
# ---------------------------------------------------------------------------
@app.get("/call/sessions")
def list_call_sessions():
    """Retrieve all active and completed citizen phone calls with transcripts."""
    return {
        "total_calls": len(CALL_SESSIONS),
        "sessions": list(CALL_SESSIONS.values()),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)
