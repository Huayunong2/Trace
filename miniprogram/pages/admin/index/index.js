// pages/admin/index/index.js - 系统管理员首页
const app = getApp();

Page({
  data: {
    statistics: null,
    loading: true
  },

  onLoad() {
    this.checkPermissionAndLoad();
  },

  onShow() {
    this.loadStatistics();
  },

  // 检查权限并加载
  checkPermissionAndLoad() {
    if (!app.globalData.token) {
      // 未登录，跳转到登录页
      wx.reLaunch({
        url: '/pages/login/login'
      });
      return;
    }

    if (!app.hasPermission('system_admin')) {
      wx.showModal({
        title: '权限不足',
        content: '您不是系统管理员，无法访问此页面',
        showCancel: false,
        success: () => {
          wx.reLaunch({
            url: '/pages/login/login'
          });
        }
      });
      return;
    }

    this.loadStatistics();
  },

  // 加载统计信息
  loadStatistics() {
    this.setData({ loading: true });

    app.request({
      url: '/system/users/statistics/',
      method: 'GET'
    }).then(result => {
      this.setData({
        statistics: result,
        loading: false
      });
    }).catch(err => {
      this.setData({ loading: false });
      wx.showToast({
        title: '加载失败',
        icon: 'none'
      });
    });
  },

  // 用户管理
  goToUserManagement() {
    wx.navigateTo({
      url: '/pages/admin/users/users'
    });
  },

  // 系统配置
  goToSystemConfig() {
    wx.navigateTo({
      url: '/pages/admin/config/config'
    });
  },

  // 刷新
  refresh() {
    this.loadStatistics();
  },

  // 退出登录
  logout() {
    wx.showModal({
      title: '确认退出',
      content: '确定要退出登录吗？退出后需要重新选择身份登录。',
      success: (res) => {
        if (res.confirm) {
          app.globalData.token = null;
          app.globalData.userInfo = null;
          app.globalData.userRole = null;
          wx.removeStorageSync('token');
          wx.removeStorageSync('userProfile');
          wx.reLaunch({
            url: '/pages/login/login'
          });
        }
      }
    });
  }
});

