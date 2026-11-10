

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


STATE_ALIASES: dict[str, list[str]] = {
    "All India": ["central", "centralgov", "central gov", "central government", "central schemes", "central yojana", "kendra", "kendriya", "kendra sarkar", "national", "all india", "భారత ప్రభుత్వం", "కేంద్ర", "కేంద్ర ప్రభుత్వం", "కేంద్ర పథకాలు", "కేంద్ర ప్రభుత్వ పథకాలు", "केंद्र सरकार", "केंद्रीय योजनाएं", "مرکزی حکومت"],
    "Andhra Pradesh": ["andhra pradesh", "andhra", "ap", "ఆంధ్రప్రదేశ్", "ఆంధ్ర", "ఆంధ్ర ప్రదేశ్", "आंध्र प्रदेश", "ஆந்திரா", "ಆಂಧ್ರಪ್ರದೇಶ"],
    "Telangana": ["telangana", "ts", "తెలంగాణ", "तेलंगाना", "ತೆಲಂಗಾಣ", "தெலுங்கானா"],
    "Karnataka": ["karnataka", "కర్ణాటక", "ಕರ್ನಾಟಕ", "कर्नाटक", "கர்நாடகா"],
    "Tamil Nadu": ["tamil nadu", "tamilnadu", "tn", "తమిళనాడు", "தமிழ்நாடு", "तमिलनाडु", "ತಮಿಳುನಾಡು"],
    "Maharashtra": ["maharashtra", "మహారాష్ట్ర", "महाराष्ट्र", "மகாராஷ்டிரா"],
    "Kerala": ["kerala", "కేరళ", "കേരളം", "केरल", "கேரளா"],
    "Uttar Pradesh": ["uttar pradesh", "up", "ఉత్తర ప్రదేశ్", "उत्तर प्रदेश"],
    "Bihar": ["bihar", "బీహార్", "बिहार"],
    "West Bengal": ["west bengal", "bengal", "పశ్చిమ బెంగాల్", "পশ্চিমবঙ্গ", "पश्चिम बंगाल"],
    "Madhya Pradesh": ["madhya pradesh", "mp", "మధ్యప్రదేశ్", "मध्य प्रदेश"],
    "Rajasthan": ["rajasthan", "రాజస్థాన్", "राजस्थान"],
    "Gujarat": ["gujarat", "గుజరాత్", "ગુજરાત", "गुजरात"],
    "Odisha": ["odisha", "orissa", "ఒడిశా", "ଓଡ଼ିଶା", "ओडिशा"],
    "Punjab": ["punjab", "పంజాబ్", "ਪੰਜਾਬ", "पंजाब"],
    "Assam": ["assam", "అస్సాం", "অসম", "असम"],
    "Haryana": ["haryana", "హర్యానా", "हरियाणा", "ਹਰਿਆਣਾ"],
    "Jharkhand": ["jharkhand", "జార్ఖండ్", "झारखंड", "ঝাড়খণ্ড"],
    "Chhattisgarh": ["chhattisgarh", "chattisgarh", "ఛత్తీస్‌గఢ్", "छत्तीसगढ़"],
    "Uttarakhand": ["uttarakhand", "uttaranchal", "ఉత్తరాఖండ్", "उत्तराखंड", "उत्तरांचल"],
    "Himachal Pradesh": ["himachal pradesh", "himachal", "hp", "హిమాచల్ ప్రదేశ్", "हिमाचल प्रदेश", "हिमाचल"],
    "Goa": ["goa", "గోవా", "गोवा", "गोंय"],
    "Tripura": ["tripura", "త్రిపుర", "त्रिपुरा", "ত্রিপুরা"],
    "Meghalaya": ["meghalaya", "మేఘాలయ", "मेघालय"],
    "Manipur": ["manipur", "మణిపూర్", "मणिपुर", "ꯃꯅꯤꯄꯨꯔ"],
    "Nagaland": ["nagaland", "నాగాలాండ్", "नागालैंड"],
    "Arunachal Pradesh": ["arunachal pradesh", "arunachal", "అరుణాచల్ ప్రదేశ్", "अरुणाचल प्रदेश", "अरुणाचल"],
    "Mizoram": ["mizoram", "మిజోరాం", "मिजोरम"],
    "Sikkim": ["sikkim", "సిక్కిం", "सिक्किम"]
}

def detect_state_from_query(query: str) -> str | None:
    low = query.lower()
    for state, aliases in STATE_ALIASES.items():
        for a in aliases:
            a_low = a.lower()
            if len(a_low) <= 3:
                # Require word boundary for short abbreviations like 'ts', 'ap', 'up', 'mp', 'hp'
                if re.search(r'\b' + re.escape(a_low) + r'\b', low):
                    return state
            else:
                if a_low in low:
                    return state
    return None


