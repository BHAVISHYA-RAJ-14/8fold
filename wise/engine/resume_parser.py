"""
engine/resume_parser.py
Extracts structured data from a resume (PDF bytes or raw text).
Uses pdfminer if available, else treats input as plain text.
Pulls: name, email, phone, education, experience, skills, github username.
"""
import re
from typing import Optional

try:
    from pdfminer.high_level import extract_text as pdf_extract
    from io import BytesIO
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

from engine.skills import extract as extract_skills


def parse_resume(file_bytes: Optional[bytes] = None,
                 raw_text:   Optional[str]   = None) -> dict:
    """
    Pass either file_bytes (PDF) or raw_text (plain string).
    Returns a structured dict.
    """
    if file_bytes and PDF_AVAILABLE:
        try:
            text = pdf_extract(BytesIO(file_bytes))
        except Exception:
            text = file_bytes.decode("utf-8", errors="ignore")
    elif file_bytes:
        text = file_bytes.decode("utf-8", errors="ignore")
    else:
        text = raw_text or ""

    text = text.strip()

    return {
        "raw_text":   text,
        "name":       _name(text),
        "email":      _email(text),
        "phone":      _phone(text),
        "github":     _github(text),
        "linkedin":   _linkedin(text),
        "skills":     extract_skills(text),
        "education":  _education(text),
        "experience": _experience(text),
        "summary":    text[:300].replace("\n", " ").strip(),
    }


# ── Regex helpers ─────────────────────────────────────────────────────────
def _email(t: str) -> str:
    m = re.search(r'[\w.+-]+@[\w-]+\.[a-zA-Z]{2,}', t)
    return m.group(0) if m else ""

def _phone(t: str) -> str:
    m = re.search(r'(\+?\d[\d\s\-().]{8,14}\d)', t)
    return m.group(0).strip() if m else ""

def _github(t: str) -> str:
    m = re.search(r'github\.com/([A-Za-z0-9_.-]+)', t, re.I)
    return m.group(1) if m else ""

def _linkedin(t: str) -> str:
    m = re.search(r'linkedin\.com/in/([A-Za-z0-9_-]+)', t, re.I)
    return m.group(1) if m else ""

def _name(t: str) -> str:
    # First non-empty line is usually the name
    for line in t.splitlines():
        line = line.strip()
        if line and len(line.split()) <= 5 and not re.search(r'[@\d]', line):
            return line
    return ""

def _education(t: str) -> list:
    edu = []
    patterns = [
        r'(B\.?Tech|B\.?E\.?|M\.?Tech|M\.?Sc|B\.?Sc|MBA|Ph\.?D|BCA|MCA)[^\n]*',
        r'(Bachelor|Master|Doctor)[^\n]*',
    ]
    for pat in patterns:
        for m in re.finditer(pat, t, re.I):
            line = m.group(0).strip()
            if line not in edu:
                edu.append(line)
    return edu[:4]

def _experience(t: str) -> str:
    m = re.search(r'(\d+\.?\d*)\s*\+?\s*years?\s*(of\s+)?(experience|exp)', t, re.I)
    if m:
        return m.group(0).strip()
    return ""
