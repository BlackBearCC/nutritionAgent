FROM registry.cn-hangzhou.aliyuncs.com/big-head/nutrition_agent:latest

WORKDIR /app

# 复制整个项目目录
COPY . .

# 如果有新的依赖，可以追加安装
# RUN pip install --no-cache-dir -r requirements.txt

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "8"]
# CMD ["python", "run.py"]