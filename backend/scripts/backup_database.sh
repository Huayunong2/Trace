#!/bin/bash
# 数据库备份脚本
# 使用方法: ./backup_database.sh
# 建议添加到crontab，每天凌晨执行: 0 2 * * * /root/Project/backend/scripts/backup_database.sh

set -e

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# 配置
PROJECT_DIR="/root/Project/backend"
BACKUP_DIR="${PROJECT_DIR}/backups"
DATE=$(date +%Y%m%d_%H%M%S)
KEEP_DAYS=30  # 保留30天的备份

# 从环境变量读取数据库配置（从.env文件）
if [ -f "${PROJECT_DIR}/.env" ]; then
    source "${PROJECT_DIR}/.env"
fi

DB_NAME=${DB_NAME:-"elderly_tracking"}
DB_USER=${DB_USER:-"root"}
DB_PASSWORD=${DB_PASSWORD:-""}
DB_HOST=${DB_HOST:-"localhost"}
DB_PORT=${DB_PORT:-"3306"}

echo -e "${YELLOW}开始数据库备份...${NC}"

# 创建备份目录
mkdir -p "${BACKUP_DIR}"

# 备份文件名
BACKUP_FILE="${BACKUP_DIR}/backup_${DB_NAME}_${DATE}.sql"

# 执行备份
if [ -n "$DB_PASSWORD" ]; then
    mysqldump -h"${DB_HOST}" -P"${DB_PORT}" -u"${DB_USER}" -p"${DB_PASSWORD}" \
        --single-transaction \
        --routines \
        --triggers \
        "${DB_NAME}" > "${BACKUP_FILE}"
else
    mysqldump -h"${DB_HOST}" -P"${DB_PORT}" -u"${DB_USER}" \
        --single-transaction \
        --routines \
        --triggers \
        "${DB_NAME}" > "${BACKUP_FILE}"
fi

# 压缩备份文件
if [ -f "${BACKUP_FILE}" ]; then
    gzip "${BACKUP_FILE}"
    BACKUP_FILE="${BACKUP_FILE}.gz"
    echo -e "${GREEN}✓ 备份完成: ${BACKUP_FILE}${NC}"
    
    # 显示文件大小
    FILE_SIZE=$(du -h "${BACKUP_FILE}" | cut -f1)
    echo -e "${GREEN}备份文件大小: ${FILE_SIZE}${NC}"
else
    echo -e "${RED}✗ 备份失败${NC}"
    exit 1
fi

# 清理旧备份
echo -e "${YELLOW}清理${KEEP_DAYS}天前的备份...${NC}"
find "${BACKUP_DIR}" -name "backup_*.sql.gz" -type f -mtime +${KEEP_DAYS} -delete
echo -e "${GREEN}✓ 清理完成${NC}"

# 可选：上传到云存储（OSS/S3等）
# 如果需要，可以在这里添加上传逻辑

echo -e "${GREEN}数据库备份任务完成${NC}"

