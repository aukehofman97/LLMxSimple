from pydantic import BaseModel

class Wagon(BaseModel):
    UUID: str
    WagonNumber: str  
    WagonType: str  



