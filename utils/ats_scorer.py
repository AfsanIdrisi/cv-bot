from typing import List, Set

try:
    from models.job import JobState
    from models.resume import ResumeState
except ImportError:
    from dataclasses import dataclass, field
    from datetime import datetime
    import uuid

    @dataclass
    class JobState:
        job_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
        title: str = ""
        company: str = ""
        required_skills: List[str] = field(default_factory=list)
        preferred_skills: List[str] = field(default_factory=list)
        experience_min: int = 0
        keywords: List[str] = field(default_factory=list)
        description: str = ""
        created_at: datetime = field(default_factory=datetime.now)

        def get_all_required_keywords(self) -> List[str]:
            return list(set(self.required_skills + self.keywords))

    @dataclass
    class ResumeState:
        version: int = 1
        skills: List[str] = field(default_factory=list)
        experience_years: int = 0
        summary: str = ""
        projects: List[str] = field(default_factory=list)
        education: List[str] = field(default_factory=list)
        keywords: List[str] = field(default_factory=list)
        format_score: float = 0.0
        ats_score: float = 0.0
        raw_text: str = ""


def calculate_ats_score(resume: ResumeState, job: JobState) -> float:
    if not job.required_skills:
        return 50.0

    resume_skills_set = set(s.lower() for s in resume.skills)
    required_set = set(s.lower() for s in job.required_skills)
    preferred_set = set(s.lower() for s in job.preferred_skills)

    if not required_set:
        return 50.0

    matched_required = len(resume_skills_set & required_set)
    required_match_score = (matched_required / len(required_set)) * 70

    matched_preferred = len(resume_skills_set & preferred_set) if preferred_set else 0
    preferred_match_score = (
        (matched_preferred / len(preferred_set)) * 15 if preferred_set else 0
    )

    exp_score = 0
    if resume.experience_years >= job.experience_min:
        exp_score = 15
    else:
        exp_score = (
            (resume.experience_years / job.experience_min) * 15
            if job.experience_min > 0
            else 15
        )

    keyword_match = 0
    if job.keywords:
        keyword_set = set(s.lower() for s in job.keywords)
        matched_keywords = len(resume_skills_set & keyword_set)
        keyword_match = (matched_keywords / len(keyword_set)) * 10

    total_score = min(
        100.0, required_match_score + preferred_match_score + exp_score + keyword_match
    )
    return round(total_score, 2)


def calculate_keyword_match(resume: ResumeState, job: JobState) -> float:
    all_job_keywords = set(s.lower() for s in job.get_all_required_keywords())
    resume_keywords = set(s.lower() for s in resume.keywords)

    if not all_job_keywords:
        return 50.0

    matched = len(all_job_keywords & resume_keywords)
    return round((matched / len(all_job_keywords)) * 100, 2)


def get_missing_keywords(resume: ResumeState, job: JobState) -> List[str]:
    resume_skills_lower = set(s.lower() for s in resume.skills)
    all_job_keywords = set(s.lower() for s in job.get_all_required_keywords())
    missing = all_job_keywords - resume_skills_lower
    return list(missing)


def simulate_application_result(ats_score: float, match_score: float) -> str:
    combined_score = (ats_score * 0.6) + (match_score * 0.4)

    if combined_score >= 75:
        return "selected"
    elif combined_score >= 50:
        return "pending"
    else:
        return "rejected"
