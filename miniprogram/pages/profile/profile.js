// pages/profile/profile.js
const app = getApp();

Page({
  data: {
    userInfo: null,
    isTestMode: false  // 关闭测试模式，不允许切换角色
  },

  onLoad() {
    this.loadUserInfo();
  },

  onShow() {
    this.loadUserInfo();
  },

  // 加载用户信息
  loadUserInfo() {
    app.getUserInfo().then(userInfo => {
      // 尝试从本地存储获取头像和昵称
      const userProfile = wx.getStorageSync('userProfile') || {};
      if (userProfile.avatarUrl) {
        userInfo.avatarUrl = userProfile.avatarUrl;
      }
      if (userProfile.nickName) {
        userInfo.nickname = userProfile.nickName;
        userInfo.username = userProfile.nickName;  // 使用昵称作为显示名
      }
      this.setData({ userInfo });
    }).catch(() => {
      // 如果获取失败，尝试登录
      app.wxLogin().then(result => {
        const userInfo = result.user || {};
        const userProfile = wx.getStorageSync('userProfile') || {};
        if (userProfile.avatarUrl) {
          userInfo.avatarUrl = userProfile.avatarUrl;
        }
        if (userProfile.nickName) {
          userInfo.nickname = userProfile.nickName;
          userInfo.username = userProfile.nickName;
        }
        this.setData({ userInfo });
      });
    });
  },

  // 切换角色（测试阶段）
  switchRole() {
    const roles = ['guardian', 'elderly', 'community_admin', 'system_admin'];
    const currentRole = app.globalData.userRole || 'guardian';
    const currentIndex = roles.indexOf(currentRole);
    const nextIndex = (currentIndex + 1) % roles.length;
    const nextRole = roles[nextIndex];
    
    const roleNames = {
      'guardian': '监护人',
      'elderly': '老人',
      'community_admin': '社区管理员',
      'system_admin': '系统管理员'
    };
    
    wx.showModal({
      title: '切换角色',
      content: `切换到：${roleNames[nextRole]}`,
      success: (res) => {
        if (res.confirm) {
          app.globalData.userRole = nextRole;
          if (this.data.userInfo) {
            this.setData({
              'userInfo.role': nextRole
            });
          }
          wx.showToast({
            title: `已切换为${roleNames[nextRole]}`,
            icon: 'success'
          });
          
          // 根据角色跳转到对应首页
          setTimeout(() => {
            if (nextRole === 'elderly') {
              wx.reLaunch({
                url: '/pages/elderly/index/index'
              });
            } else if (nextRole === 'system_admin') {
              wx.reLaunch({
                url: '/pages/admin/index/index'
              });
            } else {
              wx.reLaunch({
                url: '/pages/index/index'
              });
            }
          }, 1000);
        }
      }
    });
  },

  // 系统管理（仅系统管理员可见）
  goToSystemAdmin() {
    if (!app.hasPermission('system_admin')) {
      wx.showToast({
        title: '权限不足',
        icon: 'none'
      });
      return;
    }
    
    wx.navigateTo({
      url: '/pages/admin/index/index'
    });
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

