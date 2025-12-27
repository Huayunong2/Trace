// pages/admin/users/add/add.js - 添加用户
const app = getApp();

Page({
  data: {
    formData: {
      username: '',
      phone: '',
      role: 'guardian',
      is_active: true
    },
    roleOptions: ['guardian', 'elderly', 'system_admin'],
    roleLabels: ['监护人', '老人', '系统管理员']
  },

  onLoad() {
    this.checkPermission();
  },

  // 检查权限
  checkPermission() {
    if (!app.globalData.token) {
      app.navigateToLogin();
      return;
    }

    if (!app.hasPermission('system_admin')) {
      wx.showModal({
        title: '权限不足',
        content: '您不是系统管理员，无法访问此页面',
        showCancel: false,
        success: () => {
          wx.navigateBack();
        }
      });
      return;
    }
  },

  // 用户名输入
  onUsernameInput(e) {
    this.setData({
      'formData.username': e.detail.value
    });
  },

  // 手机号输入
  onPhoneInput(e) {
    this.setData({
      'formData.phone': e.detail.value
    });
  },

  // 角色选择
  onRoleChange(e) {
    this.setData({
      'formData.role': this.data.roleOptions[e.detail.value]
    });
  },

  // 提交表单
  submit() {
    const { formData } = this.data;

    // 验证
    if (!formData.username || !formData.username.trim()) {
      wx.showToast({
        title: '请输入用户名',
        icon: 'none'
      });
      return;
    }

    if (formData.phone && !/^1[3-9]\d{9}$/.test(formData.phone)) {
      wx.showToast({
        title: '请输入正确的手机号',
        icon: 'none'
      });
      return;
    }

    wx.showLoading({
      title: '创建中...',
      mask: true
    });

    app.request({
      url: '/system/users/',
      method: 'POST',
      data: formData
    }).then(() => {
      wx.hideLoading();
      wx.showToast({
        title: '创建成功',
        icon: 'success'
      });
      setTimeout(() => {
        wx.navigateBack();
      }, 1500);
    }).catch(err => {
      wx.hideLoading();
      wx.showToast({
        title: err.message || '创建失败',
        icon: 'none',
        duration: 2000
      });
    });
  },

  // 返回
  goBack() {
    wx.navigateBack();
  }
});

