import json
from pathlib import Path
from typing import Optional, List
from datetime import datetime

try:
    from models.resume import ResumeState
except ImportError:
    from dataclasses import dataclass, field
    from typing import Dict

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
        created_at: datetime = field(default_factory=datetime.now)

        def to_dict(self) -> Dict:
            return {
                "version": self.version,
                "skills": self.skills,
                "experience_years": self.experience_years,
                "summary": self.summary,
                "projects": self.projects,
                "education": self.education,
                "keywords": self.keywords,
                "format_score": self.format_score,
                "ats_score": self.ats_score,
                "created_at": self.created_at.isoformat(),
            }

        def get_features(self) -> str:
            return (
                ",".join(sorted(self.skills))
                + f"|{self.experience_years}|{self.summary[:50] if self.summary else ''}"
            )


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


logger = setup_logger("resume_manager")


class ResumeManager:
    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = output_dir or Path("outputs/resumes")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.current_resume: Optional[ResumeState] = None
        self.resume_history: List[ResumeState] = []
        self.best_resume: Optional[ResumeState] = None

    def create_resume_from_data(
        self,
        skills: List[str],
        experience_years: int,
        summary: str,
        projects: List[str] = None,
        education: List[str] = None,
        keywords: List[str] = None,
    ) -> ResumeState:
        resume = ResumeState(
            version=1,
            skills=skills,
            experience_years=experience_years,
            summary=summary,
            projects=projects or [],
            education=education or [],
            keywords=keywords or skills,
            raw_text=json.dumps(
                {
                    "skills": skills,
                    "experience_years": experience_years,
                    "summary": summary,
                }
            ),
        )

        self.current_resume = resume
        self.resume_history.append(resume)
        self.best_resume = resume

        logger.info(
            f"Resume created: v{resume.version}, {len(resume.skills)} skills, {resume.experience_years} years exp"
        )

        return resume

    def update_resume(self, improvements: List[dict], ats_score: float) -> ResumeState:
        if not self.current_resume:
            raise ValueError("No resume loaded")

        old_resume = self.current_resume
        new_version = old_resume.version + 1

        new_skills = list(old_resume.skills)
        new_summary = old_resume.summary
        new_keywords = list(old_resume.keywords)

        for imp in improvements:
            action = imp.get("action", "")
            content = imp.get("content", "")

            if action == "add_skill" and content:
                if isinstance(content, list):
                    new_skills.extend([str(s).strip() for s in content])
                else:
                    new_skills.extend([s.strip() for s in str(content).split(",")])
            elif action == "modify_summary" and content:
                new_summary = content if isinstance(content, str) else str(content)
            elif action == "add_keyword" and content:
                if isinstance(content, list):
                    new_keywords.extend([str(s).strip() for s in content])
                else:
                    new_keywords.extend([s.strip() for s in str(content).split(",")])

        new_skills = list(set(new_skills))
        new_keywords = list(set(new_keywords + new_skills))

        new_resume = ResumeState(
            version=new_version,
            skills=new_skills,
            experience_years=old_resume.experience_years,
            summary=new_summary,
            projects=old_resume.projects,
            education=old_resume.education,
            keywords=new_keywords,
            ats_score=ats_score,
            raw_text=old_resume.raw_text,
        )

        self.current_resume = new_resume
        self.resume_history.append(new_resume)

        if not self.best_resume or ats_score > self.best_resume.ats_score:
            self.best_resume = new_resume

        logger.info(f"Resume updated: v{new_version}, ATS={ats_score}")

        return new_resume

    def get_current_state(self) -> ResumeState:
        if not self.current_resume:
            raise ValueError("No resume loaded")
        return self.current_resume

    def get_best_resume(self) -> Optional[ResumeState]:
        return self.best_resume

    def save_resume(self, filename: Optional[str] = None) -> str:
        if not self.current_resume:
            raise ValueError("No resume to save")

        if not filename:
            filename = f"resume_v{self.current_resume.version}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        filepath = self.output_dir / filename

        with open(filepath, "w") as f:
            json.dump(self.current_resume.to_dict(), f, indent=2)

        logger.info(f"Resume saved to: {filepath}")
        return str(filepath)

    def reset(self):
        self.current_resume = None
        self.resume_history = []
        self.best_resume = None
