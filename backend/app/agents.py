from __future__ import annotations

from app.models import Action, DecisionLog, Observation


class NurseAgent:
    name = "nurse-agent"

    def run(self, observation: Observation) -> DecisionLog:
        triage = "low"
        priority = 35

        hr = observation.vitals.get("heart_rate", 80)
        spo2 = observation.vitals.get("oxygen", 98)
        temp = observation.vitals.get("temperature", 98.6)

        if "chest pain" in observation.symptoms or "severe bleeding" in observation.symptoms:
            triage = "high"
            priority = 80
        if "confusion" in observation.symptoms or "shortness of breath" in observation.symptoms:
            triage = "high"
            priority = max(priority, 82)
        if spo2 < 90 or hr > 130 or temp >= 103:
            triage = "critical"
            priority = 95
        elif spo2 < 94 or hr > 110 or temp >= 101.5:
            triage = "high"
            priority = max(priority, 75)
        elif temp >= 100.4:
            triage = "medium"
            priority = max(priority, 55)

        rationale = (
            f"Initial triage from vitals/symptoms: triage={triage}, priority={priority}."
        )
        return DecisionLog(
            agent=self.name,
            rationale=rationale,
            action=Action(triage_level=triage, department="general", priority=priority),
        )


class DoctorAgent:
    name = "doctor-agent"

    def run(self, observation: Observation, nurse_action: Action) -> DecisionLog:
        department = "general"
        triage = nurse_action.triage_level
        priority = nurse_action.priority

        s = set(observation.symptoms)

        if "chest pain" in s or "palpitations" in s:
            department = "cardiology"
            triage = "high" if triage != "critical" else triage
            priority = max(priority, 78)
        elif "slurred speech" in s or "one-sided weakness" in s or "confusion" in s:
            department = "neurology"
            triage = "critical" if "slurred speech" in s else triage
            priority = max(priority, 90 if "slurred speech" in s else 78)
        elif "shortness of breath" in s or "cough" in s:
            department = "respiratory"
            triage = "high" if triage in {"low", "medium"} else triage
            priority = max(priority, 72)
        elif "abdominal pain" in s or "vomiting" in s:
            department = "gastroenterology"
            triage = "medium" if triage == "low" else triage
            priority = max(priority, 60)
        elif "fracture pain" in s or "joint swelling" in s:
            department = "orthopedics"
            triage = "medium" if triage == "low" else triage
            priority = max(priority, 58)
        elif "rash" in s or "anaphylaxis" in s:
            department = "immunology"
            triage = "critical" if "anaphylaxis" in s else "high"
            priority = max(priority, 96 if "anaphylaxis" in s else 76)

        if observation.age >= 75 and triage in {"low", "medium"}:
            triage = "high"
            priority = max(priority, 70)

        if "heart_disease" in observation.history and department == "general":
            department = "cardiology"
            priority = max(priority, 65)

        rationale = (
            f"Doctor routed patient to {department} with triage={triage} based on symptom cluster and history."
        )
        return DecisionLog(
            agent=self.name,
            rationale=rationale,
            action=Action(triage_level=triage, department=department, priority=priority),
        )


class RiskAgent:
    name = "risk-agent"

    def run(self, observation: Observation, doctor_action: Action) -> DecisionLog:
        action = doctor_action.model_copy(deep=True)

        hr = observation.vitals.get("heart_rate", 80)
        spo2 = observation.vitals.get("oxygen", 98)
        bp_sys = observation.vitals.get("bp_sys", 120)

        emergency_signals = {
            "anaphylaxis",
            "severe bleeding",
            "slurred speech",
            "one-sided weakness",
            "chest pain",
        }

        if spo2 < 90 or bp_sys < 90 or hr > 140 or emergency_signals.intersection(observation.symptoms):
            action.triage_level = "critical"
            action.department = "emergency"
            action.priority = max(action.priority, 96)
            rationale = "Risk override triggered due to emergency indicators."
        elif observation.age > 85 and action.triage_level in {"low", "medium"}:
            action.triage_level = "high"
            action.priority = max(action.priority, 78)
            rationale = "Risk adjustment for advanced age vulnerability."
        else:
            rationale = "No safety override required."

        return DecisionLog(agent=self.name, rationale=rationale, action=action)
