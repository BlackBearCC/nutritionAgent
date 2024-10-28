from fastapi import FastAPI
from app.models import pdf_analysis
from app.api.endpoints import pdf_analysis as pdf_endpoint
from app.api.endpoints import meal_plan as meal_endpoint 
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

app = FastAPI(
    title="智能健康系统",
    description="基于AI的健康饮食推荐系统",
    version="1.0.0"
)

# PDF分析路由
app.include_router(pdf_endpoint.router)

# 添加食谱定制路由
app.include_router(meal_endpoint.router)
##dcoker从这启动
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True,workers=8)
