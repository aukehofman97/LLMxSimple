from pydantic import BaseModel

class Seal(BaseModel):
    UUID: str
    SealNumber: str  