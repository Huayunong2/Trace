// 项目配置文件
// 用于管理不同环境的API地址和其他配置

// 环境配置
// development: 开发环境（使用ngrok）
// production: 生产环境（使用正式域名）
const ENV = 'development'; // 或 'production'

// API配置
const API_CONFIG = {
  development: {
    // 开发环境：使用ngrok地址（需要根据实际ngrok域名修改）
    baseUrl: 'https://unattired-toploftily-margarete.ngrok-free.dev/api',
  },
  production: {
    // 生产环境：使用正式域名
    baseUrl: 'https://your-production-domain.com/api',
  }
};

// 获取当前环境的配置
const currentConfig = API_CONFIG[ENV] || API_CONFIG.development;

// 导出配置
module.exports = {
  // API基础地址
  apiBaseUrl: currentConfig.baseUrl,
  
  // 当前环境
  env: ENV,
  
  // 是否开发环境
  isDevelopment: ENV === 'development',
  
  // 是否生产环境
  isProduction: ENV === 'production',
  
  // 完整配置（供扩展使用）
  config: currentConfig,
};

