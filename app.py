import re
import os
import psycopg2

from dotenv import load_dotenv

from flask import Flask, request, render_template
from pypdf import PdfReader

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity




app = Flask(__name__)

load_dotenv()

# ==========================================
# Upload Folder
# ==========================================

UPLOAD_FOLDER = "uploads"

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ==========================================
# PostgreSQL Connection
# ==========================================

def get_db_connection():

    connection = psycopg2.connect(
        host="localhost",
        database="resume_analyzer",
        user="postgres",
        password="Resume@1234",
        port="5432"
    )

    return connection


# ==========================================
# Skills Database
# ==========================================

SKILLS = [

    "Python",
    "Java",
    "C++",
    "C",
    "SQL",
    "HTML",
    "CSS",
    "JavaScript",
    "React",
    "Django",
    "Flask",
    "PostgreSQL",
    "MySQL",
    "MongoDB",
    "Git",
    "GitHub",
    "Machine Learning",
    "Data Science",
    "AWS",
    "Docker",
    "REST API"

]


# ==========================================
# Home Page
# ==========================================

@app.route("/")
def home():

    return render_template(
        "index.html"
    )


# ==========================================
# Analysis History
# ==========================================

@app.route("/history")
def history():

    connection = get_db_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            filename,
            resume_score,
            match_score,
            nlp_score,
            combined_score,
            created_at
        FROM analyses
        ORDER BY created_at DESC
        """
    )

    analyses = cursor.fetchall()

    cursor.close()

    connection.close()

    return render_template(
        "history.html",
        analyses=analyses
    )


# ==========================================
# Dashboard
# ==========================================

@app.route("/dashboard")
def dashboard():

    connection = get_db_connection()

    cursor = connection.cursor()


    # Total analyses

    cursor.execute(
        "SELECT COUNT(*) FROM analyses"
    )

    total_analyses = cursor.fetchone()[0]


    # Average match

    cursor.execute(
        "SELECT AVG(combined_score) FROM analyses"
    )

    average_match = cursor.fetchone()[0]

    if average_match is None:

        average_match = 0

    else:

        average_match = round(
            float(average_match),
            2
        )


    # Best match

    cursor.execute(
        "SELECT MAX(combined_score) FROM analyses"
    )

    best_match = cursor.fetchone()[0]

    if best_match is None:

        best_match = 0

    else:

        best_match = round(
            float(best_match),
            2
        )


    # Recent analyses

    cursor.execute(
        """
        SELECT
            id,
            filename,
            resume_score,
            combined_score,
            created_at
        FROM analyses
        ORDER BY created_at DESC
        LIMIT 10
        """
    )

    recent_analyses = cursor.fetchall()


    cursor.close()

    connection.close()


    return render_template(
        "dashboard.html",
        total_analyses=total_analyses,
        average_match=average_match,
        best_match=best_match,
        recent_analyses=recent_analyses
    )


# ==========================================
# Analysis Details
# ==========================================

@app.route("/analysis/<int:analysis_id>")
def analysis_details(analysis_id):

    connection = get_db_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            filename,
            email,
            phone,
            resume_score,
            match_score,
            nlp_score,
            combined_score,
            matched_skills,
            missing_skills,
            created_at
        FROM analyses
        WHERE id = %s
        """,
        (analysis_id,)
    )

    analysis = cursor.fetchone()

    cursor.close()

    connection.close()


    if analysis is None:

        return "Analysis not found", 404


    return render_template(
        "analysis_details.html",
        analysis=analysis
    )


# ==========================================
# Resume Upload + Analysis
# ==========================================

