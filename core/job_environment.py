from typing import List, Dict, Optional
import random

try:
    from models.job import JobState
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


logger = setup_logger("job_environment")

ROLE_SKILLS = {
    "Software Engineer": {
        "required": ["Python", "Java", "JavaScript", "SQL", "Git", "REST API"],
        "preferred": ["AWS", "Docker", "React", "Node.js", "Agile", "CI/CD", "MongoDB"],
    },
    "Data Scientist": {
        "required": [
            "Python",
            "Machine Learning",
            "SQL",
            "Statistics",
            "Data Analysis",
        ],
        "preferred": ["TensorFlow", "PyTorch", "AWS", "Tableau", "R", "Deep Learning"],
    },
    "DevOps Engineer": {
        "required": ["AWS", "Docker", "Kubernetes", "CI/CD", "Git", "Linux"],
        "preferred": ["Terraform", "Jenkins", "Azure", "GCP", "Ansible", "Python"],
    },
    "Full Stack Developer": {
        "required": ["JavaScript", "React", "Node.js", "SQL", "Git", "REST API"],
        "preferred": ["AWS", "MongoDB", "TypeScript", "Docker", "GraphQL", "Python"],
    },
    "Frontend Developer": {
        "required": ["JavaScript", "React", "HTML", "CSS", "Git"],
        "preferred": ["TypeScript", "Vue.js", "Angular", "REST API", "Webpack"],
    },
    "Backend Developer": {
        "required": ["Python", "Java", "SQL", "Git", "REST API"],
        "preferred": ["Spring", "Django", "Node.js", "MongoDB", "PostgreSQL", "Docker"],
    },
    "Machine Learning Engineer": {
        "required": [
            "Python",
            "Machine Learning",
            "TensorFlow",
            "SQL",
            "Deep Learning",
        ],
        "preferred": [
            "PyTorch",
            "AWS",
            "Kubernetes",
            "Docker",
            "Scikit-learn",
            "Spark",
        ],
    },
    "Data Analyst": {
        "required": ["SQL", "Excel", "Python", "Data Analysis", "Statistics"],
        "preferred": ["Tableau", "PowerBI", "R", "AWS", "Excel VBA"],
    },
    "Product Manager": {
        "required": ["Agile", "Scrum", "Product Management", "Communication"],
        "preferred": ["SQL", "Jira", "Confluence", "Google Analytics", "Python"],
    },
}

TECH_SKILLS = [
    "Python",
    "Java",
    "JavaScript",
    "TypeScript",
    "C++",
    "C#",
    "Go",
    "Rust",
    "Ruby",
    "PHP",
    "React",
    "Angular",
    "Vue",
    "Node.js",
    "Django",
    "Flask",
    "Spring",
    "Express",
    "SQL",
    "NoSQL",
    "MongoDB",
    "PostgreSQL",
    "MySQL",
    "Redis",
    "Elasticsearch",
    "AWS",
    "Azure",
    "GCP",
    "Docker",
    "Kubernetes",
    "Jenkins",
    "Terraform",
    "Machine Learning",
    "Deep Learning",
    "TensorFlow",
    "PyTorch",
    "Scikit-learn",
    "Git",
    "DevOps",
    "Agile",
    "Scrum",
    "CI/CD",
    "REST API",
    "GraphQL",
    "Data Analysis",
    "Data Science",
    "Statistics",
    "Excel",
    "PowerBI",
    "Tableau",
    "Linux",
    "Spark",
    "Hadoop",
    "Kafka",
    "FastAPI",
]

JOB_TITLES = [
    "Software Engineer",
    "Senior Software Engineer",
    "Full Stack Developer",
    "Frontend Developer",
    "Backend Developer",
    "DevOps Engineer",
    "Data Scientist",
    "Machine Learning Engineer",
    "Data Analyst",
    "Product Manager",
    "QA Engineer",
]

COMPANY_PREFIXES = [
    "Tech",
    "Cloud",
    "Data",
    "AI",
    "Digital",
    "Smart",
    "Cyber",
    "Global",
    "Next",
    "Future",
]
COMPANY_SUFFIXES = [
    "Solutions",
    "Systems",
    "Technologies",
    "Innovations",
    "Labs",
    "Corp",
    "Works",
    "Soft",
]


class JobEnvironment:
    def __init__(
        self,
        target_role: Optional[str] = None,
        selected_jobs: Optional[List[str]] = None,
    ):
        self.target_role = target_role or "Software Engineer"
        self.selected_jobs = selected_jobs or [self.target_role]
        self.job_history: List[JobState] = []

        self.role_skills = ROLE_SKILLS.get(
            self.target_role, ROLE_SKILLS["Software Engineer"]
        )

    def generate_dummy_job(self) -> JobState:
        chosen_role = random.choice(self.selected_jobs)

        role_skills = ROLE_SKILLS.get(chosen_role, ROLE_SKILLS["Software Engineer"])

        role_required = role_skills.get(
            "required", ROLE_SKILLS["Software Engineer"]["required"]
        )
        role_preferred = role_skills.get(
            "preferred", ROLE_SKILLS["Software Engineer"]["preferred"]
        )

        num_required = min(len(role_required), random.randint(3, 5))
        required_skills = random.sample(role_required, num_required)

        num_preferred = min(len(role_preferred), random.randint(2, 4))
        preferred_skills = random.sample(
            [s for s in role_preferred if s not in required_skills], num_preferred
        )

        experience_min = random.randint(2, 6)

        company = f"{random.choice(COMPANY_PREFIXES)}{random.choice(COMPANY_SUFFIXES)}"

        job_description = f"""We are seeking a talented {chosen_role} to join our team.

Requirements:
- {", ".join(required_skills)}
- {experience_min}+ years of relevant experience

Preferred Skills:
- {", ".join(preferred_skills)}

Responsibilities:
- Design and develop high-quality software solutions
- Collaborate with cross-functional teams
- Participate in code reviews and agile processes"""

        job = JobState(
            title=chosen_role,
            company=company,
            required_skills=required_skills,
            preferred_skills=preferred_skills,
            experience_min=experience_min,
            keywords=required_skills + preferred_skills,
            description=job_description,
        )

        self.job_history.append(job)
        logger.info(
            f"Generated job: {job.title} at {job.company} - Skills: {required_skills}"
        )
        return job

    def get_job_stats(self) -> Dict:
        if not self.job_history:
            return {"total_jobs": 0, "avg_experience": 0}

        return {
            "total_jobs": len(self.job_history),
            "avg_experience": sum(j.experience_min for j in self.job_history)
            / len(self.job_history),
            "unique_skills": len(
                set(s for j in self.job_history for s in j.required_skills)
            ),
        }

    def reset(self):
        self.job_history = []
