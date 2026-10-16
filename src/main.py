
from fastapi import FastAPI

app = FastAPI(
    title="FastAPI Starter Project",
    description="FastAPI Starter Project",
    version="1.0.0"
)

@app.get('/')
def read_root():
    return {"Hello": "World"}