@app.route(
    "/upload",
    methods=["POST"]
)
def upload_resume():


    # ======================================
    # Check Resume
    # ======================================

    if "resume" not in request.files:

        return "No resume uploaded", 400


    file = request.files["resume"]


    if file.filename == "":

        return "No file selected", 400


    # ======================================
    # Get Job Description
    # ======================================

    job_description = request.form.get(
        "job_description",
        ""
    )


    # ======================================
    # Save Resume
    # ======================================

    file_path = os.path.join(
        app.config["UPLOAD_FOLDER"],
        file.filename
    )

    file.save(file_path)


    # ======================================
    # Extract Text From PDF
    # ======================================

    reader = PdfReader(file_path)

    text = ""


    for page in reader.pages:

        page_text = page.extract_text()

        if page_text:

            text += page_text + "\n"


    # ======================================
    # Extract Email
    # ======================================

    email_match = re.search(
        r'[\w\.-]+@[\w\.-]+\.\w+',
        text
    )


    if email_match:

        email = email_match.group(0)

    else:

        email = "Not found"


    # ======================================
    # Extract Phone Number
    # ======================================

    phone_match = re.search(
        r'(?:\+91[\s-]?)?[6-9]\d{9}',
        text
    )


    if phone_match:

        phone = phone_match.group(0)

    else:

        phone = "Not found"


    # ======================================
    # Extract Skills From Resume
    # ======================================

    found_skills = []


    for skill in SKILLS:

        if re.search(
            r'\b' + re.escape(skill) + r'\b',
            text,
            re.IGNORECASE
        ):

            found_skills.append(skill)


    # ======================================
    # Extract Required Skills
    # From Job Description
    # ======================================

    required_skills = []


    for skill in SKILLS:

        if re.search(
            r'\b' + re.escape(skill) + r'\b',
            job_description,
            re.IGNORECASE
        ):

            required_skills.append(skill)


    # ======================================
    # Matched + Missing Skills
    # ======================================

    matched_skills = []

    missing_skills = []


    for skill in required_skills:

        if skill in found_skills:

            matched_skills.append(skill)

        else:

            missing_skills.append(skill)


    # ======================================
    # Keyword Match Score
    # ======================================

    if len(required_skills) > 0:

        match_score = (
            len(matched_skills)
            / len(required_skills)
        ) * 100

    else:

        match_score = 0


    match_score = round(
        match_score,
        2
    )


    # ======================================
    # NLP Similarity using TF-IDF
    # ======================================

    if job_description.strip():

        documents = [
            text,
            job_description
        ]


        vectorizer = TfidfVectorizer(
            stop_words="english"
        )


        tfidf_matrix = vectorizer.fit_transform(
            documents
        )


        similarity = cosine_similarity(
            tfidf_matrix[0:1],
            tfidf_matrix[1:2]
        )


        nlp_score = (
            similarity[0][0]
            * 100
        )

    else:

        nlp_score = 0


    nlp_score = round(
        nlp_score,
        2
    )


    # ======================================
    # Combined Job Match Score
    # ======================================

    if job_description.strip():

        combined_score = (
            (match_score * 0.60)
            +
            (nlp_score * 0.40)
        )

    else:

        combined_score = 0


    combined_score = round(
        combined_score,
        2
    )


    # ======================================
    # Resume Score
    # ======================================

    resume_score = 0


    # Contact Information

    if email != "Not found":

        resume_score += 5


    if phone != "Not found":

        resume_score += 5


    # Skills

    if len(found_skills) >= 5:

        resume_score += 25

    elif len(found_skills) >= 3:

        resume_score += 20

    elif len(found_skills) >= 1:

        resume_score += 10


    # Education

    if re.search(
        r'\b(B\.?Tech|B\.?E\.?|Bachelor|Bachelors|Degree|Education)\b',
        text,
        re.IGNORECASE
    ):

        resume_score += 15


    # Projects

    if re.search(
        r'\b(project|projects)\b',
        text,
        re.IGNORECASE
    ):

        resume_score += 20


    # Experience / Internship

    if re.search(
        r'\b(experience|internship|intern|employment|work experience)\b',
        text,
        re.IGNORECASE
    ):

        resume_score += 20


    # Job Match Contribution

    resume_score += round(
        combined_score * 0.10
    )


    # Maximum 100

    resume_score = min(
        resume_score,
        100
    )


    resume_score = round(
        resume_score
    )


    # ======================================
    # Suggestions
    # ======================================

    suggestions = []


    # Email

    if email == "Not found":

        suggestions.append(
            "Add a professional email address."
        )


    # Phone

    if phone == "Not found":

        suggestions.append(
            "Add your phone number to the resume."
        )


    # Skills

    if len(found_skills) < 5:

        suggestions.append(
            "Add more relevant technical skills."
        )


    # Projects

    if not re.search(
        r'\b(project|projects)\b',
        text,
        re.IGNORECASE
    ):

        suggestions.append(
            "Add a Projects section with 2-3 strong projects."
        )


    # Experience

    if not re.search(
        r'\b(experience|internship|intern|employment|work experience)\b',
        text,
        re.IGNORECASE
    ):

        suggestions.append(
            "Add internship or work experience if available."
        )


    # Missing skills

    if missing_skills:

        suggestions.append(
            "Relevant missing skills: "
            + ", ".join(missing_skills)
        )


    # Low match

    if combined_score < 50:

        suggestions.append(
            "Customize your resume according to the job description."
        )


    # No suggestions

    if len(suggestions) == 0:

        suggestions.append(
            "Your resume looks well aligned with this job description!"
        )


    # ======================================
    # Save Analysis To PostgreSQL
    # ======================================

    connection = get_db_connection()

    cursor = connection.cursor()


    cursor.execute(
        """
        INSERT INTO analyses
        (
            filename,
            email,
            phone,
            resume_score,
            match_score,
            nlp_score,
            combined_score,
            matched_skills,
            missing_skills
        )

        VALUES
        (
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s
        )
        """,

        (
            file.filename,
            email,
            phone,
            int(resume_score),
            float(match_score),
            float(nlp_score),
            float(combined_score),
            ", ".join(matched_skills),
            ", ".join(missing_skills)
        )
    )


    connection.commit()

    cursor.close()

    connection.close()


    # ======================================
    # Display Results
    # ======================================

    return render_template(

        "results.html",

        filename=file.filename,

        email=email,

        phone=phone,

        resume_skills=found_skills,

        required_skills=required_skills,

        matched_skills=matched_skills,

        missing_skills=missing_skills,

        match_score=match_score,

        nlp_score=nlp_score,

        combined_score=combined_score,

        resume_score=resume_score,

        suggestions=suggestions

    )


# ==========================================
# Run Flask Application
# ==========================================

if __name__ == "__main__":

    app.run(
        debug=True
    )