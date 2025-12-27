// pages/login/login.js
const app = getApp();

Page({
  data: {
    loading: false,
    showRoleSelector: false,
    selectedRole: '',
    tempCode: '',
    avatarUrl: '',
    nickname: ''
  },

  onLoad() {
    // 如果已经登录，直接跳转到对应页面（不再清除登录状态）
    const token = wx.getStorageSync('token');
    if (token && app.globalData.token) {
      // 已经登录，直接跳转
      const role = app.globalData.userRole || wx.getStorageSync('userRole');
      if (role === 'elderly') {
        wx.reLaunch({
          url: '/pages/elderly/index/index'
        });
      } else if (role === 'system_admin') {
        wx.reLaunch({
          url: '/pages/admin/index/index'
        });
      } else {
        wx.switchTab({
          url: '/pages/index/index'
        });
      }
      return;
    }
    // 如果没有登录，显示登录页面
  },

  // 微信登录（使用2022年后推荐的方式）
  onLogin() {
    this.setData({ loading: true });
    
    // 直接调用wx.login()获取code（不再使用wx.getUserProfile）
    wx.login({
      success: (loginRes) => {
        if (loginRes.code) {
          // 获取code后，显示角色选择弹窗
          this.setData({
            tempCode: loginRes.code,
            showRoleSelector: true,
            loading: false
          });
        } else {
          this.setData({ loading: false });
          wx.showToast({
            title: '获取登录凭证失败',
            icon: 'none'
          });
        }
      },
      fail: () => {
        this.setData({ loading: false });
        wx.showToast({
          title: '获取登录凭证失败，请重试',
          icon: 'none'
        });
      }
    });
  },

  // 选择身份
  selectRole(e) {
    const role = e.currentTarget.dataset.role;
    this.setData({ selectedRole: role });
  },

  // 确认登录
  confirmLogin() {
    if (!this.data.selectedRole) {
      wx.showToast({
        title: '请选择身份',
        icon: 'none'
      });
      return;
    }

    this.setData({ loading: true, showRoleSelector: false });
    this.doLogin(
      this.data.tempCode, 
      this.data.selectedRole, 
      this.data.avatarUrl, 
      this.data.nickname
    );
  },

  // 选择头像（2022年后推荐的方式）
  onChooseAvatar(e) {
    try {
      const { avatarUrl } = e.detail;
      if (avatarUrl) {
        this.setData({
          avatarUrl
        });
      }
    } catch (error) {
      wx.showToast({
        title: '选择头像失败',
        icon: 'none'
      });
    }
  },

  // 输入昵称（2022年后推荐的方式）
  onInputNickname(e) {
    const { value } = e.detail;
    this.setData({
      nickname: value
    });
  },

  // 取消选择身份
  cancelRoleSelect() {
    this.setData({
      showRoleSelector: false,
      selectedRole: '',
      tempCode: '',
      avatarUrl: '',
      nickname: '',
      loading: false
    });
  },

  // 阻止弹窗背景滚动
  preventTouchMove() {
    return false;
  },

  // 阻止事件冒泡
  stopPropagation() {
    return false;
  },

  // 执行登录
  doLogin(code, role, avatarUrl, nickname) {
    app.request({
      url: '/auth/users/login/',
      method: 'POST',
      data: { 
        code, 
        role,
        avatar_url: avatarUrl || '',  // 传递头像URL
        nickname: nickname || ''  // 传递昵称
      }
    }).then(result => {
      if (result.token) {
        app.globalData.token = result.token;
        app.globalData.userInfo = result.user || {};
        app.globalData.userRole = result.user?.role || role;
        wx.setStorageSync('token', result.token);
        wx.setStorageSync('userRole', result.user?.role || role);
        
        // 保存用户信息（头像、昵称等，如果有填写）
        const userProfile = {};
        if (avatarUrl) {
          userProfile.avatarUrl = avatarUrl;
        }
        if (nickname) {
          userProfile.nickName = nickname;
        }
        if (Object.keys(userProfile).length > 0) {
          wx.setStorageSync('userProfile', userProfile);
        }
        
        wx.showToast({
          title: '登录成功',
          icon: 'success'
        });
        
        setTimeout(() => {
          this.navigateByRole();
        }, 1000);
      } else {
        throw new Error('登录失败');
      }
    }).catch(err => {
      this.setData({ loading: false });
      wx.showToast({
        title: err.message || '登录失败，请重试',
        icon: 'none'
      });
    });
  },

  // 根据角色导航
  navigateByRole() {
    const role = app.globalData.userRole || app.globalData.userInfo?.role;
    
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
});
