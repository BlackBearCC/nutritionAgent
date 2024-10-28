from fastapi import FastAPI
from app.models import pdf_analysis
from app.api.endpoints import pdf_analysis as pdf_endpoint
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

app = FastAPI(
    title="智能健康分析系统",
    description="基于AI的健康报告分析系统",
    version="1.0.0"
)

# 直接使用路由，不添加前缀
app.include_router(pdf_endpoint.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
