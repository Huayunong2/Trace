// app.js
const config = require('./config.js');

App({
  globalData: {
    userInfo: null,
    token: null,
    userRole: 'guardian',  // 用户角色：guardian(监护人)、community_admin(社区管理员)、system_admin(系统管理员)
    apiBaseUrl: config.apiBaseUrl, // 从配置文件读取API地址
    currentDeviceId: null, // 当前选择的设备ID（用于tabBar页面跳转）
  },

  onLaunch() {
    // 检查本地存储的token，如果存在则恢复登录状态
    const token = wx.getStorageSync('token');
    const userRole = wx.getStorageSync('userRole');
    
    if (token) {
      // 有token，恢复登录状态
      this.globalData.token = token;
      if (userRole) {
        this.globalData.userRole = userRole;
      }
      
      // 验证token是否有效（通过获取用户信息）
      this.getUserInfo().then(userInfo => {
        this.globalData.userInfo = userInfo;
        // 保存角色信息
        if (userInfo && userInfo.role) {
          this.globalData.userRole = userInfo.role;
          wx.setStorageSync('userRole', userInfo.role);
        }
        // 根据角色跳转到对应页面
        this.checkRoleAndNavigate();
      }).catch(() => {
        this.globalData.token = null;
        wx.removeStorageSync('token');
        wx.removeStorageSync('userRole');
        wx.reLaunch({
          url: '/pages/login/login'
        });
      });
    } else {
      // 没有token，跳转到登录页
      wx.reLaunch({
        url: '/pages/login/login'
      });
    }
  },

  // 微信登录
  wxLogin() {
    return new Promise((resolve, reject) => {
      wx.login({
        success: (res) => {
          if (res.code) {
            // 发送code到后端
            this.request({
              url: '/auth/users/login/',
              method: 'POST',
              data: { code: res.code }
            }).then(result => {
          if (result.token) {
            this.globalData.token = result.token;
            wx.setStorageSync('token', result.token);
            this.globalData.userInfo = result.user;
            // 保存用户角色信息
            if (result.user && result.user.role) {
              this.globalData.userRole = result.user.role;
              wx.setStorageSync('userRole', result.user.role);
            }
            resolve(result);
          } else {
            reject(new Error('登录失败'));
          }
            }).catch(reject);
          } else {
            reject(new Error('获取code失败'));
          }
        },
        fail: reject
      });
    });
  },

  // 获取用户信息
  getUserInfo() {
    if (!this.globalData.token) {
      return Promise.reject(new Error('未登录'));
    }
    
    return this.request({
      url: '/auth/users/me/',
      method: 'GET'
    }).then(result => {
      this.globalData.userInfo = result;
      // 更新用户角色
      if (result && result.role) {
        this.globalData.userRole = result.role;
        wx.setStorageSync('userRole', result.role);
      }
      return result;
    }).catch(err => {
      // 如果是认证失败，清除token并跳转到登录页
      if (err.statusCode === 401 || err.statusCode === 403) {
        this.globalData.token = null;
        this.globalData.userInfo = null;
        this.globalData.userRole = null;
        wx.removeStorageSync('token');
        wx.removeStorageSync('userRole');
        wx.reLaunch({
          url: '/pages/login/login'
        });
      }
      return Promise.reject(err);
    });
  },

  // 检查用户角色并导航到对应页面
  checkRoleAndNavigate() {
    const role = this.globalData.userRole || this.globalData.userInfo?.role || 'guardian';
    
    // 获取当前页面路径
    const pages = getCurrentPages();
    const currentPage = pages[pages.length - 1];
    const currentRoute = currentPage ? currentPage.route : '';
    
    // 如果是登录页，根据角色跳转
    if (currentRoute === 'pages/login/login' && this.globalData.token) {
      if (role === 'elderly') {
        wx.reLaunch({
          url: '/pages/elderly/index/index'
        });
      } else if (role === 'system_admin') {
        wx.reLaunch({
          url: '/pages/admin/index/index'
        });
      } else {
        // 监护人和其他角色
        wx.switchTab({
          url: '/pages/index/index'
        });
      }
    }
  },

  // 检查用户是否有权限执行操作
  hasPermission(requiredRole) {
    const roleHierarchy = {
      'guardian': 1,
      'community_admin': 2,
      'system_admin': 3
    };
    
    const userLevel = roleHierarchy[this.globalData.userRole] || 1;
    const requiredLevel = roleHierarchy[requiredRole] || 1;
    
    return userLevel >= requiredLevel;
  },

  // 统一请求方法
        request(options) {
          return new Promise((resolve, reject) => {
            const header = {
              'Content-Type': 'application/json'
            };
            
            if (this.globalData.token) {
              header['Authorization'] = `Bearer ${this.globalData.token}`;
            }
            
            // ngrok免费版需要添加浏览器验证header
            if (this.globalData.apiBaseUrl.includes('ngrok-free.dev')) {
              header['ngrok-skip-browser-warning'] = 'any';
            }
            
            // 是否静默处理错误（不显示toast提示）
            const silent = options.silent || false;
            
            wx.request({
              url: this.globalData.apiBaseUrl + options.url,
              method: options.method || 'GET',
              data: options.data || {},
              header: header,
              timeout: options.timeout || 60000, // 默认60秒超时（ngrok可能较慢）
        success: (res) => {
          // 检查返回的是否是 HTML（ngrok 验证页面）
          const contentType = res.header['content-type'] || res.header['Content-Type'] || '';
          const isHtml = typeof res.data === 'string' && (
            res.data.trim().startsWith('<!DOCTYPE') || 
            res.data.trim().startsWith('<html') ||
            contentType.includes('text/html')
          );
          
          // 如果是HTML响应，检查是否是错误页面
          if (isHtml) {
            const htmlContent = typeof res.data === 'string' ? res.data : '';
            
            // 检查是否是Django错误页面
            if (htmlContent.includes('Internal Server Error') || 
                htmlContent.includes('DisallowedHost') ||
                htmlContent.includes('Page not found')) {
              let errorMsg = `服务器错误 (${res.statusCode})`;
              if (htmlContent.includes('DisallowedHost')) {
                errorMsg = '服务器配置错误，请联系管理员';
              } else if (htmlContent.includes('Page not found')) {
                errorMsg = '接口不存在，请检查API地址';
              } else if (res.statusCode === 500) {
                errorMsg = '服务器内部错误，请稍后重试';
              }
              reject(new Error(errorMsg));
              return;
            }
            
            // 检查是否是ngrok验证页面（排除503等服务器错误）
            if (res.statusCode !== 503 && res.statusCode !== 502 && res.statusCode !== 500 &&
                (htmlContent.includes('ngrok') || 
                 htmlContent.includes('browser-warning') ||
                 htmlContent.includes('ngrok-free.dev'))) {
              wx.showToast({
                title: '服务连接异常，请检查网络',
                icon: 'none',
                duration: 3000
              });
              reject(new Error('服务连接异常'));
              return;
            }
            
            // 503等服务器错误直接返回错误信息
            if (res.statusCode === 503 || res.statusCode === 502 || res.statusCode === 500) {
              let errorMsg = `服务器错误 (${res.statusCode})`;
              if (res.statusCode === 503) {
                errorMsg = '服务暂时不可用，请稍后重试';
              } else if (res.statusCode === 502) {
                errorMsg = '网关错误，请检查服务';
              }
              reject(new Error(errorMsg));
              return;
            }
            
            // 其他HTML错误
            reject(new Error(`服务器返回错误 (${res.statusCode})`));
            return;
          }
          
          if (res.statusCode === 200 || res.statusCode === 201 || res.statusCode === 204) {
            // 200: OK, 201: Created, 204: No Content - 都是成功状态
            // 204通常用于DELETE请求，没有响应体
            resolve(res.statusCode === 204 ? { statusCode: 204 } : res.data);
          } else if (res.statusCode === 401) {
            // token过期，清除登录状态并跳转到登录页
            this.globalData.token = null;
            this.globalData.userInfo = null;
            this.globalData.userRole = null;
            wx.removeStorageSync('token');
            wx.removeStorageSync('userRole');
            wx.showToast({
              title: '登录已过期',
              icon: 'none'
            });
            setTimeout(() => {
              wx.reLaunch({
                url: '/pages/login/login'
              });
            }, 1500);
            reject(new Error('登录已过期'));
          } else {
            // 尝试从 JSON 响应中提取错误信息
            let errorMsg = `请求失败(${res.statusCode})`;
            let errorDetails = '';
            
            if (res.data) {
              if (typeof res.data === 'object') {
                // 处理Django REST Framework的错误格式
                if (res.data.detail) {
                  errorMsg = res.data.detail;
                } else if (res.data.error) {
                  errorMsg = res.data.error;
                } else if (res.data.message) {
                  errorMsg = res.data.message;
                } else if (res.data.non_field_errors) {
                  // 非字段错误
                  errorMsg = Array.isArray(res.data.non_field_errors) 
                    ? res.data.non_field_errors.join(', ') 
                    : res.data.non_field_errors;
                } else {
                  // 字段错误
                  const fieldErrors = [];
                  for (const key in res.data) {
                    if (Array.isArray(res.data[key])) {
                      fieldErrors.push(`${key}: ${res.data[key].join(', ')}`);
                    } else {
                      fieldErrors.push(`${key}: ${res.data[key]}`);
                    }
                  }
                  if (fieldErrors.length > 0) {
                    errorMsg = fieldErrors.join('; ');
                  }
                }
                errorDetails = JSON.stringify(res.data);
              } else if (typeof res.data === 'string' && !isHtml) {
                try {
                  const jsonData = JSON.parse(res.data);
                  errorMsg = jsonData.error || jsonData.detail || jsonData.message || errorMsg;
                  errorDetails = res.data;
                } catch (e) {
                  // 不是 JSON，使用默认错误信息
                  errorDetails = res.data;
                }
              }
            }
            
            // 判断是否是正常情况（不需要显示错误）
            // 204 No Content 是 DELETE 请求的正常返回，应该视为成功
            const isNormalCase = res.statusCode === 204 || (res.statusCode === 404 && errorMsg.includes('未找到位置信息'));
            
            // 如果是204状态码，视为成功
            if (res.statusCode === 204) {
              resolve({ statusCode: 204, data: null });
              return;
            }
            
            
            // 如果是静默模式，或者404且错误信息是"未找到位置信息"，不显示toast
            if (!silent && !isNormalCase) {
              wx.showToast({
                title: errorMsg.length > 20 ? errorMsg.substring(0, 20) + '...' : errorMsg,
                icon: 'none',
                duration: 2500
              });
            }
            reject(new Error(errorMsg));
          }
        },
        fail: (err) => {
          let errorMsg = '网络请求失败';
          if (err.errMsg) {
            if (err.errMsg.includes('timeout')) {
              errorMsg = '请求超时，请检查网络连接';
            } else if (err.errMsg.includes('fail')) {
              errorMsg = '网络连接失败，请检查网络';
            } else {
              errorMsg = err.errMsg;
            }
          }
          
          if (!silent) {
            wx.showToast({
              title: errorMsg,
              icon: 'none',
              duration: 2000
            });
          }
          reject(new Error(errorMsg));
        }
      });
    });
  }
});

