#!/bin/bash
# ValueGraph 后端启动脚本

echo "🚀 启动 ValueGraph 后端服务..."

# 设置 Python 路径
export PYTHONPATH=/usr/local/soft/anaconda3/lib/python3.9/site-packages

# 禁用 tqdm
export TQDM_DISABLE=1

# 进入后端目录
cd ~/valuegraph/backend

# 启动服务
/usr/local/soft/anaconda3/bin/python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
