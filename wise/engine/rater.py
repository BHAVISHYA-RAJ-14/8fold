"""
engine/rater.py
Multi-criteria rating of a candidate profile.

Criteria (each 0-100):
  1. Technical Skills Match   — how many required skills covered
  2. GitHub Signal Strength   — credibility + activity + language depth
  3. Resume Quality           — completeness, education, experience
  4. Communication Signals    — documentation, project descriptions
  5. Overall Fit              — weighted blend of above

Each criterion has a score, a label, and a plain-English reason.
"""
from __future__ import annotations
from typing import List, Optional
from engine.skills import extract, parse_jd, get_weight


def rate(
    candidate_skills:  List[str],
    jd_text:           str,
    github_data:       Optional[dict] = None,
    resume_data:       Optional[dict] = None,
    profile:           Optional[dict] = None,
) -> dict:
    """
    Returns a multi-criteria rating dict.
    All sub-scores 0-100. Overall is weighted blend.
    """
    jd = parse_jd(jd_text)

    tech   = _technical(candidate_skills, jd)
    gh     = _github_signal(github_data)
    res    = _resume_quality(resume_data, profile)
    comm   = _communication(github_data, resume_data)

    overall = round(
        tech["score"]  * 0.40 +
        gh["score"]    * 0.25 +
        res["score"]   * 0.20 +
        comm["score"]  * 0.15,
        1
    )

    return {
        "overall":    overall,
        "grade":      _grade(overall),
        "label":      _label(overall),
        "criteria": {
            "technical_match":    tech,
            "github_signal":      gh,
            "resume_quality":     res,
            "communication":      comm,
        },
        "matched_skills":  tech["matched"],
        "missing_skills":  tech["missing"],
        "recommendation":  _recommendation(overall),
        "summary":         _summary(overall, tech, gh, res, comm),
    }


# ── Criterion scorers ─────────────────────────────────────────────────────

def _technical(skills: List[str], jd: dict) -> dict:
    required  = jd["must_have"]
    preferred = jd["nice_to_have"]
    sl        = [s.lower() for s in skills]

    matched = [r for r in required  if any(r.lower() in c or c in r.lower() for c in sl)]
    missing = [r for r in required  if r not in matched]
    pref_m  = [p for p in preferred if any(p.lower() in c or c in p.lower() for c in sl)]

    n_req   = max(len(required), 1)
    n_pref  = max(len(preferred), 1)

    w_match = sum(get_weight(s) for s in matched)
    w_total = sum(get_weight(s) for s in required)
    blended = 0.65 * (len(matched)/n_req) + 0.35 * (w_match/max(w_total,1))

    score = round(min(blended * 90 + (len(pref_m)/n_pref) * 10, 100), 1)

    return {
        "score":   score,
        "label":   _label(score),
        "matched": matched,
        "missing": missing,
        "preferred_matched": pref_m,
        "reason":  (f"{len(matched)}/{len(required)} required skills matched"
                    + (f", {len(pref_m)} preferred skills also present." if pref_m else ".")),
    }


def _github_signal(gh: Optional[dict]) -> dict:
    if not gh:
        return {"score": 0, "label": "No Data",
                "reason": "No GitHub profile provided. Score based on resume only.",
                "credibility": 0, "activity": "unknown", "top_langs": []}

    cred   = gh.get("credibility", {})
    cs     = cred.get("score", 0)
    cm     = gh.get("commit_signals", {})
    cx     = gh.get("complexity", {})
    langs  = gh.get("primary_languages", [])

    act_bonus = {"very active":20,"active":15,"moderate":8,"inactive":0}.get(
                 cm.get("activity","inactive"), 0)
    star_bonus = min(cx.get("stars", 0) / 200 * 15, 15)
    doc_bonus  = 5 if cx.get("documented", 0) > 3 else 0

    score = round(min(cs * 0.60 + act_bonus + star_bonus + doc_bonus, 100), 1)

    return {
        "score":       score,
        "label":       _label(score),
        "credibility": cs,
        "activity":    cm.get("activity", "unknown"),
        "top_langs":   langs[:3],
        "stars":       cx.get("stars", 0),
        "reason":      (f"GitHub credibility {cs}/100, activity: {cm.get('activity','—')}, "
                        f"{cx.get('stars',0)} stars, primary: {', '.join(langs[:3]) or '—'}."),
    }


