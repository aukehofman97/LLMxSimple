from typing import List, Optional
from pydantic import BaseModel, field_validator

class Event(BaseModel):
    Event_UUID: str
    Actual_Time: str
    milestone: str
    involvesLocation: Optional[List[str]]
    involvesBusinessTransaction: Optional[str]
    involvesSeal: Optional[str] = []
    involvesWagon: Optional[str] = []
    involvesContainer: Optional[list[str]]
    @field_validator('involvesLocation')
    def check_location_length(cls, v):
        if v is not None:
            if len(v) != 2:
                raise ValueError('involvesLocation must contain exactly two elements')
        return v