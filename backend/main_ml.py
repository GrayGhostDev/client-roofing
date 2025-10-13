"""
FastAPI ML Prediction Server
Serves ML endpoints for iSwitch Roofs CRM Phase 4
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Import ML routes
from app.routes.ml_predictions import router as ml_router
from app.routes.transcription import router as transcription_router

# Create FastAPI app
app = FastAPI(
    title="iSwitch Roofs ML API",
    description="Machine Learning prediction endpoints for CRM",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "http://localhost:3000"],  # Streamlit & React
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include ML routes (router already has /api/v1/ml prefix)
app.include_router(ml_router)

# Include transcription routes (for call transcription service)
app.include_router(transcription_router)

# Root endpoint
@app.get("/")
async def root():
    return {
        "service": "iSwitch Roofs ML API",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "health": "/api/v1/ml/health",
            "metrics": "/api/v1/ml/metrics",
            "predict": "/api/v1/ml/predict/nba",
            "enhanced": "/api/v1/ml/predict/nba/enhanced",
            "transcription": "/api/transcription",
            "docs": "/docs"
        }
    }

# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "ml-api"}

if __name__ == "__main__":
    uvicorn.run(
        "main_ml:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