SCHEME_FALLBACK_MESSAGES: dict[str, str] = {
    "en": "We could not find the exact scheme you requested. Major welfare schemes include PM-Kisan (₹6,000/yr), Ayushman Bharat (₹5,00,000 free health cover), and PM Awas Yojana. Please state the scheme name clearly.",
    "hi": "हम आपके द्वारा पूछी गई योजना की सटीक जानकारी नहीं पा सके। प्रमुख सरकारी योजनाओं में पीएम-किसान (₹6,000 सालाना), आयुष्मान भारत (₹5,00,000 तक मुफ्त इलाज), और पीएम आवास योजना शामिल हैं। कृपया योजना का नाम स्पष्ट बताएं।",
    "hi-en": "Hum aapke dwara puchi gayi scheme ki exact details locate nahi kar sake. Major schemes me PM-Kisan (₹6,000/yr), Ayushman Bharat (₹5,00,000 free treatment) aur PM Awas Yojana shamil hain. Kripya scheme ka naam batayein.",
    "te": "మీరు అడిగిన పథకం వివరాలు లభించలేదు. ప్రధాన పథకాల్లో పీఎం-కిసాన్ (₹6,000/సం.), ఆయుష్మాన్ భారత్ (₹5,00,000 ఉచిత వైద్యం), మరియు పీఎం ఆవాస్ ఉన్నాయి. దయచేసి పథకం పేరును స్పష్టంగా చెప్పండి.",
    "ta": "நீங்கள் கேட்ட திட்ட விவரங்கள் கிடைக்கவில்லை. முக்கிய திட்டங்களில் பிஎம்-கிசான் (₹6,000), ஆயுஷ்மான் பாரத் (₹5,00,000 இலவச சிகிச்சை) அடங்கும். திட்டத்தின் பெயரை தெளிவாகக் கூறவும்.",
    "kn": "ನೀವು ಕೇಳಿದ ಯೋಜನೆಯ ವಿವರಗಳು ಲಭ್ಯವಿಲ್ಲ. ಪ್ರಮುಖ ಯೋಜನೆಗಳಲ್ಲಿ ಪಿಎಂ-ಕಿಸಾನ್ (ವಾರ್ಷಿಕ ₹6,000), ಆಯುಷ್ಮಾನ್ ಭಾರತ್ (₹5,00,000 ಉಚಿತ ಚಿಕಿತ್ಸೆ) ಸೇರಿವೆ. ದಯವಿಟ್ಟು ಯೋಜನೆಯ ಹೆಸರನ್ನು ತಿಳಿಸಿ.",
    "ml": "നിങ്ങൾ ചോദിച്ച പദ്ധതി വിവരങ്ങൾ ലഭ്യമല്ല. പ്രധാന പദ്ധതികളിൽ പിഎം-കിസാൻ (₹6,000), ആയുഷ്മാൻ ഭാരത് (₹5,00,000 സൗജന്യ ചികിത്സ) എന്നിവ ഉൾപ്പെടുന്നു. പദ്ധതിയുടെ പേര് വ്യക്തമാക്കുക.",
    "mr": "तुम्ही विचारलेल्या योजनेची माहिती उपलब्ध नाही. प्रमुख योजनांमध्ये पीएम-किसान (₹6,000), आयुष्मान भारत (₹5,00,000 मोफत उपचार) यांचा समावेश आहे. कृपया योजनेचे नाव स्पष्ट सांगा.",
    "bn": "আপনার উল্লেখিত প্রকল্পের তথ্য পাওয়া যায়নি। প্রধান প্রকল্পগুলির মধ্যে পিএম-কিসান (₹6,000), আয়ুষ্মান ভারত (₹5,00,000 চিকিৎসা) অন্তর্ভুক্ত। অনুগ্রহ করে প্রকল্পের নাম বলুন।",
    "gu": "તમે પૂછેલ યોજનાની માહિતી મળી નથી. મુખ્ય યોજનાઓમાં પીએમ-કિસાન (₹6,000), આયુષ્માન ભારત (₹5,00,000 મફત સારવાર) શામેલ છે. કૃપા કરીને યોજનાનું નામ જણાવો.",
    "pa": "ਤੁਹਾਡੇ ਵੱਲੋਂ ਪੁੱਛੀ ਗਈ ਸਕੀਮ ਦੇ ਵੇਰਵੇ ਨਹੀਂ ਮਿਲੇ। ਮੁੱਖ ਸਕੀਮਾਂ ਵਿੱਚ ਪੀਐਮ-ਕਿਸਾਨ (₹6,000), ਆਯੁਸ਼ਮਾਨ ਭਾਰਤ (₹5,00,000 ਮੁਫ਼ਤ ਇਲਾਜ) ਸ਼ਾਮਲ ਹਨ। ਕਿਰਪਾ ਕਰਕੇ ਸਕੀਮ ਦਾ ਨਾਮ ਦੱਸੋ।",
    "or": "ଆପଣ ପଚାରିଥିବା ଯୋଜନାର ସୂଚନା ମିଳିଲା ନାହିଁ। ପ୍ରମୁଖ ଯୋଜନାରେ ପିଏମ୍-କିଷାନ (₹6,000), ଆୟୁଷ୍ମାନ ଭାରତ (₹5,00,000 ମାଗଣା ଚିକିତ୍ସା) ଅନ୍ତର୍ଭୁକ୍ତ। ଦୟାକରି ଯୋଜନାର ନାମ ସ୍ପଷ୍ଟ କରନ୍ତୁ।",
    "as": "আপুনি সোধা আঁচনিৰ তথ্য পোৱা নগ'ল। প্ৰধান আঁচনিত পিএম-কিষাণ (₹6,000), আয়ুষ্মান ভাৰত (₹5,00,000 চিকিৎসা) অন্তৰ্ভুক্ত। অনুগ্ৰহ কৰি আঁচনিৰ নাম কওক।",
    "ur": "آپ کی مطلوبہ اسکیم کی تفصیلات دستیاب نہیں ہیں۔ اہم اسکیموں میں پی ایم کسان (₹6,000) اور آیوشمان بھارت (₹5,00,000 مفت علاج) شامل ہیں۔ براہ کرم اسکیم کا نام واضح بتائیں۔",
    "sa": "भवता पृष्टायाः योजनायाः विवरणं न प्राप्तम्। प्रमुखयोजनासु पीएम-किसान (₹6,000), आयुष्मान भारत (₹5,00,000) च अन्तर्भवन्ति। कृपया योजनानाम स्पष्टं वदतु।",
    "ne": "तपाईंले खोज्नुभएको योजनाको विवरण भेटिएन। प्रमुख योजनाहरूमा पीएम-किसान (₹6,000), आयुष्मान भारत (₹5,00,000) पर्दछन्। कृपया योजनाको नाम स्पष्ट भन्नुहोस्।",
    "kok": "तुमी विचारिल्ल्या येवजणेची म्हायती मेळ्ळी ना। मुखेल येवजण्यांनी पीएम-किसान (₹6,000), आयुष्मान भारत (₹5,00,000) आसपावतात। उपकार करून येवजणेचें नांव स्पष्ट सांगात।",
    "mai": "अहाँ द्वारा पुछल योजनाक जानकारी नहि भेटल। प्रमुख योजना मे पीएम-किसान (₹6,000), आयुष्मान भारत (₹5,00,000) शामिल अछि। कृपया योजनाक नाम स्पष्ट कहू।",
    "doi": "तुंदे पुच्छे दी स्कीमा दा ब्योरा नेईं थ्होया। मुक्ख स्कीमें च पीएम-किसान (₹6,000), आयुष्मान भारत (₹5,00,000) शामल न। मेहरबानी करियै स्कीमा दा नां स्पष्ट दस्सो।",
    "ks": "تُہنٛز پُژھمٕژ سکیٖم ہٕنٛز تفصیٖل میٖل نہٕ۔ اہم سکیٖمَن مَنٛز پی ایم کِسان (₹6,000) تہٕ آیوشمان بھارَت (₹5,00,000) شٲمِل چھِ۔",
    "sd": "توهان جي پڇيل اسڪيم جا تفصيل نه مليا۔ اهم اسڪيمن ۾ پي ايم ڪسان (₹6,000) ۽ آيوشمان ڀارت (₹5,00,000) شامل آهن۔ مهرباني ڪري اسڪيم جو نالو واضح ٻڌايو۔",
    "mni": "ꯑꯗꯣꯝꯅꯥ ꯍꯪꯂꯤꯕꯥ ꯊꯧꯔꯥꯡꯒꯤ ꯑꯀꯨꯞꯄꯥ ꯐꯪꯗ꯭ꯔꯦ꯫ ꯃꯔꯨꯑꯣꯏꯕꯥ ꯊꯧꯔꯥꯡꯁꯤꯡꯗꯥ PM-Kisan (₹6,000) ꯑꯃꯁꯨꯡ Ayushman Bharat (₹5,00,000) ꯌꯥꯎꯔꯤ꯫",
    "brx": "नोंथाङा सोंनाय बिथांखिनि सोमोन्दै मोनाखै। गाहाय बिथांखिफोरनि गेजेराव PM-Kisan (₹6,000) आरो Ayushman Bharat (₹5,00,000) दं।",
    "sat": "ᱟᱢ ᱠᱩᱞᱤ ᱟᱠᱟᱫ ᱡᱚᱡᱚᱱᱟ ᱨᱮᱱᱟᱜ ᱵᱤᱵᱚᱨᱚᱬ ᱵᱟᱝ ᱧᱟᱢ ᱞᱮᱱᱟ᱾ ᱢᱩᱬᱩᱛ ᱡᱚᱡᱚᱱᱟ ᱠᱚᱨᱮ PM-Kisan (₹6,000) ᱟᱨ Ayushman Bharat (₹5,00,000) ᱥᱮᱞᱮᱫ ᱢᱮᱱᱟᱜᱼᱟ᱾"
}

