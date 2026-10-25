import imaplib
import smtplib
import email
from email.header import decode_header
from email.mime.text import MIMEText
import re
import html
import asyncio
from googletrans import Translator

# Email configuration
EMAIL_ID = "arivuarmy26@gmail.com"
EMAIL_PASS = "sxqv znib iveb kgmm"
IMAP_SERVER = "imap.gmail.com"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

LANGUAGE_MAP = {
    "english": "en",
    "tamil": "ta",
    "hindi": "hi",
    "telugu": "te"
}

SPEECH_LOCALES = {
    "en": "en-US",
    "ta": "ta-IN",
    "hi": "hi-IN",
    "te": "te-IN"
}

STATUS_PHRASES = {
    "en": {
        "no_unread": "No unread emails found.",
        "mail_prompt": "Please provide receiver email, subject, and message.",
        "help_prompt": "Say read mail or send mail.",
        "mail_sent": "Email sent successfully.",
        "mail_failed": "Failed to send email.",
        "read_error": "Error reading email."
    },
    "ta": {
        "no_unread": "புதிய படிக்காத மின்னஞ்சல்கள் எதுவும் இல்லை.",
        "mail_prompt": "பெறுநர் முகவரி, தலைப்பு மற்றும் செய்தியைக் கூறவும்.",
        "help_prompt": "மின்னஞ்சல் படிக்க 'read mail' அல்லது அனுப்ப 'send mail' என்று கூறவும்.",
        "mail_sent": "மின்னஞ்சல் வெற்றிகரமாக அனுப்பப்பட்டது.",
        "mail_failed": "மின்னஞ்சல் அனுப்புவதில் தோல்வி ஏற்பட்டது.",
        "read_error": "மின்னஞ்சல் படிப்பதில் பிழை ஏற்பட்டது."
    },
    "hi": {
        "no_unread": "कोई नया अपठित ईमेल नहीं मिला।",
        "mail_prompt": "कृपया प्राप्तकर्ता, विषय और संदेश प्रदान करें।",
        "help_prompt": "ईमेल पढ़ने के लिए 'read mail' या भेजने के लिए 'send mail' कहें।",
        "mail_sent": "ईमेल सफलतापूर्वक भेजा गया।",
        "mail_failed": "ईमेल भेजने में विफल।",
        "read_error": "ईमेल पढ़ने में त्रुटि हुई।"
    },
    "te": {
        "no_unread": "చదవని ఇమెయిల్‌లు ఏవీ కనుగొనబడలేదు.",
        "mail_prompt": "దయచేసి గ్రహీత చిరునామా, విషయం మరియు సందేశాన్ని అందించండి.",
        "help_prompt": "ఇమెయిల్ చదవడానికి 'read mail' లేదా పంపడానికి 'send mail' అని చెప్పండి.",
        "mail_sent": "ఇమెయిల్ విజయవంతంగా పంపబడింది.",
        "mail_failed": "ఇమెయిల్ పంపడం విఫలమైంది.",
        "read_error": "ఇమెయిల్ చదవడంలో లోపం ఏర్పడింది."
    }
}

translator = Translator()

def get_phrase(key: str, lang_code: str) -> str:
    phrases = STATUS_PHRASES.get(lang_code, STATUS_PHRASES["en"])
    return phrases.get(key, STATUS_PHRASES["en"].get(key, ""))

def decode_mime_words(header_val: str) -> str:
    if not header_val:
        return ""
    decoded_fragments = []
    for fragment, encoding in decode_header(header_val):
        if isinstance(fragment, bytes):
            try:
                decoded_fragments.append(fragment.decode(encoding or "utf-8", errors="ignore"))
            except Exception:
                decoded_fragments.append(fragment.decode("latin1", errors="ignore"))
        else:
            decoded_fragments.append(str(fragment))
    return " ".join(decoded_fragments).strip()

def clean_text(text: str) -> str:
    if not text:
        return ""
    # Strip HTML tags if present
    text = re.sub(r'<[^>]+>', ' ', text)
    # Unescape HTML entities (&nbsp;, &amp;, etc.)
    text = html.unescape(text)
    # Strip URLs (as detailed in paper section IV-C)
    text = re.sub(r'https?://\S+|www\.\S+', '', text)
    # Strip parenthetical remarks and tracking fragments
    text = re.sub(r'\(.*?\)', '', text)
    # Normalize excess spaces and line breaks
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def translate_text(text: str, target_lang: str) -> str:
    if not text:
        return ""
    target_code = LANGUAGE_MAP.get(target_lang.lower(), target_lang.lower())
    if target_code == "en":
        return text
    try:
        coro = translator.translate(text, dest=target_code)
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                result = pool.submit(asyncio.run, coro).result()
        else:
            result = loop.run_until_complete(coro)
            
        return result.text if hasattr(result, "text") else str(result)
    except Exception as e:
        print(f"Translation fallback: {e}")
        return text

