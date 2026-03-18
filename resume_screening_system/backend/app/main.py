from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.job_api import router as job_router
from app.api.resume_api import router as resume_router
from app.api.match_api import router as match_router

app = FastAPI(
    title="智能简历筛选系统",
    description="Resume screening system backend APIs",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", summary="System home")
def root():
    return {"message": "Backend service is running"}


app.include_router(job_router, prefix="/api/jobs", tags=["岗位管理"])
app.include_router(resume_router, prefix="/api/resumes", tags=["简历管理"])
app.include_router(match_router, prefix="/api/match", tags=["匹配评分"])