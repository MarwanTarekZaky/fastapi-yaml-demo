from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="YAML learninig Api")

class Health(BaseModel):
    status: str = "ok"

@app.get("/")
def read_root():
    return {"message": "Hello, Yaml world!"}

@app.get("/health", response_model=Health)
def health():
    return Health()

