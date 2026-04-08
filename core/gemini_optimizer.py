from google import genai
from typing import List, Dict, Optional
import json

try:
    from config.gemini_config import (
        GEMINI_MODEL,
        GEMINI_API_KEY,
        MAX_TOKENS,
        TEMPERATURE,
    )
except ImportError:
    import os
    from dotenv import load_dotenv

    load_dotenv()
    GEMINI_MODEL = "gemini-2.5-pro"
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    MAX_TOKENS = 8192
    TEMPERATURE = 0.7

try:
    from utils.logger import setup_logger
except ImportError:
    import logging

    def setup_logger(name):
        logger = logging.getLogger(name)
        if not logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(
                logging.Formatter(
                    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                )
            )
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger


logger = setup_logger("gemini_optimizer")


class GeminiOptimizer:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or GEMINI_API_KEY
        self.model_name = GEMINI_MODEL
        self.max_tokens = MAX_TOKENS
        self.temperature = TEMPERATURE

        if not self.api_key:
            logger.warning("No Gemini API key provided - using mock mode")
            self.client = None
        else:
            self.client = genai.Client(api_key=self.api_key)

    def evaluate_resume_for_job(
        self,
        resume_text: str,
        job_description: str,
        job_required_skills: List[str],
        job_preferred_skills: List[str],
        job_experience_min: int,
    ) -> Dict:
        """Evaluate resume against job using strict RAG-style prompt"""

        prompt = f"""You are an ATS (Applicant Tracking System) resume screening expert. Your job is to FAIRLY and ACCURATELY evaluate if a resume matches a job description.

CONTEXT:
- You are a traditional ATS system that existed before AI
- Be strict but fair - don't reject good candidates, don't pass unqualified ones
- Evaluate based on REAL match, not keyword stuffing

RESUME:
{resume_text}

JOB DESCRIPTION:
{job_description}

JOB REQUIREMENTS:
- Required Skills: {", ".join(job_required_skills)}
- Preferred Skills: {", ".join(job_preferred_skills)}
- Minimum Experience: {job_experience_min} years

INSTRUCTIONS:
1. Analyze the resume thoroughly
2. Check if required skills are present (exact or close match)
3. Check if preferred skills are present  
4. Verify experience level
5. Consider overall qualifications

OUTPUT (JSON only):
{{
    "decision": "selected" or "rejected",
    "ats_score": 0-100 (based on match quality),
    "reason": "detailed explanation of why selected or rejected",
    "matched_skills": ["list of skills that match"],
    "missing_skills": ["list of required skills missing"],
    "experience_match": "meets/partial/does_not_meet experience requirement"
}}

SCORING GUIDELINES:
- 90-100: Excellent match, almost all required skills + good experience
- 75-89: Good match, most required skills met
- 60-74: Partial match, some required skills missing but acceptable
- 40-59: Weak match, significant skills missing
- 0-39: Poor match, major requirements not met

DECISION RULES:
- If missing 3+ required skills -> reject
- If experience doesn't meet minimum -> reject
- If ats_score < 50 -> reject
- Otherwise evaluate holistically"""

        if not self.client:
            return {
                "decision": "selected",
                "ats_score": 75,
                "reason": "Mock evaluation (no API key)",
                "matched_skills": job_required_skills[:3]
                if job_required_skills
                else [],
                "missing_skills": [],
                "experience_match": "meets",
            }

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config={
                    "temperature": 0.2,
                    "max_output_tokens": 2000,
                    "response_mime_type": "application/json",
                },
            )

            text: str = response.text if response.text else ""
            if not text:
                return {
                    "decision": "selected",
                    "ats_score": 75,
                    "reason": "Could not parse response",
                    "matched_skills": [],
                    "missing_skills": [],
                    "experience_match": "meets",
                }
            return json.loads(text)

        except Exception as e:
            logger.error(f"Gemini evaluation error: {e}")
            return {
                "decision": "selected",
                "ats_score": 70,
                "reason": f"API error, defaulting to selected: {str(e)}",
                "matched_skills": [],
                "missing_skills": [],
                "experience_match": "meets",
            }

    def suggest_improvements(
        self, resume_state: Dict, job_requirements: Dict, feedback: str
    ) -> List[Dict]:
        if not self.client:
            return self._mock_suggest_improvements(resume_state, job_requirements)

        prompt = f"""You are an expert career consultant. Based on the job rejection feedback, suggest targeted improvements for this resume.

Current Resume State:
- Skills: {resume_state.get("skills", [])}
- Summary: {resume_state.get("summary", "")}
- Experience: {resume_state.get("experience_years", 0)} years

Job Requirements:
- Required Skills: {job_requirements.get("required_skills", [])}
- Preferred Skills: {job_requirements.get("preferred_skills", [])}
- Experience Min: {job_requirements.get("experience_min", 0)} years

Rejection Feedback: {feedback}

Generate 3-5 targeted recommendations that:
1. Add missing skills from job requirements
2. Improve summary to match job
3. Quantify achievements where possible
4. Add relevant keywords

Return JSON array with each recommendation having:
- "action": the type of change (add_skill, modify_summary, quantify_experience, etc.)
- "description": detailed description of the change
- "priority": high/medium/low
- "content": the actual content to add/modify"""

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config={
                    "temperature": self.temperature,
                    "max_output_tokens": self.max_tokens,
                    "response_mime_type": "application/json",
                },
            )

            text: str = response.text if response.text else ""
            if not text:
                return self._mock_suggest_improvements(resume_state, job_requirements)
            return json.loads(text)
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            return self._mock_suggest_improvements(resume_state, job_requirements)

    def _mock_suggest_improvements(
        self, resume_state: Dict, job_requirements: Dict
    ) -> List[Dict]:
        required_skills = job_requirements.get("required_skills", [])
        current_skills = set(s.lower() for s in resume_state.get("skills", []))
        missing = [s for s in required_skills if s.lower() not in current_skills]

        return [
            {
                "action": "add_skill",
                "description": "Add missing technical skills",
                "priority": "high",
                "content": missing[:3] if missing else ["AWS", "Docker"],
            },
            {
                "action": "modify_summary",
                "description": "Update summary to match role",
                "priority": "medium",
                "content": "Experienced developer with strong technical background...",
            },
            {
                "action": "add_keyword",
                "description": "Add relevant keywords",
                "priority": "medium",
                "content": required_skills[:2]
                if required_skills
                else ["Agile", "CI/CD"],
            },
        ]

    def parse_resume_with_gemini(self, resume_text: str) -> Dict:
        """Parse resume completely using Gemini - extract all fields"""

        prompt = f"""Read the resume below carefully and extract ALL information.

RESUME CONTENT:
{resume_text[:15000]}

Extract into this JSON format (use EXACT field names):
{{
    "name": "",
    "email": "",
    "phone": "",
    "summary": "",
    "skills": [],
    "experience_years": 0.0,
    "experience": [
        {{"company": "", "title": "", "start_date": "", "end_date": "", "duration_months": 0, "responsibilities": []}}
    ],
    "education": [{{"degree": "", "field": "", "university": "", "year": ""}}],
    "projects": [{{"name": "", "description": "", "technologies": []}}],
    "certifications": [],
    "languages": [],
    "keywords": []
}}

EXPERIENCE CALCULATION - VERY IMPORTANT:
- Current date is April 2026
- For each job: find start_date and end_date from the resume
- Calculate duration in months: (end_year - start_year) * 12 + (end_month - start_month)
- If end_date = "Present" or "Current" or similar, use April 2026 as end date
- Sum up all job durations in months
- experience_years = round(total_months / 12, 1)
- Example: 38 months = round(3.167, 1) = 3.2 years
- Example: 40 months = round(3.333, 1) = 3.3 years

Return ONLY valid JSON, no explanations."""

        if not self.client:
            return {
                "name": "John Doe",
                "email": "john@example.com",
                "skills": ["Python", "Java", "SQL"],
                "experience_years": 3,
                "summary": "Experienced developer",
            }

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config={
                    "temperature": 0.2,
                    "max_output_tokens": 6000,
                },
            )

            text: str = response.text if response.text else ""
            if not text:
                return {"error": "Empty response from API"}

            logger.info(f"Raw response: {text[:1500]}")

            text = text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()

            try:
                parsed = json.loads(text)
                return parsed
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error: {e}, trying to fix...")
                try:
                    text_fixed = text + "]}"
                    parsed = json.loads(text_fixed)
                    return parsed
                except:
                    return {
                        "error": f"Could not parse JSON: {str(e)}",
                        "raw": text[:500],
                    }
        except Exception as e:
            logger.error(f"Gemini parse error: {e}")
            return {"error": str(e)}
