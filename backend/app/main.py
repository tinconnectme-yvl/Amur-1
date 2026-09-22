"""
Main FastAPI Application Entry Point.
Situational Center «АМУР-ГИДРОСКАН» // Amur Hydro-Radar Analytics.
Case #2: KosmoHack 2026 (Team Vector).
"""
import os
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.app.api.routers import analytics, inspector, export, rasters

app = FastAPI(
    title="АМУР-ГИДРОСКАН // Situational Hydro-Radar Analytics",
    description="Геоинформационный комплекс оперативного мониторинга гидрологической динамики по данным Sentinel-1 SAR и Sentinel-2 MSI (КосмоХакатон 2026)",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS configuration for development and production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(analytics.router)
app.include_router(inspector.router)
app.include_router(export.router)
app.include_router(rasters.router)

@app.get("/api/health")
def api_health():
    return {
        "status": "HEALTHY",
        "service": "AMUR-HYDROSCAN-API",
        "version": "2.0.0",
        "author": "Team Vector",
        "sensors": ["Sentinel-1 IW GRD (C-SAR)", "Sentinel-2 L2A (MSI)"],
        "competition": "KosmoHack 2026 (Blagoveshchensk)",
        "case": "Case 2 - Hydrological Monitoring"
    }

# Mount static build of frontend if exists
FRONTEND_DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST / "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        file_path = FRONTEND_DIST / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(FRONTEND_DIST / "index.html")
else:
    @app.get("/")
    def index_fallback():
        return {
            "message": "АМУР-ГИДРОСКАН API активен. Запустите сборку фронтенда (npm run build в frontend/) для отображения геопортала.",
            "docs": "/api/docs",
            "summary": "/api/summary",
            "pairs": "/api/pairs"
        }
