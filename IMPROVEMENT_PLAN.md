# YojanaVaani AI - Improvement Plan

## Project Overview
A voice-first multilingual AI assistant for Indian government welfare schemes, built with:
- Gnani AI Prisma STT (Speech-to-Text)
- Gnani AI Timbre TTS (Text-to-Speech)
- Gemini Flash for dynamic scheme resolution
- Streamlit web UI

## Current State Assessment

### ✅ Working Well
- `.env` configured with GNANI_API_KEY and GEMINI_API_KEY
- `services.py` - Complete audio DSP, STT/TTS pipeline, scheme matching, guardrails
- `knowledge_base.json` - 29+ verified welfare schemes with multilingual translations
- `app.py` - Streamlit admin console on port 8502
- `telephony_server.py` - FastAPI telephony server on port 8000
- Web frontend at `Desktop\YojanaVaani-AI\web\index.html` with 22-language i18n
- Audio DSP preprocessing (enhance_audio, convert_to_pcm_wav, simulate_telephony_channel)
- Scam/or fraud detection with SENSITIVE_PATTERNS
- Language detection (detect_query_language, detect_script_language)
- Multi-scheme response generation (generate_multi_scheme_response)
- End-to-end voice pipeline (process_voice_turn)

### 🔧 Areas for Improvement

#### 1. **Frontend-Backend Integration**
- Web index.html needs `/api/voice`, `/api/chat`, `/api/schemes` endpoints
- Language auto-detection flow not fully connected
- Real-time visualizer needs audio stream connection

#### 2. **Knowledge Base Enhancement**
- `knowledge_base.json` needs structured keyword/ID fields for better scoring
- State filtering needs standardization (Andhra Pradesh, Telangana, etc.)
- Multi-scheme queries need better Gemini integration

#### 3. **Audio Pipeline Optimization**
- VAD (Voice Activity Detection) tuning for 1.2s auto-cutoff
- DSP gain normalization for rural microphones
- Telephony narrowband simulation for testing

#### 4. **Scheme Matching Accuracy**
- Token overlap scoring needs multi-word phrase support
- Code-mixed Hinglish detection improvement
- ID token extraction (kisan, ayushman, etc.)

#### 5. **TTS & Audio Feedback**
- TTS caching optimization
- Multi-language voice selection (Poorvi, other regional voices)
- Low-latency spoken response (<1.0s target)

#### 6. **Security & Guardrails**
- Sensitive pattern detection (Aadhaar 12-digit, PAN, OTP, card numbers)
- Scam term detection in multiple Indian languages
- Out-of-scope query blocking

#### 7. **User Experience**
- Sample prompt capsules in user's language
- Visual scheme cards with benefits/eligibility
- CSC ticket registration flow
- Analytics dashboard for citizen demand

## Priority Improvements (Sprint 1)

### High Priority
1. **Connect frontend `/api` endpoints** - Wire up the web interface to backend services
2. **Enhance knowledge_base.json** - Add structured keywords and state fields
3. **Improve language detection** - Better Hinglish/code-mixed support
4. **Fix .env.example** - Document all required API keys

### Medium Priority
5. **Optimize DSP gain** - Better normalization for rural microphone qualities
6. **Add multi-scheme summary** - Gemini-powered combined scheme answers
7. **Enhance scam shield** - More sensitive pattern detection in Hindi/Regional languages
8. **Improve TTS latency** - Cache warming and pre-loading

### Low Priority
9. **Add analytics dashboard** - Visualize scheme queries by region/language
10. **Add more sample prompts** - All 22 languages with regional questions
11. **Telephony call continuity** - Stateful IVR memory over PSTN
12. **Automated scheme sync** - Pull from myscheme.gov.in

## Technical Debt to Address

- [ ] `.env` has real keys committed - should be in `.env.example` template only
- [ ] `requirements.txt` missing `python-dotenv` explicit reference
- [ ] No unit tests for `services.py` guardrail functions
- [ ] `knowledge_base.json` needs backup/versioning
- [ ] Web frontend has hardcoded API URLs - should use environment vars
- [ ] No Docker configuration for deployment
- [ ] Telephony server needs Twilio webhook validation

## Integration with MetaGPT

### Potential Auto-Gen Agents
Based on the Paperclip organizational chart from PROJECT_ONBOARDING.md:

| Role | Agent Name | MetaGPT Persona |
|------|-----------|----------------|
| CEO / Product Director | `yojana-ceo` | Product roadmap, challenge alignment |
| Lead Voice AI Architect | `yojana-voice-lead` | Gnani Prisma STT, TTS latency, DSP |
| Full-Stack Telephony Engineer | `yojana-telecom-eng` | FastAPI, Twilio, webhooks |
| Linguistics & Grounding Specialist | `yojana-indic-nlu` | knowledge_base.json, multilingual eval |
| Anti-Fraud & Security Guardian | `yojana-sec-guard` | PII regex, scam classification |

### MetaGPT Workflow Ideas
1. **Scheme Discovery Pipeline**: Parse `myscheme.gov.in` → normalize → translate → `knowledge_base.json`
2. **Multilingual Evaluation**: Translate schemes across 22 languages → validate native speaker accuracy
3. **DSP Benchmark**: Record audio samples → enhance_audio → STT test → accuracy metrics
4. **Scam Pattern Mining**: Analyze fraud reports → extract new SENSITIVE_PATTERNS → update guardrails
5. **Query Router**: Classify citizen queries → route to scheme match → Gemini dynamic response → TTS

## Next Steps

1. **Week 1**: Connect frontend-backend APIs, fix .env.example
2. **Week 2**: Enhance knowledge_base.json structure, improve language detection
3. **Week 3**: Optimize DSP pipeline, add multi-scheme Gemini responses
4. **Week 4**: Security guardrails enhancement, TTS latency optimization
5. **Week 5**: Analytics dashboard, automated scheme sync setup

---
*Plan created for YojanaVaani AI autonomous workforce development*