# 🇮🇳 YojanaVaani AI — JanSeva Government Schemes Voice Assistant

> **Aapki Bhasha Me Sarkari Yojnaon Ki Jankari (Voice of Bharat)**  
> Built for the **[Gnani AI Great Indian AI Internship Challenge (November 2026)](https://www.gnani.ai/great-indian-ai-internship-registration-form)**  
> Powered by **Gnani Prisma Indic STT** and **Gnani Timbre TTS (v2.5)** with **Google Gemini Reasoning**.  
> 🌐 **Live Public App**: [https://yojanavaani-ai.onrender.com](https://yojanavaani-ai.onrender.com)  
> 📂 **GitHub Repository**: [https://github.com/Sandeepkumar154/YojanaVaani-AI](https://github.com/Sandeepkumar154/YojanaVaani-AI)  
> 📄 **1-Page Solution Pitch**: [SOLUTION_PITCH.md](SOLUTION_PITCH.md)

---

## 🌟 The Vision & Social Impact

Over **800 million citizens** across Bharat (villages, small towns, and Tier 2/3 cities) are eligible for Central and State welfare schemes—such as **PM-Kisan, Ayushman Bharat, PM Awas Yojana, PM Mudra Loans, and Sukanya Samriddhi**. 

However, millions miss out because:
1. Complex government web portals are written in formal text/English.
2. Many beneficiaries cannot read or type comfortably on smartphones.
3. Citizens do not know which documents are needed or who is eligible.

**YojanaVaani AI** solves this with a **voice-first, multilingual AI assistant**:
Citizens simply **tap the mic and speak naturally in their mother tongue or Hinglish** (e.g. *"Kisan samman nidhi ka paisa kab aayega?"*, *"నాకు తెలుగు schemes, ఆంధ్రప్రదేశ్లో అమ్మ ఒడి గురించి explain చేయండి"*), and receive an immediate, culturally nuanced spoken voice reply with eligibility criteria, benefits, required documents, and local CSC/Sachivalayam guidance.

---

## 🏆 How YojanaVaani AI Targets 8+ Challenge Award Categories

| Award Category | How YojanaVaani AI Hits It |
|---|---|
| 🗣️ **24 Official Languages** | Covers all 22 Eighth Schedule Indian languages (Hindi, Bengali, Telugu, Marathi, Tamil, Kannada, Malayalam, Gujarati, Punjabi, Odia, Assamese, etc.) + Hinglish & English via Prisma STT (`indic-auto`) & Timbre TTS |
| 🏛️ **Central + All 28 States** | 356+ verified major welfare schemes covering Central Government & **ALL 28 STATES OF INDIA** (at least 12 schemes per state) across AP, Telangana, UP, Bihar, Maharashtra, Karnataka, West Bengal, and beyond |
| 🔀 **Code-Mixed Voice / Hinglish** | Built specifically to understand natural Indian code-mixing (e.g. *"Dukan ke liye Mudra loan kaise apply karein?"*, *"PM Kisan scheme me kitna milta hai?"*) |
| 📞 **Telephony-Ready IVR** | Engineered to bridge with PSTN toll-free gateways so citizens on basic ₹1,000 keypad feature phones can call in without internet |
| 🌍 **Real-World Impact** | Connects marginalized rural & small-town families to life-changing healthcare, housing, and livelihood funds |
| 🏘️ **Grassroots CSC Focus** | Guides citizens directly to their nearest Common Service Center (CSC) or Gram/Ward Sachivalayam |
| 🛡️ **Scam & Privacy Shield** | Real-time guardrail that detects and blocks fraudulent attempts to steal OTPs, ATM PINs, or sensitive Aadhaar numbers |
| ⚡ **Sub-150ms Performance** | Optimized local knowledge retrieval with deterministic fallback guaranteeing 100% uptime under any network condition |

---

## 🚀 Key Features

- **🎙️ Live Mic Voice Assistant**: Tap the microphone orb in the browser to speak in your mother tongue; auto-processed through Gnani Prisma Indic STT and Timbre TTS.
- **💬 Citizen Chat Assistant**: Dual-mode input allowing citizens to either speak into the microphone OR type text questions in English, Hindi, Telugu, or regional scripts with instant audio replay buttons.
- **🏛️ Complete Pan-India Knowledge Base**: 356+ verified flagship welfare schemes covering Central Government and ALL 28 States of India with benefits, eligibility, and required documents.
- **🔊 Natural Indic Voice Synthesis**: Generates studio-quality synthesized speech using Timbre v2.5 (`Aarohi`) in the citizen's detected language.
- **🛡️ Anti-Fraud & Privacy Guardrails**: Flags sensitive OTPs, card numbers, and full Aadhaar mentions to prevent scams and educate citizens.
- **📡 24/7 Production Deployment**: Live on Render cloud infrastructure with automated keep-alive monitoring and zero cold-start latency.

---

## 🛠️ Architecture & Tech Stack

```
[ Citizen Voice Query ]
       │
       ▼
 1. GNANI PRISMA STT  ───► Converted to Text (24 Official Indian Languages)
       │
       ▼
 2. SECURITY GUARDRAILS ──► Scans for Scams, OTPs, or Out-of-Scope Queries
       │
       ▼
 3. REASONING ENGINE  ───► Google Gemini Brain + 356 Scheme Knowledge Base
       │
       ▼
 4. GNANI TIMBRE TTS  ───► Natural Spoken Voice Output delivered back to Citizen
```

* **STT (Speech-to-Text)**: Gnani Prisma STT (`POST https://api.vachana.ai/stt/v3`, `indic-auto`)
* **TTS (Text-to-Speech)**: Gnani Timbre TTS (`POST https://api.vachana.ai/api/v1/tts/inference`, v2.5, 24kHz)
* **Backend Engine**: FastAPI + Uvicorn (`telephony_server.py`)
* **Knowledge Store**: Structured local index (`knowledge_base.json`, 356 schemes)
* **Hosting**: Render Cloud PaaS (`https://yojanavaani-ai.onrender.com`)

---

## 🏃 Quick Start (Local Setup)

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Sandeepkumar154/YojanaVaani-AI.git
   cd YojanaVaani-AI
   ```
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Configure Environment Variables**:
   Create a `.env` file from the example:
   ```env
   GNANI_API_KEY=your_actual_gnani_api_key_here
   GEMINI_API_KEY=your_gemini_api_key_here
   ```
4. **Launch the Production Web App**:
   ```bash
   uvicorn telephony_server:app --host 0.0.0.0 --port 8000 --reload
   ```
5. Open your browser at **`http://localhost:8000`**.

---

## 📄 Submission Information

* **Contest**: Gnani AI — Great Indian AI Internship Challenge (November 2026)
* **Solution Pitch**: See full details in [SOLUTION_PITCH.md](SOLUTION_PITCH.md)
* **Live Application**: [https://yojanavaani-ai.onrender.com](https://yojanavaani-ai.onrender.com)
* **License**: Open Source for public good under the MIT License
