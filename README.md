# 🇮🇳 YojanaVaani AI — JanSeva Government Schemes Voice Assistant

> **Aapki Bhasha Me Sarkari Yojnaon Ki Jankari**  
> Built for the **[Gnani AI Great Indian AI Internship Challenge](https://www.gnani.ai/great-indian-ai-internship-registration-form)**  
> Powered by **Gnani Prisma Indic STT** and **Gnani Timbre TTS (v2.5)**.  
> 🌐 **Live Public App**: [https://yojanavaani-ai.onrender.com](https://yojanavaani-ai.onrender.com)  
> 📂 **GitHub Repository**: [https://github.com/Sandeepkumar154/YojanaVaani-AI](https://github.com/Sandeepkumar154/YojanaVaani-AI)

---

## 🌟 The Vision & Social Impact

Over **800 million citizens** across Bharat (villages, small towns, and Tier 2/3 cities) are eligible for Central and State welfare schemes—such as **PM-Kisan, Ayushman Bharat, PM Awas Yojana, PM Mudra Loans, and Sukanya Samriddhi**. 

However, millions miss out because:
1. Complex government web portals are written in formal text/English.
2. Many beneficiaries cannot read or type comfortably on smartphones.
3. Citizens do not know which documents are needed or who is eligible.

**YojanaVaani AI** solves this with a **voice-first, multilingual AI assistant**:
Citizens simply **tap the mic and speak naturally in their mother tongue or Hinglish** (e.g. *"Kisan samman nidhi ka paisa kab aayega?"*, *"Ayushman card me 5 lakh ka free ilaaj kaise milta hai?"*), and receive an immediate spoken voice reply with eligibility criteria, benefits, required documents, and CSC follow-up assistance.

---

## 🏆 How YojanaVaani AI Targets 8+ Challenge Award Categories

| Award Category | How YojanaVaani AI Hits It |
|---|---|
| 🗣️ **22 Official Languages** | Covers all 22 Eighth Schedule Indian languages (Hindi, Bengali, Telugu, Marathi, Tamil, Kannada, Malayalam, Gujarati, Punjabi, Odia, Assamese, etc.) + Hinglish & English via Prisma STT (`indic-auto`) & Timbre TTS |
| 🏛️ **Central + All State Schemes** | 356+ verified major welfare schemes covering Central Government & ALL 28 STATES OF INDIA (at least 12 schemes per state) across Andhra Pradesh, Arunachal Pradesh, Assam, Bihar, Chhattisgarh, Goa, Gujarat, Haryana, Himachal Pradesh, Jharkhand, Karnataka, Kerala, Madhya Pradesh, Maharashtra, Manipur, Meghalaya, Mizoram, Nagaland, Odisha, Punjab, Rajasthan, Sikkim, Tamil Nadu, Telangana, Tripura, Uttar Pradesh, Uttarakhand, and West Bengal |
| 🔀 **Code-Mixed Voice / Hinglish** | Built specifically to understand natural Indian code-mixing (e.g. *"Dukan ke liye Mudra loan kaise apply karein?"*, *"Ladki Bahin yojana me kitna milta hai?"*) |
| 📞 **Noisy Audio Robustness** | Tested for real-world ambient street/village noise using Prisma's telephony-grade speech model |
| 🌍 **Real-World Impact** | Connects marginalized rural & small-town families to life-changing healthcare, housing, and livelihood funds |
| 🏘️ **Tier 2/3 Town Focus** | Directly designed for grassroots Common Service Centers (CSCs) and Gram Panchayats |
| 🛡️ **Scam & Privacy Shield** | Detects and blocks fraudulent attempts to steal OTPs, ATM PINs, or sensitive Aadhaar numbers |
| ⏱️ **60-Second Demo** | Tap mic → speak in Hinglish/mother tongue → hear instant spoken response with visual scheme card & CSC ticket |
| ❤️ **Crowd Favourite** | Highly relatable, shareable, and inspiring social cause for LinkedIn / X demo videos |

---

## 🚀 Key Features

- **🎙️ Live Mic Voice Assistant**: Tap the microphone button in the browser to speak; auto-processes through Prisma STT and Timbre TTS.
- **⚡ One-Click Citizen Scenarios**: Instant demo buttons for Farmers (PM-Kisan), Healthcare (Ayushman Bharat), Livelihoods (Mudra Loan), Girls' Education (Sukanya Samriddhi), Housing (PM Awas), and Scam Guardrail.
- **🏛️ Complete Pan-India Grounded Knowledge Base**: 356+ verified flagship welfare schemes covering Central Government and ALL 28 States of India (at least 12 complete schemes per state) with benefits, eligibility, and required documents in 24 Indian languages and Hinglish.
- **🔊 Spoken Multilingual Voice Output**: Generates synthesized speech using Timbre v2.5 in the citizen's detected language.
- **📋 CSC / Gram Panchayat Ticket Desk**: Citizens can register for local representative follow-up with their Village/District details (stored in SQLite).
- **📊 Real-Time Analytics Dashboard**: Visualizes citizen demand by scheme and lists pending assistance tickets.
- **🛡️ Anti-Fraud & Privacy Guardrails**: Flags sensitive OTPs, card numbers, and full Aadhaar mentions to prevent scams.

---

## 🛠️ Tech Stack & Gnani API Verification

* **STT (Speech-to-Text)**: `POST https://api.vachana.ai/stt/v3` (`prisma-v3.0`, `indic-auto`, `format=codemix`)
* **TTS (Text-to-Speech)**: `POST https://api.vachana.ai/api/v1/tts/inference` (`timbre-v2.5`, 24kHz linear PCM WAV)
* **Frontend UI**: Streamlit + `audio-recorder-streamlit`
* **Local Database**: SQLite (`yojanavaani.db`)
* **Knowledge Base**: `knowledge_base.json` (multilingual scheme repository)

---

## 🏃 Quick Start (Local Setup)

1. **Clone or navigate to the folder**:
   ```powershell
   cd bharatvoice-ai
   ```
2. **Install dependencies**:
   ```powershell
   pip install -r requirements.txt
   ```
3. **Configure your Gnani API Key**:
   - Copy `.env.example` to `.env`:
     ```env
     GNANI_API_KEY=your_actual_gnani_api_key_here
     ```
4. **Launch the Voice Assistant**:
   ```powershell
   streamlit run app.py
   ```
5. Open your browser at **`http://localhost:8502`**.

---

## 🎬 60-Second Demo Video Script (For Submission)

* **[0:00 - 0:10] The Problem**: *"Over 800 million citizens in India qualify for welfare schemes, but miss out because government portals are hard to read and navigate."*
* **[0:10 - 0:25] The Solution**: *"Meet YojanaVaani AI. An AI voice assistant powered by Gnani AI's Prisma and Timbre."*
* **[0:25 - 0:45] Live Demo**:
  * Tap mic: Speak *"Mujhe 5 lakh wala Ayushman hospital card banwana hai."*
  * Prisma transcribes in Hinglish & detects language.
  * Timbre speaks back in natural voice.
  * Show the interactive scheme breakdown (Benefit: ₹5 Lakh, Docs: Ration Card + Aadhaar).
  * Click *"Request CSC Follow-up"* to log the ticket.
* **[0:45 - 0:55] Scam Shield & Analytics**:
  * Speak an OTP → show the instant Scam Protection Warning!
  * Switch to the Gram Panchayat Analytics tab showing live citizen demand charts.
* **[0:55 - 1:00] Closing**: *"YojanaVaani AI: Empowering every citizen with the power of voice. Built with @GnaniAI #GnaniAI #GreatIndianAIInternshipChallenge"*