def _resume_quality(resume: Optional[dict], profile: Optional[dict]) -> dict:
    score = 0
    reasons = []

    if not resume and not profile:
        return {"score": 30, "label": _label(30),
                "reason": "No resume uploaded. Basic profile score applied."}

    # Profile completeness
    p = profile or {}
    if p.get("name"):       score += 10; reasons.append("Name provided")
    if p.get("email"):      score += 5
    if p.get("cgpa"):       score += 10; reasons.append(f"CGPA {p['cgpa']}")
    if p.get("branch"):     score += 5;  reasons.append(f"Branch: {p['branch']}")
    if p.get("experience_years"): score += 10
    if p.get("education"):  score += 10; reasons.append("Education listed")

    # Resume content
    r = resume or {}
    if r.get("skills") and len(r["skills"]) > 3:
        score += 15; reasons.append(f"{len(r['skills'])} skills extracted")
    if r.get("education"):  score += 10
    if r.get("github"):     score += 10; reasons.append("GitHub link in resume")
    if r.get("email"):      score += 5
    if r.get("experience"): score += 10

    score = min(score, 100)
    return {
        "score":  round(score, 1),
        "label":  _label(score),
        "reason": ", ".join(reasons) + "." if reasons else "Partial profile provided.",
    }


def _communication(gh: Optional[dict], resume: Optional[dict]) -> dict:
    score = 40   # baseline
    reasons = []

    if gh:
        cx = gh.get("complexity", {})
        doc = cx.get("documented", 0)
        top = cx.get("top_repos", [])
        if doc > 10: score += 25; reasons.append("Well-documented repositories")
        elif doc > 4: score += 15; reasons.append("Some documented repositories")
        desc_count = sum(1 for r in top if r.get("desc","").strip())
        if desc_count > 2: score += 15; reasons.append("Projects have clear descriptions")

    if resume:
        if resume.get("linkedin"): score += 10; reasons.append("LinkedIn profile")
        if len(resume.get("raw_text","")) > 500: score += 10

    score = min(score, 100)
    return {
        "score":  round(score, 1),
        "label":  _label(score),
        "reason": ", ".join(reasons) + "." if reasons else "Based on available profile data.",
    }


# ── Utilities ─────────────────────────────────────────────────────────────

def _grade(s: float) -> str:
    if s >= 85: return "A+"
    if s >= 75: return "A"
    if s >= 65: return "B+"
    if s >= 55: return "B"
    if s >= 45: return "C+"
    if s >= 35: return "C"
    return "D"

def _label(s: float) -> str:
    if s >= 80: return "Excellent"
    if s >= 65: return "Strong"
    if s >= 50: return "Good"
    if s >= 35: return "Average"
    return "Needs Work"

def _recommendation(s: float) -> str:
    if s >= 80: return "Strong hire — proceed to technical interview"
    if s >= 65: return "Recommended — schedule a screening call"
    if s >= 50: return "Potential — consider with onboarding support"
    if s >= 35: return "Development track — better for growth roles"
    return "Not recommended for this specific role"

def _summary(overall, tech, gh, res, comm) -> str:
    parts = []
    if tech["score"] >= 60:
        parts.append(f"strong technical match ({len(tech['matched'])} skills verified)")
    elif tech["matched"]:
        parts.append(f"partial technical match ({len(tech['matched'])} of {len(tech['matched'])+len(tech['missing'])} skills)")
    else:
        parts.append("limited direct skill overlap")

    if gh["score"] >= 60:
        parts.append(f"strong GitHub presence (credibility {gh['credibility']}/100)")
    elif gh["score"] > 0:
        parts.append(f"moderate GitHub signal")
    else:
        parts.append("no GitHub data")

    return (f"Overall {overall}/100 — {', '.join(parts)}. "
            f"{_recommendation(overall)}.")
