from __future__ import annotations

from app.agents import DoctorAgent, NurseAgent, RiskAgent
from app.models import Action, DecisionLog, Observation


nurse_agent = NurseAgent()
doctor_agent = DoctorAgent()
risk_agent = RiskAgent()


def run_triage_workflow(observation: Observation) -> tuple[Action, list[DecisionLog]]:
    nurse_log = nurse_agent.run(observation)
    doctor_log = doctor_agent.run(observation, nurse_log.action)
    risk_log = risk_agent.run(observation, doctor_log.action)

    final_action = risk_log.action
    trace = [nurse_log, doctor_log, risk_log]
    return final_action, trace
