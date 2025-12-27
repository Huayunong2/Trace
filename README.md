# 👴 防走失预警系统 v1.0.5

<div align="center">

基于微信小程序的智能老人防走失预警系统，通过实时定位、电子围栏和智能警报等功能，帮助监护人及时掌握老人的位置信息，有效防止老人走失。

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-4.x-green.svg)](https://www.djangoproject.com/)
[![WeChat MiniProgram](https://img.shields.io/badge/WeChat-MiniProgram-07C160.svg)](https://developers.weixin.qq.com/miniprogram/dev/framework/)

</div>

---

## 📋 目录

- [项目简介](#-项目简介)
- [核心功能](#-核心功能)
- [技术架构](#-技术架构)
- [快速开始](#-快速开始)
- [功能模块](#-功能模块)
- [权限说明](#-权限说明)
- [配置说明](#-配置说明)
- [部署指南](#-部署指南)
- [开发指南](#-开发指南)
- [常见问题](#-常见问题)

---

## 🎯 项目简介

防走失预警系统是一个面向老年人群体的智能定位与预警平台，旨在通过现代化的技术手段，为监护人提供实时、准确的老人位置信息和安全预警服务。系统采用微信小程序作为用户入口，后端基于Django REST Framework构建，支持多种设备接入和实时数据同步。

### ✨ 核心特色

- 🎯 **实时定位追踪**：支持GPS定位，实时获取老人位置，历史轨迹可查询
- 🛡️ **智能电子围栏**：创建安全区域，自动检测越界并触发警报
- 🚨 **多类型警报系统**：围栏越界、SOS紧急求助、设备离线、低电量警报
- 📱 **微信订阅消息推送**：重要警报实时推送至监护人微信，不遗漏任何紧急情况
- 👥 **多角色权限管理**：监护人、老人、系统管理员三种角色，权限严格隔离
- 📊 **可视化数据展示**：地图展示、轨迹回放、统计图表
- 🔒 **安全可靠**：JWT认证、数据加密、权限控制

---

## 💡 核心功能

### 1. 实时定位追踪
- 实时位置上传与查询
- 历史轨迹查询与回放
- 地图可视化展示
- 位置信息加密存储

### 2. 电子围栏管理
- 创建圆形电子围栏（中心点+半径）
- 围栏激活/禁用控制
- 自动越界检测
- 越界警报实时推送

### 3. 智能警报系统
- **围栏越界警报**：老人离开安全区域时自动触发
- **SOS紧急求助**：老人主动触发一键求救
- **设备离线警报**：设备长时间未上报位置时触发
- **低电量警报**：设备电量过低时提醒
- 警报分级处理（紧急/一般）
- 批量处理与清理功能

### 4. 微信订阅消息推送
- 订阅消息模板管理
- 实时推送警报通知至微信
- 推送失败自动重试机制
- 订阅状态动态管理

### 5. 老人档案管理
- 完整的老人信息管理
- 紧急联系人信息
- 多监护人对多老人的管理
- 设备绑定与管理

### 6. 系统管理
- 用户管理与权限分配
- 系统配置管理
- 数据统计与分析
- 日志查询与管理

---

## 🏗️ 技术架构

### 后端技术栈

| 技术 | 版本 | 说明 |
|------|------|------|
| Python | 3.8+ | 编程语言 |
| Django | 4.x | Web框架 |
| Django REST Framework | 3.x | RESTful API框架 |
| MySQL / SQLite | - | 数据库 |
| Celery | - | 异步任务队列 |
| Redis | - | 缓存与消息队列 |
| JWT | - | 身份认证 |
| PyMySQL | - | MySQL驱动 |

### 前端技术栈

| 技术 | 说明 |
|------|------|
| 微信小程序原生框架 | 小程序开发框架 |
| 微信小程序地图API | 地图展示与定位 |
| 微信订阅消息API | 消息推送 |

### 系统架构

```
┌─────────────────┐
│  微信小程序前端  │
│  (miniprogram)  │
└────────┬────────┘
         │ HTTPS/WebSocket
         │
┌────────▼────────────────────────┐
│    Django REST Framework API   │
│         (backend)               │
├─────────────────────────────────┤
│  - 用户认证 (JWT)               │
│  - 位置追踪                     │
│  - 围栏管理                     │
│  - 警报处理                     │
└────────┬────────┬───────────────┘
         │        │
    ┌────▼────┐ ┌─▼────────┐
    │  MySQL  │ │  Redis   │
    │ Database│ │  Cache   │
    └─────────┘ └──────────┘
         │
    ┌────▼────┐
    │  Celery │
    │ Workers │
    └─────────┘
         │
    ┌────▼────┐
    │ WeChat  │
    │  API    │
    └─────────┘
```

---

## 🚀 快速开始

### 环境要求

- Python 3.8+
- MySQL 5.7+ (或使用SQLite)
- Redis (可选，用于缓存)
- 微信开发者工具
- 微信小程序账号

### 1. 克隆项目

```bash
git clone <repository-url>
cd Project
```

### 2. 后端部署

#### 方式一：使用启动脚本（推荐）

```bash
chmod +x start.sh
./start.sh
```

#### 方式二：手动部署

```bash
cd backend

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入必要的配置

# 数据库迁移
python manage.py migrate

# 创建超级用户（可选）
python manage.py createsuperuser

# 启动开发服务器
python manage.py runserver
```

后端API地址：`http://localhost:8000/api`

### 3. 前端部署

1. **使用微信开发者工具**
   - 打开微信开发者工具
   - 选择"导入项目"
   - 选择 `miniprogram` 目录
   - 填写AppID（可使用测试号）
   - 点击"编译"

2. **配置API地址**

   编辑 `miniprogram/config.js`：
   ```javascript
   const ENV = 'development'; // 或 'production'
   
   const API_CONFIG = {
     development: {
       baseUrl: 'https://your-ngrok-url.ngrok-free.dev/api',
     },
     production: {
       baseUrl: 'https://your-production-domain.com/api',
     }
   };
   ```

### 4. 微信小程序配置

在微信公众平台配置：

1. **服务器域名配置**
   - 登录微信公众平台
   - 开发 → 开发管理 → 开发设置
   - 配置request合法域名（API服务器地址）
   - 配置socket合法域名（如使用WebSocket）

2. **订阅消息配置**
   - 订阅消息 → 公共模板库
   - 选择并添加以下模板：
     - 老年人越界提醒
     - 老人紧急呼叫求助通知
     - 设备状态异常通知

---

## 📦 功能模块

### 用户认证模块

- 微信登录（使用2022年推荐的头像昵称填写方式）
- 角色选择（监护人/老人/系统管理员）
- JWT Token认证
- Token自动刷新
- 身份隔离机制

### 老人档案管理模块

- 创建、查看、编辑、删除老人档案
- 监护人管理多个老人档案
- 老人查看和管理自己的档案
- 紧急联系人信息管理
- 头像与基本信息管理

### 设备管理模块

- 设备UUID生成（老人角色）
- 设备绑定（监护人通过设备ID绑定）
- 设备状态监控（在线/离线/低电量）
- 设备信息管理
- 支持多种设备类型

### 位置追踪模块

- 实时位置上传（GPS定位）
- 当前位置查询
- 历史轨迹查询与回放
- 地图可视化展示
- 位置数据存储与管理

### 电子围栏模块

- 创建圆形围栏（设置中心点和半径）
- 围栏列表管理
- 围栏激活/禁用
- 自动越界检测（Celery异步任务）
- 围栏越界警报生成

### 警报系统模块

- **警报类型**：
  - 围栏越界警报
  - SOS紧急求助
  - 设备离线警报
  - 低电量警报
- 警报列表与筛选（全部/待处理/已处理）
- 警报详情查看
- 警报处理与批量处理
- 已处理警报清理
- 警报分级（紧急/一般）

### 微信推送模块

- 订阅消息模板管理
- 用户订阅状态管理
- 实时推送警报通知
- 推送失败重试机制
- Access Token缓存管理

### 系统管理模块（管理员）

- 用户列表与详情
- 用户角色管理
- 系统配置管理
- 数据统计与报表
- 日志查询

---

## 🔐 权限说明

### 监护人角色

- ✅ 创建和管理老人档案
- ✅ 查看管理的老人设备位置
- ✅ 创建和管理电子围栏
- ✅ 接收和处理警报
- ✅ 绑定设备到老人档案
- ✅ 查看历史轨迹
- ❌ 查看其他监护人的数据

### 老人角色

- ✅ 创建和管理自己的档案
- ✅ 生成设备UUID
- ✅ 查看自己的设备信息
- ✅ 查看自己的位置信息
- ✅ 上传位置信息
- ✅ 触发SOS警报
- ❌ 查看其他老人的数据

### 系统管理员角色

- ✅ 查看所有用户
- ✅ 管理系统配置
- ✅ 查看系统统计信息
- ✅ 修改用户角色
- ✅ 访问Django Admin后台

---

## ⚙️ 配置说明

### 后端环境变量配置

创建 `backend/.env` 文件：

```env
# Django配置
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,your-domain.com

# 数据库配置
USE_SQLITE=False  # 设置为True使用SQLite
DB_NAME=elderly_tracking
DB_USER=root
DB_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=3306

# JWT配置
JWT_SECRET_KEY=your-jwt-secret-key

# 微信小程序配置
WECHAT_APPID=your-wechat-appid
WECHAT_SECRET=your-wechat-secret

# 微信订阅消息模板ID（可选，可在后台配置）
WECHAT_TEMPLATE_FENCE_VIOLATION=vwOW-gQe_HZOxvu7cjduB8ZMjQEPLpwu2w6FgNSzhSg
WECHAT_TEMPLATE_DEVICE_OFFLINE=6dVj7hpIRDy_zTaOMjPEvAdcwR3nIKcRMMZ-JFxFl9M
WECHAT_TEMPLATE_LOW_BATTERY=6dVj7hpIRDy_zTaOMjPEvAdcwR3nIKcRMMZ-JFxFl9M
WECHAT_TEMPLATE_SOS=hU3HDKaWcVL4P8HbntKk5DbgDlV9gW-6f_-w4k8yY7o

# 超级管理员OpenID（多个用逗号分隔）
SUPER_ADMIN_OPENIDS=openid1,openid2

# Redis配置（可选，用于缓存）
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Celery配置（可选）
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2
```

### 前端配置

编辑 `miniprogram/config.js`：

```javascript
const ENV = 'development'; // 'development' | 'production'

const API_CONFIG = {
  development: {
    baseUrl: 'https://your-ngrok-url.ngrok-free.dev/api',
  },
  production: {
    baseUrl: 'https://your-production-domain.com/api',
  }
};

module.exports = {
  ENV,
  ...API_CONFIG[ENV]
};
```

### 微信订阅消息模板配置

系统支持以下订阅消息模板：

1. **老年人越界提醒**
   - 模板ID：`vwOW-gQe_HZOxvu7cjduB8ZMjQEPLpwu2w6FgNSzhSg`
   - 字段：越界时间(time1)、越界地点(thing2)

2. **老人紧急呼叫求助通知**
   - 模板ID：`hU3HDKaWcVL4P8HbntKk5DbgDlV9gW-6f_-w4k8yY7o`
   - 字段：老人姓名(thing1)、触发时间(time4)

3. **设备状态异常通知**
   - 模板ID：`6dVj7hpIRDy_zTaOMjPEvAdcwR3nIKcRMMZ-JFxFl9M`
   - 字段：时间(time1)、异常状态(phrase2)
   - 用于：设备离线、低电量

---

## 🚢 部署指南

### 生产环境部署

#### 1. 后端部署

```bash
# 使用Gunicorn启动（推荐）
pip install gunicorn
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4

# 使用Nginx反向代理
# 配置Nginx指向 http://127.0.0.1:8000
```

#### 2. 数据库迁移

```bash
python manage.py migrate
python manage.py collectstatic --noinput
```

#### 3. 环境变量配置

- 设置 `DEBUG=False`
- 配置安全的 `SECRET_KEY`
- 配置正确的 `ALLOWED_HOSTS`
- 使用HTTPS协议

#### 4. 安全配置

- 启用HTTPS
- 配置CORS允许的域名
- 设置数据库密码
- 定期备份数据库

### Docker部署（可选）

```dockerfile
# Dockerfile示例
FROM python:3.9
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
```

---

## 🛠️ 开发指南

### 项目结构

```
Project/
├── backend/                    # 后端Django项目
│   ├── apps/                  # 应用模块
│   │   ├── users/            # 用户管理
│   │   │   ├── models.py     # 用户模型
│   │   │   ├── views.py      # API视图
│   │   │   ├── serializers.py # 序列化器
│   │   │   └── wechat_push.py # 微信推送服务
│   │   ├── devices/          # 设备管理
│   │   ├── locations/        # 位置管理
│   │   ├── fences/           # 电子围栏
│   │   │   └── tasks.py      # 围栏检测异步任务
│   │   ├── alerts/           # 警报管理
│   │   └── system/           # 系统管理
│   ├── config/               # 配置文件
│   │   ├── settings.py       # Django配置
│   │   ├── urls.py           # URL路由
│   │   └── middleware.py     # 中间件
│   ├── manage.py             # Django管理脚本
│   ├── requirements.txt      # Python依赖
│   └── .env                  # 环境变量配置
├── miniprogram/              # 微信小程序前端
│   ├── pages/                # 页面文件
│   │   ├── login/           # 登录页面
│   │   ├── index/           # 首页
│   │   ├── map/             # 地图页面
│   │   ├── fence/           # 围栏管理
│   │   ├── track/           # 轨迹查询
│   │   ├── alert/           # 警报列表
│   │   ├── profile/         # 个人中心
│   │   ├── elderly/         # 老人档案
│   │   └── admin/           # 管理员页面
│   ├── utils/                # 工具函数
│   │   └── subscribe.js      # 订阅消息工具
│   ├── images/               # 图片资源
│   ├── app.js                # 小程序入口
│   ├── app.json              # 小程序配置
│   └── config.js             # API配置
├── start.sh                   # 一键启动脚本
├── sub.md                     # 订阅消息模板说明
└── README.md                  # 项目说明文档
```

### 数据库迁移

```bash
# 创建迁移文件
python manage.py makemigrations

# 执行迁移
python manage.py migrate

# 查看迁移状态
python manage.py showmigrations
```

### 代码规范

- **后端**：遵循 PEP 8 Python 代码规范
- **前端**：遵循微信小程序开发规范
- 使用 ESLint 检查前端代码
- 使用 Black 格式化 Python 代码（可选）

### 日志管理

日志文件位于 `backend/logs/`：

- `django.log`：Django 应用日志
- `server.log`：服务器日志
- `celery.log`：Celery 任务日志

日志级别：
- `DEBUG`：开发环境详细日志
- `INFO`：一般信息
- `WARNING`：警告信息
- `ERROR`：错误信息

### API 开发

1. **创建新的 API 端点**

```python
# backend/apps/xxx/views.py
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

class YourViewSet(viewsets.ModelViewSet):
    queryset = YourModel.objects.all()
    serializer_class = YourSerializer
    
    @action(detail=False, methods=['get'])
    def custom_action(self, request):
        return Response({'message': 'Hello'})
```

2. **配置 URL 路由**

```python
# backend/config/urls.py
from rest_framework.routers import DefaultRouter
from apps.xxx.views import YourViewSet

router = DefaultRouter()
router.register(r'your-endpoint', YourViewSet)
```

### 前端开发

1. **页面开发**

```javascript
// miniprogram/pages/xxx/xxx.js
Page({
  data: {
    // 页面数据
  },
  onLoad() {
    // 页面加载
  },
  onShow() {
    // 页面显示
  }
})
```

2. **API 请求**

```javascript
// 使用封装的 request 方法
const app = getApp();
app.request({
  url: '/api/endpoint/',
  method: 'POST',
  data: { key: 'value' }
}).then(res => {
  // 处理响应
}).catch(err => {
  // 处理错误
});
```

---

## ❓ 常见问题

### 1. 微信登录失败

**问题**：微信登录提示失败或无法获取用户信息

**解决方案**：
- 检查 `WECHAT_APPID` 和 `WECHAT_SECRET` 是否正确配置
- 确认微信开发者工具中使用的 AppID 与后端配置一致
- 检查网络连接，确保可以访问微信 API

### 2. 定位权限被拒绝

**问题**：小程序无法获取位置信息

**解决方案**：
- 在微信开发者工具中设置位置信息权限
- 真机调试时，需要在系统设置中允许小程序获取位置权限
- 检查 `app.json` 中的 `permission` 配置

### 3. 订阅消息推送不工作

**问题**：收到警报但微信中没有推送通知

**解决方案**：
- 确认用户已订阅消息模板（在相关页面触发订阅）
- 检查后端日志，查看推送失败的错误码
- 错误码 `43101`：用户未订阅，需要重新订阅
- 错误码 `43104`：用户拒绝接收，需要在设置中重新授权
- 确认模板 ID 配置正确

### 4. 数据库连接失败

**问题**：无法连接 MySQL 数据库

**解决方案**：
- 检查数据库服务是否启动
- 确认 `.env` 文件中的数据库配置正确
- 检查数据库用户权限
- 如果 MySQL 不可用，可在 `.env` 中设置 `USE_SQLITE=True` 使用 SQLite

### 5. Celery 任务不执行

**问题**：围栏检测等异步任务未执行

**解决方案**：
- 确认 Redis 服务已启动
- 检查 Celery Worker 是否运行：`celery -A config worker -l info`
- 检查 `CELERY_BROKER_URL` 配置是否正确
- 查看 Celery 日志排查问题

### 6. API 请求跨域错误

**问题**：前端请求 API 时出现 CORS 错误

**解决方案**：
- 检查 `CORS_ALLOWED_ORIGINS` 配置
- 确认后端 `ALLOWED_HOSTS` 包含前端域名
- 开发环境可以使用 `CORS_ALLOW_ALL_ORIGINS=True`（仅开发环境）

### 7. 生产环境部署问题

**问题**：生产环境部署后出现各种问题

**解决方案**：
- 确认 `DEBUG=False`
- 检查 `SECRET_KEY` 是否安全
- 配置正确的 `ALLOWED_HOSTS`
- 使用 HTTPS 协议
- 配置 Nginx 反向代理
- 使用 Gunicorn 等 WSGI 服务器
- 定期备份数据库

---

## 📚 相关文档

- [微信小程序开发文档](https://developers.weixin.qq.com/miniprogram/dev/framework/)
- [Django REST Framework 文档](https://www.django-rest-framework.org/)
- [微信订阅消息文档](https://developers.weixin.qq.com/miniprogram/dev/api-backend/open-api/subscribe-message/subscribeMessage.send.html)
- [Celery 文档](https://docs.celeryproject.org/)

---

## 🔄 版本历史

### v1.0.5 (当前版本)

- ✨ 新增版本号显示功能
- ✨ 优化微信推送机制
- ✨ 新增清理已处理警报功能
- 🐛 修复订阅消息 API 500 错误
- 🐛 修复用户权限隔离问题
- 📝 完善项目文档

### v1.0.0

- 🎉 项目初始版本
- ✨ 基础功能实现

---

## 📄 许可证

本项目为毕业设计项目，仅供学习和研究使用。

---


<div align="center">

**⭐ 如果这个项目对你有帮助，请给一个 Star ⭐**

Made with ❤️ by the development team

</div>