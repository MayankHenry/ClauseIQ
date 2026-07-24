from fastapi import FastAPI

from app.api.documents import router as documents_router
from app.api.search import router as search_router
from app.api.query import router as query_router

app = FastAPI(title="ClauseIQ API")

app.include_router(documents_router)
app.include_router(search_router)
app.include_router(query_router)


@app.get("/health")
def health():
    return {"status": "ok"}
