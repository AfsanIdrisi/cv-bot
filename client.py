# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""Cv Bot Environment Client."""

from typing import Dict, Optional

from openenv.core import EnvClient
from openenv.core.client_types import StepResult
from openenv.core.env_server.types import State

from cv_bot.models import CvBotAction, CvBotObservation


class CvBotEnv(EnvClient[CvBotAction, CvBotObservation, State]):
    """
    Client for the Cv Bot Environment - Resume Optimization with RL.

    This client maintains a persistent WebSocket connection to the environment server,
    enabling efficient multi-step interactions with lower latency.
    Each client instance has its own dedicated environment session on the server.

    Example:
        >>> # Connect to a running server
        >>> with CvBotEnv(base_url="http://localhost:8000") as client:
        ...     # Initialize with resume data
        ...     action = CvBotAction(
        ...         skills=["Python", "Java"],
        ...         experience_years=3,
        ...         summary="Experienced developer",
        ...         target_role="Software Engineer"
        ...     )
        ...     result = client.reset(action)
        ...     print(f"Initialized: {result.observation.iteration_count} iterations")
        ...
        ...     # Apply to job - one iteration
        ...     result = client.step()
        ...     print(f"Job: {result.observation.job_title}")
        ...     print(f"Result: {result.observation.application_result}")
        ...
        ...     # Another iteration
        ...     result = client.step()
        ...     print(f"Selected: {result.observation.total_selected}")

    Example with Docker:
        >>> # Automatically start container and connect
        >>> client = CvBotEnv.from_docker_image("cv_bot-env:latest")
        >>> try:
        ...     action = CvBotAction(skills=["Python"], experience_years=2, summary="Dev")
        ...     result = client.reset(action)
        ...     result = client.step()
        ... finally:
        ...     client.close()
    """

    def _step_payload(self, action: Optional[CvBotAction]) -> Dict:
        """
        Convert CvBotAction to JSON payload for step message.

        Args:
            action: CvBotAction instance (optional for step)

        Returns:
            Dictionary representation suitable for JSON encoding
        """
        if action:
            return {
                "skills": action.skills,
                "experience_years": action.experience_years,
                "summary": action.summary,
                "projects": action.projects,
                "education": action.education,
                "keywords": action.keywords,
                "target_role": action.target_role,
            }
        return {}

    def _parse_result(self, payload: Dict) -> StepResult[CvBotObservation]:
        """
        Parse server response into StepResult[CvBotObservation].

        Args:
            payload: JSON response data from server

        Returns:
            StepResult with CvBotObservation
        """
        obs_data = payload.get("observation", {})

        observation = CvBotObservation(
            ats_score=obs_data.get("ats_score", 0.0),
            application_result=obs_data.get("application_result", "pending"),
            matched_skills=obs_data.get("matched_skills", []),
            missing_skills=obs_data.get("missing_skills", []),
            job_company=obs_data.get("job_company", ""),
            job_title=obs_data.get("job_title", ""),
            suggested_improvement=obs_data.get("suggested_improvement"),
            iteration_count=obs_data.get("iteration_count", 0),
            total_selected=obs_data.get("total_selected", 0),
            total_rejected=obs_data.get("total_rejected", 0),
            best_ats_sofar=obs_data.get("best_ats_sofar", 0.0),
            resume_skills=obs_data.get("resume_skills", []),
            resume_summary=obs_data.get("resume_summary", ""),
            step_reward=obs_data.get("step_reward", 0.0),
            done=payload.get("done", False),
            metadata=obs_data.get("metadata", {}),
        )

        return StepResult(
            observation=observation,
            reward=obs_data.get("step_reward", 0.0),
            done=payload.get("done", False),
        )

    def _parse_state(self, payload: Dict) -> State:
        """
        Parse server response into State object.

        Args:
            payload: JSON response from state request

        Returns:
            State object with episode_id and step_count
        """
        return State(
            episode_id=payload.get("episode_id"),
            step_count=payload.get("step_count", 0),
        )
