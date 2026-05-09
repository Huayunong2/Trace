#!/bin/bash
# 老年痴呆防走失系统 - 一键启动脚本

set -e  # 遇到错误立即退出

echo "=========================================="
echo "  老年痴呆防走失系统 - 一键启动脚本"
echo "=========================================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 项目路径
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="${SCRIPT_DIR}"
BACKEND_DIR="${PROJECT_DIR}/backend"
MINIPROGRAM_DIR="${PROJECT_DIR}/miniprogram"

# 进入后端目录
cd "${BACKEND_DIR}"

echo -e "${YELLOW}[1/6] 检查Python环境...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}错误: 未找到Python3，请先安装Python3${NC}"
    exit 1
fi
PYTHON_VERSION=$(python3 --version)
echo -e "${GREEN}✓ Python版本: ${PYTHON_VERSION}${NC}"
echo ""

# 检查虚拟环境
echo -e "${YELLOW}[2/6] 检查虚拟环境...${NC}"
if [ ! -d "venv" ] || [ ! -f "venv/bin/activate" ]; then
    echo -e "${YELLOW}虚拟环境不存在，正在创建...${NC}"
    python3 -m venv venv
    echo -e "${GREEN}✓ 虚拟环境创建成功${NC}"
else
    echo -e "${GREEN}✓ 虚拟环境已存在${NC}"
fi

# 激活虚拟环境
echo -e "${YELLOW}[3/6] 激活虚拟环境并安装依赖...${NC}"
source venv/bin/activate

# 升级pip
pip install --upgrade pip --quiet

# 检查并安装依赖
if [ -f "requirements.txt" ]; then
    echo "正在安装依赖包..."
    pip install -r requirements.txt --quiet
    echo -e "${GREEN}✓ 依赖安装完成${NC}"
else
    echo -e "${RED}警告: 未找到requirements.txt${NC}"
fi
echo ""

# 检查环境变量文件
echo -e "${YELLOW}[4/6] 检查环境配置...${NC}"
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}未找到.env文件，正在创建默认配置...${NC}"
    cat > .env <<EOF
# Django配置
SECRET_KEY=$(python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,47.121.189.30,0.0.0.0

# 数据库配置
DB_NAME=elderly_tracking
DB_USER=root
DB_PASSWORD=
DB_HOST=localhost
DB_PORT=3306

# JWT配置
JWT_SECRET_KEY=$(python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')

# 高德地图API（可选）
AMAP_KEY=
AMAP_SECRET=
EOF
    echo -e "${GREEN}✓ .env文件已创建，请根据需要修改配置${NC}"
else
    echo -e "${GREEN}✓ .env文件已存在${NC}"
fi
echo ""

# 检查数据库配置
echo -e "${YELLOW}[5/6] 检查数据库配置...${NC}"
# 检查是否已配置使用SQLite
if grep -q "USE_SQLITE=True" .env 2>/dev/null; then
    echo -e "${GREEN}✓ 已配置使用SQLite数据库${NC}"
elif command -v mysql &> /dev/null; then
    echo -e "${GREEN}✓ 检测到MySQL，将使用MySQL数据库${NC}"
    echo -e "${YELLOW}  提示: 如果MySQL连接失败，可在.env中设置 USE_SQLITE=True 使用SQLite${NC}"
else
    echo -e "${YELLOW}⚠ 未检测到MySQL，将在.env中配置使用SQLite数据库${NC}"
    if ! grep -q "USE_SQLITE" .env; then
        echo "USE_SQLITE=True" >> .env
    fi
fi
echo ""

# 数据库迁移
echo -e "${YELLOW}[6/6] 执行数据库迁移...${NC}"
if python manage.py makemigrations --noinput 2>&1 | grep -q "No changes detected"; then
    echo "模型未变更，跳过makemigrations"
else
    python manage.py makemigrations --noinput 2>/dev/null || true
fi
python manage.py migrate --noinput
echo -e "${GREEN}✓ 数据库迁移完成${NC}"
echo ""

# 收集静态文件
echo -e "${YELLOW}收集静态文件...${NC}"
python manage.py collectstatic --noinput 2>/dev/null || echo "静态文件收集跳过"
echo ""

# 检查是否需要创建超级用户
echo -e "${YELLOW}检查管理员账户...${NC}"
if ! python manage.py shell -c "from apps.users.models import User; User.objects.filter(is_superuser=True).exists()" 2>/dev/null | grep -q "True"; then
    echo -e "${YELLOW}未找到超级用户，您可以稍后运行以下命令创建：${NC}"
    echo -e "${GREEN}  python manage.py createsuperuser${NC}"
fi
echo ""

# 启动服务器
echo "=========================================="
echo -e "${GREEN}启动Django开发服务器...${NC}"
echo "=========================================="
echo ""
echo -e "${GREEN}服务器将在 0.0.0.0:8000 启动（允许外部访问）${NC}"
echo -e "${YELLOW}本地访问: http://127.0.0.1:8000${NC}"
echo -e "${YELLOW}外部访问: http://47.121.189.30:8000${NC}"
echo -e "${YELLOW}管理后台: http://47.121.189.30:8000/admin/${NC}"
echo -e "${YELLOW}API接口: http://47.121.189.30:8000/api/${NC}"
echo ""
echo -e "${YELLOW}按 Ctrl+C 停止服务器${NC}"
echo ""

# 启动Django开发服务器（绑定到0.0.0.0允许外部访问）
python manage.py runserver 0.0.0.0:8000

