import re

def scrub_payload(text):
    """Protocol D: Sanitizes PII/Secrets before logging."""
    if not text: return ""
    text = re.sub(r'[\w\.-]+@[\w\.-]+\.\w+', '[REDACTED_EMAIL]', text)
    text = re.sub(r'(?i)(api_key|token|secret)\s*[:=]\s*[\w-]+', r'\1=[REDACTED_SECRET]', text)
    return text
