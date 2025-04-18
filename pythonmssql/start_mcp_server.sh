#!/bin/bash
# สคริปต์เรียกใช้งาน MCP Server

# ตรวจสอบว่ามีการติดตั้ง conda หรือไม่
if ! command -v conda &> /dev/null; then
    echo "❌ ไม่พบการติดตั้ง Conda กรุณาติดตั้ง Miniconda หรือ Anaconda ก่อน"
    echo "   เข้าชม: https://docs.conda.io/en/latest/miniconda.html"
    exit 1
fi

# ตรวจสอบว่ามี environment mssql-mcp หรือไม่
if ! conda info --envs | grep -q "mssql-mcp"; then
    echo "❌ ไม่พบ environment mssql-mcp ใน conda"
    echo "   กรุณารันสคริปต์ setup_conda.sh ก่อน:"
    echo "   ./setup_conda.sh"
    exit 1
fi

# พาธของไฟล์ mssql_server.py
SERVER_PATH="$(pwd)/mssql_server.py"

# ตรวจสอบว่ามีไฟล์ mssql_server.py หรือไม่
if [ ! -f "$SERVER_PATH" ]; then
    echo "❌ ไม่พบไฟล์ MCP Server ที่ $SERVER_PATH"
    exit 1
fi

echo "🚀 กำลังเริ่มต้น MSSQL MCP Server..."
echo "📌 เซิร์ฟเวอร์: 35.239.50.206"
echo "📌 ฐานข้อมูล: Telco"

# เปิดใช้งาน conda environment และรัน server
eval "$(conda shell.bash hook)"
conda activate mssql-mcp
python "$SERVER_PATH"
