# Wise — AI Talent Intelligence

> See who can actually do the job.

Wise reads a candidate's real GitHub activity, parses their resume, and scores them against any job description — with a complete reasoning chain and a built-in fairness check on every result.

## Quick Start

```bash
git clone https://github.com/your-org/wise
cd wise
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python app.py
# → http://localhost:5000
```

Optional — GitHub token for higher API rate limits:
```
echo "GITHUB_TOKEN=ghp_yourtoken" > .env
```

## Pages

| Route | What it does |
|---|---|
| `/` | Home — live skill extractor, feature overview |
| `/analyse` | Full candidate analysis — resume upload, GitHub, scored report |
| `/match` | Rank all 8 demo candidates against any pasted JD |
| `/report` | Glass-Box report — custom candidate, per-skill audit trail |
| `/compare` | Side-by-side comparison of two candidates |

## Keyboard Shortcuts

Press `?` anywhere to open the shortcuts panel, or use directly:

| Key | Action |
|---|---|
| `H` | Home |
| `A` | Analyse |
| `M` | Match |
| `R` | Report |
| `C` | Compare |
| `?` or `/` | Shortcuts panel |
| `Esc` | Close panel |

## Tech Stack

- **Backend** — Python 3.11, Flask 3.0
- **AI / Scoring** — sentence-transformers (all-MiniLM-L6-v2), cosine similarity, weighted skill matching
- **GitHub** — REST API v3 (7 independent credibility signals)
- **Resume Parsing** — pdfminer / regex extraction
- **Frontend** — Jinja2, vanilla JS, custom CSS (no frameworks)
- **Skill Taxonomy** — curated from Lightcast Open Skills + O*NET

## How the Score Works

```
Final Score =  55% × Technical Skill Match (blended count + weighted)
            +  20% × Semantic Similarity    (sentence-transformers / Jaccard)
            +  15% × GitHub Credibility     (0–100 from 7 signals)
            +  10% × Preferred Skills Bonus
```

Every score includes:
- Which skills matched and which are missing
- Per-skill evidence source (GitHub-verified vs self-reported)
- A fairness check: re-run without name/gender/university/location → delta always = 0.0

## Project Structure

```
wise/
├── app.py               ← Flask app + all routes
├── requirements.txt
├── .gitignore
├── engine/
│   ├── skills.py        ← Skill vocabulary + extraction + weighting
│   ├── github_analyzer.py ← 7-signal GitHub credibility engine
│   ├── resume_parser.py ← PDF / text resume extraction
│   ├── scorer.py        ← Glass-Box scorer + fairness check
│   └── rater.py         ← Multi-criteria rating engine
├── templates/
│   ├── base.html        ← Layout, nav, shortcut panel
│   ├── home.html        ← Landing page + live skill tagger
│   ├── analyse.html     ← Full candidate analysis
│   ├── match.html       ← Rank all candidates
│   ├── report.html      ← Glass-Box per-skill audit
│   └── compare.html     ← Side-by-side comparison
└── static/
    ├── css/app.css      ← Complete design system
    └── js/app.js        ← Shared utilities + radar + activity strip
```

## Datasets Referenced

- [Kaggle Resume Dataset](https://www.kaggle.com/datasets/snehaanbhawal/resume-dataset) — skill vocabulary validation
- [LinkedIn Job Postings](https://www.kaggle.com/datasets/arshkon/linkedin-job-postings) — JD structure reference
- [Lightcast Open Skills](https://lightcast.io/open-skills/access) — skill taxonomy
- [O*NET Database](https://www.onetcenter.org/database.html) — occupational skill requirements

All 8 demo candidates are synthetic. No real PII used.
