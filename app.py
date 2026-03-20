"""
Wise — AI Talent Intelligence
Reads real GitHub signals, parses resumes, and scores candidates
against any job description with a full, auditable reasoning chain.
"""
import os, json
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)
app.config["SECRET_KEY"]         = os.environ.get("SECRET_KEY", "wise-2025")
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024
app.config["JSON_SORT_KEYS"]     = False

os.makedirs(os.path.join(os.path.dirname(__file__), "static", "uploads"), exist_ok=True)
os.makedirs(os.path.join(os.path.dirname(__file__), "instance"),           exist_ok=True)


def get_analyzer():
    from engine.github_analyzer import GitHubAnalyzer
    return GitHubAnalyzer(token=os.environ.get("GITHUB_TOKEN", ""))

def get_scorer():
    from engine.scorer import get_scorer as _gs
    return _gs()


# ── Pages ─────────────────────────────────────────────────────────────────────
@app.route("/")
def home():    return render_template("home.html")

@app.route("/analyse")
def analyse(): return render_template("analyse.html")

@app.route("/match")
def match():   return render_template("match.html")

@app.route("/report")
def report():  return render_template("report.html")

@app.route("/compare")
def compare(): return render_template("compare.html")


# ── API: GitHub profile ────────────────────────────────────────────────────────
@app.route("/api/github", methods=["POST"])
def api_github():
    from engine.github_analyzer import demo_profile
    body     = request.get_json() or {}
    username = body.get("username", "").strip()
    if not username:
        return jsonify({"error": "Username required"}), 400
    if username.lower() in ("demo", "test", "example"):
        return jsonify(demo_profile(username))
    data = get_analyzer().analyze(username)
    if "error" in data:
        fb = demo_profile(username)
        fb["fallback_note"] = data["error"]
        return jsonify(fb)
    return jsonify(data)


# ── API: Resume parsing ────────────────────────────────────────────────────────
@app.route("/api/parse-resume", methods=["POST"])
def api_parse_resume():
    from engine.resume_parser import parse_resume
    if "resume" in request.files:
        f = request.files["resume"]
        if f.filename:
            return jsonify(parse_resume(file_bytes=f.read()))
    raw = (request.get_json() or {}).get("text", "")
    if raw:
        return jsonify(parse_resume(raw_text=raw))
    return jsonify({"error": "No resume provided"}), 400


# ── API: Full analysis (resume + GitHub + JD) ─────────────────────────────────
@app.route("/api/analyse", methods=["POST"])
def api_analyse():
    from engine.rater import rate
    from engine.github_analyzer import demo_profile
    from engine.resume_parser import parse_resume

    profile = {
        "name":             request.form.get("name",             "").strip(),
        "email":            request.form.get("email",            "").strip(),
        "phone":            request.form.get("phone",            "").strip(),
        "branch":           request.form.get("branch",           "").strip(),
        "cgpa":             request.form.get("cgpa",             "").strip(),
        "experience_years": request.form.get("experience_years", "").strip(),
        "education":        request.form.get("education",        "").strip(),
        "college":          request.form.get("college",          "").strip(),
        "graduation_year":  request.form.get("graduation_year",  "").strip(),
        "skills_raw":       request.form.get("skills",           "").strip(),
        "github_username":  request.form.get("github_username",  "").strip(),
        "linkedin":         request.form.get("linkedin",         "").strip(),
        "projects":         request.form.get("projects",         "").strip(),
        "certifications":   request.form.get("certifications",   "").strip(),
        "role":             request.form.get("role",             "").strip(),
    }
    jd_text = request.form.get("jd_text", "").strip()

    resume_data = None
    if "resume" in request.files:
        f = request.files["resume"]
        if f.filename:
            resume_data = parse_resume(file_bytes=f.read())

    manual_skills = [s.strip() for s in profile["skills_raw"].split(",") if s.strip()]
    resume_skills = (resume_data or {}).get("skills", [])
    all_skills    = list(dict.fromkeys(manual_skills + resume_skills))

    github_username = profile["github_username"] or (resume_data or {}).get("github", "")
    github_data = None
    if github_username:
        if github_username.lower() in ("demo", "test", "example"):
            github_data = demo_profile(github_username)
        else:
            github_data = get_analyzer().analyze(github_username)
            if "error" in github_data:
                github_data = demo_profile(github_username)
                github_data["fallback_note"] = github_data.get("fallback_note", "")

    if not jd_text:
        jd_text = "Required: python, javascript, sql, communication, problem solving"

    rating = rate(
        candidate_skills=all_skills,
        jd_text=jd_text,
        github_data=github_data,
        resume_data=resume_data,
        profile=profile,
    )

    bias = get_scorer().score(
        candidate_skills=all_skills,
        jd_text=jd_text,
        candidate_name=profile.get("name", "Candidate"),
        github_data=github_data,
        candidate_meta={
            "name":       profile.get("name"),
            "gender":     request.form.get("gender", ""),
            "university": profile.get("college"),
            "location":   request.form.get("location", ""),
        },
    )

    return jsonify({
        "profile":     profile,
        "skills":      all_skills,
        "github":      github_data,
        "resume":      resume_data,
        "rating":      rating,
        "bias_check":  bias.get("bias_check"),
        "jd_text":     jd_text,
    })


