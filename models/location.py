from pydantic import BaseModel

# Pydantic classes for structured output - the string output from chatgpt are transformed to json
# next step: transform json to json-ld --> then extract triples
# Update the Pydantic classes by running the OpenAI transformation from Pydantic:
# datamodel-codegen  --input event_schema.json --input-file-type jsonschema --output model.py

class Location(BaseModel):
    UUID: str
    function: str
    locationCode: str

