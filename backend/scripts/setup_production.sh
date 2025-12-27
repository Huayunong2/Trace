#!/bin/bash
# 生产环境初始化脚本

set -e

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

PROJECT_DIR="/root/Project/backend"

echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}  生产环境初始化脚本${NC}"
echo -e "${YELLOW}========================================${NC}"
echo ""

cd "${PROJECT_DIR}"

# 1. 检查.env文件
echo -e "${YELLOW}[1/6] 检查环境变量配置...${NC}"
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo -e "${YELLOW}复制.env.example为.env，请编辑后重新运行此脚本${NC}"
        cp .env.example .env
        echo -e "${RED}请编辑 .env 文件，配置所有必需的变量${NC}"
        exit 1
    else
        echo -e "${RED}错误: .env文件不存在，且没有.env.example${NC}"
        exit 1
    fi
fi

# 检查必需的环境变量
source .env
if [ -z "$SECRET_KEY" ] || [ "$SECRET_KEY" = "your-secret-key-here-change-this-in-production" ]; then
    echo -e "${RED}错误: SECRET_KEY未配置或使用默认值${NC}"
    exit 1
fi

if [ -z "$ALLOWED_HOSTS" ] || [ "$ALLOWED_HOSTS" = "your-domain.com" ]; then
    echo -e "${RED}错误: ALLOWED_HOSTS未配置或使用默认值${NC}"
    exit 1
fi

echo -e "${GREEN}✓ 环境变量配置检查通过${NC}"

# 2. 生成SECRET_KEY（如果使用默认值）
echo -e "${YELLOW}[2/6] 检查SECRET_KEY...${NC}"
if grep -q "your-secret-key-here" .env; then
    echo -e "${YELLOW}生成新的SECRET_KEY...${NC}"
    NEW_SECRET_KEY=$(python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")
    sed -i "s/SECRET_KEY=.*/SECRET_KEY=${NEW_SECRET_KEY}/" .env
    echo -e "${GREEN}✓ SECRET_KEY已生成${NC}"
fi

# 3. 激活虚拟环境
echo -e "${YELLOW}[3/6] 设置虚拟环境...${NC}"
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✓ 虚拟环境已创建${NC}"
fi

source venv/bin/activate
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
pip install gunicorn --quiet  # 安装Gunicorn
echo -e "${GREEN}✓ 依赖已安装${NC}"

# 4. 数据库迁移
echo -e "${YELLOW}[4/6] 执行数据库迁移...${NC}"
export DJANGO_SETTINGS_MODULE=config.settings_prod
python manage.py migrate --noinput
echo -e "${GREEN}✓ 数据库迁移完成${NC}"

# 5. 收集静态文件
echo -e "${YELLOW}[5/6] 收集静态文件...${NC}"
python manage.py collectstatic --noinput --clear
echo -e "${GREEN}✓ 静态文件收集完成${NC}"

# 6. 创建缓存表
echo -e "${YELLOW}[6/6] 创建缓存表...${NC}"
python manage.py createcachetable 2>/dev/null || echo "缓存表已存在"
echo -e "${GREEN}✓ 缓存表检查完成${NC}"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  初始化完成！${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}下一步：${NC}"
echo -e "1. 创建超级用户: python manage.py createsuperuser"
echo -e "2. 配置Nginx: 参考 nginx.conf.example"
echo -e "3. 配置systemd服务: 参考 systemd/ 目录"
echo -e "4. 启动服务: sudo systemctl start gunicorn-elderly-tracking"

