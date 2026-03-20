"""
engine/skills.py
Single source of truth for skill vocabulary, extraction, and weighting.
Used by both Impact Area 01 (Signal Extraction) and Impact Area 04 (Glass-Box).
"""
import re
from typing import List, Dict

VOCAB: List[str] = [
    # ── Programming Languages ──────────────────────────────────────────────
    "python","javascript","typescript","java","c++","c#","c","rust","go","golang",
    "kotlin","swift","ruby","php","scala","r","matlab","dart","julia","perl","bash",
    "shell scripting","powershell","haskell","elixir","clojure","groovy",
    # ── Web Frontend ──────────────────────────────────────────────────────
    "react","vue","angular","next.js","nuxt","svelte","html","css","sass","tailwind",
    "bootstrap","jquery","webpack","vite","redux","graphql","restful api","rest api",
    # ── Web Backend ───────────────────────────────────────────────────────
    "node.js","express","flask","django","fastapi","spring boot","rails","laravel",
    "asp.net","grpc","websockets","microservices",
    # ── Data / ML / AI ───────────────────────────────────────────────────
    "machine learning","deep learning","nlp","computer vision","tensorflow","pytorch",
    "scikit-learn","pandas","numpy","matplotlib","seaborn","data science",
    "data analysis","statistics","tableau","power bi","feature engineering",
    "model deployment","mlops","llm","transformers","hugging face","langchain",
    "reinforcement learning","xgboost","lightgbm","opencv","a/b testing",
    # ── Cloud / DevOps ────────────────────────────────────────────────────
    "aws","azure","gcp","docker","kubernetes","terraform","ansible","ci/cd",
    "jenkins","github actions","gitlab ci","devops","linux","cloud computing",
    "serverless","site reliability engineering","prometheus","grafana","helm",
    # ── Databases ─────────────────────────────────────────────────────────
    "sql","postgresql","mysql","sqlite","mongodb","redis","elasticsearch",
    "cassandra","dynamodb","nosql","database design","data warehousing","dbt",
    "snowflake","bigquery","firebase","supabase",
    # ── Mobile ────────────────────────────────────────────────────────────
    "ios development","android development","react native","flutter",
    "mobile development","swiftui","jetpack compose",
    # ── Security / Other Tech ─────────────────────────────────────────────
    "cybersecurity","penetration testing","cryptography","blockchain","solidity",
    "web3","smart contracts","unity","game development","embedded systems","iot",
    "apache spark","kafka","airflow","etl","data engineering","rabbitmq",
    # ── Design / PM ───────────────────────────────────────────────────────
    "figma","ui/ux","wireframing","prototyping","user research","accessibility",
    "agile","scrum","kanban","jira","project management","product management",
    # ── Soft Skills ───────────────────────────────────────────────────────
    "leadership","communication","problem solving","teamwork","mentoring",
    "critical thinking","time management","collaboration",
]

# Higher weight = more strategically important when matching
_WEIGHTS: Dict[str, float] = {
    "python":1.3,"javascript":1.2,"typescript":1.2,"machine learning":1.4,
    "deep learning":1.4,"nlp":1.3,"docker":1.2,"kubernetes":1.3,"aws":1.2,
    "react":1.2,"sql":1.15,"java":1.1,"go":1.2,"rust":1.2,
    "data science":1.3,"devops":1.2,"tensorflow":1.2,"pytorch":1.2,
}
DEFAULT_W = 1.0

def get_weight(skill: str) -> float:
    return _WEIGHTS.get(skill.lower(), DEFAULT_W)

def extract(text: str) -> List[str]:
    """Return deduplicated ordered list of skills found in text."""
    low = text.lower()
    found: List[str] = []
    for s in VOCAB:
        if re.search(r'\b' + re.escape(s) + r'\b', low):
            found.append(s)
    return list(dict.fromkeys(found))

def parse_jd(text: str) -> dict:
    """
    Parse a job description into must-have vs nice-to-have skills + seniority level.
    Returns dict with keys: all_skills, must_have, nice_to_have, level
    """
    all_skills = extract(text)
    must: List[str] = []
    nice: List[str] = []
    mode = "required"

    for line in text.splitlines():
        ll = line.lower()
        if any(w in ll for w in ["preferred","nice to have","bonus","plus","optional","good to have","desirable"]):
            mode = "preferred"
        elif any(w in ll for w in ["required","must have","essential","mandatory","minimum","you need","you must"]):
            mode = "required"
        for s in extract(line):
            if mode == "required" and s not in must:
                must.append(s)
            elif mode == "preferred" and s not in nice:
                nice.append(s)

    if not must:
        must = all_skills

    tl = text.lower()
    if any(w in tl for w in ["senior","lead","principal","staff","director","head of","vp","architect"]):
        level = "senior"
    elif any(w in tl for w in ["junior","entry","graduate","intern","fresher","trainee","associate"]):
        level = "junior"
    else:
        level = "mid"

    return {"all_skills": all_skills, "must_have": must, "nice_to_have": nice, "level": level}