def extract_body(msg) -> str:
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            cdisp = str(part.get("Content-Disposition", ""))
            if ctype == "text/plain" and "attachment" not in cdisp:
                payload = part.get_payload(decode=True)
                if payload:
                    charset = part.get_content_charset() or "utf-8"
                    body = payload.decode(charset, errors="ignore")
                    break
        if not body:
            # Fallback to HTML if plain text missing
            for part in msg.walk():
                if part.get_content_type() == "text/html":
                    payload = part.get_payload(decode=True)
                    if payload:
                        charset = part.get_content_charset() or "utf-8"
                        body = payload.decode(charset, errors="ignore")
                        break
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            charset = msg.get_content_charset() or "utf-8"
            body = payload.decode(charset, errors="ignore")
    return clean_text(body)

def read_latest_email(language: str = "english") -> dict:
    lang_code = LANGUAGE_MAP.get(language.lower(), "en")
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(EMAIL_ID, EMAIL_PASS)
        mail.select("inbox")

        status, messages = mail.search(None, 'UNSEEN')
        email_ids = messages[0].split()

        if not email_ids:
            mail.logout()
            msg_text = get_phrase("no_unread", lang_code)
            return {
                "success": True,
                "has_unread": False,
                "text": msg_text,
                "sender": "",
                "subject": "",
                "body": "",
                "lang_code": lang_code,
                "locale": SPEECH_LOCALES.get(lang_code, "en-US")
            }

        latest_id = email_ids[-1]
        status, msg_data = mail.fetch(latest_id, "(RFC822)")
        raw_email = msg_data[0][1]
        msg = email.message_from_bytes(raw_email)

        sender = decode_mime_words(msg.get("From", "Unknown Sender"))
        subject = decode_mime_words(msg.get("Subject", "No Subject"))
        body = extract_body(msg)

        # Truncate extremely long newsletters to protect TTS clarity (max ~350 chars)
        if len(body) > 350:
            body = body[:350] + "..."

        spoken_template = f"Email from {sender}. Subject: {subject}. Message: {body}"
        translated_spoken = translate_text(spoken_template, lang_code)

        mail.logout()
        return {
            "success": True,
            "has_unread": True,
            "text": translated_spoken,
            "sender": sender,
            "subject": subject,
            "body": body,
            "lang_code": lang_code,
            "locale": SPEECH_LOCALES.get(lang_code, "en-US")
        }
    except Exception as e:
        print(f"Error reading email: {e}")
        return {
            "success": False,
            "text": get_phrase("read_error", lang_code),
            "error": str(e),
            "lang_code": lang_code,
            "locale": SPEECH_LOCALES.get(lang_code, "en-US")
        }

def send_email_message(receiver: str, subject: str, message: str, language: str = "english") -> dict:
    lang_code = LANGUAGE_MAP.get(language.lower(), "en")
    if not receiver or not message:
        return {
            "success": False,
            "text": "Receiver email and message body are required.",
            "lang_code": lang_code,
            "locale": SPEECH_LOCALES.get(lang_code, "en-US")
        }

    try:
        msg = MIMEText(message, "plain", "utf-8")
        msg["From"] = EMAIL_ID
        msg["To"] = receiver.strip()
        msg["Subject"] = subject.strip() if subject else "Voice Assistant Message"

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_ID, EMAIL_PASS)
        server.send_message(msg)
        server.quit()

        return {
            "success": True,
            "text": get_phrase("mail_sent", lang_code),
            "lang_code": lang_code,
            "locale": SPEECH_LOCALES.get(lang_code, "en-US")
        }
    except Exception as e:
        print(f"Error sending email: {e}")
        return {
            "success": False,
            "text": get_phrase("mail_failed", lang_code),
            "error": str(e),
            "lang_code": lang_code,
            "locale": SPEECH_LOCALES.get(lang_code, "en-US")
        }

def process_command(raw_command: str, language: str = "english") -> dict:
    cmd = (raw_command or "").strip().lower()
    lang_code = LANGUAGE_MAP.get(language.lower(), "en")

    if "read" in cmd or "check" in cmd or "படி" in cmd or "படியுங்கள்" in cmd or "पढ़ो" in cmd or "చదువు" in cmd:
        email_res = read_latest_email(language)
        return {
            "action": "read",
            "response": email_res["text"],
            "details": email_res,
            "lang_code": lang_code,
            "locale": SPEECH_LOCALES.get(lang_code, "en-US")
        }
    elif "send" in cmd or "compose" in cmd or "write" in cmd or "அனுப்பு" in cmd or "भेजो" in cmd or "పంపు" in cmd:
        prompt_text = get_phrase("mail_prompt", lang_code)
        return {
            "action": "send",
            "response": prompt_text,
            "lang_code": lang_code,
            "locale": SPEECH_LOCALES.get(lang_code, "en-US")
        }
    else:
        help_text = get_phrase("help_prompt", lang_code)
        return {
            "action": "none",
            "response": help_text,
            "lang_code": lang_code,
            "locale": SPEECH_LOCALES.get(lang_code, "en-US")
        }
