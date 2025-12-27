#!/bin/bash
# 生产环境部署脚本

set -e

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

PROJECT_DIR="/root/Project/backend"
VENV_DIR="${PROJECT_DIR}/venv"

echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}  生产环境部署脚本${NC}"
echo -e "${YELLOW}========================================${NC}"
echo ""

# 检查是否在生产环境
if [ -z "$DJANGO_SETTINGS_MODULE" ]; then
    export DJANGO_SETTINGS_MODULE="config.settings_prod"
fi

cd "${PROJECT_DIR}"

# 1. 激活虚拟环境
echo -e "${YELLOW}[1/8] 激活虚拟环境...${NC}"
source "${VENV_DIR}/bin/activate"

# 2. 拉取最新代码（如果有git）
# echo -e "${YELLOW}[2/8] 更新代码...${NC}"
# git pull  # 如果有使用git

# 3. 安装/更新依赖
echo -e "${YELLOW}[2/8] 安装依赖...${NC}"
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
echo -e "${GREEN}✓ 依赖安装完成${NC}"

# 4. 数据库迁移
echo -e "${YELLOW}[3/8] 执行数据库迁移...${NC}"
python manage.py migrate --noinput
echo -e "${GREEN}✓ 数据库迁移完成${NC}"

# 5. 收集静态文件
echo -e "${YELLOW}[4/8] 收集静态文件...${NC}"
python manage.py collectstatic --noinput --clear
echo -e "${GREEN}✓ 静态文件收集完成${NC}"

# 6. 创建缓存表（如果使用数据库缓存）
echo -e "${YELLOW}[5/8] 创建缓存表...${NC}"
python manage.py createcachetable 2>/dev/null || echo "缓存表已存在或不需要"
echo -e "${GREEN}✓ 缓存表检查完成${NC}"

# 7. 重启Gunicorn
echo -e "${YELLOW}[6/8] 重启Gunicorn服务...${NC}"
if systemctl is-active --quiet gunicorn-elderly-tracking; then
    sudo systemctl restart gunicorn-elderly-tracking
    echo -e "${GREEN}✓ Gunicorn服务已重启${NC}"
else
    echo -e "${YELLOW}Gunicorn服务未运行，请手动启动${NC}"
fi

# 8. 重启Celery（如果使用）
echo -e "${YELLOW}[7/8] 检查Celery服务...${NC}"
if systemctl is-active --quiet celery-elderly-tracking; then
    sudo systemctl restart celery-elderly-tracking
    echo -e "${GREEN}✓ Celery服务已重启${NC}"
else
    echo -e "${YELLOW}Celery服务未运行，跳过${NC}"
fi

# 9. 重载Nginx
echo -e "${YELLOW}[8/8] 重载Nginx配置...${NC}"
if sudo nginx -t 2>/dev/null; then
    sudo systemctl reload nginx
    echo -e "${GREEN}✓ Nginx配置已重载${NC}"
else
    echo -e "${RED}✗ Nginx配置有误，请检查${NC}"
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  部署完成！${NC}"
echo -e "${GREEN}========================================${NC}"