# ── API: Rank all demo candidates ─────────────────────────────────────────────
@app.route("/api/rank", methods=["POST"])
def api_rank():
    from engine.skills import parse_jd
    body    = request.get_json() or {}
    jd_text = body.get("jd_text", "").strip()
    if not jd_text:
        return jsonify({"error": "jd_text required"}), 400
    ranked = get_scorer().rank(demo_candidates(), jd_text)
    jd     = parse_jd(jd_text)
    return jsonify({
        "ranked": ranked,
        "jd":     {"must_have": jd["must_have"], "nice_to_have": jd["nice_to_have"], "level": jd["level"]},
    })


# ── API: Score one custom candidate ───────────────────────────────────────────
@app.route("/api/score-one", methods=["POST"])
def api_score_one():
    body   = request.get_json() or {}
    name   = body.get("name", "Candidate").strip()
    skills = body.get("skills", [])
    jd     = body.get("jd_text", "").strip()
    meta   = body.get("meta", {})
    if not skills or not jd:
        return jsonify({"error": "skills and jd_text required"}), 400
    return jsonify(get_scorer().score(
        candidate_skills=skills, jd_text=jd, candidate_name=name, candidate_meta=meta
    ))


# ── API: Extract skills from text ─────────────────────────────────────────────
@app.route("/api/extract-skills", methods=["POST"])
def api_extract_skills():
    from engine.skills import extract
    body = request.get_json() or {}
    sk   = extract(body.get("text", ""))
    return jsonify({"skills": sk, "count": len(sk)})


# ── API: Utilities ─────────────────────────────────────────────────────────────
@app.route("/api/sample-jds")
def api_sample_jds():
    return jsonify(sample_jds())

@app.route("/api/health")
def api_health():
    return jsonify({"status": "ok", "app": "Wise", "version": "1.0.0"})