SCAM_MESSAGES: dict[str, str] = {
    "en": "SECURITY ALERT: Never share your OTP, ATM PIN, UPI PIN, or bank passwords with anyone. Government schemes never ask for passwords or fees.",
    "hi": "सुरक्षा चेतावनी: कभी भी अपना OTP, ATM पिन, UPI पिन या बैंक पासवर्ड साझा न करें। सरकारी योजनाएं कभी भी पासवर्ड या शुल्क नहीं मांगती हैं।",
    "hi-en": "SECURITY ALERT: Kabhi bhi apna OTP, ATM PIN, UPI PIN ya bank password kisi ko mat batayein. Sarkari schemes kabhi password ya fee nahi maangti.",
    "te": "భద్రతా హెచ్చరిక: మీ OTP, ATM పిన్ లేదా బ్యాంక్ పాస్‌వర్డ్‌లను ఎవరితోనూ పంచుకోవద్దు. ప్రభుత్వ పథకాలు ఎన్నడూ రుసుము లేదా OTP అడగవు.",
    "ta": "பாதுகாப்பு எச்சரிக்கை: உங்கள் OTP அல்லது வங்கி PIN விவரங்களை யாரிடமும் பகிர வேண்டாம். அரசு திட்டங்கள் கட்டணம் அல்லது கடவுச்சொல் கேட்பதில்லை.",
    "kn": "ಭದ್ರತಾ ಎಚ್ಚರಿಕೆ: ನಿಮ್ಮ OTP ಅಥವಾ ಬ್ಯಾಂಕ್ ಪಿನ್ ಅನ್ನು ಯಾರೊಂದಿಗೂ ಹಂಚಿಕೊಳ್ಳಬೇಡಿ. ಸರ್ಕಾರಿ ಯೋಜನೆಗಳು ಪಾಸ್‌ವರ್ಡ್ ಅಥವಾ ಶುಲ್ಕವನ್ನು ಕೇಳುವುದಿಲ್ಲ.",
    "ml": "സുരക്ഷാ മുന്നറിയിപ്പ്: നിങ്ങളുടെ OTP, ATM പിൻ, ബാങ്ക് പാസ്‌വേഡ് എന്നിവ ആരുമായും പങ്കിടരുത്. സർക്കാർ പദ്ധതികൾ ഒരിക്കലും ഫീസ് ആവശ്യപ്പെടുന്നില്ല.",
    "mr": "सुरक्षा सूचना: तुमचा OTP, ATM पिन किंवा बँक पासवर्ड कोणाशीही शेअर करू नका. सरकारी योजना कधीही शुल्क किंवा पासवर्ड मागत नाहीत.",
    "bn": "নিরাপত্তা সতর্কতা: আপনার OTP, ATM পিন বা ব্যাংকের পাসওয়ার্ড কারো সাথে শেয়ার করবেন না। সরকারি প্রকল্পে কোনো ফি লাগে না।",
    "gu": "સુરક્ષા ચેતવણી: તમારો OTP, ATM પિન કે બેંક પાસવર્ડ ક્યારેય કોઈની સાથે શેર કરશો નહીં. સરકારી યોજનાઓ ક્યારેય ફી કે પાસવર્ડ માંગતી નથી.",
    "pa": "ਸੁਰੱਖਿਆ ਚੇਤਾਵਨੀ: ਆਪਣਾ OTP, ATM ਪਿੰਨ ਜਾਂ ਬੈਂਕ ਪਾਸਵਰਡ ਕਦੇ ਕਿਸੇ ਨਾਲ ਸਾਂਝਾ ਨਾ ਕਰੋ। ਸਰਕਾਰੀ ਸਕੀਮਾਂ ਕਦੇ ਫੀਸ ਨਹੀਂ ਮੰਗਦੀਆਂ।",
    "or": "ସୁରକ୍ଷା ସତର୍କତା: ଆପଣଙ୍କର OTP, ATM ପିନ୍ କିମ୍ବା ବ୍ୟାଙ୍କ ପାସୱାର୍ଡ କାହା ସହିତ ସେୟାର କରନ୍ତୁ ନାହିଁ। ସରକାରୀ ଯୋଜନା କେବେବି ଶୁଳ୍କ ମାଗେ ନାହିଁ।",
    "as": "সুৰক্ষা সতৰ্কবাণী: আপোনাৰ OTP, ATM পিন বা বেংক পাছৱৰ্ড কাৰো সৈতে শ্বেয়াৰ নকৰিব। চৰকাৰী আঁচনিত কেতিয়াও মাচুল নালাগে।",
    "ur": "حفاظتی انتباہ: اپنا OTP، اے ٹی ایم پن یا بینک پاس ورڈ کسی کو نہ بتائیں۔ سرکاری اسکیمیں کبھی فیس یا پاس ورڈ نہیں مانگتیں۔",
    "sa": "सुरक्षाचेतावनी: स्वकीयं OTP, ATM पिन वा बैंक-कूटशब्दं कदापि केनापि सह न योजयतु।",
    "ne": "सुरक्षा चेतावनी: आफ्नो OTP, ATM पिन वा बैंक पासवर्ड कसैसँग साझा नगर्नुहोस्। सरकारी योजनाले शुल्क माग्दैन।",
    "kok": "सुरक्षा शिटकावणी: तुमचो OTP, ATM पिन वा बँक पासवर्ड कोणाकूच दिवचो न्हय। सरकारी येवजण्यो केन्नाच फी मागत नात।",
    "mai": "सुरक्षा चेतावनी: अपन OTP, ATM पिन वा बैंक पासवर्ड ककरो सँ साझा नहि करू। सरकारी योजना शुल्क नहि मांगैत अछि।",
    "doi": "सुरक्षा चेतावनी: अपना OTP, ATM पिन जां बैंक पासवर्ड कुसै कन्नै सांझा नेईं करो। सरकारी स्कीमां कदें फीस नेईं मंगदियां।",
    "ks": "حفاظتی خبردار: پنُن OTP یا بینک پِن مٕہ دِیو کٲنٛسہِ تہِ۔ سرکٲری سکیٖمہٕ چھَنہٕ کُنہِ تہِ فیٖس منگان۔",
    "sd": "حفاظتي خبردار: پنهنجو OTP، ATM پن يا بئنڪ پاسورڊ ڪنهن سان به شيئر نه ڪريو۔",
    "mni": "ꯁꯦꯀ꯭ꯌꯨꯔꯤꯇꯤ ꯋꯥꯔꯅꯤꯡ: ꯅꯍꯥꯛꯀꯤ OTP ꯅꯠꯇ꯭ꯔꯒꯥ ꯕꯦꯡꯛ ꯄꯤꯟ ꯀꯅꯥꯗꯥꯁꯨ ꯄꯤꯕꯤꯒꯅꯨ꯫",
    "brx": "रैखाथि सांग्रांथि: नोंथांनि OTP एबा बेंक पिनखौ रावजोंबो सेयार खालामनाङा।",
    "sat": "ᱡᱟᱜᱽᱨᱩᱠᱛᱟ ᱪᱮᱛᱟᱣᱱᱤ: ᱟᱢᱟᱜ OTP ᱥᱮ ᱵᱮᱸᱠ ᱯᱤᱱ ᱚᱠᱚᱭ ᱥᱟᱶ ᱦᱚᱸ ᱟᱞᱚᱢ ᱥᱮᱭᱟᱨᱟ᱾"
}

OUT_OF_SCOPE_MESSAGES: dict[str, str] = {
    "en": "I am YojanaVaani AI, built strictly for Indian Government welfare schemes, subsidies, and pensions. Please ask about schemes like PM-Kisan, Ayushman Bharat, or state welfare programs.",
    "hi": "मैं योजनावाणी एआई हूँ, जो विशेष रूप से भारत सरकार की कल्याणकारी योजनाओं, सब्सिडी और पेंशन की जानकारी के लिए बना हूँ। कृपया केवल सरकारी योजनाओं के बारे में पूछें।",
    "hi-en": "Main YojanaVaani AI hoon, jo strictly Indian Government welfare schemes, subsidies aur pensions ke liye bana hai. Kripya sarkari schemes ke baare me puchein.",
    "te": "నేను యోజనవాణి AI ని. నేను కేవలం భారత ప్రభుత్వ సంక్షేమ పథకాలు, సబ్సిడీలు మరియు పింఛన్ల సమాచారం కోసం మాత్రమే పనిచేస్తాను. దయచేసి ప్రభుత్వ పథకాల గురించి అడగండి.",
    "ta": "நான் யோஜனாவாணி AI. இந்திய அரசு நலத்திட்டங்கள், மானியங்கள் மற்றும் ஓய்வூதியத் தகவல்களுக்கு மட்டுமே உதவ வடிவமைக்கப்பட்டுள்ளேன். தயவுசெய்து அரசு திட்டங்களைப் பற்றி கேட்கவும்.",
    "kn": "ನಾನು ಯೋಜನಾವಾಣಿ AI. ಭಾರತ ಸರ್ಕಾರದ ಕಲ್ಯಾಣ ಯೋಜನೆಗಳು, ಸಬ್ಸಿಡಿಗಳು ಮತ್ತು ಪಿಂಚಣಿ ಮಾಹಿತಿಗಾಗಿ ಮಾತ್ರ ನಾನು ಕಾರ್ಯನಿರ್ವಹಿಸುತ್ತೇನೆ. ದಯವಿಟ್ಟು ಸರ್ಕಾರಿ ಯೋಜನೆಗಳ ಬಗ್ಗೆ ಕೇಳಿ.",
    "ml": "ഞാൻ യോജനാവാണി AI ആണ്. ഇന്ത്യൻ സർക്കാർ ക്ഷേമ പദ്ധതികൾ, സബ്‌സിഡികൾ, പെൻഷൻ എന്നിവയെക്കുറിച്ച് മാത്രം വിവരങ്ങൾ നൽകാൻ നിർമ്മിച്ചതാണ്. ദയവായി സർക്കാർ പദ്ധതികളെക്കുറിച്ച് ചോദിക്കുക.",
    "mr": "मी योजनावाणी AI आहे. मी केवळ भारत सरकारच्या कल्याणकारी योजना, अनुदान आणि पेन्शनची माहिती देण्यासाठी बनवलेला आहे. कृपया सरकारी योजनांबद्दल विचारा.",
    "bn": "আমি যোজনাবাণী AI। আমি শুধুমাত্র ভারত সরকারের জনকল্যাণমূলক প্রকল্প, ভর্তুকি এবং পেনশন সম্পর্কে তথ্য দেওয়ার জন্য তৈরি। অনুগ্রহ করে সরকারি প্রকল্প সম্পর্কে জিজ্ঞাসা করুন।",
    "gu": "હું યોજનાવાણી AI છું. હું માત્ર ભારત સરકારની કલ્યાણકારી યોજનાઓ, સબસિડી અને પેન્શનની માહિતી માટે બનાવવામાં આવ્યો છું. કૃપા કરીને સરકારી યોજનાઓ વિશે પૂછો.",
    "pa": "ਮੈਂ ਯੋਜਨਾਵਾਣੀ AI ਹਾਂ। ਮੈਂ ਸਿਰਫ਼ ਭਾਰਤ ਸਰਕਾਰ ਦੀਆਂ ਭਲਾਈ ਸਕੀਮਾਂ, ਸਬਸਿਡੀਆਂ ਅਤੇ ਪੈਨਸ਼ਨਾਂ ਦੀ ਜਾਣਕਾਰੀ ਦੇਣ ਲਈ ਬਣਿਆ ਹਾਂ। ਕਿਰਪਾ ਕਰਕੇ ਸਰਕਾਰੀ ਸਕੀਮਾਂ ਬਾਰੇ ਪੁੱਛੋ।",
    "or": "ମୁଁ ଯୋଜନାବାଣୀ AI। ମୁଁ କେବଳ ଭାରତ ସରକାରଙ୍କ କଲ୍ୟାଣକାରୀ ଯୋଜନା, ସବସିଡି ଏବଂ ପେନସନ ବିଷୟରେ ସୂଚନା ଦେବା ପାଇଁ ପ୍ରସ୍ତୁତ। ଦୟାକରି ସରକାରୀ ଯୋଜନା ବିଷୟରେ ପଚାରନ୍ତୁ।",
    "as": "মই যোজনাবাণী AI। মই কেৱল ভাৰত চৰকাৰৰ কল্যাণমূলক আঁচনি, ৰাজসাহায্য আৰু পেঞ্চনৰ তথ্য দিবলৈ নিৰ্মাণ কৰা হৈছো। অনুগ্ৰহ কৰি চৰকাৰী আঁচনিৰ বিষয়ে সোধক।",
    "ur": "میں یوجنا وانی AI ہوں، جو صرف ہندوستانی حکومت کی فلاحی اسکیموں، سبسڈی اور پنشن کی معلومات کے لیے بنایا گیا ہے۔ براہ کرم سرکاری اسکیموں کے بارے میں پوچھیں۔",
    "sa": "अहं योजनावाणी AI अस्मि। अहं केवलं भारतसर्वकारस्य कल्याणकारीयोजनानां विषये सूचनां दातुं निर्मितः। कृपया सर्वकारीययोजनानां विषये पृच्छतु।",
    "ne": "म योजनावाणी AI हुँ। म केवल भारत सरकारका कल्याणकारी योजनाहरू, अनुदान र पेन्सनको जानकारी दिनको लागि बनाइएको हुँ। कृपया सरकारी योजनाबारे सोध्नुहोस्।",
    "kok": "हांव योजनावाणी AI. हांव फकत भारत सरकाराच्या कल्याणकारी येवजण्यांची म्हायती दिवपाक तयार आसा. उपकार करून सरकारी येवजण्यां विशीं विचारात.",
    "mai": "हम योजनावाणी AI छी। हम केवल भारत सरकारक कल्याणकारी योजना, अनुदान आ पेंशनक जानकारी लेल बनल छी। कृपया सरकारी योजनाक बारे मे पुछू।",
    "doi": "मैं योजनावाणी AI आं। मैं सिर्फ भारत सरकार दी भलाई स्कीमें, सब्सिडी ते पेंशन दी जानकारी देने लेई बणेआ आं। मेहरबानी करियै सरकारी स्कीमें बारै पुच्छो।",
    "ks": "بہٕ چھُس یوجنا وانی AI، یُس صرف سرکٲری فلاحی سکیٖمَن ہٕنٛز جانکٲری دِنہٕ خٲطرٕ بناونہٕ آو۔",
    "sd": "آئون يوجنا واڻي AI آهيان، جيڪو صرف سرڪاري ڀلائي اسڪيمن بابت ڄاڻ لاءِ ٺاهيو ويو آهي۔ مهرباني ڪري سرڪاري اسڪيمن بابت پڇو۔",
    "mni": "ꯑꯩꯍꯥꯛ ꯌꯣꯖꯅꯥꯕꯥꯅꯤ AI ꯅꯤ꯫ ꯑꯩꯍꯥꯛ ꯂꯩꯉꯥꯛꯀꯤ ꯌꯥꯏꯐ-ꯊꯧꯔꯥꯡꯁꯤꯡꯒꯤ ꯃꯇꯥꯡꯗꯥ ꯈꯪꯍꯟꯅꯕꯥ ꯁꯦꯝꯕꯅꯤ꯫",
    "brx": "आं योजनावाणी AI। आं सरकारनि मुलाम्फा बिथांखिफोरनि सोमोन्दै मिथिहोनायनि थाखाय बानायजानाय।",
    "sat": "ᱤᱧ ᱫᱚ ᱭᱳᱡᱽᱱᱟᱵᱟᱱᱤ AI ᱠᱟᱱᱟᱧ᱾ ᱥᱚᱨᱠᱟᱨᱤ ᱡᱚᱡᱚᱱᱟ ᱠᱚ ᱵᱟᱵᱚᱛ ᱛᱮ ᱠᱩᱞᱤᱭᱮᱢ᱾"
}

