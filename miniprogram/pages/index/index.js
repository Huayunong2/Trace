// pages/index/index.js
const app = getApp();

Page({
  data: {
    elderlyList: [],
    unhandledAlertCount: 0,
    loading: true,
    userInfo: null
  },

  onLoad() {
    this.checkLoginAndLoad();
  },

  onShow() {
    this.checkLoginAndLoad();
  },

  // 检查登录并加载数据
  checkLoginAndLoad() {
    if (!app.globalData.token) {
      // 未登录，先尝试登录
      app.wxLogin().then(() => {
        this.setData({ userInfo: app.globalData.userInfo });
        this.loadData();
      }).catch(err => {
        wx.showToast({
          title: '请先登录',
          icon: 'none'
        });
        this.setData({ loading: false });
      });
    } else {
      // 已登录，获取用户信息
      if (!app.globalData.userInfo) {
        app.getUserInfo().then(userInfo => {
          this.setData({ userInfo });
          this.loadData();
        }).catch(() => {
          this.loadData();
        });
      } else {
        this.setData({ userInfo: app.globalData.userInfo });
        this.loadData();
      }
    }
  },

  // 加载数据
  loadData() {
    this.setData({ loading: true });
    
    Promise.all([
      this.loadElderlyList(),
      this.loadAlertCount()
    ]).finally(() => {
      this.setData({ loading: false });
    });
  },

  // 加载老人列表
  loadElderlyList() {
    return app.request({
      url: '/auth/elderly/',
      method: 'GET',
      timeout: 20000 // 20秒超时
    }).then(result => {
      this.setData({
        elderlyList: result.results || result
      });
    }).catch(err => {
      // 如果是认证错误，清除token
      if (err.message && err.message.includes('认证')) {
        app.globalData.token = null;
        wx.removeStorageSync('token');
      }
    });
  },

  // 加载未处理预警数量
  loadAlertCount() {
    return app.request({
      url: '/alerts/unhandled_count/',
      method: 'GET',
      timeout: 15000, // 15秒超时
      silent: true // 静默处理错误，不显示toast
    }).then(result => {
      this.setData({
        unhandledAlertCount: result.count || 0
      });
    }).catch(err => {
      // 静默失败，不影响其他功能，设置为0
      this.setData({
        unhandledAlertCount: 0
      });
    });
  },

  // 跳转到老人详情
  goToElderlyDetail(e) {
    const id = e.currentTarget.dataset.id;
    wx.navigateTo({
      url: `/pages/elderly/detail/detail?id=${id}`
    });
  },

  // 添加老人
  addElderly() {
    wx.navigateTo({
      url: '/pages/elderly/add/add'
    });
  },

  // 长按显示操作菜单
  showElderlyActions(e) {
    const item = e.currentTarget.dataset.item;
    const itemId = e.currentTarget.dataset.id;
    
    wx.showActionSheet({
      itemList: ['编辑', '删除'],
      success: (res) => {
        if (res.tapIndex === 0) {
          // 编辑
          wx.navigateTo({
            url: `/pages/elderly/detail/detail?id=${itemId}`
          });
        } else if (res.tapIndex === 1) {
          // 删除
          wx.showModal({
            title: '确认删除',
            content: `确定要删除老人"${item.name}"吗？此操作不可恢复。`,
            success: (modalRes) => {
              if (modalRes.confirm) {
                this.deleteElderly(itemId);
              }
            }
          });
        }
      }
    });
  },

  // 删除老人
  deleteElderly(id) {
    wx.showLoading({
      title: '删除中...',
      mask: true
    });
    
    app.request({
      url: `/auth/elderly/${id}/`,
      method: 'DELETE'
    }).then((result) => {
      wx.hideLoading();
      // 204状态码是DELETE请求的正常返回，视为成功
      wx.showToast({
        title: '删除成功',
        icon: 'success'
      });
      this.loadData();
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
        wx.showToast({
          title: '删除成功',
          icon: 'success'
        });
        this.loadData();
      }
    });
  },

  // 跳转到预警页面
  goToAlerts() {
    wx.switchTab({
      url: '/pages/alert/alert'
    });
  },

  // 跳转到地图页面
  goToMap(e) {
    const deviceId = e.currentTarget.dataset.deviceId;
    if (!deviceId) {
      wx.showToast({
        title: '设备ID不存在',
        icon: 'none'
      });
      return;
    }
    // switchTab 不支持参数传递，需要先保存到全局或使用 navigateTo
    // 但由于 map 是 tabBar 页面，只能使用 switchTab
    // 解决方案：将 deviceId 保存到全局或本地存储
    app.globalData.currentDeviceId = deviceId;
    wx.switchTab({
      url: '/pages/map/map'
    });
  }
});

