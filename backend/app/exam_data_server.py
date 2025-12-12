from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.api.exam_data import router as exam_data_router
from backend.app.api.logs import router as logs_router
from backend.app.api.telemetry import router as telemetry_router
from backend.app.middleware.logging_middleware import APILoggingMiddleware

app = FastAPI(title="Exam Data Sync Server")

app.add_middleware(APILoggingMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(exam_data_router)
app.include_router(logs_router)
app.include_router(telemetry_router)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "exam-data-sync"}
