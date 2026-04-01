from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.job_api import router as job_router
from app.api.match_api import router as match_router
from app.api.resume_api import router as resume_router
from app.core.database import bootstrap_schema


@asynccontextmanager
async def lifespan(_: FastAPI):
    bootstrap_schema()
    yield


app = FastAPI(
    title="智能简历筛选系统",
    description="面向中文招聘场景的简历解析、脱敏筛选与可解释匹配后端服务",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", summary="系统首页")
def root():
    return {"message": "智能简历筛选系统后端服务运行中"}


app.include_router(job_router, prefix="/api/jobs", tags=["岗位管理"])
app.include_router(resume_router, prefix="/api/resumes", tags=["简历管理"])
app.include_router(match_router, prefix="/api/match", tags=["匹配评分"])
