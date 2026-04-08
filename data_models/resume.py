from dataclasses import dataclass, field
from typing import List, Dict
from datetime import datetime


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
        features = f"skills:{','.join(sorted(self.skills))}"
        features += f"|exp:{self.experience_years}"
        features += f"|keywords:{','.join(sorted(self.keywords))}"
        return features
