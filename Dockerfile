FROM registry.cn-hangzhou.aliyuncs.com/big-head/nutrition_agent:latest

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir pydantic-settings
# RUN pip install --no-cache-dir -r requirements.txt

# 暴露端口
EXPOSE 8000


CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "8"]
# CMD ["python", "run.py"]