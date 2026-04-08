# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""
FastAPI application for the Cv Bot Environment.

This module creates an HTTP server that exposes the CvBotEnvironment
over HTTP and WebSocket endpoints, compatible with EnvClient.

Endpoints:
    - POST /reset: Reset the environment
    - POST /step: Execute an action
    - GET /state: Get current environment state
    - GET /schema: Get action/observation schemas
    - WS /ws: WebSocket endpoint for persistent sessions
    - POST /parse-resume: Parse resume file using Gemini

Usage:
    # Development (with auto-reload):
    uvicorn server.app:app --reload --host 0.0.0.0 --port 8000

    # Production:
    uvicorn server.app:app --host 0.0.0.0 --port 8000 --workers 4

    # Or run directly:
    python -m server.app
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, APIRouter, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import tempfile
import os
import shutil
from pathlib import Path
import uuid
import logging

# Session management - store environment instances
_sessions = {}

try:
    from openenv.core.env_server.http_server import create_app
except Exception as e:  # pragma: no cover
    raise ImportError(
        "openenv is required for the web interface. Install dependencies with '\n    uv sync\n'"
    ) from e

try:
    from cv_bot.models import CvBotAction, CvBotObservation
    from cv_bot.server.cv_bot_environment import CvBotEnvironment
    from cv_bot.core.gemini_optimizer import GeminiOptimizer
    from cv_bot.utils.file_handler import extract_text_from_file
    from cv_bot.config.gemini_config import GEMINI_API_KEY
except ImportError:
    pass


_temp_parser = None


def _get_parser():
    global _temp_parser
    if _temp_parser is None:
        _temp_parser = GeminiOptimizer(GEMINI_API_KEY)
    return _temp_parser


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _temp_parser
    _temp_parser = GeminiOptimizer(GEMINI_API_KEY)
    yield


# Create the app with web interface and README integration
base_app = create_app(
    CvBotEnvironment,
    CvBotAction,
    CvBotObservation,
    env_name="cv_bot",
    max_concurrent_envs=1,
)

app: FastAPI = FastAPI(lifespan=lifespan)

# Include all routes from base_app
app.include_router(base_app.router)


# Define custom routes after include_router
static_dir = Path(__file__).parent / "static"


@app.get("/web")
async def get_ui():
    """Serve the custom web UI."""
    static_dir = Path(__file__).parent / "static"
    index_path = static_dir / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    raise HTTPException(status_code=404, detail="UI not found")


@app.get("/web/")
async def get_ui_slash():
    """Serve the custom web UI (with trailing slash)."""
    static_dir = Path(__file__).parent / "static"
    index_path = static_dir / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    raise HTTPException(status_code=404, detail="UI not found")


@app.get("/web/{path:path}")
async def get_ui_assets(path: str):
    """Serve static assets for the UI."""
    asset_path = static_dir / path
    if asset_path.exists() and asset_path.is_file():
        return FileResponse(asset_path)
    raise HTTPException(status_code=404, detail="Asset not found")


@app.post("/parse-resume")
async def parse_resume(file: UploadFile = File(...)):
    """
    Parse a resume file (PDF, DOCX, or TXT) using Gemini.

    Extracts: name, email, phone, summary, skills, experience_years,
    experience, education, projects, certifications, languages, keywords.
    """
    filename = file.filename or "resume.pdf"
    try:
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=os.path.splitext(filename)[1]
        ) as temp_file:
            shutil.copyfileobj(file.file, temp_file)
            temp_path = temp_file.name

        try:
            resume_text, _ = extract_text_from_file(temp_path)
        finally:
            os.unlink(temp_path)

        if not resume_text or not resume_text.strip():
            raise HTTPException(
                status_code=400, detail="Could not extract text from file"
            )

        parser = _get_parser()
        parsed_data = parser.parse_resume_with_gemini(resume_text)

        if "error" in parsed_data:
            raise HTTPException(status_code=500, detail=parsed_data["error"])

        return JSONResponse(content={"success": True, "parsed": parsed_data})

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/session-reset")
async def session_reset(request_data: dict = None):
    """Custom reset that maintains session state"""
    global _sessions

    env = CvBotEnvironment()
    _sessions["current"] = env

    action = None
    if request_data and "action" in request_data:
        action = request_data["action"]

    if action and isinstance(action, dict):
        # Extract and format skills (comma-separated string to list)
        skills_input = action.get("skills", [])
        if isinstance(skills_input, str):
            skills = [s.strip() for s in skills_input.split(",") if s.strip()]
        else:
            skills = skills_input or []

        # Convert experience to integer
        exp = action.get("experience_years", 0)
        experience_years = int(exp) if exp else 0

        # Handle projects - extract names from dicts or use as-is
        projects_input = action.get("projects", [])
        projects = []
        if projects_input:
            for p in projects_input:
                if isinstance(p, dict):
                    projects.append(p.get("name", str(p)))
                elif isinstance(p, str):
                    projects.append(p)

        # Handle education - extract degrees from dicts or use as-is
        education_input = action.get("education", [])
        education = []
        if education_input:
            for e in education_input:
                if isinstance(e, dict):
                    education.append(e.get("degree", str(e)))
                elif isinstance(e, str):
                    education.append(e)

        # Keywords
        keywords_input = action.get("keywords", []) or skills

        action_obj = CvBotAction(
            skills=skills,
            experience_years=experience_years,
            summary=action.get("summary", ""),
            target_role=action.get("target_role", "Software Engineer"),
            projects=projects,
            education=education,
            keywords=keywords_input,
        )
    else:
        action_obj = CvBotAction()

    obs = env.reset(action_obj)

    return {"observation": obs.__dict__, "reward": obs.step_reward, "done": obs.done}


@app.post("/session-step")
async def session_step(request_data: dict = None):
    """Custom step that uses persistent session"""
    global _sessions

    if "current" not in _sessions:
        return {"error": "No active session. Call /session-reset first."}

    env = _sessions["current"]
    obs = env.step()

    return {"observation": obs.__dict__, "reward": obs.step_reward, "done": obs.done}


@app.get("/session-state")
async def session_state():
    """Get current session state"""
    global _sessions

    if "current" not in _sessions:
        return {"error": "No active session"}

    env = _sessions["current"]
    state = env.state

    return {"episode_id": state.episode_id, "step_count": state.step_count}


def main(host: str = "0.0.0.0", port: int = 8000):
    """
    Entry point for direct execution via uv run or python -m.

    This function enables running the server without Docker:
        uv run --project . server
        uv run --project . server --port 8001
        python -m cv_bot.server.app

    Args:
        host: Host address to bind to (default: "0.0.0.0")
        port: Port number to listen on (default: 8000)

    For production deployments, consider using uvicorn directly with
    multiple workers:
        uvicorn cv_bot.server.app:app --workers 4
    """
    import uvicorn

    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    main(port=args.port)
