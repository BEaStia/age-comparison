from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field


class Person(BaseModel):
    person_id: str
    name_ru: str
    name_en: str | None = None
    birth_date: date
    death_date: date | None = None
    origin_group: str | None = None
    notes: str | None = None


class Position(BaseModel):
    person_id: str
    position: str
    start_date: date
    end_date: date | None = None
    tier: int = Field(ge=1)
    institution: str
    influence_weight: float = Field(ge=0)
    is_ruler: bool
    is_core_elite: bool
    notes: str | None = None


class PoliticalEntry(BaseModel):
    person_id: str
    political_entry_date: date | None = None
    elite_entry_date: date | None = None
    ruling_circle_entry_date: date | None = None
    notes: str | None = None


class Event(BaseModel):
    event_id: str
    date: date
    event_name: str
    event_type: str
    severity: int = Field(ge=1, le=5)
    decision_direction: str | None = None
    notes: str | None = None