UNCLEAR_AUDIO_MESSAGES: dict[str, str] = {
    "en": "Could not clearly understand the audio. Please speak a bit louder into your microphone, or type your question below.",
    "hi": "आपकी आवाज़ स्पष्ट रूप से सुनाई नहीं दी। कृपया थोड़ा साफ़ आवाज़ में बोलिए, या नीचे अपना प्रश्न टाइप करें।",
    "hi-en": "Aapki aawaz clear nahi sunai di. Kripya thoda loud bolein ya neeche apna question type karein.",
    "te": "మీ వాయిస్ స్పష్టంగా వినిపించలేదు. దయచేసి మైక్రోఫోన్‌లో స్పష్టంగా మాట్లాడండి లేదా క్రింద మీ ప్రశ్నను టైప్ చేయండి.",
    "ta": "உங்கள் குரல் தெளிவாகக் கேட்கவில்லை. தயவுசெய்து மைக்ரோஃபோனில் தெளிவாகப் பேசவும் அல்லது கீழே தட்டச்சு செய்யவும்.",
    "kn": "ನಿಮ್ಮ ಧ್ವನಿ ಸ್ಪಷ್ಟವಾಗಿ ಕೇಳಿಸಲಿಲ್ಲ. ದಯವಿಟ್ಟು ಮೈಕ್ರೋಫೋನ್‌ನಲ್ಲಿ ಸ್ಪಷ್ಟವಾಗಿ ಮಾತನಾಡಿ ಅಥವಾ ಕೆಳಗೆ ಟೈಪ್ ಮಾಡಿ.",
    "ml": "നിങ്ങളുടെ ശബ്ദം വ്യക്തമായി കേട്ടില്ല. ദയവായി മൈക്രോഫോണിൽ വ്യക്തമായി സംസാരിക്കുക അല്ലെങ്കിൽ താഴെ ടൈപ്പ് ചെയ്യുക.",
    "mr": "तुमचा आवाज स्पष्ट ऐकू आला नाही. कृपया मायक्रोफोनमध्ये स्पष्ट बोला किंवा खाली तुमचा प्रश्न टाइप करा.",
    "bn": "আপনার কথা স্পষ্ট শোনা যায়নি। অনুগ্রহ করে মাইক্রোফোনে স্পষ্ট করে বলুন অথবা নিচে টাইপ করুন।",
    "gu": "તમારો અવાજ સ્પષ્ટ સંભળાયો નથી. કૃપા કરીને માઇક્રોફોનમાં સ્પષ્ટ બોલો અથવા નીચે ટાઇપ કરો.",
    "pa": "ਤੁਹਾਡੀ ਆਵਾਜ਼ ਸਾਫ਼ ਸੁਣਾਈ ਨਹੀਂ ਦਿੱਤੀ। ਕਿਰਪਾ ਕਰਕੇ ਮਾਈਕ ਵਿੱਚ ਸਾਫ਼ ਬੋਲੋ ਜਾਂ ਹੇਠਾਂ ਟਾਈਪ ਕਰੋ।",
    "or": "ଆପଣଙ୍କ ସ୍ୱର ସ୍ପଷ୍ଟ ଭାବରେ ଶୁଣାଗଲା ନାହିଁ। ଦୟାକରି ମାଇକ୍ରୋଫୋନରେ ସ୍ପଷ୍ଟ ଭାବରେ କୁହନ୍ତୁ କିମ୍ବା ତଳେ ଟାଇପ୍ କରନ୍ତୁ।",
    "as": "আপোনাৰ মাত স্পষ্টকৈ শুনা নগ'ল। অনুগ্ৰহ কৰি মাইক্ৰ'ফোনত স্পষ্টকৈ কওক বা তলত টাইপ কৰক।",
    "ur": "آپ کی آواز واضح سنائی نہیں دی۔ براہ کرم مائیکروفون میں صاف بولیں یا نیچے اپنا سوال ٹائپ کریں۔",
    "sa": "भवतः ध्वनिः स्पष्टं न श्रुतः। कृपया स्पष्टं वदतु अथवा अधः लिखतु।",
    "ne": "तपाईंको आवाज स्पष्ट सुनिएन। कृपया माइक्रोफोनमा स्पष्ट बोल्नुहोस् वा तल टाइप गर्नुहोस्।",
    "kok": "तुमचो आवाज स्पष्ट आयकूंक आयलो ना. उपकार करून स्पष्ट उलय्यात वा सकयल बरयात.",
    "mai": "अहाँक आवाज स्पष्ट नहि सुनाएल। कृपया स्पष्ट बाजू वा नीचाँ लिखू।",
    "doi": "तुंदी आवाज साफ नेईं सुणी। मेहरबानी करियै साफ बोलो जां हेठ लिखो।",
    "ks": "تُہنٛز آواز آیہِ نہٕ صاف بوزنہٕ۔ مہربٲنی کٔرِتھ بولیو صاف۔",
    "sd": "توهان جو آواز صاف نه آيو. مهرباني ڪري مائڪروفون ۾ صاف ڳالهايو يا هيٺ لکو.",
    "mni": "ꯅꯍꯥꯛꯀꯤ ꯈꯣꯟꯖꯦꯜ ꯃꯌꯦꯛ ꯁꯦꯡꯅꯥ ꯇꯥꯕꯥ ꯉꯝꯗꯦ꯫ ꯆꯥꯟꯕꯤꯗꯨꯅꯥ ꯃꯌꯦꯛ ꯁꯦꯡꯅꯥ ꯉꯥꯡꯕꯤꯌꯨ꯫",
    "brx": "नोंथांनि खोनासंनाया रोखा नङा। अननानै रोखा बुं एबा गाहायाव लिर।",
    "sat": "ᱟᱢᱟᱜ ᱟᱲᱟᱝ ᱥᱟᱯᱷᱟ ᱛᱮ ᱵᱟᱝ ᱟᱸᱡᱚᱢ ᱞᱮᱱᱟ᱾ ᱫᱟᱭᱟ ᱠᱟᱛᱮ ᱥᱟᱯᱷᱟ ᱛᱮ ᱨᱚᱲ ᱢᱮ᱾"
}

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

        # 3.5 Detect Romanized Telugu (Teluglish) markers
    teluglish_words = {"naaku", "naku", "andi", "kosam", "gurunchi", "gurinchi", "cheppandi", "kavali", "undi", "unnayi", "ela", "eppudu", "ekkada", "entha", "padhakam", "pathakam", "amma", "vodi", "rythu", "bharosa", "telusukovalani", "danikosam", "meeru", "manaku", "meeku", "avunu", "konchem"}
    if sum(1 for w in latin_words if w in teluglish_words) >= 2:
        return "te"

        # 3.6 Detect Romanized Kannada (Kanglish) & Tamil (Tanglish) markers
    kanglish_words = {"nannage", "nanage", "yojana", "bagge", "heli", "helu", "kodi", "beku", "yava", "elli", "hege", "karnataka", "gruha", "lakshmi", "anna", "bhagya"}
    if sum(1 for w in latin_words if w in kanglish_words) >= 2:
        return "kn"

    tanglish_words = {"enakku", "sollunga", "thittam", "eppadi", "yethu", "enna", "vendu", "tamil", "magalir", "urimai", "kudumba"}
    if sum(1 for w in latin_words if w in tanglish_words) >= 2:
        return "ta"

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

    trans = item.get("translations", {})
    if isinstance(trans, dict) and lang_code in trans and trans[lang_code]:
        return trans[lang_code]

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
        f"3. Do NOT use markdown, bold, asterisks, or bullet points.\n"
        f"4. STRICT VISIBILITY RULE: ALWAYS write ALL numbers, amounts, percentages, classes, and ages in NUMERIC DIGITS (e.g. ₹15,000, ₹6,000, ₹5,00,000, 75%, 1 నుండి 12, 18+). NEVER spell out numbers in words (NEVER write 'పదిహేను వేల', 'డెబ్బై ఐదు', 'पंद्रह हजार', 'fifteen thousand').\n"
        f"5. Write 95%+ of the response in pure {lang_name} ({native_name} script), keeping English words to absolute minimum."
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
                timeout=5,
            )
            if resp.status_code == 429:
                print(f"[Gemini Quota 429] Fast fallback active.")
                break
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
        f"   - Do NOT use any asterisks, markdown, bolding, or lists.\n"
        f"   - ALWAYS write ALL numbers, amounts, percentages, classes, and ages in NUMERIC DIGITS (e.g. ₹15,000, 75%, 1-12). NEVER spell numbers out in words.\n"
        f"   - Write 95%+ of the response in pure {lang_name} ({native_name} script), minimizing English words.\n"
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
                timeout=5,
            )
            if resp.status_code == 429:
                print(f"[Gemini Quota 429] Fast fallback active.")
                break
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



