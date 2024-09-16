from typing import List, Optional
from pydantic import BaseModel
from .businesstransaction import BusinessTransaction
from .arrivalEvent import Event
from .location import Location


class ArrivalEventData(BaseModel):
    Event: List[Event]
    Location: Optional[List[Location]]
    BusinessTransaction: Optional[List[BusinessTransaction]]
