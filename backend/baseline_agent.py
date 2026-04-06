from __future__ import annotations

import json
import os
from statistics import fmean

from openai import OpenAI

from app.database import SessionLocal, init_db
from app.env import OpenEnvTriage
from app.models import Action, Observation

SYSTEM_PROMPT = """
You are a hospital triage model. Output JSON only with keys:
triage_level (low|medium|high|critical), department, priority(1-100).
Prefer safety for emergency indicators.
""".strip()


def _heuristic_action(obs: Observation) -> Action:
    if "slurred speech" in obs.symptoms or "one-sided weakness" in obs.symptoms:
        return Action(triage_level="critical", department="emergency", priority=98)
    if "chest pain" in obs.symptoms:
        return Action(triage_level="high", department="cardiology", priority=86)
    if "shortness of breath" in obs.symptoms:
        return Action(triage_level="high", department="respiratory", priority=80)
    if "abdominal pain" in obs.symptoms:
        return Action(triage_level="medium", department="gastroenterology", priority=62)
    return Action(triage_level="medium", department="general", priority=55)


def _openai_action(client: OpenAI, obs: Observation) -> Action:
    user_prompt = json.dumps(
        {
            "symptoms": obs.symptoms,
            "vitals": obs.vitals,
            "history": obs.history,
            "allergies": obs.allergies,
            "age": obs.age,
            "task_level": obs.task_level,
        }
    )

    response = client.responses.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
        temperature=0,
        input=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    )
    text = response.output_text.strip()
    payload = json.loads(text)
    return Action(**payload)


def run_baseline(episodes: int = 50) -> dict:
    init_db()
    env = OpenEnvTriage(SessionLocal, seed=1337)

    api_key = os.getenv("OPENAI_API_KEY")
    client = OpenAI(api_key=api_key) if api_key else None

    scores = []
    task_scores = {"easy": [], "medium": [], "hard": []}

    env.reset()
    for _ in range(episodes):
        observation = env.queue[0]
        if client:
            try:
                action = _openai_action(client, observation)
            except Exception:
                action = _heuristic_action(observation)
        else:
            action = _heuristic_action(observation)

        step = env.step(action)
        scores.append(step.reward.score)
        task_scores[step.task_evaluation.task_level].append(step.task_evaluation.score)

    result = {
        "episodes": episodes,
        "average_reward": round(fmean(scores), 4) if scores else 0.0,
        "easy_score": round(fmean(task_scores["easy"]), 4) if task_scores["easy"] else 0.0,
        "medium_score": round(fmean(task_scores["medium"]), 4) if task_scores["medium"] else 0.0,
        "hard_score": round(fmean(task_scores["hard"]), 4) if task_scores["hard"] else 0.0,
    }
    return result


if __name__ == "__main__":
    output = run_baseline()
    print(json.dumps(output, indent=2))
