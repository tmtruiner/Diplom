from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers.dashboard import router as dashboard_router
from app.routers.customers import router as customers_router
from app.routers.segments import router as segments_router
from app.routers.recommendations import router as recommendations_router
from app.routers.export import router as export_router

app = FastAPI(title="Churn Analytics API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5173",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dashboard_router)
app.include_router(customers_router)
app.include_router(segments_router)
app.include_router(recommendations_router)
app.include_router(export_router)

@app.get("/health")
def health_check():
    return {"status": "ok"}