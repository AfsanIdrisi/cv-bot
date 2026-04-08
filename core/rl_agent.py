import numpy as np
from typing import Dict, Tuple, Optional, List
from dataclasses import dataclass

try:
    from config.rl_config import (
        LEARNING_RATE,
        DISCOUNT_FACTOR,
        EXPLORATION_RATE,
        EXPLORATION_DECAY,
        MIN_EXPLORATION,
        REWARD_SELECTED,
        REWARD_REJECTED,
        REWARD_PENDING,
        REWARD_STEP,
        BONUS_ATS_IMPROVEMENT,
        BONUS_KEYWORD_MATCH,
        ATS_MILESTONES,
        BONUS_ATS_MILESTONE,
        REWARD_EFFICIENCY,
        MAX_ITERATIONS_BONUS,
        REWARD_NEAR_SELECTED,
        NEAR_SELECTED_THRESHOLD,
    )
except ImportError:
    LEARNING_RATE = 0.1
    DISCOUNT_FACTOR = 0.95
    EXPLORATION_RATE = 1.0
    EXPLORATION_DECAY = 0.995
    MIN_EXPLORATION = 0.01
    REWARD_SELECTED = 10.0
    REWARD_REJECTED = -1.0
    REWARD_PENDING = 0.0
    REWARD_STEP = 0.1
    BONUS_ATS_IMPROVEMENT = 0.5
    BONUS_KEYWORD_MATCH = 0.3
    ATS_MILESTONES = [60, 70, 80, 90]
    BONUS_ATS_MILESTONE = 2.0
    REWARD_EFFICIENCY = 5.0
    MAX_ITERATIONS_BONUS = 20
    REWARD_NEAR_SELECTED = 2.0
    NEAR_SELECTED_THRESHOLD = 5

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


logger = setup_logger("rl_agent")


@dataclass
class QTableEntry:
    q_value: float
    visits: int


class RLAgent:
    def __init__(self):
        self.learning_rate = LEARNING_RATE
        self.discount_factor = DISCOUNT_FACTOR
        self.exploration_rate = EXPLORATION_RATE
        self.exploration_decay = EXPLORATION_DECAY
        self.min_exploration = MIN_EXPLORATION

        self.q_table: Dict[Tuple[str, str], QTableEntry] = {}
        self.experiences: list = []

        self.total_reward = 0
        self.episode_count = 0

    def get_state_key(self, resume_features: str, job_features: str) -> str:
        return f"{resume_features}|{job_features}"

    def get_action_key(self, action: str) -> str:
        return action

    def choose_action(self, state_key: str, available_actions: List[str]) -> str:
        if np.random.random() < self.exploration_rate:
            return np.random.choice(available_actions)

        best_action = available_actions[0]
        best_q = float("-inf")

        for action in available_actions:
            entry = self.q_table.get((state_key, action))
            if entry and entry.q_value > best_q:
                best_q = entry.q_value
                best_action = action

        return best_action

    def update_q_value(
        self,
        state_key: str,
        action: str,
        reward: float,
        next_state_key: str,
        available_actions: List[str],
    ):
        current_entry = self.q_table.get((state_key, action))
        current_q = current_entry.q_value if current_entry else 0.0

        max_next_q = float("-inf")
        for a in available_actions:
            entry = self.q_table.get((next_state_key, a))
            if entry and entry.q_value > max_next_q:
                max_next_q = entry.q_value

        if max_next_q == float("-inf"):
            max_next_q = 0.0

        new_q = current_q + self.learning_rate * (
            reward + self.discount_factor * max_next_q - current_q
        )

        self.q_table[(state_key, action)] = QTableEntry(
            q_value=new_q, visits=current_entry.visits + 1 if current_entry else 1
        )

        self.experiences.append(
            {
                "state": state_key,
                "action": action,
                "reward": reward,
                "next_state": next_state_key,
                "q_value": new_q,
            }
        )

    def calculate_reward(
        self,
        application_result: str,
        ats_improvement: float = 0,
        keyword_improvement: float = 0,
        current_ats: float = 0,
        iteration_count: int = 0,
        previous_ats: float = 0,
    ) -> float:
        reward = 0.0

        if application_result == "selected":
            reward = REWARD_SELECTED

            if iteration_count > 0 and iteration_count <= MAX_ITERATIONS_BONUS:
                efficiency_bonus = REWARD_EFFICIENCY * (
                    1 - iteration_count / MAX_ITERATIONS_BONUS
                )
                reward += efficiency_bonus

        elif application_result == "rejected":
            if (
                previous_ats > 0
                and current_ats < previous_ats + NEAR_SELECTED_THRESHOLD
            ):
                reward = REWARD_NEAR_SELECTED
            else:
                reward = REWARD_REJECTED

        else:
            reward = REWARD_PENDING

        reward += REWARD_STEP

        if ats_improvement > 0:
            reward += BONUS_ATS_IMPROVEMENT * ats_improvement

            for milestone in ATS_MILESTONES:
                if current_ats >= milestone and previous_ats < milestone:
                    reward += BONUS_ATS_MILESTONE

        if keyword_improvement > 0:
            reward += BONUS_KEYWORD_MATCH * keyword_improvement

        self.total_reward += reward
        return reward

    def decay_exploration(self):
        self.exploration_rate = max(
            self.min_exploration, self.exploration_rate * self.exploration_decay
        )
        self.episode_count += 1

    def get_stats(self) -> Dict:
        return {
            "total_episodes": self.episode_count,
            "total_reward": self.total_reward,
            "exploration_rate": self.exploration_rate,
            "q_table_size": len(self.q_table),
            "avg_reward": self.total_reward / max(1, self.episode_count),
        }

    def reset(self):
        self.q_table = {}
        self.experiences = []
        self.total_reward = 0
        self.episode_count = 0
        self.exploration_rate = EXPLORATION_RATE


AVAILABLE_ACTIONS = [
    "keep",
    "add_skill",
    "modify_summary",
    "quantify_experience",
    "add_keyword",
    "format_improvement",
]