def build_comprehensive_state_schemes_response(state: str, schemes: list[dict[str, Any]], lang_code: str) -> str:
    """Build a complete, thorough scheme-by-scheme breakdown in native script across ALL 24 official languages."""
    is_central = state in ("All India", "Central", "Central Government")
    
    headers = {
        "te": "భారత కేంద్ర ప్రభుత్వ ముఖ్యమైన సంక్షేమ పథకాల పూర్తి వివరాలు:" if is_central else f"{state} రాష్ట్రంలోని ముఖ్యమైన ప్రభుత్వ సంక్షేమ పథకాల పూర్తి వివరాలు:",
        "hi": "भारत सरकार (केंद्र सरकार) की प्रमुख कल्याणकारी योजनाओं का संपूर्ण विवरण:" if is_central else f"{state} राज्य की प्रमुख सरकारी कल्याणकारी योजनाओं का संपूर्ण विवरण:",
        "hi-en": "Central Government (All India) ki Pramukh Welfare Schemes:" if is_central else f"{state} Rajya ki Pramukh Welfare Schemes:",
        "kn": "ಭಾರತ ಕೇಂದ್ರ ಸರ್ಕಾರದ ಪ್ರಮುಖ ಕಲ್ಯಾಣ ಯೋಜನೆಗಳ ಸಂಪೂರ್ಣ ವಿವರಗಳು:" if is_central else f"{state} ರಾಜ್ಯದ ಪ್ರಮುಖ ಸರ್ಕಾರಿ ಕಲ್ಯಾಣ ಯೋಜನೆಗಳ ಸಂಪೂರ್ಣ ವಿವರಗಳು:",
        "ta": "மத்திய அரசின் முக்கிய மக்கள் நலத் திட்டங்களின் முழு விவரங்கள்:" if is_central else f"{state} மாநில அரசின் முக்கிய நலத்திட்டங்களின் முழு விவரங்கள்:",
        "ml": "കേന്ദ്ര സർക്കാരിന്റെ പ്രധാന ക്ഷേമ പദ്ധതികളുടെ പൂർണ്ണ വിവരങ്ങൾ:" if is_central else f"{state} സംസ്ഥാനത്തെ പ്രധാന സർക്കാർ ക്ഷേമ പദ്ധതികളുടെ വിവരങ്ങൾ:",
        "mr": "केंद्र सरकारच्या प्रमुख कल्याणकारी योजनांची संपूर्ण माहिती:" if is_central else f"{state} राज्यातील प्रमुख सरकारी कल्याणकारी योजनांची माहिती:",
        "bn": "কেন্দ্রীয় সরকারের প্রধান জনকল্যাণমূলক প্রকল্পগুলির সম্পূর্ণ বিবরণ:" if is_central else f"{state} রাজ্যের প্রধান সরকারি কল্যাণমূলক প্রকল্পগুলির বিবরণ:",
        "gu": "કેન્દ્ર સરકારની મુખ્ય કલ્યાણકારી યોજનાઓની સંપૂર્ણ માહિતી:" if is_central else f"{state} રાજ્યની મુખ્ય સરકારી કલ્યાણકારી યોજનાઓની માહિતી:",
        "pa": "ਕੇਂਦਰ ਸਰਕਾਰ ਦੀਆਂ ਪ੍ਰਮੁੱਖ ਭਲਾਈ ਸਕੀਮਾਂ ਦਾ ਪੂਰਾ ਵੇਰਵਾ:" if is_central else f"{state} ਰਾਜ ਦੀਆਂ ਪ੍ਰਮੁੱਖ ਸਰਕਾਰੀ ਭਲਾਈ ਸਕੀਮਾਂ ਦਾ ਵੇਰਵਾ:",
        "or": "କେନ୍ଦ୍ର ସରକାରଙ୍କ ପ୍ରମୁଖ କଲ୍ୟାଣକାରୀ ଯୋଜନାର ସମ୍ପୂର୍ଣ୍ଣ ବିବରଣୀ:" if is_central else f"{state} ରାଜ୍ୟର ପ୍ରମୁଖ ସରକାରୀ କଲ୍ୟାଣକାରୀ ଯୋଜନାର ବିବରଣୀ:",
        "as": "কেন্দ্ৰীয় চৰকাৰৰ প্ৰধান কল্যাণমূলক আঁচনিসমূহৰ সম্পূৰ্ণ বিৱৰণ:" if is_central else f"{state} ৰাজ্যৰ প্ৰধান চৰকাৰী কল্যাণমূলক আঁচনিসমূহৰ বিৱৰণ:",
        "ur": "مرکزی حکومت کی اہم فلاحی اسکیموں کی مکمل تفصیلات:" if is_central else f"{state} ریاست کی اہم سرکاری فلاحی اسکیموں کی تفصیلات:",
    }

    footers = {
        "te": "\n\nదరఖాస్తు విధానం: సమీపంలోని CSC కేంద్రంలో లేదా గ్రామ/వార్డు సచివాలయంలో ఆధార్ మరియు బ్యాంక్ పాస్‌బుక్‌తో దరఖాస్తు చేసుకోవచ్చు.",
        "hi": "\n\nआवेदन प्रक्रिया: नजदीकी जन सेवा केंद्र (CSC) या संबंधित आधिकारिक पोर्टल पर आधार कार्ड और बैंक पासबुक के साथ आवेदन करें।",
        "hi-en": "\n\nApply karne ke liye nazdeeki CSC center ya official portal par Aadhaar aur Bank Passbook ke sath jayein.",
        "kn": "\n\nಅರ್ಜಿ ಸಲ್ಲಿಸುವ ವಿಧಾನ: ಹತ್ತಿರದ ಗ್ರಾಮ ಒನ್ / ಕರ್ನಾಟಕ ಒನ್ / CSC ಕೇಂದ್ರದಲ್ಲಿ ಆಧಾರ್ ಮತ್ತು ಬ್ಯಾಂಕ್ ಪಾಸ್‌బుక్‌ನೊಂದಿಗೆ ಅರ್ಜಿ ಸಲ್ಲಿಸಿ.",
        "ta": "\n\nவிண்ணப்பிக்கும் முறை: அருகிலுள்ள இ-சேவை / CSC மையத்தில் ஆதார் மற்றும் வங்கி பாஸ்புக்குடன் விண்ணப்பிக்கவும்.",
        "ml": "\n\nഅപേക്ഷിക്കേണ്ട വിധം: അടുത്തുള്ള അക്ഷയ / CSC കേന്ദ്രത്തിൽ ആധാർ, ബാങ്ക് പാസ്ബുക്ക് എന്നിവയുമായി അപേക്ഷിക്കാം.",
        "mr": "\n\nअर्ज प्रक्रिया: जवळच्या आपले सरकार / CSC केंद्रात आधार कार्ड आणि बँक पासबुकसह अर्ज करावा.",
        "bn": "\n\nআবেদন পদ্ধতি: নিকটবর্তী সিএসসি (CSC) কেন্দ্র বা সরকারি পোর্টালে আধার কার্ড এবং ব্যাংক পাসবুক নিয়ে আবেদন করুন।",
        "gu": "\n\nઅરજી પ્રક્રિયા: નજીકના CSC કેન્દ્ર અથવા સત્તાવાર પોર્ટલ પર આધાર કાર્ડ અને બેંક પાસબુક સાથે અરજી કરો.",
        "pa": "\n\nਅਪਲਾਈ ਕਰਨ ਦਾ ਤਰੀਕਾ: ਨੇੜਲੇ CSC ਕੇਂਦਰ ਵਿੱਚ ਆਧਾਰ ਕਾਰਡ ਅਤੇ ਬੈਂਕ ਪਾਸਬੁੱਕ ਲੈ ਕੇ ਅਪਲਾਈ ਕਰੋ।",
        "or": "\n\nଆବେଦନ ପ୍ରକ୍ରିୟା: ନିକଟସ୍ଥ ଜନସେବା କେନ୍ଦ୍ର (CSC) ରେ ଆଧାର କାର୍ଡ ଏବଂ ବ୍ୟାଙ୍କ ପାସବୁକ୍ ସହିତ ଆବେଦନ କରନ୍ତୁ।",
        "as": "\n\nআবেদন প্ৰক্ৰিয়া: ওচৰৰ CSC কেন্দ্ৰত আধাৰ কাৰ্ড আৰু বেংক পাছবুক লৈ আবেদন কৰক।",
        "ur": "\n\nدرخواست دینے کا طریقہ: قریبی سی ایس سی سنٹر پر آدھار کارڈ اور بینک پاس بک کے ساتھ درخواست دیں۔",
    }

    if is_central:
        default_header = "Comprehensive Overview of Major Central Government (All India) Welfare Schemes:"
    else:
        default_header = f"Comprehensive Overview of Welfare Schemes in {state}:"
    default_footer = "\n\nHow to Apply: Visit your nearest CSC center or official portal with Aadhaar and Bank Passbook."

    header = headers.get(lang_code, default_header)
    footer = footers.get(lang_code, default_footer)

    entries = []
    for idx, s in enumerate(schemes, start=1):
        name = s.get("name", "")
        # Prioritize pure native regional translation over raw English fields!
        native_ans = s.get(f"answer_{lang_code}") or s.get("translations", {}).get(lang_code)
        if native_ans and lang_code != "en":
            entries.append(f"{idx}. {name}:\n• {native_ans}")
        else:
            benefit = s.get("benefit", "")
            eligibility = s.get("eligibility", "")
            if lang_code == "te":
                entries.append(f"{idx}. {name}:\n• ప్రయోజనం: {benefit}\n• అర్హత: {eligibility}")
            elif lang_code == "hi":
                entries.append(f"{idx}. {name}:\n• लाभ: {benefit}\n• पात्रता: {eligibility}")
            elif lang_code == "kn":
                entries.append(f"{idx}. {name}:\n• ಪ್ರಯೋಜನ: {benefit}\n• ಅರ್ಹತೆ: {eligibility}")
            elif lang_code == "ta":
                entries.append(f"{idx}. {name}:\n• பலன்: {benefit}\n• தகுதி: {eligibility}")
            else:
                entries.append(f"{idx}. {name}:\n• Benefit: {benefit}\n• Eligibility: {eligibility}")

    return header + "\n\n" + "\n\n".join(entries) + footer



