"""
Inference Script for CV Bot Competition
======================================

Compatible with cv_bot RL environment for resume optimization benchmark.

STDOUT FORMAT (MANDATORY):
    [START] task=<task_name> env=<benchmark> model=<model_name>
    [STEP]  step=<n> action=<action_str> reward=<0.00> done=<true|false> error=<msg|null>
    [END]   success=<true|false> steps=<n> score=<score> rewards=<r1,r2,...,rn>

Requirements:
    - Docker container must be running: docker run -p 8000:8000 cv_bot-env
    - inference.py connects to http://localhost:8000

Environment Variables:
    MAX_STEPS     Number of steps per episode (default: 8)
    HF_TOKEN      HuggingFace token (for logs)
    MODEL_NAME    Model name for logs (default: gemini-2.5-pro)
"""

import requests
import os
from typing import List, Optional

from cv_bot.config.gemini_config import GEMINI_MODEL

API_BASE_URL = "http://localhost:8000"
MAX_STEPS = int(os.getenv("MAX_STEPS", "8"))
TASK_NAME = os.getenv("TASK_NAME", "resume_optimization")
BENCHMARK = os.getenv("BENCHMARK", "cv_bot")
MODEL_NAME = os.getenv("MODEL_NAME", GEMINI_MODEL)
SUCCESS_SCORE_THRESHOLD = 0.5

MAX_TOTAL_REWARD = MAX_STEPS * 100.0

DEFAULT_FRONTEND_RESUME = {
    "skills": ["JavaScript", "React", "HTML", "CSS", "TypeScript"],
    "experience_years": 3,
    "summary": "Frontend Developer with experience in React and modern web technologies",
    "projects": ["Portfolio Website", "E-commerce Dashboard"],
    "education": ["BS Computer Science"],
    "target_role": "Frontend Developer",
}


def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)


def log_step(
    step: int, action: str, reward: float, done: bool, error: Optional[str]
) -> None:
    error_val = error if error else "null"
    done_val = str(done).lower()
    print(
        f"[STEP] step={step} action={action} reward={reward:.2f} done={done_val} error={error_val}",
        flush=True,
    )


def log_end(success: bool, steps: int, score: float, rewards: List[float]) -> None:
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(
        f"[END] success={str(success).lower()} steps={steps} score={score:.3f} rewards={rewards_str}",
        flush=True,
    )


def main() -> None:
    rewards: List[float] = []
    steps_taken = 0
    score = 0.0
    success = False

    log_start(task=TASK_NAME, env=BENCHMARK, model=MODEL_NAME)

    try:
        reset_payload = {
            "action": {
                "skills": DEFAULT_FRONTEND_RESUME["skills"],
                "experience_years": DEFAULT_FRONTEND_RESUME["experience_years"],
                "summary": DEFAULT_FRONTEND_RESUME["summary"],
                "projects": DEFAULT_FRONTEND_RESUME["projects"],
                "education": DEFAULT_FRONTEND_RESUME["education"],
                "keywords": DEFAULT_FRONTEND_RESUME["skills"],
                "target_role": DEFAULT_FRONTEND_RESUME["target_role"],
            }
        }

        response = requests.post(
            f"{API_BASE_URL}/session-reset", json=reset_payload, timeout=30
        )
        response.raise_for_status()
        reset_data = response.json()
        print(
            f"[DEBUG] Reset done: iteration={reset_data['observation'].get('iteration_count', 0)}",
            flush=True,
        )

        for step in range(1, MAX_STEPS + 1):
            try:
                step_response = requests.post(
                    f"{API_BASE_URL}/session-step", json={}, timeout=120
                )
                step_response.raise_for_status()
                step_data = step_response.json()
            except requests.exceptions.Timeout:
                print(f"[DEBUG] Step {step} timed out, retrying...", flush=True)
                import time

                time.sleep(5)
                step_response = requests.post(
                    f"{API_BASE_URL}/session-step", json={}, timeout=180
                )
                step_response.raise_for_status()
                step_data = step_response.json()

            obs = step_data.get("observation", {})
            reward = obs.get("ats_score", 0.0)
            done = obs.get("done", False)

            job_title = obs.get("job_title", "")
            job_company = obs.get("job_company", "")
            application_result = obs.get("application_result", "pending")

            rewards.append(reward)
            steps_taken = step

            action_str = f"apply(job={job_title}, company={job_company}, ats={reward:.2f}, result={application_result})"

            log_step(step=step, action=action_str, reward=reward, done=done, error=None)

            if done:
                break

        score = sum(rewards) / MAX_TOTAL_REWARD if MAX_TOTAL_REWARD > 0 else 0.0
        score = min(max(score, 0.0), 1.0)
        success = score >= SUCCESS_SCORE_THRESHOLD

    except Exception as e:
        print(f"[DEBUG] Error: {e}", flush=True)
        success = False
    finally:
        log_end(success=success, steps=steps_taken, score=score, rewards=rewards)


if __name__ == "__main__":
    main()
