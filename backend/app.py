from fastapi import FastAPI

app = FastAPI(title="novel_flow backend")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