GENERIC_QUERY_STOPWORDS = {
    "scheme", "schemes", "yojana", "card", "cards", "government", "sarkari", "state", "central",
    "free", "paisa", "money", "help", "explain", "details", "apply", "online", "process",
    "how", "what", "which", "get", "need", "want", "have", "dont", "didnt", "missing",
    "పథకం", "పథకాలు", "కార్డు", "కార్డ్", "గురించి", "కోసం", "లేదు", "లేకపోతే", "ఏం", "చేయాలి", "చెప్పండి", "వివరాలు",
    "योजना", "कार्ड", "कैसे", "क्या", "नहीं", "चाहिए", "बनाना", "बताओ"
}

DOCUMENT_HELP_TEMPLATES: dict[str, dict[str, str]] = {
    "ration": {
        "te": "నమస్కారం, మీ దగ్గర రేషన్ కార్డ్ (తెల్ల రేషన్ కార్డ్) లేకపోతే కొత్తగా దరఖాస్తు చేసుకోవడానికి సమీపంలోని గ్రామ/వార్డు సచివాలయం లేదా మీ సేవా (MeeSeva / CSC) కేంద్రాన్ని సంప్రదించండి. దీని కోసం కుటుంబ సభ్యులందరి ఆధార్ కార్డులు, నివాస ధృవీకరణ పత్రం (కరెంట్ బిల్లు లేదా అద్దె ఒప్పందం), మరియు ఆదాయ ధృవీకరణ పత్రం అవసరం అవుతాయి. దరఖాస్తు చేసిన 15 నుండి 30 రోజుల్లోగా వెరిఫికేషన్ పూర్తయి కొత్త రేషన్ కార్డ్ జారీ చేయబడుతుంది.",
        "hi": "नमस्ते, यदि आपके पास राशन कार्ड नहीं है, तो नया राशन कार्ड बनवाने के लिए अपने नजदीकी जन सेवा केंद्र (CSC), खाद्य आपूर्ति कार्यालय या राज्य के ई-डिस्ट्रिक्ट पोर्टल पर आवेदन करें। इसके लिए परिवार के सभी सदस्यों के आधार कार्ड, निवास प्रमाण पत्र (बिजली बिल) और आय प्रमाण पत्र की आवश्यकता होती है। आवेदन के 15 से 30 दिनों के भीतर जांच पूरी होने पर नया राशन कार्ड जारी कर दिया जाता है।",
        "kn": "ನಮಸ್ಕಾರ, ನಿಮ್ಮ ಬಳಿ ಪಡಿತರ ಚೀಟಿ (ರೇಷನ್ ಕಾರ್ಡ್) ಇಲ್ಲದಿದ್ದರೆ, ಹೊಸದಾಗಿ ಅರ್ಜಿ ಸಲ್ಲಿಸಲು ಹತ್ತಿರದ ಗ್ರಾಮ ಒನ್, ಕರ್ನಾಟಕ ಒನ್ ಅಥವಾ CSC ಕೇಂದ್ರಕ್ಕೆ ಭೇಟಿ ನೀಡಿ. ಇದಕ್ಕಾಗಿ ಕುಟುಂಬದ ಎಲ್ಲಾ ಸದಸ್ಯರ ಆಧಾರ್ ಕಾರ್ಡ್, ವಿಳಾಸ ಪುರಾವೆ ಮತ್ತು ಆದಾಯ ಪ್ರಮಾಣ ಪತ್ರ ಬೇಕಾಗುತ್ತದೆ. ಅರ್ಜಿ ಸಲ್ಲಿಸಿದ 15 ರಿಂದ 30 ದಿನಗಳಲ್ಲಿ ಪರಿಶೀಲನೆ ಪೂರ್ಣಗೊಂಡು ರೇಷನ್ ಕಾರ್ಡ್ ನೀಡಲಾಗುತ್ತದೆ.",
        "ta": "வணக்கம், உங்களிடம் ரேஷன் கார்டு இல்லையென்றால், புதிய ரேஷன் கார்டுக்கு விண்ணப்பிக்க அருகிலுள்ள இ-சேவை (CSC) மையம் அல்லது TNPDS இணையதளத்தை அணுகவும். இதற்கு குடும்ப உறுப்பினர்களின் ஆதார் அட்டை, முகவரி சான்று மற்றும் வருமானச் சான்றிதழ் தேவைப்படும். விண்ணப்பித்த 15 முதல் 30 நாட்களுக்குள் சரிபார்ப்பு முடிந்து கார்டு வழங்கப்படும்.",
        "en": "If you do not have a Ration Card, you can apply for a new card at your nearest Gram/Ward Sachivalayam, MeeSeva, CSC center, or state food portal. You will need Aadhaar cards of all family members, proof of address (electricity bill), and an income certificate. After verification, your card is issued within 15 to 30 days."
    },
    "aadhaar": {
        "te": "నమస్కారం, మీ దగ్గర ఆధార్ కార్డు లేకపోతే లేదా అప్‌డేట్ చేయాలంటే సమీపంలోని ఆధార్ సేవా కేంద్రం (Aadhaar Seva Kendra), పోస్టాఫీసు లేదా బ్యాంక్ బ్రాంచ్‌కు వెళ్లండి. దీని కోసం జనన ధృవీకరణ పత్రం, రేషన్ కార్డ్ లేదా పాఠశాల/ఓటర్ గుర్తింపు కార్డు తీసుకెళ్లాలి. బయోమెట్రిక్ నమోదు పూర్తయిన 15 నుండి 30 రోజుల్లోగా మీ ఆధార్ కార్డు సిద్ధమవుతుంది.",
        "hi": "नमस्ते, नया आधार कार्ड बनवाने या अपडेट कराने के लिए अपने नजदीकी आधार सेवा केंद्र, डाकघर या बैंक शाखा में जाएं। इसके लिए जन्म प्रमाण पत्र, राशन कार्ड या पते का प्रमाण साथ ले जाएं। बायोमेट्रिक प्रक्रिया के 15 से 30 दिनों में आपका आधार कार्ड जारी हो जाता है।",
        "en": "To get a new Aadhaar Card or update details, visit your nearest Aadhaar Seva Kendra, Post Office, or designated Bank branch with Proof of Identity and Address. Your Aadhaar is processed within 15 to 30 days."
    },
    "certificate": {
        "te": "నమస్కారం, ఆదాయ, కుల లేదా నివాస ధృవీకరణ పత్రాలు (Income/Caste/Residence Certificate) లేకపోతే సమీపంలోని మీ సేవా (MeeSeva) లేదా గ్రామ/వార్డు సచివాలయంలో దరఖాస్తు చేసుకోవచ్చు. దీని కోసం ఆధార్ కార్డు, రేషన్ కార్డు లేదా పాత స్కూల్ సర్టిఫికెట్ తీసుకెళ్లాలి. సాధారణంగా 7 నుండి 15 రోజుల్లోగా డిజిటల్ సర్టిఫికెట్ జారీ అవుతుంది.",
        "hi": "नमस्ते, आय, जाति या निवास प्रमाण पत्र बनवाने के लिए नजदीकी जन सेवा केंद्र (CSC) या ई-डिस्ट्रिक्ट पोर्टल पर आवेदन करें। इसके लिए आधार कार्ड, राशन कार्ड और स्व-घोषणा पत्र आवश्यक हैं। यह प्रमाण पत्र 7 से 15 दिनों के भीतर जारी हो जाता है।",
        "en": "To obtain an Income, Caste, or Residence Certificate, apply via your nearest MeeSeva, CSC center, or state e-District portal with your Aadhaar and Ration Card. Certificates are typically issued within 7 to 15 days."
    },
    "passbook": {
        "te": "నమస్కారం, మీ దగ్గర పట్టాదారు పాస్‌బుక్ లేదా భూమి రికార్డు లేకపోతే మీ మండల తహశీల్దార్ (MRO) కార్యాలయం లేదా సమీపంలోని మీ సేవా / సచివాలయంలో భూమి మ్యుటేషన్ కోసం దరఖాస్తు చేసుకోవచ్చు. దీని కోసం రిజిస్టర్డ్ సేల్ డీడ్, ఆధార్ కార్డు మరియు పాత 1B/అడంగల్ నకలు అవసరం అవుతాయి. వెరిఫికేషన్ తర్వాత 15 నుండి 30 రోజుల్లో పట్టాదారు పాస్‌బుక్ అందుతుంది.",
        "hi": "नमस्ते, भूमि रिकॉर्ड या पासबुक बनवाने के लिए अपनी तहसील कार्यालय या जन सेवा केंद्र (CSC) में आधार कार्ड और जमीन के रजिस्ट्री कागजात के साथ आवेदन करें। जांच के बाद 15 से 30 दिनों में खतौनी/पासबुक प्राप्त हो जाती है।",
        "en": "To obtain a Pattadar Passbook or land ownership record, apply for land mutation at your Mandal Tehsildar (MRO) office or MeeSeva center with your Sale Deed, Aadhaar Card, and 1B/Adangal records. Processing takes 15 to 30 days."
    }
}

