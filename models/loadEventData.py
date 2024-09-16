from typing import List, Optional
from pydantic import BaseModel
from .businesstransaction import BusinessTransaction
from .loadEvent import Event
from .location import Location
from .container import Container
from .seal import Seal
from .wagon import Wagon

class LoadEventData(BaseModel):
    Event: List[Event]
    Location: Optional[List[Location]]
    BusinessTransaction: Optional[List[BusinessTransaction]]
    Container: Optional[List[Container]]
    Seal: Optional[List[Seal]]
    Wagon: Optional[List[Wagon]]