from __future__ import annotations

import json
import os
import random
from typing import Generator, List

from sqlalchemy import Integer, String, Text, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./triage.db")


class Base(DeclarativeBase):
    pass


class PatientEHR(Base):
    __tablename__ = "patient_ehr"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    age: Mapped[int] = mapped_column(Integer, nullable=False)
    past_diseases: Mapped[str] = mapped_column(Text, nullable=False)
    allergies: Mapped[str] = mapped_column(Text, nullable=False)


engine_kwargs = {"connect_args": {"check_same_thread": False}} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, **engine_kwargs)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_session() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def _seed_ehr_data(session: Session) -> None:
    diseases = [
        "hypertension",
        "diabetes",
        "asthma",
        "ckd",
        "copd",
        "heart_disease",
        "stroke_history",
        "none",
    ]
    allergies = ["penicillin", "nuts", "latex", "pollen", "none"]

    rng = random.Random(42)
    for _ in range(120):
        disease_count = rng.randint(0, 3)
        allergy_count = rng.randint(0, 2)

        past = rng.sample([d for d in diseases if d != "none"], k=disease_count)
        allergy = rng.sample([a for a in allergies if a != "none"], k=allergy_count)

        if not past:
            past = ["none"]
        if not allergy:
            allergy = ["none"]

        session.add(
            PatientEHR(
                age=rng.randint(5, 95),
                past_diseases=json.dumps(past),
                allergies=json.dumps(allergy),
            )
        )


def init_db() -> None:
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as session:
        existing = session.scalar(select(PatientEHR.id).limit(1))
        if existing is None:
            _seed_ehr_data(session)
            session.commit()


def fetch_random_ehr(session: Session, rng: random.Random) -> tuple[int, List[str], List[str]]:
    records = session.scalars(select(PatientEHR)).all()
    if not records:
        return 30, ["none"], ["none"]

    rec = rng.choice(records)
    return rec.age, json.loads(rec.past_diseases), json.loads(rec.allergies)