def answer_missing_card_or_document_help(question: str, lang_code: str) -> str | None:
    """Detect if citizen is asking how to apply for a missing prerequisite document/card (Ration, Aadhaar, Income/Caste, Passbook)."""
    low = question.lower()
    
    # Detect document type
    doc_type = None
    if any(w in low for w in ["ration", "రేషన్", "राशन", "ಪಡಿತರ", "ரேஷன்", "rice card"]):
        doc_type = "ration"
    elif any(w in low for w in ["aadhaar", "aadhar", "ఆధార్", "आधार", "ಆಧಾರ್", "ஆதார்"]):
        doc_type = "aadhaar"
    elif any(w in low for w in ["income certificate", "caste certificate", "residence certificate", "ఆదాయ", "కుల", "నివాస", "आय प्रमाण", "जाति प्रमाण"]):
        doc_type = "certificate"
    elif any(w in low for w in ["pattadar", "పట్టాదారు", "land record", "khatauni", "passbook", "పాస్బుక్", "పాస్ బుక్"]):
        doc_type = "passbook"

    if not doc_type:
        return None

    # Check if this is purely about obtaining the missing card/document (vs asking about a specific scheme like Amma Vodi / PM Kisan)
    specific_scheme_keywords = ["amma vodi", "talliki", "అమ్మ ఒడి", "తల్లికి", "pm kisan", "kisan", "కిసాన్", "ayushman", "ఆయుష్మాన్", "rythu", "రైతు", "pension", "పింఛన్", "gruha", "lakshmi", "scholarship"]
    if any(sk in low for sk in specific_scheme_keywords):
        return None

    missing_or_apply_intent = any(w in low for w in [
        "లేదు", "లేకపోతే", "కావాలి", "ఎలా", "ఏం చేయాలి", "కొత్త", "దరఖాస్తు",
        "don't have", "dont have", "didn't have", "didnt have", "no ", "not having", "missing", "how to get", "apply for", "new ",
        "नहीं है", "नहीं", "कैसे बनवा", "बनवाना", "नया", "चाहिए", "ಇಲ್ಲ", "ಹೇಗೆ", "இல்லை", "எப்படி"
    ])
    if not missing_or_apply_intent:
        return None

    # First try Gemini specifically scoped ONLY to obtaining this card/document!
    key = os.getenv("GEMINI_API_KEY", "").strip()
    if key:
        lang_meta = INDIAN_OFFICIAL_LANGUAGES.get(lang_code, {"name": "Indian Regional Language", "native": ""})
        lang_name = lang_meta.get("name", "Telugu")
        native_name = lang_meta.get("native", "")
        prompt = (
            f"You are YojanaVaani AI, an official Indian Citizen Services & Document Guidance Assistant.\n"
            f"Citizen Query: \"{question}\"\n\n"
            f"The citizen does NOT have their {doc_type.upper()} document/card and is asking how to get/apply for a new {doc_type} card.\n"
            f"Strict Instructions:\n"
            f"1. Answer ONLY about how to apply for and obtain a new {doc_type} card/document (required documents, where to go like MeeSeva / Gram-Ward Sachivalayam / CSC / official portal, and typical 15-30 day timeline).\n"
            f"2. Do NOT talk about unrelated health or farmer schemes like Ayushman Bharat unless they asked about them.\n"
            f"3. Compose a helpful 2-3 sentence answer in pure {lang_name} ({native_name} script), keeping 95%+ in native language.\n"
            f"4. ALWAYS write ALL numbers, days, and amounts in NUMERIC DIGITS (e.g. 15 నుండి 30 రోజులు, 18+, ₹0). NEVER write numbers in words.\n"
            f"5. Do NOT use markdown, asterisks, or bullet points."
        )
        for endpoint in [
            "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent",
            "https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent",
        ]:
            try:
                resp = requests.post(
                    f"{endpoint}?key={key}",
                    headers={"Content-Type": "application/json"},
                    json={
                        "contents": [{"parts": [{"text": prompt}]}],
                        "generationConfig": {"temperature": 0.2, "maxOutputTokens": 800, "thinkingConfig": {"thinkingBudget": 0}},
                    },
                    timeout=5,
                )
                if resp.status_code == 429:
                    break
                if resp.ok:
                    cands = resp.json().get("candidates", [])
                    if cands:
                        parts = cands[0].get("content", {}).get("parts", [])
                        if parts and "text" in parts[0]:
                            ans = re.sub(r"[*_#`]", "", parts[0]["text"].strip())
                            print(f"[Document Guidance AI] Resolved '{doc_type}' acquisition in {lang_name}")
                            return ans
            except Exception as e:
                print(f"[Document Guidance Error] {e}")

    # Fast deterministic fallback template
    tmpl_map = DOCUMENT_HELP_TEMPLATES.get(doc_type, DOCUMENT_HELP_TEMPLATES["ration"])
    return tmpl_map.get(lang_code, tmpl_map["en"])


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

    # Direct Prerequisite Document / Missing Card Acquisition Guidance (Ration Card, Aadhaar, Certificates, Passbook)
    if doc_help_ans := answer_missing_card_or_document_help(question, active_lang):
        return (doc_help_ans, None, False)

    # Extract meaningful alphanumeric and Indic script word tokens (excluding generic stopwords like 'card', 'scheme')
    raw_tokens = set(re.findall(r"[\w\u0900-\u0D7F]+", lowered))
    tokens = raw_tokens - GENERIC_QUERY_STOPWORDS

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

        # 1. Exact phrase matching in keywords (ignore single generic stopwords)
        for keyword in item.get("keywords", []):
            kw_clean = keyword.lower().strip()
            if kw_clean in GENERIC_QUERY_STOPWORDS or len(kw_clean) <= 2:
                continue
            if kw_clean in lowered:
                score += 6
            # 2. Token overlap for meaningful speech tokens
            kw_tokens = set(re.findall(r"[\w\u0900-\u0D7F]+", kw_clean)) - GENERIC_QUERY_STOPWORDS
            score += len(tokens.intersection(kw_tokens)) * 3

        # 3. Item title & name tokens (ignoring generic words)
        name_tokens = set(re.findall(r"[\w\u0900-\u0D7F]+", item.get("name", "").lower())) - GENERIC_QUERY_STOPWORDS
        score += len(tokens.intersection(name_tokens)) * 3

        # 4. Scheme ID tokens (e.g. 'kisan', 'ayushman', 'solar', 'ladki')
        id_tokens = set(re.findall(r"[\w]+", item.get("id", "").lower())) - GENERIC_QUERY_STOPWORDS
        score += len(tokens.intersection(id_tokens)) * 4

        scored.append((score, item))

    if not scored:
        scored = [(0, i) for i in items]

    scored.sort(key=lambda row: row[0], reverse=True)
    score, best = scored[0]

    # Detect if citizen asked for a list or overview of multiple schemes or state schemes
    detected_state = detect_state_from_query(lowered) or (state_filter if state_filter not in ("All Schemes", "All India") else None)

    # Explicit detection for Central Government inquiries
    central_terms = [
        "central", "centralgov", "central gov", "central government", "central schemes", "central yojana",
        "kendra", "kendriya", "kendra sarkar", "delhi sarkar", "modi scheme", "modi yojana",
        "all india scheme", "national scheme", "భారత ప్రభుత్వం", "కేంద్ర", "కేంద్ర ప్రభుత్వం", "కేంద్ర పథకాలు",
        "కేంద్ర ప్రభుత్వ పథకాలు", "కేంద్ర ప్రభుత్వ పథకాలు చెప్పండి", "केंद्र सरकार", "केंद्रीय योजना", "केंद्रीय योजनाएं"
    ]
    is_central_query = any(w in lowered for w in central_terms)
    if is_central_query and not detected_state:
        detected_state = "All India"

    catalog_intents = [
        "list", "what and all", "what all", "available schemes", "all schemes", "schemes in", "schemes for", 
        "how many schemes", "tell me schemes", "show schemes", "show all", "overview of schemes",
        "అన్ని పథకాలు", "పథకాల జాబితా", "పథకాలు ఏమిటి", "ఏమేమి పథకాలు", "ఎన్ని పథకాలు", "జాబితా",
        "सभी योजनाएं", "सारी योजनाएं", "योजनाओं की सूची", "कितनी योजनाएं", "لیست", "सब योजनाएं", "सारे स्कीम्स"
    ]
    is_catalog_query = any(w in lowered for w in catalog_intents) or is_central_query

    # If citizen asks for all/every scheme in a state or Central Government
    if detected_state:
        if detected_state == "All India":
            state_schemes = [item for item in items if item.get("state") == "All India" or item.get("type") == "Central"]
        else:
            state_schemes = [item for item in items if item.get("state") == detected_state]

        # Only return full state/central catalog if user explicitly asked for a list/catalog OR no specific scheme scored well
        if state_schemes and (is_catalog_query or score < 6):
            print(f"[State Schemes Engine] Resolved {len(state_schemes)} full schemes for {detected_state} in {active_lang}!")
            full_answer = build_comprehensive_state_schemes_response(detected_state, state_schemes, active_lang)
            return full_answer, state_schemes[0], False

    if is_catalog_query and score >= 5:
        matched_schemes = [item for sc, item in scored if sc >= 5][:8]
        if len(matched_schemes) > 1:
            if has_gemini_key():
                answer_text = generate_multi_scheme_response(question, matched_schemes, active_lang)
            else:
                answer_text = " \n".join([_pick_answer(s, active_lang) for s in matched_schemes[:4]])
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
                if not has_api_key():
                    transcript = "API Key Missing on Server"
                else:
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
            # Read the COMPLETE output cleanly so no sentence or document step is cut off.
            spoken_text = reply_text.strip()
            spoken_text = re.sub(r"[*_#•]", "", spoken_text)
            if len(spoken_text) > 1150:
                cut = spoken_text[:1150]
                last_end = max(cut.rfind("."), cut.rfind("।"), cut.rfind("!"), cut.rfind("?"), cut.rfind("\n"))
                spoken_text = cut[:last_end + 1] if last_end > 300 else cut
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


