from pydantic import BaseModel

class BusinessTransaction(BaseModel):
    UUID: str
    externalReference: str