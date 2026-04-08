import os
import re
from pathlib import Path
from typing import Tuple
import pdfplumber
from docx import Document


def extract_text_from_file(file_path: str) -> Tuple[str, str]:
    ext = Path(file_path).suffix.lower()

    if ext == ".pdf":
        return extract_text_from_pdf(file_path), ext
    elif ext == ".docx":
        return extract_text_from_docx(file_path), ext
    elif ext == ".txt":
        return extract_text_from_txt(file_path), ext
    else:
        raise ValueError(f"Unsupported file format: {ext}")


def extract_text_from_pdf(file_path: str) -> str:
    text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text


def extract_text_from_docx(file_path: str) -> str:
    doc = Document(file_path)
    text = ""
    for para in doc.paragraphs:
        text += para.text + "\n"
    return text


def extract_text_from_txt(file_path: str) -> str:
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


def extract_skills(text: str) -> list:
    skill_patterns = [
        r"Python|Java|JavaScript|TypeScript|C\+\+|C#|Go|Rust|React|Angular|Vue",
        r"Node\.js|Express|Django|Flask|FastAPI|Spring",
        r"SQL|NoSQL|MongoDB|PostgreSQL|MySQL|Redis",
        r"AWS|Azure|GCP|Docker|Kubernetes|Jenkins",
        r"Machine Learning|Deep Learning|TensorFlow|PyTorch",
        r"Git|DevOps|Agile|Scrum|CI/CD",
        r"Data Analysis|Data Science|Statistics|Excel",
        r"REST API|GraphQL|Microservices",
    ]

    skills = []
    for pattern in skill_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        skills.extend([s.strip() for s in matches])

    return list(set(skills))


def extract_experience_years(text: str) -> int:
    from datetime import datetime

    current_year = datetime.now().year

    patterns = [
        r"(\d+)\+?\s*(?:years?|yrs?)\s*(?:of\s*)?experience",
        r"(\d+)\+?\s*(?:years?|yrs?)",
        r"experience[:\s]+(\d+)\+?",
    ]

    years = []
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        years.extend([int(m) for m in matches])

    if years:
        return max(years)

    date_patterns = [
        r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+(\d{4})\s*[--to]+\s*(?:(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+)?(\d{4}|Present|Current)",
        r"(\d{4})\s*[--to]+\s*(\d{4}|Present|Current)",
        r"(\d{4})\s*-\s*(?:Present|Current)",
    ]

    total_months = 0
    for pattern in date_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            start_year = int(match[0])
            end_year = (
                current_year
                if len(match) > 1 and match[1].lower() in ["present", "current"]
                else int(match[1])
                if len(match) > 1
                else current_year
            )
            if end_year > start_year:
                total_months += (end_year - start_year) * 12

    if total_months > 0:
        return round(total_months / 12)

    return 0
