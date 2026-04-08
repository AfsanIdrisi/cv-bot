from dataclasses import dataclass, field
from typing import List, Dict
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

    def to_dict(self) -> Dict:
        return {
            "job_id": self.job_id,
            "title": self.title,
            "company": self.company,
            "required_skills": self.required_skills,
            "preferred_skills": self.preferred_skills,
            "experience_min": self.experience_min,
            "keywords": self.keywords,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
        }

    def get_features(self) -> str:
        features = f"title:{self.title}"
        features += f"|req_skills:{','.join(sorted(self.required_skills))}"
        features += f"|pref_skills:{','.join(sorted(self.preferred_skills))}"
        features += f"|exp:{self.experience_min}"
        return features

    def get_all_required_keywords(self) -> List[str]:
        return list(set(self.required_skills + self.keywords))
