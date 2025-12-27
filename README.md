# 防走失预警系统

基于微信小程序的老人防走失预警系统，通过实时定位、电子围栏和智能警报等功能，帮助监护人及时掌握老人的位置信息，防止老人走失。

## 📱 项目简介

本项目是一个面向老年人群体的防走失预警系统，主要功能包括：

- **实时定位追踪**：实时获取老人位置信息，支持历史轨迹查询
- **电子围栏**：设置安全区域，老人离开围栏范围时自动触发警报
- **智能警报系统**：支持围栏越界、SOS紧急求助、低电量等多种警报类型
- **多角色管理**：支持监护人、老人、系统管理员三种角色，角色权限严格隔离
- **设备管理**：支持多种设备类型（智能手环、手机）

## 🛠 技术栈

### 后端
- **框架**: Django 4.x + Django REST Framework
- **数据库**: SQLite（开发）/ PostgreSQL（生产推荐）
- **认证**: JWT (JSON Web Token)
- **API风格**: RESTful API

### 前端
- **框架**: 微信小程序原生框架
- **UI**: 自定义组件 + 微信小程序组件
- **地图**: 微信小程序地图API

## 📁 项目结构

```
Project/
├── backend/                 # 后端Django项目
│   ├── apps/               # 应用模块
│   │   ├── users/         # 用户管理
│   │   ├── devices/       # 设备管理
│   │   ├── locations/     # 位置管理
│   │   ├── fences/        # 电子围栏
│   │   ├── alerts/        # 警报管理
│   │   └── system/        # 系统管理
│   ├── config/            # 配置文件
│   └── manage.py          # Django管理脚本
├── miniprogram/            # 微信小程序前端
│   ├── pages/             # 页面文件
│   ├── images/            # 图片资源
│   ├── app.js             # 小程序入口
│   └── config.js          # 配置文件
└── README.md              # 项目说明文档
```

## 🚀 快速开始

### 环境要求

- Python 3.8+
- Django 4.x
- 微信开发者工具
- 微信小程序账号（用于开发测试）

### 后端部署

1. **克隆项目**
```bash
cd backend
```

2. **创建虚拟环境（推荐）**
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

3. **安装依赖**
```bash
pip install -r requirements.txt
```

4. **配置环境变量**

创建 `.env` 文件：
```env
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
WECHAT_APPID=your-wechat-appid
WECHAT_SECRET=your-wechat-secret
SUPER_ADMIN_OPENIDS=test_openid1,test_openid2
```

5. **数据库迁移**
```bash
python manage.py migrate
```

6. **创建超级用户（可选）**
```bash
python manage.py createsuperuser
```

7. **运行服务器**
```bash
python manage.py runserver
# 或使用gunicorn（生产环境）
gunicorn config.wsgi:application
```

后端API地址：`http://localhost:8000/api`

### 前端部署

1. **配置API地址**

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

2. **使用微信开发者工具**

- 打开微信开发者工具
- 选择"导入项目"
- 选择 `miniprogram` 目录
- 填写AppID（测试可以使用测试号）
- 点击"编译"

## 📋 功能模块

### 1. 用户认证

- 微信登录（使用2022年推荐的头像昵称填写方式）
- 角色选择（监护人/老人/系统管理员）
- JWT Token认证
- 身份隔离机制

### 2. 老人档案管理

- 创建、查看、编辑、删除老人档案
- 监护人管理多个老人档案
- 老人查看和管理自己的档案
- 紧急联系人信息管理

### 3. 设备管理

- 设备UUID生成（老人角色）
- 设备绑定（监护人通过设备ID绑定）
- 设备状态监控（在线/离线/低电量）
- 支持多种设备类型

### 4. 位置追踪

- 实时位置上传
- 当前位置查询
- 历史轨迹查询
- 地图显示

### 5. 电子围栏

- 创建圆形围栏（设置中心点和半径）
- 围栏激活/禁用
- 自动越界检测
- 围栏越界警报

### 6. 警报系统

- 围栏越界警报
- SOS紧急求助
- 低电量警报
- 警报列表和详情
- 警报处理

### 7. 系统管理（管理员）

- 用户管理
- 系统统计
- 系统配置

## 🔐 权限说明

### 监护人角色
- 创建和管理老人档案
- 查看管理的老人设备位置
- 创建和管理电子围栏
- 接收和处理警报
- 绑定设备到老人档案

### 老人角色
- 创建自己的档案
- 生成设备UUID
- 查看自己的设备信息
- 查看自己的位置信息
- 触发SOS警报

### 系统管理员角色
- 查看所有用户
- 管理系统配置
- 查看系统统计信息
- 修改用户角色

## 📡 API文档

详细API文档请参考：[API_DOCUMENTATION.md](./API_DOCUMENTATION.md)

## 🧪 测试

运行单元测试：

```bash
cd backend
python manage.py test
```

测试覆盖范围：
- 用户模型和API测试
- 设备模型测试
- 围栏功能测试

## 📝 开发说明

### 数据库迁移

```bash
# 创建迁移文件
python manage.py makemigrations

# 执行迁移
python manage.py migrate
```

### 日志

日志文件位于 `backend/logs/`：
- `django.log`: Django应用日志
- `server.log`: 服务器日志

### 代码规范

- 后端：遵循PEP 8 Python代码规范
- 前端：遵循微信小程序开发规范

## 🔧 配置说明

### 后端配置

主要配置文件：`backend/config/settings.py`

关键配置项：
- `DEBUG`: 调试模式（生产环境需设为False）
- `ALLOWED_HOSTS`: 允许的主机
- `WECHAT_APPID`: 微信小程序AppID
- `WECHAT_SECRET`: 微信小程序Secret
- `FENCE_VIOLATION_THRESHOLD`: 围栏越界触发阈值（默认1次）

### 前端配置

主要配置文件：`miniprogram/config.js`

- `ENV`: 环境（development/production）
- `apiBaseUrl`: API基础地址

## 🚨 注意事项

1. **生产环境部署**
   - 关闭DEBUG模式
   - 配置安全的SECRET_KEY
   - 使用HTTPS
   - 配置正确的ALLOWED_HOSTS
   - 使用生产级数据库（推荐PostgreSQL）

2. **微信小程序配置**
   - 在微信公众平台配置服务器域名
   - 配置合法域名（API域名、地图服务域名等）
   - 配置业务域名（如需要）

3. **数据安全**
   - 位置信息属于敏感数据，需做好数据加密
   - 定期备份数据库
   - 遵循数据保护相关法规

## 📄 许可证

本项目为毕业设计项目，仅供学习和研究使用。

## 👥 作者

毕业设计项目

## 📞 联系方式

如有问题，请通过以下方式联系：
- 提交Issue
- 发送邮件

## 🙏 致谢

- Django REST Framework
- 微信小程序开发团队
- 所有开源贡献者

