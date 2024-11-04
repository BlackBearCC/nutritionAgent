#!/bin/bash
# 激活conda环境
source ~/miniconda3/etc/profile.d/conda.sh
conda activate nutrition-agent

# 加载环境变量
export $(cat .env | xargs)


uvicorn app.main:app --host 0.0.0.0 --port 8089