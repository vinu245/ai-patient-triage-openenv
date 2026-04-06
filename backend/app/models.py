from __future__ import annotations

from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field


TriageLevel = Literal["low", "medium", "high", "critical"]
Department = Literal[
    "general",
    "cardiology",
    "neurology",
    "respiratory",
    "gastroenterology",
    "orthopedics",
    "immunology",
    "emergency",
]


class Observation(BaseModel):
    patient_id: str
    symptoms: List[str]
    vitals: Dict[str, float]
    history: List[str] = Field(default_factory=list)
    allergies: List[str] = Field(default_factory=list)
    age: int
    arrived_at: float
    task_level: Literal["easy", "medium", "hard"]


class Action(BaseModel):
    triage_level: TriageLevel
    department: Department
    priority: int = Field(ge=1, le=100)


class Reward(BaseModel):
    score: float = Field(ge=0.0, le=1.0)
    feedback: str


class DecisionLog(BaseModel):
    agent: str
    rationale: str
    action: Optional[Action] = None


class TaskEvaluation(BaseModel):
    task_level: Literal["easy", "medium", "hard"]
    score: float = Field(ge=0.0, le=1.0)


class EnvironmentState(BaseModel):
    queue: List[Observation]
    current_patient: Optional[Observation]
    last_action: Optional[Action]
    last_reward: Optional[Reward]
    last_decision_trace: List[DecisionLog]
    total_steps: int


class MetricsSnapshot(BaseModel):
    reward: float
    accuracy: float
    queue_load: int
    response_time: float
    reward_history: List[float]
    accuracy_history: List[float]
    patient_load_history: List[int]
    response_time_history: List[float]


class StepRequest(BaseModel):
    action: Optional[Action] = None


class StepResult(BaseModel):
    observation: Observation
    agent_action: Action
    expected_action: Action
    reward: Reward
    task_evaluation: TaskEvaluation
    decision_trace: List[DecisionLog]
    queue_size: int


class StepResponse(BaseModel):
    result: StepResult
    state: EnvironmentState
    metrics: MetricsSnapshot
