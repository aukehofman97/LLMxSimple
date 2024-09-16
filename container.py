from typing import Optional
from pydantic import BaseModel

class Container(BaseModel):
    UUID: str
    ContainerNumber: str
    ContainerSize: int
    ContainerType: str
    Full_Empty: bool
    DamageRemarks: Optional[str] = None  
    DangerousIndication: Optional[str] = None  
    Description: Optional[str] = None 