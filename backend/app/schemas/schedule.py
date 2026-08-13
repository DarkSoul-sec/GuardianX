from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ScheduleCadence = Literal["DAILY", "WEEKLY", "MONTHLY"]
WeekDay = Literal["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]


class ScheduledScanCreate(BaseModel):
    asset_id: int
    cadence: ScheduleCadence
    time_of_day: str = Field(
        pattern=r"^([01]\d|2[0-3]):[0-5]\d$",
        description="UTC time of day, format HH:MM",
    )
    week_day: WeekDay | None = None
    month_day: int | None = Field(
        default=None,
        ge=1,
        le=31,
    )
    scanner: str = "nmap"
    enabled: bool = True


class ScheduledScanUpdate(BaseModel):
    cadence: ScheduleCadence | None = None
    time_of_day: str | None = Field(
        default=None,
        pattern=r"^([01]\d|2[0-3]):[0-5]\d$",
    )
    week_day: WeekDay | None = None
    month_day: int | None = Field(
        default=None,
        ge=1,
        le=31,
    )
    scanner: str | None = None
    enabled: bool | None = None


class ScheduledScanResponse(BaseModel):
    id: int
    asset_id: int
    asset_name: str | None = None
    scanner: str
    cadence: str
    time_of_day: str
    week_day: str | None
    month_day: int | None
    enabled: bool
    last_run_at: datetime | None
    next_run_at: datetime | None
    created_by: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )
