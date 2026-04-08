# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""
Cv Bot Environment Implementation - Resume Optimization with RL.

Each step() performs one job application + RL learning iteration.
The Q-table "brain" learns which resume improvements work best.
"""

import json
import sys
from uuid import uuid4

try:
    from openenv.core.env_server.interfaces import Environment
    from openenv.core.env_server.types import State
except ImportError:

    class Environment:
        SUPPORTS_CONCURRENT_SESSIONS = True

    class State:
        pass


try:
    from cv_bot.models import CvBotAction, CvBotObservation
except ImportError:
    pass

try:
    from cv_bot.core.gemini_optimizer import GeminiOptimizer
    from cv_bot.core.job_environment import JobEnvironment
    from cv_bot.core.rl_agent import RLAgent, AVAILABLE_ACTIONS
    from cv_bot.core.resume_manager import ResumeManager
    from cv_bot.config.gemini_config import GEMINI_API_KEY
except ImportError:
    pass


class CvBotEnvironment(Environment):
    """
    Resume Optimization Environment with Q-Learning Brain.

    Each step() = one job application + RL learning iteration.
    The Q-table learns which resume improvements lead to job selection.

    Example:
        >>> env = CvBotEnvironment()
        >>>
        >>> # Initialize with resume data
        >>> action = CvBotAction(
        ...     skills=["Python", "Java"],
        ...     experience_years=3,
        ...     summary="Experienced developer",
        ...     target_role="Software Engineer"
        ... )
        >>> obs = env.reset(action)
        >>> print(f"Initialized: {obs.iteration_count} iterations")
        >>>
        >>> # Apply to job - one iteration
        >>> obs = env.step()
        >>> print(f"Job: {obs.job_title} at {obs.job_company}")
        >>> print(f"Result: {obs.application_result}, ATS: {obs.ats_score}")
        >>> print(f"Skills now: {obs.resume_skills}")
        >>>
        >>> # Another iteration - brain learns more
        >>> obs = env.step()
        >>> print(f"Result: {obs.application_result}, Selected: {obs.total_selected}")
    """

    SUPPORTS_CONCURRENT_SESSIONS = True

    def __init__(self):
        self._state = State(episode_id=str(uuid4()), step_count=0)

        self.gemini = GeminiOptimizer(GEMINI_API_KEY)
        self.rl_agent = RLAgent()
        self.job_environment = None
        self.resume_manager = ResumeManager()

        self._iteration_count = 0
        self._total_selected = 0
        self._total_rejected = 0
        self._best_ats = 0.0
        self._current_ats = 0.0
        self._initialized = False

    def reset(
        self,
        action: CvBotAction = None,
        seed: int = None,
        episode_id: str = None,
        **kwargs,
    ) -> CvBotObservation:
        """
        Initialize/reset the environment with resume data.

        Args:
            action: CvBotAction containing resume data (skills, experience, etc.)
            seed: Random seed (optional)
            episode_id: Episode ID (optional)

        Returns:
            CvBotObservation with initial state
        """
        self._state = State(episode_id=episode_id or str(uuid4()), step_count=0)
        self._iteration_count = 0
        self._total_selected = 0
        self._total_rejected = 0
        self._best_ats = 0.0

        self.rl_agent.reset()

        # Handle both dict (from HTTP API) and CvBotAction object (from Python client)
        if action:
            if isinstance(action, dict):
                target_role = action.get("target_role") or "Software Engineer"
                skills = action.get("skills") or []
                experience_years = action.get("experience_years") or 0
                summary = action.get("summary") or ""
                projects = action.get("projects") or []
                education = action.get("education") or []
                keywords = action.get("keywords") or action.get("skills") or []
            else:
                target_role = action.target_role or "Software Engineer"
                skills = action.skills or []
                experience_years = action.experience_years or 0
                summary = action.summary or ""
                projects = action.projects or []
                education = action.education or []
                keywords = action.keywords or action.skills or []

            self.resume_manager.create_resume_from_data(
                skills=skills,
                experience_years=experience_years,
                summary=summary,
                projects=projects,
                education=education,
                keywords=keywords,
            )
        else:
            target_role = "Software Engineer"

        self.job_environment = JobEnvironment(
            target_role=target_role, selected_jobs=[target_role]
        )

        self._initialized = True

        # Get skills and summary for observation (handle dict or object)
        if action:
            if isinstance(action, dict):
                resume_skills = action.get("skills") or []
                resume_summary = action.get("summary") or ""
            else:
                resume_skills = action.skills or []
                resume_summary = action.summary or ""
        else:
            resume_skills = []
            resume_summary = ""

        return CvBotObservation(
            ats_score=0.0,
            application_result="pending",
            matched_skills=[],
            missing_skills=[],
            job_company="",
            job_title="",
            suggested_improvement=None,
            iteration_count=0,
            total_selected=0,
            total_rejected=0,
            best_ats_sofar=0.0,
            resume_skills=resume_skills,
            resume_summary=resume_summary,
            reward=0.0,
            done=False,
            metadata={
                "message": "Resume optimization environment ready. Call step() to apply to jobs."
            },
        )

    def step(self, action: CvBotAction = None) -> CvBotObservation:
        """
        Execute one iteration: apply to job + learn.

        Each step() performs:
        1. Generate a dummy job
        2. Evaluate resume against job (Gemini)
        3. Get ats_score + decision
        4. If rejected, get improvement suggestions
        5. Update resume
        6. Update Q-table (learning!)
        7. Return observation

        Args:
            action: Optional action (not used in current implementation)

        Returns:
            CvBotObservation with job application results
        """
        print("=== STEP START ===", flush=True)

        if not self._initialized:
            print("=== STEP: Not initialized, calling reset", flush=True)
            default_action = CvBotAction(
                skills=["Python", "JavaScript"],
                experience_years=2,
                summary="Developer",
                target_role="Software Engineer",
            )
            return self.reset(default_action)

        self._state.step_count += 1
        self._iteration_count += 1

        job = self.job_environment.generate_dummy_job()
        print(f"=== STEP: Generated job: {job.title} at {job.company}", flush=True)

        resume = self.resume_manager.get_current_state()
        resume_text = json.dumps(
            {
                "skills": resume.skills,
                "experience_years": resume.experience_years,
                "summary": resume.summary,
                "keywords": resume.keywords,
            }
        )
        print(f"=== STEP: resume_text={resume_text[:100]}...", flush=True)

        evaluation = self.gemini.evaluate_resume_for_job(
            resume_text=resume_text,
            job_description=job.description,
            job_required_skills=job.required_skills,
            job_preferred_skills=job.preferred_skills,
            job_experience_min=job.experience_min,
        )
        print(f"=== STEP: Got evaluation: {evaluation}", flush=True)

        ats_score = evaluation.get("ats_score", 50)
        decision = evaluation.get("decision", "rejected")
        print(f"=== STEP: Decision={decision}, ATS={ats_score}", flush=True)
        matched_skills = evaluation.get("matched_skills", [])
        missing_skills = evaluation.get("missing_skills", [])
        reason = evaluation.get("reason", "")

        if ats_score > self._best_ats:
            ats_improvement = ats_score - self._best_ats
            self._best_ats = ats_score
        else:
            ats_improvement = 0

        previous_ats = self._current_ats
        self._current_ats = ats_score

        reward = self.rl_agent.calculate_reward(
            decision,
            ats_improvement,
            0,
            ats_score,
            self._iteration_count,
            previous_ats,
        )

        suggested_improvement = None
        if decision == "rejected":
            job_requirements = {
                "required_skills": job.required_skills,
                "preferred_skills": job.preferred_skills,
                "experience_min": job.experience_min,
            }

            suggestions = self.gemini.suggest_improvements(
                resume_state={
                    "skills": resume.skills,
                    "summary": resume.summary,
                    "experience_years": resume.experience_years,
                },
                job_requirements=job_requirements,
                feedback=reason,
            )

            if suggestions:
                self.resume_manager.update_resume(suggestions, ats_score)
                suggested_improvement = suggestions[0] if suggestions else None

        if decision == "selected":
            self._total_selected += 1
        elif decision == "rejected":
            self._total_rejected += 1

        state_key = resume.get_features()
        next_state_key = state_key

        self.rl_agent.update_q_value(
            state_key=state_key,
            action=decision,
            reward=reward,
            next_state_key=next_state_key,
            available_actions=AVAILABLE_ACTIONS,
        )

        self.rl_agent.decay_exploration()

        current_resume = self.resume_manager.get_current_state()

        return CvBotObservation(
            ats_score=ats_score,
            application_result=decision,
            matched_skills=matched_skills,
            missing_skills=missing_skills,
            job_company=job.company,
            job_title=job.title,
            suggested_improvement=suggested_improvement,
            iteration_count=self._iteration_count,
            total_selected=self._total_selected,
            total_rejected=self._total_rejected,
            best_ats_sofar=self._best_ats,
            resume_skills=current_resume.skills,
            resume_summary=current_resume.summary,
            step_reward=reward,
            done=False,
            metadata={
                "reason": reason,
                "exploration_rate": self.rl_agent.exploration_rate,
                "q_table_size": len(self.rl_agent.q_table),
            },
        )

    @property
    def state(self) -> State:
        return self._state
