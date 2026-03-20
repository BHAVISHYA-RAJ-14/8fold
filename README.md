# Wise — AI Talent Intelligence

> See who can actually do the job.

Wise reads real GitHub activity, parses resumes, and scores candidates against
any job description — with a complete reasoning chain, a per-skill evidence
audit trail, and a built-in fairness check on every single result.

---

## Quick Start

```bash
git clone https://github.com/your-org/wise
cd wise
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Open http://localhost:5000

Optional — add a GitHub token to avoid rate limits:
```bash
echo "GITHUB_TOKEN=ghp_yourtoken" > .env
```

---

## Pages

| Route      | What it does                                                    |
|------------|-----------------------------------------------------------------|
| /          | Home — live skill extractor, feature overview                   |
| /analyse   | Full candidate analysis — resume upload, GitHub, scored report  |
| /match     | Rank all 8 demo candidates against any pasted job description   |
| /report    | Glass-Box report — custom candidate, per-skill audit trail      |
| /compare   | Side-by-side comparison of two candidates with head-to-head bars|

---

## Keyboard Shortcuts

Press `?` anywhere to open the shortcuts panel. Works on every page.

| Key   | Action                  |
|-------|-------------------------|
| H     | Go to Home              |
| A     | Analyse a Candidate     |
| M     | Match and Rank          |
| R     | Glass-Box Report        |
| C     | Compare Two Candidates  |
| ?     | Open shortcuts panel    |
| Esc   | Close panel             |

Shortcuts are disabled automatically when typing in any input field.

---

## How the Score Works

Every candidate receives an Overall Score (0–100) built from four criteria:

```
Technical Match   40% — how many required skills match, weighted by importance
GitHub Signal     25% — credibility score from 7 independent GitHub signals
Resume Quality    20% — profile completeness, education, experience, links
Communication     15% — documentation quality, project descriptions, LinkedIn
```

Each criterion is scored from 0–100. Every point is traceable to a specific input.

The GitHub credibility score itself combines:
- Language distribution weighted by actual code volume
- Commit recency — days since last push
- Repository complexity and average size
- Community stars as peer-validation evidence
- Documentation rate across repositories
- Account age as anti-spam indicator
- Topic signals mapped to skill inferences

---

## Fairness Check

Every score is re-run with name, gender, university, and location removed.
The delta is always 0.0 — because those fields structurally never enter any
scoring component. This is proven mathematically, not just claimed.

---

## Project Structure

```
wise/
├── app.py                   Flask app and all API routes
├── requirements.txt
├── .gitignore
├── engine/
│   ├── skills.py            100+ skill vocabulary, extraction, importance weights
│   ├── github_analyzer.py   7-signal GitHub credibility engine
│   ├── resume_parser.py     PDF and plain text resume extraction
│   ├── scorer.py            Glass-Box scorer with fairness check
│   └── rater.py             4-criteria overall rating engine
├── templates/
│   ├── base.html            Layout, nav, shortcut panel, theme toggle
│   ├── home.html            Landing page with live skill extractor
│   ├── analyse.html         Full candidate analysis with radar chart
│   ├── match.html           Rank all candidates against any JD
│   ├── report.html          Glass-Box per-skill audit trail
│   └── compare.html         Side-by-side candidate comparison
└── static/
    ├── css/app.css          Complete design system, light and dark mode
    └── js/app.js            Shared utilities, animations, theme toggle
```

---

## API Endpoints

| Method | Endpoint              | Description                              |
|--------|-----------------------|------------------------------------------|
| POST   | /api/analyse          | Full analysis — resume + GitHub + JD     |
| POST   | /api/rank             | Rank all candidates against a JD         |
| POST   | /api/score-one        | Score a single custom candidate          |
| POST   | /api/github           | Fetch and analyse a GitHub profile       |
| POST   | /api/parse-resume     | Extract structured data from a resume    |
| POST   | /api/extract-skills   | Extract skills from any free text        |
| GET    | /api/sample-jds       | Return 6 sample job descriptions         |
| GET    | /api/health           | Health check                             |

---

## Tech Stack

| Layer              | Technology                                    |
|--------------------|-----------------------------------------------|
| Backend            | Python 3.11, Flask 3.0                        |
| Semantic matching  | sentence-transformers (all-MiniLM-L6-v2)      |
| GitHub data        | GitHub REST API v3                            |
| Resume parsing     | pdfminer, regex                               |
| Skill taxonomy     | Lightcast Open Skills + O*NET (curated)       |
| Frontend           | Jinja2, vanilla JS, custom CSS                |
| Theme              | Light and dark mode with localStorage persist |

---

## Datasets Referenced

- Kaggle Resume Dataset (snehaanbhawal/resume-dataset)
  Used to validate skill vocabulary coverage across 24 job categories

- LinkedIn Job Postings (arshkon/linkedin-job-postings)
  Used to validate JD parsing and must-have vs preferred detection

- Lightcast Open Skills — lightcast.io/open-skills/access
  Industry-standard skill taxonomy for vocabulary and importance weights

- O*NET Database — onetcenter.org/database.html
  Occupational framework for seniority level detection and skill grouping

All 8 demo candidate profiles are synthetic. No real PII is used anywhere.

---

## Known Limitations

- GitHub API allows 60 requests per hour without a token.
  Add GITHUB_TOKEN to .env to raise this limit significantly.
- Semantic similarity falls back to Jaccard set overlap if
  sentence-transformers is not installed. Core scoring still works.
- Skill vocabulary covers approximately 100 key technical skills.
  The full Lightcast taxonomy has 32,000+ terms.
- Resume parsing works on text-layer PDFs. Scanned image PDFs
  require OCR preprocessing not included in this version.

---

## What's Next

- FAISS vector index for sub-millisecond similarity at scale
- Full Lightcast 32k taxonomy integration
- Candidate self-serve portal with shareable report links
- SHAP values per feature for explainability heatmaps
- Compliance audit log export as PDF for HR and legal use
- OAuth GitHub integration for private repository signals
