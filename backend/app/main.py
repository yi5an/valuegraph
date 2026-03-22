from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routers import stocks, financial

app = FastAPI(
    title="ValueGraph API",
    description="价值投资知识图谱平台",
    version="1.0.0"
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://127.0.0.1:3000", "http://127.0.0.1:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(stocks.router)
app.include_router(financial.router)

@app.get("/")
async def root():
    return {"message": "ValueGraph API is running"}

@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "valuegraph"}

@app.get("/api/config")
async def config():
    return {
        "tushare_configured": bool(settings.tushare_token),
        "database_configured": bool(settings.database_url),
        "redis_configured": bool(settings.redis_url)
    }
