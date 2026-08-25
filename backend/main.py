from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.database.db import init_db
from backend.api.auth_routes import router as auth_router
from backend.api.sales_routes import router as sales_router
from backend.api.dashboard_routes import router as dashboard_router
from backend.api.prediction_routes import router as prediction_router
from backend.api.ai_routes import router as ai_router
from backend.api.report_routes import router as report_router

# Initialize Database tables
init_db()

app = FastAPI(
    title="AI – Sales & Revenue Intelligence API",
    description="Full-stack AI Sales & Revenue Dashboard API with ML Forecasting and Agentic AI",
    version="1.0.0"
)

# Configure CORS for local development and web clients (supports localhost, local IP, and Vercel domains)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[],
    allow_origin_regex=r"https?://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(auth_router)
app.include_router(sales_router)
app.include_router(dashboard_router)
app.include_router(prediction_router)
app.include_router(ai_router)
app.include_router(report_router)

@app.get("/")
def root():
    return {
        "system": "AI – Sales & Revenue Intelligence Platform",
        "status": "online",
        "version": "1.0.0",
        "endpoints": {
            "docs": "/docs",
            "auth": "/api/auth",
            "sales": "/api/sales",
            "dashboard": "/api/dashboard",
            "ml": "/api/predict",
            "ai_agent": "/api/ai",
            "reports": "/api/report"
        }
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
