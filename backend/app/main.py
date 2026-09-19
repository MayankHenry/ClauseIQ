from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.documents import router as documents_router
from app.api.search import router as search_router
from app.api.query import router as query_router
from app.api.risk import router as risk_router
from app.api.auth import router as auth_router

app = FastAPI(title="ClauseIQ API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents_router)
app.include_router(search_router)
app.include_router(query_router)
app.include_router(risk_router)
app.include_router(auth_router)


@app.get("/health")
def health():
    return {"status": "ok"}
