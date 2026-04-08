# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""
Data models for the Cv Bot Environment - Resume Optimization Version.

Each step() performs one job application + RL learning iteration.
"""

from openenv.core.env_server.types import Action, Observation
from pydantic import Field
from typing import List, Dict, Optional


class CvBotAction(Action):
    """Action for initializing the Cv Bot environment with resume data.

    Used in reset() to set up the resume for optimization.
    """

    skills: List[str] = Field(default_factory=list, description="Resume skills")
    experience_years: int = Field(default=0, description="Years of experience")
    summary: str = Field(default="", description="Professional summary")
    projects: List[str] = Field(default_factory=list, description="Projects")
    education: List[str] = Field(default_factory=list, description="Education")
    keywords: List[str] = Field(default_factory=list, description="Keywords")
    target_role: str = Field(default="Software Engineer", description="Target job role")


class CvBotObservation(Observation):
    """Observation from the Cv Bot environment - resume optimization results.

    Each step() returns results from one job application + learning.
    """

    ats_score: float = Field(default=0.0, description="ATS score for current job")
    application_result: str = Field(
        default="pending", description="selected, rejected, or pending"
    )
    matched_skills: List[str] = Field(
        default_factory=list, description="Skills that matched"
    )
    missing_skills: List[str] = Field(
        default_factory=list, description="Missing skills"
    )
    job_company: str = Field(default="", description="Company name")
    job_title: str = Field(default="", description="Job title")
    suggested_improvement: Optional[Dict] = Field(
        default=None, description="Improvement suggestion if rejected"
    )
    iteration_count: int = Field(default=0, description="Total iterations run")
    total_selected: int = Field(default=0, description="Total selected count")
    total_rejected: int = Field(default=0, description="Total rejected count")
    best_ats_sofar: float = Field(default=0.0, description="Best ATS score achieved")
    resume_skills: List[str] = Field(
        default_factory=list, description="Current resume skills"
    )
    resume_summary: str = Field(default="", description="Current resume summary")
    step_reward: float = Field(default=0.0, description="RL reward for this step")
    done: bool = Field(default=False, description="Whether to end episode")
    metadata: Dict = Field(default_factory=dict, description="Additional metadata")
