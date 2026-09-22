"""Drosophila-NeuroAtlas — FastAPI backend application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.health import router as health_router
from app.api.connectome import router as connectome_router

app = FastAPI(
    title="Drosophila-NeuroAtlas",
    description="Connectome-driven computational neuroscience platform",
    version="0.1.0",
)

# CORS configuration — allow the Vite dev server during development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(connectome_router)
