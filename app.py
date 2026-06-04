# from fastapi import FastAPI, UploadFile, File
# from fastapi.middleware.cors import CORSMiddleware
# import fitz
# import spacy
# import requests
# import os
# from dotenv import load_dotenv

# load_dotenv()

# app = FastAPI()

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
# RAPIDAPI_HOST = os.getenv("RAPIDAPI_HOST")

# nlp = spacy.load("en_core_web_sm")

# SKILL_CATEGORIES = {
#     "Languages": ["python", "java", "c++", "c", "javascript", "typescript"],
#     "Frameworks": ["react", "node.js", "express", "django", "flask"],
#     "Databases": ["mongodb", "mysql", "postgresql", "oracle"],
#     "Tools": ["git", "docker", "aws", "gcp", "azure"]
# }

# # =========================
# # Extract PDF Text
# # =========================

# def extract_text_from_pdf(file_content):

#     text = ""

#     doc = fitz.open(stream=file_content, filetype="pdf")

#     for page in doc:
#         text += page.get_text()

#     return text

# # =========================
# # Extract Skills
# # =========================

# def extract_skills(text):

#     text = text.lower()

#     tokens = [
#         token.text
#         for token in nlp(text)
#         if not token.is_stop and not token.is_punct
#     ]

#     found_skills = {
#         category: []
#         for category in SKILL_CATEGORIES
#     }

#     for category, keywords in SKILL_CATEGORIES.items():

#         for keyword in keywords:

#             if keyword.lower() in tokens:
#                 found_skills[category].append(keyword)

#     return {
#         k: v
#         for k, v in found_skills.items()
#         if v
#     }

# # =========================
# # Fetch Jobs
# # =========================

# def fetch_jobs(role, location):

#     query = f"{role} in {location}"

#     url = "https://jsearch.p.rapidapi.com/search"

#     querystring = {
#         "query": query,
#         "page": "1",
#         "num_pages": "1",
#         "page_size": "5",
#         "country": "IN"
#     }

#     headers = {
#         "X-RapidAPI-Key": RAPIDAPI_KEY,
#         "X-RapidAPI-Host": RAPIDAPI_HOST
#     }

#     response = requests.get(
#         url,
#         headers=headers,
#         params=querystring
#     )

#     results = []

#     if response.status_code == 200:

#         data = response.json()

#         for job in data.get("data", [])[:5]:

#             results.append({
#                 "title": job.get("job_title", "N/A"),
#                 "company": job.get("employer_name", "Unknown"),
#                 "location": f"{job.get('job_city')} , {job.get('job_country')}",
#                 "link": job.get("job_apply_link")
#             })

#     return results

# # =========================
# # Analyze Resume
# # =========================

# @app.post("/analyze")

# async def analyze_resume(
#     file: UploadFile = File(...)
# ):

#     content = await file.read()

#     resume_text = extract_text_from_pdf(content)

#     skills = extract_skills(resume_text)

#     roles = []

#     all_skills = [
#         s
#         for slist in skills.values()
#         for s in slist
#     ]

#     if "react" in all_skills:
#         roles.append("Frontend Developer")

#     if "node.js" in all_skills:
#         roles.append("Backend Developer")

#     if all(
#         x in all_skills
#         for x in ["react", "node.js", "mongodb"]
#     ):
#         roles.append("MERN Stack Developer")

#     if any(
#         x in all_skills
#         for x in ["python", "java", "c++"]
#     ):
#         roles.append("Full Stack Developer")

#     return {
#         "skills": skills,
#         "roles": roles
#     }

# # =========================
# # Dynamic Job Fetching
# # =========================

# @app.get("/fetch-jobs")

# def get_jobs(
#     role: str,
#     location: str
# ):

#     jobs = fetch_jobs(role, location)

#     return {
#         "jobs": jobs
#     }



from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware

from groq import Groq

import fitz
import json
import requests
import os
import re

from dotenv import load_dotenv

load_dotenv()

# =========================
# FASTAPI APP
# =========================

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# GROQ CLIENT
# =========================

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

# =========================
# RAPID API
# =========================

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
RAPIDAPI_HOST = os.getenv("RAPIDAPI_HOST")

# =========================
# EXTRACT PDF TEXT
# =========================

def extract_text_from_pdf(file_content):

    text = ""

    doc = fitz.open(
        stream=file_content,
        filetype="pdf"
    )

    for page in doc:
        text += page.get_text()

    return text

# =========================
# AI SKILL + ROLE EXTRACTION
# =========================

def extract_skills_and_roles(resume_text):

    prompt = f"""
    Analyze the resume and return ONLY valid JSON.

    Extract:

    1. Skills (all technical and professional skills)
    2. Recommended job roles
    3. Experience level
    4. Job search keywords

    Format:

    {{
        "skills": [
            "Python",
            "React",
            "MongoDB"
        ],
        "roles": [
            "Full Stack Developer"
        ],
        "experience_level": "Fresher",
        "job_keywords": [
            "Software Developer",
            "React Developer",
            "Node.js Developer"
        ]
    }}

    Resume:

    {resume_text}
    """

    completion = client.chat.completions.create(

        model="llama-3.3-70b-versatile",

        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],

        temperature=0
    )

    result = completion.choices[0].message.content

    return result

# =========================
# FETCH JOBS
# =========================

def fetch_jobs(role, location):

    query = f"{role} jobs in {location}"

    url = "https://jsearch.p.rapidapi.com/search"

    querystring = {
        "query": query,
        "page": "1",
        "num_pages": "1",
        "page_size": "5"
    }

    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": RAPIDAPI_HOST
    }

    response = requests.get(
        url,
        headers=headers,
        params=querystring
    )

    results = []

    if response.status_code == 200:

        data = response.json()

        for job in data.get("data", [])[:5]:

            results.append({

                "title": job.get(
                    "job_title",
                    "N/A"
                ),

                "company": job.get(
                    "employer_name",
                    "Unknown"
                ),

                "location": f"""
                {job.get('job_city', '')},
                {job.get('job_country', '')}
                """.strip(),

                "link": job.get(
                    "job_apply_link",
                    "#"
                )
            })

    return results

# =========================
# ANALYZE RESUME
# =========================

@app.post("/analyze")
async def analyze_resume(
    file: UploadFile = File(...)
):
    try:

        content = await file.read()

        resume_text = extract_text_from_pdf(content)

        ai_result = extract_skills_and_roles(
            resume_text
        )

        ai_result = ai_result.replace(
            "```json",
            ""
        ).replace(
            "```",
            ""
        ).strip()

        parsed = json.loads(ai_result)

        return {
            "skills": parsed.get(
                "skills",
                {}
            ),
            "roles": parsed.get(
                "roles",
                []
            )
        }

    except Exception as e:

        return {
            "error": str(e)
        }
    
@app.get("/fetch-jobs")
def get_jobs(
    role: str,
    location: str
):

    jobs = fetch_jobs(
        role,
        location
    )

    return {
        "jobs": jobs
    }