# ── Demo data ──────────────────────────────────────────────────────────────────
def demo_candidates():
    return [
        {"id":"C001","name":"Arjun Mehta","title":"Software Engineer","experience_years":3,
         "education":"B.Tech CS — NIT Trichy",
         "skills":["python","machine learning","scikit-learn","pandas","numpy","flask","sql","postgresql","git","linux","statistics","data analysis","rest api"],
         "github":{"credibility":{"score":72,"label":"High","factors":["3.5yr account","18 repos","41 stars"],"note":"Strong signal."},"commit_signals":{"activity":"active","days_since":12,"consistency":0.78,"recent_repos":8,"total_repos":18},"complexity":{"level":"medium","score":0.65,"stars":41,"documented":14,"top_repos":[{"name":"ml-pipeline","stars":41,"desc":"End-to-end ML pipeline"}]},"primary_languages":["Python","SQL"],"language_distribution":{"Python":61.0,"SQL":22.0,"Shell":17.0},"inferred_skills":[{"skill":"python","confidence":0.91,"label":"Strong","evidence":["Python: 61%"],"verified":False,"source":"synthetic"},{"skill":"machine learning","confidence":0.68,"label":"Moderate","evidence":["Topics"],"verified":False,"source":"synthetic"}],"signal_summary":"Active Python/ML developer.","data_source":"synthetic_demo","verified":False,"profile":{"name":"Arjun Mehta","public_repos":18,"followers":22,"account_age_years":3.5,"avatar_url":"","url":"https://github.com/arjunm_dev","bio":"Building ML things"}},"meta":{"gender":"M","university":"NIT Trichy","location":"Chennai"}},
        {"id":"C002","name":"Priya Krishnamurthy","title":"Full Stack Developer","experience_years":4,
         "education":"B.E. IT — BITS Pilani",
         "skills":["javascript","typescript","react","node.js","next.js","css","html","mongodb","sql","docker","aws","git","rest api","graphql","agile"],
         "github":{"credibility":{"score":81,"label":"High","factors":["4yr account","25 repos","93 stars"],"note":"Strong signal."},"commit_signals":{"activity":"very active","days_since":3,"consistency":0.88,"recent_repos":12,"total_repos":25},"complexity":{"level":"large","score":0.9,"stars":93,"documented":20,"top_repos":[{"name":"nextjs-saas","stars":67,"desc":"SaaS boilerplate"}]},"primary_languages":["TypeScript","JavaScript","CSS"],"language_distribution":{"TypeScript":44.0,"JavaScript":31.0,"CSS":15.0,"HTML":10.0},"inferred_skills":[{"skill":"typescript","confidence":0.88,"label":"Strong","evidence":["TypeScript: 44%"],"verified":False,"source":"synthetic"},{"skill":"react","confidence":0.79,"label":"Strong","evidence":["Topics"],"verified":False,"source":"synthetic"}],"signal_summary":"Highly active TypeScript/React developer.","data_source":"synthetic_demo","verified":False,"profile":{"name":"Priya K","public_repos":25,"followers":61,"account_age_years":4.1,"avatar_url":"","url":"https://github.com/priya_dev","bio":"React / TypeScript / design systems"}},"meta":{"gender":"F","university":"BITS Pilani","location":"Bangalore"}},
        {"id":"C003","name":"Rohan Desai","title":"Data Engineer","experience_years":5,
         "education":"M.Tech Data Science — IIT Bombay",
         "skills":["python","sql","apache spark","kafka","airflow","data engineering","etl","postgresql","aws","docker","pandas","data warehousing","linux","bash"],
         "github":{"credibility":{"score":65,"label":"High","factors":["5yr account","12 repos","28 stars"],"note":"Strong signal."},"commit_signals":{"activity":"moderate","days_since":45,"consistency":0.55,"recent_repos":4,"total_repos":12},"complexity":{"level":"large","score":0.85,"stars":28,"documented":10,"top_repos":[{"name":"spark-etl","stars":28,"desc":"Scalable ETL with Spark"}]},"primary_languages":["Python","Shell","SQL"],"language_distribution":{"Python":55.0,"Shell":28.0,"SQL":17.0},"inferred_skills":[{"skill":"python","confidence":0.87,"label":"Strong","evidence":["Python: 55%"],"verified":False,"source":"synthetic"}],"signal_summary":"Experienced data engineer.","data_source":"synthetic_demo","verified":False,"profile":{"name":"Rohan Desai","public_repos":12,"followers":18,"account_age_years":5.0,"avatar_url":"","url":"https://github.com/rohan_data","bio":"Data pipelines at scale"}},"meta":{"gender":"M","university":"IIT Bombay","location":"Mumbai"}},
        {"id":"C004","name":"Sneha Iyer","title":"Junior Python Developer","experience_years":1,
         "education":"B.Sc Mathematics — Christ University",
         "skills":["python","flask","html","css","sql","git","statistics","data analysis","pandas"],
         "github":{"credibility":{"score":42,"label":"Medium","factors":["1yr account","7 repos","5 stars"],"note":"Moderate signal."},"commit_signals":{"activity":"active","days_since":21,"consistency":0.51,"recent_repos":4,"total_repos":7},"complexity":{"level":"small","score":0.3,"stars":5,"documented":4,"top_repos":[{"name":"flask-blog","stars":5,"desc":"Blog app"}]},"primary_languages":["Python","HTML"],"language_distribution":{"Python":70.0,"HTML":20.0,"CSS":10.0},"inferred_skills":[{"skill":"python","confidence":0.82,"label":"Strong","evidence":["Python: 70%"],"verified":False,"source":"synthetic"}],"signal_summary":"Early-career Python developer.","data_source":"synthetic_demo","verified":False,"profile":{"name":"Sneha Iyer","public_repos":7,"followers":9,"account_age_years":1.1,"avatar_url":"","url":"https://github.com/sneha_codes","bio":"Learning Python, one bug at a time"}},"meta":{"gender":"F","university":"Christ University","location":"Bangalore"}},
        {"id":"C005","name":"Vikram Nair","title":"DevOps Engineer","experience_years":6,
         "education":"B.Tech IT — VIT Vellore",
         "skills":["devops","docker","kubernetes","aws","terraform","ansible","ci/cd","github actions","linux","bash","python","site reliability engineering","microservices"],
         "github":{"credibility":{"score":78,"label":"High","factors":["6yr account","21 repos","67 stars"],"note":"Strong signal."},"commit_signals":{"activity":"very active","days_since":2,"consistency":0.91,"recent_repos":15,"total_repos":21},"complexity":{"level":"medium","score":0.65,"stars":67,"documented":18,"top_repos":[{"name":"k8s-templates","stars":52,"desc":"Production K8s manifests"}]},"primary_languages":["HCL","Shell","Python"],"language_distribution":{"HCL":35.0,"Shell":30.0,"Python":22.0,"YAML":13.0},"inferred_skills":[{"skill":"terraform","confidence":0.89,"label":"Strong","evidence":["HCL: 35%"],"verified":False,"source":"synthetic"},{"skill":"devops","confidence":0.84,"label":"Strong","evidence":["Topics"],"verified":False,"source":"synthetic"}],"signal_summary":"Senior DevOps engineer.","data_source":"synthetic_demo","verified":False,"profile":{"name":"Vikram Nair","public_repos":21,"followers":44,"account_age_years":6.2,"avatar_url":"","url":"https://github.com/vikram_ops","bio":"Kubernetes + Terraform advocate"}},"meta":{"gender":"M","university":"VIT Vellore","location":"Hyderabad"}},
        {"id":"C006","name":"Aisha Sharma","title":"ML Research Engineer","experience_years":3,
         "education":"M.Tech AI — IIT Delhi",
         "skills":["python","deep learning","pytorch","tensorflow","nlp","transformers","computer vision","statistics","machine learning","scikit-learn","data analysis","numpy"],
         "github":{"credibility":{"score":85,"label":"High","factors":["3yr account","14 repos","156 stars"],"note":"Strong signal."},"commit_signals":{"activity":"active","days_since":8,"consistency":0.73,"recent_repos":7,"total_repos":14},"complexity":{"level":"large","score":0.9,"stars":156,"documented":13,"top_repos":[{"name":"bert-finetune","stars":102,"desc":"BERT fine-tuning toolkit"}]},"primary_languages":["Python","Jupyter Notebook"],"language_distribution":{"Python":58.0,"Jupyter Notebook":42.0},"inferred_skills":[{"skill":"python","confidence":0.93,"label":"Strong","evidence":["Python: 58%"],"verified":False,"source":"synthetic"},{"skill":"deep learning","confidence":0.81,"label":"Strong","evidence":["Topics"],"verified":False,"source":"synthetic"}],"signal_summary":"High-credibility ML researcher.","data_source":"synthetic_demo","verified":False,"profile":{"name":"Aisha Sharma","public_repos":14,"followers":88,"account_age_years":3.3,"avatar_url":"","url":"https://github.com/aisha_ml","bio":"NLP | Vision | IIT Delhi"}},"meta":{"gender":"F","university":"IIT Delhi","location":"Delhi"}},
        {"id":"C007","name":"Karan Patel","title":"Backend Engineer","experience_years":4,
         "education":"B.Tech CS — DAIICT",
         "skills":["go","python","postgresql","redis","docker","kubernetes","grpc","rest api","microservices","linux","sql","aws","system design"],
         "github":{"credibility":{"score":70,"label":"High","factors":["4.5yr account","19 repos","38 stars"],"note":"Strong signal."},"commit_signals":{"activity":"active","days_since":18,"consistency":0.69,"recent_repos":9,"total_repos":19},"complexity":{"level":"medium","score":0.7,"stars":38,"documented":16,"top_repos":[{"name":"go-api-gateway","stars":38,"desc":"High-perf API gateway in Go"}]},"primary_languages":["Go","Python","Shell"],"language_distribution":{"Go":62.0,"Python":24.0,"Shell":14.0},"inferred_skills":[{"skill":"go","confidence":0.90,"label":"Strong","evidence":["Go: 62%"],"verified":False,"source":"synthetic"}],"signal_summary":"Backend specialist with Go expertise.","data_source":"synthetic_demo","verified":False,"profile":{"name":"Karan Patel","public_repos":19,"followers":33,"account_age_years":4.5,"avatar_url":"","url":"https://github.com/karanp_dev","bio":"Go, distributed systems, coffee"}},"meta":{"gender":"M","university":"DAIICT","location":"Ahmedabad"}},
        {"id":"C008","name":"Divya Menon","title":"Frontend Engineer","experience_years":2,
         "education":"B.E. CS — PSG Tech",
         "skills":["javascript","typescript","react","css","html","figma","ui/ux","tailwind","next.js","git","agile","accessibility"],
         "github":{"credibility":{"score":58,"label":"Medium","factors":["2yr account","11 repos","19 stars"],"note":"Moderate-high signal."},"commit_signals":{"activity":"active","days_since":9,"consistency":0.74,"recent_repos":7,"total_repos":11},"complexity":{"level":"small","score":0.35,"stars":19,"documented":9,"top_repos":[{"name":"ui-kit","stars":19,"desc":"Accessible React component library"}]},"primary_languages":["TypeScript","JavaScript","CSS"],"language_distribution":{"TypeScript":50.0,"JavaScript":30.0,"CSS":20.0},"inferred_skills":[{"skill":"typescript","confidence":0.85,"label":"Strong","evidence":["TypeScript: 50%"],"verified":False,"source":"synthetic"},{"skill":"react","confidence":0.76,"label":"Strong","evidence":["Topics"],"verified":False,"source":"synthetic"}],"signal_summary":"Frontend specialist with accessibility focus.","data_source":"synthetic_demo","verified":False,"profile":{"name":"Divya Menon","public_repos":11,"followers":27,"account_age_years":2.4,"avatar_url":"","url":"https://github.com/divya_ui","bio":"Accessible interfaces, one component at a time"}},"meta":{"gender":"F","university":"PSG Tech","location":"Coimbatore"}},
    ]

def sample_jds():
    return {
        "ml_engineer":   {"label":"ML Engineer",   "text":"Required: python, machine learning, pytorch, tensorflow, nlp, sql, docker\nPreferred: transformers, aws, mlops, computer vision"},
        "fullstack":     {"label":"Full Stack",     "text":"Required: react, typescript, node.js, sql, rest api, git\nPreferred: next.js, docker, graphql, aws, agile"},
        "data_engineer": {"label":"Data Engineer",  "text":"Required: python, sql, apache spark, kafka, airflow, etl, docker, aws\nPreferred: dbt, snowflake, data warehousing, terraform"},
        "devops":        {"label":"DevOps",          "text":"Required: docker, kubernetes, aws, ci/cd, terraform, linux, bash\nPreferred: ansible, prometheus, microservices, python"},
        "backend_go":    {"label":"Go Backend",     "text":"Required: go, postgresql, redis, rest api, docker, kubernetes, linux\nPreferred: aws, grpc, kafka, microservices, system design"},
        "frontend":      {"label":"Frontend",        "text":"Required: react, typescript, css, html, javascript, git\nPreferred: next.js, figma, tailwind, accessibility, agile"},
    }


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
