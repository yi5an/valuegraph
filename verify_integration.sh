#!/bin/bash
echo "=== 验证 AkShare 集成 ==="
echo ""

# 检查后端文件
echo "1. 检查后端代码文件..."
files=(
    "backend/app/services/data_source.py"
    "backend/app/services/akshare_adapter.py"
    "backend/app/services/stock_service.py"
    "backend/app/routers/stocks.py"
    "backend/app/main.py"
    "backend/requirements.txt"
)

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "   ✅ $file"
    else
        echo "   ❌ $file (缺失)"
    fi
done

echo ""
echo "2. 检查测试和文档文件..."
files=(
    "test_akshare_simple.py"
    "test_api.sh"
    "start_backend.sh"
    "AKSHARE_INTEGRATION_REPORT.md"
    "README_AKSHARE.md"
    "AKSHARE_TASK_SUMMARY.md"
)

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "   ✅ $file"
    else
        echo "   ❌ $file (缺失)"
    fi
done

echo ""
echo "3. 检查 Python 语法..."
cd backend
/usr/local/soft/anaconda3/bin/python -m py_compile \
    app/services/data_source.py \
    app/services/akshare_adapter.py \
    app/services/stock_service.py \
    app/routers/stocks.py \
    app/main.py 2>&1 | grep -v "UserWarning" | grep -v "from pandas"

if [ $? -eq 0 ]; then
    echo "   ✅ 所有 Python 文件语法正确"
else
    echo "   ❌ Python 语法检查失败"
fi

echo ""
echo "=== 验证完成 ==="
