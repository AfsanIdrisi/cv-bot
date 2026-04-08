from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
RESUMES_DIR = BASE_DIR / "outputs" / "resumes"
LOGS_DIR = BASE_DIR / "outputs" / "logs"

RESUMES_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

SUPPORTED_FORMATS = [".pdf", ".docx", ".txt"]
MAX_FILE_SIZE = 10 * 1024 * 1024
MAX_RESUME_VERSIONS = 50
