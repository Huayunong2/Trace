// pages/admin/users/detail/detail.js - 用户详情
const app = getApp();

Page({
  data: {
    userId: null,
    user: null,
    loading: true,
    showEditForm: false,
    editForm: {
      role: '',
      phone: '',
      is_active: true
    }
  },

  onLoad(options) {
    if (options.id) {
      this.setData({ userId: options.id });
      this.checkPermissionAndLoad();
    }
  },

  // 检查权限并加载
  checkPermissionAndLoad() {
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

    this.loadUserDetail();
  },

  // 加载用户详情
  loadUserDetail() {
    this.setData({ loading: true });

    app.request({
      url: `/system/users/${this.data.userId}/`,
      method: 'GET'
    }).then(result => {
      this.setData({
        user: result,
        loading: false,
        editForm: {
          role: result.role,
          phone: result.phone || '',
          is_active: result.is_active
        }
      });
    }).catch(err => {
      this.setData({ loading: false });
      wx.showToast({
        title: '加载失败',
        icon: 'none'
      });
    });
  },

  // 显示编辑表单
  showEditForm() {
    this.setData({ showEditForm: true });
  },

  // 取消编辑
  cancelEdit() {
    this.setData({ showEditForm: false });
  },

  // 角色选择
  onRoleChange(e) {
    this.setData({
      'editForm.role': e.detail.value
    });
  },

  // 手机号输入
  onPhoneInput(e) {
    this.setData({
      'editForm.phone': e.detail.value
    });
  },

  // 保存修改
  saveEdit() {
    const { editForm, userId } = this.data;
    const currentUser = app.globalData.userInfo;

    // 不能修改自己
    if (userId == currentUser.id) {
      wx.showToast({
        title: '不能修改自己',
        icon: 'none'
      });
      return;
    }

    wx.showLoading({
      title: '保存中...',
      mask: true
    });

    app.request({
      url: `/system/users/${userId}/`,
      method: 'PUT',
      data: {
        role: editForm.role,
        phone: editForm.phone,
        is_active: editForm.is_active
      }
    }).then(() => {
      wx.hideLoading();
      wx.showToast({
        title: '保存成功',
        icon: 'success'
      });
      this.setData({ showEditForm: false });
      this.loadUserDetail();
    }).catch(err => {
      wx.hideLoading();
      wx.showToast({
        title: err.message || '保存失败',
        icon: 'none'
      });
    });
  },

  // 修改角色
  changeRole() {
    const { user, userId } = this.data;
    const currentUser = app.globalData.userInfo;

    // 不能修改自己
    if (userId == currentUser.id) {
      wx.showToast({
        title: '不能修改自己',
        icon: 'none'
      });
      return;
    }

    const roleNames = ['guardian', 'elderly', 'system_admin'];
    const roleDisplays = ['监护人', '老人', '系统管理员'];
    
    wx.showActionSheet({
      itemList: roleDisplays,
      success: (res) => {
        const newRole = roleNames[res.tapIndex];
        
        wx.showLoading({
          title: '修改中...',
          mask: true
        });

        app.request({
          url: `/system/users/${userId}/change_role/`,
          method: 'POST',
          data: { role: newRole }
        }).then(() => {
          wx.hideLoading();
          wx.showToast({
            title: '修改成功',
            icon: 'success'
          });
          this.loadUserDetail();
        }).catch(err => {
          wx.hideLoading();
          wx.showToast({
            title: err.message || '修改失败',
            icon: 'none'
          });
        });
      }
    });
  },

  // 删除用户
  deleteUser() {
    const { user, userId } = this.data;
    const currentUser = app.globalData.userInfo;

    // 不能删除自己
    if (userId == currentUser.id) {
      wx.showToast({
        title: '不能删除自己',
        icon: 'none'
      });
      return;
    }

    wx.showModal({
      title: '确认删除',
      content: `确定要删除用户"${user.username}"吗？此操作不可恢复。`,
      confirmColor: '#FF5252',
      success: (res) => {
        if (res.confirm) {
          wx.showLoading({
            title: '删除中...',
            mask: true
          });

          app.request({
            url: `/system/users/${userId}/`,
            method: 'DELETE'
          }).then((result) => {
            wx.hideLoading();
            // 204状态码是DELETE请求的正常返回，视为成功
            wx.showToast({
              title: '删除成功',
              icon: 'success'
            });
            setTimeout(() => {
              wx.navigateBack();
            }, 1500);
          }).catch(err => {
            wx.hideLoading();
            // 204状态码不应该显示错误
            if (!err.message || !err.message.includes('204')) {
              wx.showToast({
                title: err.message || '删除失败',
                icon: 'none'
              });
            } else {
              // 204是成功的，只返回
              wx.showToast({
                title: '删除成功',
                icon: 'success'
              });
              setTimeout(() => {
                wx.navigateBack();
              }, 1500);
            }
          });
        }
      }
    });
  }
});