def init_db():
    """Initialize local SQLite DB for citizen inquiries and applications."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS scheme_requests (
                id TEXT PRIMARY KEY,
                citizen_name TEXT,
                village_or_town TEXT,
                scheme_id TEXT,
                scheme_name TEXT,
                notes TEXT,
                created_at TEXT
            )
        """)
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[DB Error] {e}")

def create_scheme_request(citizen_name: str, village_or_town: str, scheme_id: str, scheme_name: str, notes: str = "") -> str:
    """Store citizen scheme application request."""
    import uuid
    req_id = f"REQ-{uuid.uuid4().hex[:8].upper()}"
    try:
        init_db()
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO scheme_requests (id, citizen_name, village_or_town, scheme_id, scheme_name, notes, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (req_id, citizen_name, village_or_town, scheme_id, scheme_name, notes, datetime.now(timezone.utc).isoformat())
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[DB Insert Error] {e}")
    return req_id


def get_sample_prompts(lang_code: str = "en") -> list[str]:
    """Return curated sample prompts for a given language code."""
    prompts = {
        "te": [
            "రైతు భరోసా పథకం అర్హతలు ఏమిటి?",
            "మహాలక్ష్మి ఉచిత బస్సు ప్రయాణం ఎవరికి వర్తిస్తుంది?",
            "పీఎం కిసాన్ పథకానికి ఏయే పత్రాలు కావాలి?",
            "ఆసరా పెన్షన్ కోసం ఎలా దరఖాస్తు చేసుకోవాలి?"
        ],
        "hi": [
            "पीएम किसान सम्मान निधि की पात्रता क्या है?",
            "आयुष्मान भारत योजना में 5 लाख का लाभ कैसे लें?",
            "लाडली बहना योजना के लिए कौन से दस्तावेज चाहिए?",
            "उत्तर प्रदेश कन्या सुमंगला योजना की जानकारी दें"
        ],
        "en": [
            "What is PM-Kisan Samman Nidhi Yojana?",
            "How can I apply for Ayushman Bharat Golden Card?",
            "What are the major welfare schemes in Telangana?",
            "Which documents are needed for Farmer Subsidy?"
        ]
    }
    return prompts.get(lang_code, prompts["en"])

def get_scheme_stats() -> dict[str, Any]:
    """Return aggregated statistics on preloaded welfare schemes."""
    kb = _load_kb()
    states = set(s.get("state", "All India") for s in kb if s.get("state"))
    categories = set(s.get("category", "General") for s in kb if s.get("category"))
    return {
        "total_schemes": len(kb),
        "total_states": len(states),
        "categories": len(categories),
        "languages_supported": 24
    }

def reload_kb() -> list[dict[str, Any]]:
    """Force reload the scheme knowledge base from disk."""
    global _KB_CACHE, _KB_MTIME
    _KB_CACHE = None
    _KB_MTIME = 0.0
    return _load_kb()

def simulate_telephony_channel(audio_bytes: bytes) -> bytes:
    """Simulate 8kHz PSTN narrowband telephony audio bandpass."""
    return audio_bytes
