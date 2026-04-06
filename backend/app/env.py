from __future__ import annotations

import random
import threading
import time
import uuid
from collections import deque
from statistics import fmean
from typing import Callable, Deque, Dict, List, Optional

from sqlalchemy.orm import Session, sessionmaker

from app.database import fetch_random_ehr
from app.models import (
    Action,
    DecisionLog,
    EnvironmentState,
    MetricsSnapshot,
    Observation,
    Reward,
    StepResult,
    TaskEvaluation,
)
from app.workflow import run_triage_workflow

TRIAGE_TO_WEIGHT = {"low": 0.25, "medium": 0.55, "high": 0.8, "critical": 1.0}


class OpenEnvTriage:
    def __init__(self, session_factory: sessionmaker[Session], seed: int = 7) -> None:
        self.session_factory = session_factory
        self.seed = seed
        self.rng = random.Random(seed)
        self._lock = threading.Lock()
        self._listeners: List[Callable[[dict], None]] = []

        self.queue: Deque[Observation] = deque()
        self.current_patient: Optional[Observation] = None
        self.last_action: Optional[Action] = None
        self.last_reward: Optional[Reward] = None
        self.last_trace: List[DecisionLog] = []
        self.total_steps = 0

        self.reward_history: List[float] = []
        self.accuracy_history: List[float] = []
        self.patient_load_history: List[int] = []
        self.response_time_history: List[float] = []

        self.correct_decisions = 0
        self.total_decisions = 0
        self.reset()

    def register_listener(self, listener: Callable[[dict], None]) -> None:
        self._listeners.append(listener)

    def _emit(self, payload: dict) -> None:
        for listener in self._listeners:
            listener(payload)

    def reset(self) -> EnvironmentState:
        with self._lock:
            self.rng = random.Random(self.seed)
            self.queue.clear()
            self.current_patient = None
            self.last_action = None
            self.last_reward = None
            self.last_trace = []
            self.total_steps = 0

            self.reward_history = []
            self.accuracy_history = []
            self.patient_load_history = []
            self.response_time_history = []
            self.correct_decisions = 0
            self.total_decisions = 0

            for _ in range(8):
                self.queue.append(self._generate_patient())
            self._sort_queue()

            state = self.state()
            self._emit({"event": "reset", "state": state.model_dump(), "metrics": self.metrics().model_dump()})
            return state

    def state(self) -> EnvironmentState:
        return EnvironmentState(
            queue=list(self.queue),
            current_patient=self.current_patient,
            last_action=self.last_action,
            last_reward=self.last_reward,
            last_decision_trace=self.last_trace,
            total_steps=self.total_steps,
        )

    def metrics(self) -> MetricsSnapshot:
        reward = fmean(self.reward_history) if self.reward_history else 0.0
        accuracy = self.correct_decisions / self.total_decisions if self.total_decisions else 0.0
        queue_load = len(self.queue)
        response_time = fmean(self.response_time_history) if self.response_time_history else 0.0

        return MetricsSnapshot(
            reward=round(reward, 4),
            accuracy=round(accuracy, 4),
            queue_load=queue_load,
            response_time=round(response_time, 4),
            reward_history=self.reward_history[-120:],
            accuracy_history=self.accuracy_history[-120:],
            patient_load_history=self.patient_load_history[-120:],
            response_time_history=self.response_time_history[-120:],
        )

    def step(self, action: Optional[Action] = None) -> StepResult:
        with self._lock:
            if not self.queue:
                for _ in range(self.rng.randint(2, 4)):
                    self.queue.append(self._generate_patient())
                self._sort_queue()

            started_at = time.perf_counter()
            self.current_patient = self.queue.popleft()

            expected_action = self._expected_action(self.current_patient)
            if action is None:
                selected_action, trace = run_triage_workflow(self.current_patient)
            else:
                selected_action = action
                trace = [DecisionLog(agent="external-agent", rationale="Action supplied by client", action=action)]

            reward = self._calculate_reward(self.current_patient, selected_action, expected_action)
            task_eval = self._grade_task(self.current_patient.task_level, selected_action, expected_action, reward.score)

            elapsed = time.perf_counter() - started_at
            self.total_steps += 1
            self.last_action = selected_action
            self.last_reward = reward
            self.last_trace = trace

            if self._is_correct(selected_action, expected_action):
                self.correct_decisions += 1
            self.total_decisions += 1

            self.reward_history.append(round(reward.score, 4))
            self.accuracy_history.append(round(self.correct_decisions / self.total_decisions, 4))
            self.patient_load_history.append(len(self.queue))
            self.response_time_history.append(round(elapsed, 5))

            for _ in range(self.rng.randint(0, 2)):
                self.queue.append(self._generate_patient())
            self._sort_queue()

            result = StepResult(
                observation=self.current_patient,
                agent_action=selected_action,
                expected_action=expected_action,
                reward=reward,
                task_evaluation=task_eval,
                decision_trace=trace,
                queue_size=len(self.queue),
            )

            self._emit(
                {
                    "event": "step",
                    "result": result.model_dump(),
                    "state": self.state().model_dump(),
                    "metrics": self.metrics().model_dump(),
                }
            )
            return result

    def _grade_task(
        self,
        task_level: str,
        action: Action,
        expected_action: Action,
        reward_score: float,
    ) -> TaskEvaluation:
        base = reward_score
        if task_level == "easy":
            score = min(1.0, base + 0.1 if action.department == expected_action.department else base)
        elif task_level == "medium":
            score = base
        else:
            emergency_bonus = 0.2 if action.triage_level == "critical" and action.department == "emergency" else 0.0
            score = min(1.0, base + emergency_bonus)

        return TaskEvaluation(task_level=task_level, score=round(max(0.0, score), 4))

    def _is_correct(self, action: Action, expected: Action) -> bool:
        return action.department == expected.department and action.triage_level == expected.triage_level

    def _calculate_reward(self, observation: Observation, action: Action, expected: Action) -> Reward:
        score = 0.0
        feedback: List[str] = []

        if action.triage_level == expected.triage_level:
            score += 0.5
            feedback.append("triage match")
        elif TRIAGE_TO_WEIGHT[action.triage_level] >= TRIAGE_TO_WEIGHT[expected.triage_level]:
            score += 0.25
            feedback.append("safe over-triage")
        else:
            feedback.append("under-triage penalty")
            score -= 0.25

        if action.department == expected.department:
            score += 0.35
            feedback.append("department match")
        elif action.department == "emergency" and expected.triage_level == "critical":
            score += 0.15
            feedback.append("defensive emergency routing")
        else:
            score -= 0.2
            feedback.append("wrong department penalty")

        wait_seconds = max(0.0, time.time() - observation.arrived_at)
        if wait_seconds > 60:
            score -= min(0.2, wait_seconds / 600)
            feedback.append("delay penalty")

        if expected.triage_level == "critical" and action.triage_level != "critical":
            score -= 0.3
            feedback.append("critical miss penalty")

        final_score = max(0.0, min(1.0, score))
        return Reward(score=round(final_score, 4), feedback=", ".join(feedback))

    def _urgency_score(self, obs: Observation) -> float:
        vitals_factor = 0.0
        hr = obs.vitals.get("heart_rate", 80)
        spo2 = obs.vitals.get("oxygen", 98)
        temp = obs.vitals.get("temperature", 98.6)

        if hr > 130:
            vitals_factor += 25
        elif hr > 110:
            vitals_factor += 12

        if spo2 < 90:
            vitals_factor += 30
        elif spo2 < 94:
            vitals_factor += 15

        if temp >= 103:
            vitals_factor += 15
        elif temp >= 100.4:
            vitals_factor += 8

        symptom_factor = 0
        critical_symptoms = {"chest pain", "slurred speech", "one-sided weakness", "anaphylaxis", "severe bleeding"}
        medium_symptoms = {"shortness of breath", "vomiting", "abdominal pain", "fracture pain"}

        if critical_symptoms.intersection(obs.symptoms):
            symptom_factor += 40
        elif medium_symptoms.intersection(obs.symptoms):
            symptom_factor += 18

        history_factor = 0
        if "heart_disease" in obs.history or "stroke_history" in obs.history:
            history_factor += 8
        if obs.age >= 75:
            history_factor += 6

        return vitals_factor + symptom_factor + history_factor

    def _sort_queue(self) -> None:
        ordered = sorted(self.queue, key=self._urgency_score, reverse=True)
        self.queue = deque(ordered)

    def _generate_patient(self) -> Observation:
        with self.session_factory() as session:
            age, history, allergies = fetch_random_ehr(session, self.rng)

        easy_pool = [
            ["mild fever", "cough"],
            ["joint swelling"],
            ["headache"],
            ["rash"],
        ]
        medium_pool = [
            ["abdominal pain", "vomiting"],
            ["shortness of breath", "cough"],
            ["fracture pain"],
            ["palpitations", "dizziness"],
        ]
        hard_pool = [
            ["chest pain", "shortness of breath"],
            ["slurred speech", "one-sided weakness"],
            ["anaphylaxis", "rash"],
            ["severe bleeding", "confusion"],
        ]

        task_level = self.rng.choices(["easy", "medium", "hard"], weights=[0.4, 0.4, 0.2], k=1)[0]
        if task_level == "easy":
            symptoms = self.rng.choice(easy_pool)
        elif task_level == "medium":
            symptoms = self.rng.choice(medium_pool)
        else:
            symptoms = self.rng.choice(hard_pool)

        vitals = {
            "heart_rate": float(self.rng.randint(65, 150)),
            "oxygen": float(self.rng.randint(85, 100)),
            "temperature": round(self.rng.uniform(97.0, 104.0), 1),
            "bp_sys": float(self.rng.randint(85, 170)),
            "bp_dia": float(self.rng.randint(55, 110)),
        }

        return Observation(
            patient_id=str(uuid.uuid4())[:8],
            symptoms=symptoms,
            vitals=vitals,
            history=history,
            allergies=allergies,
            age=age,
            arrived_at=time.time(),
            task_level=task_level,
        )

    def _expected_action(self, obs: Observation) -> Action:
        s = set(obs.symptoms)
        triage = "low"
        department = "general"
        priority = 35

        if {"slurred speech", "one-sided weakness"}.intersection(s):
            triage = "critical"
            department = "emergency"
            priority = 98
        elif "anaphylaxis" in s or "severe bleeding" in s:
            triage = "critical"
            department = "emergency"
            priority = 97
        elif "chest pain" in s:
            triage = "critical" if obs.vitals.get("oxygen", 98) < 93 else "high"
            department = "cardiology" if triage == "high" else "emergency"
            priority = 95 if triage == "critical" else 84
        elif "shortness of breath" in s:
            triage = "high"
            department = "respiratory"
            priority = 78
        elif "abdominal pain" in s or "vomiting" in s:
            triage = "medium"
            department = "gastroenterology"
            priority = 62
        elif "fracture pain" in s:
            triage = "medium"
            department = "orthopedics"
            priority = 60
        elif "rash" in s:
            triage = "medium"
            department = "immunology"
            priority = 58

        if obs.vitals.get("oxygen", 98) < 90 or obs.vitals.get("bp_sys", 120) < 90:
            triage = "critical"
            department = "emergency"
            priority = max(priority, 96)

        if obs.age > 80 and triage in {"low", "medium"}:
            triage = "high"
            priority = max(priority, 72)

        if "heart_disease" in obs.history and department == "general":
            department = "cardiology"
            triage = "medium" if triage == "low" else triage
            priority = max(priority, 63)

        return Action(triage_level=triage, department=department, priority=priority)
