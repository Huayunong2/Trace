// pages/admin/users/users.js - 用户管理
const app = getApp();

Page({
  data: {
    users: [],
    loading: true,
    roleFilter: 'all',
    searchKeyword: ''
  },

  onLoad() {
    this.checkPermissionAndLoad();
  },

  onShow() {
    this.loadUsers();
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

    this.loadUsers();
  },

  // 加载用户列表
  loadUsers() {
    this.setData({ loading: true });

    let url = '/system/users/';
    const params = [];
    
    if (this.data.roleFilter !== 'all') {
      params.push(`role=${this.data.roleFilter}`);
    }
    
    if (this.data.searchKeyword) {
      params.push(`search=${encodeURIComponent(this.data.searchKeyword)}`);
    }
    
    if (params.length > 0) {
      url += '?' + params.join('&');
    }

    app.request({
      url: url,
      method: 'GET'
    }).then(result => {
      this.setData({
        users: result.results || result || [],
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

  // 搜索输入
  onSearchInput(e) {
    this.setData({
      searchKeyword: e.detail.value
    });
  },

  // 搜索
  onSearch() {
    this.loadUsers();
  },

  // 角色过滤
  onRoleFilterChange(e) {
    const roleMap = ['all', 'guardian', 'elderly', 'system_admin'];
    const selectedIndex = parseInt(e.detail.value);
    const selectedRole = roleMap[selectedIndex] || 'all';
    this.setData({
      roleFilter: selectedRole
    });
    this.loadUsers();
  },

  // 查看用户详情
  viewUserDetail(e) {
    const userId = e.currentTarget.dataset.id;
    wx.navigateTo({
      url: `/pages/admin/users/detail/detail?id=${userId}`
    });
  },

  // 刷新
  refresh() {
    this.loadUsers();
  },

  // 添加用户
  addUser() {
    wx.navigateTo({
      url: '/pages/admin/users/add/add'
    });
  },

  // 删除用户
  deleteUser(e) {
    const userId = e.currentTarget.dataset.id;
    const user = e.currentTarget.dataset.user;
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
            this.loadUsers();
          }).catch(err => {
            wx.hideLoading();
            // 204状态码不应该显示错误
            if (!err.message || !err.message.includes('204')) {
              wx.showToast({
                title: err.message || '删除失败',
                icon: 'none'
              });
            } else {
              // 204是成功的，只刷新列表
              this.loadUsers();
            }
          });
        }
      }
    });
  }
});

