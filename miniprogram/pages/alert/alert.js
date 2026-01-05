// pages/alert/alert.js
const app = getApp();

Page({
  data: {
    alerts: [],
    filter: 'all', // all, pending, handled
    loading: true,
    pendingCount: 0 // 待处理警告数量
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
        this.loadAlerts();
      }).catch(err => {
        wx.showToast({
          title: '请先登录',
          icon: 'none'
        });
        this.setData({ loading: false });
      });
    } else {
      this.loadAlerts();
    }
  },

  // 加载预警列表
  loadAlerts() {
    this.setData({ loading: true });
    
    let url = '/alerts/';
    if (this.data.filter !== 'all') {
      url += `?status=${this.data.filter}`;
    }
    
    // 同时获取待处理数量
    Promise.all([
      app.request({
        url: url,
        method: 'GET'
      }),
      app.request({
        url: '/alerts/unhandled_count/',
        method: 'GET'
      }).catch(() => ({ count: 0 })) // 如果失败，默认返回0
    ]).then(([result, countResult]) => {
      const alerts = result.results || result;
      const pendingCount = countResult.count || 0;
      this.setData({
        alerts: alerts,
        loading: false,
        pendingCount: pendingCount
      });
    }).catch(err => {
      // 如果是认证错误，清除token并重新登录
      if (err.message && err.message.includes('认证')) {
        app.globalData.token = null;
        wx.removeStorageSync('token');
        this.checkLoginAndLoad();
      } else {
        this.setData({ loading: false });
      }
    });
  },

  // 切换筛选
  switchFilter(e) {
    const filter = e.currentTarget.dataset.filter;
    this.setData({ filter });
    this.loadAlerts();
  },

  // 处理预警
  handleAlert(e) {
    const id = e.currentTarget.dataset.id;
    wx.showModal({
      title: '处理预警',
      placeholderText: '请输入处理备注（可选）',
      editable: true,
      success: (res) => {
        if (res.confirm) {
          app.request({
            url: `/alerts/${id}/handle/`,
            method: 'POST',
            data: { note: res.content || '' }
          }).then(() => {
            wx.showToast({
              title: '处理成功',
              icon: 'success'
            });
            this.loadAlerts();
            
            // 提示用户重新订阅消息（微信订阅消息是"一次性"的，处理警报后需要重新订阅才能收到新推送）
            setTimeout(() => {
              wx.showModal({
                title: '提示',
                content: '为了及时接收新的警报通知，建议重新订阅消息',
                confirmText: '重新订阅',
                cancelText: '稍后',
                success: (modalRes) => {
                  if (modalRes.confirm) {
                    this.resubscribeMessages();
                  }
                }
              });
            }, 1500);
          }).catch(err => {
            wx.showToast({
              title: err.message || '处理失败，请重试',
              icon: 'none'
            });
          });
        }
      }
    });
  },
  
  // 重新订阅消息
  resubscribeMessages() {
    const subscribe = require('../../utils/subscribe.js');
    wx.showLoading({
      title: '订阅中...',
      mask: true
    });
    
    subscribe.subscribeAllAlerts({ showToast: false }).then(result => {
      wx.hideLoading();
      if (result.success) {
        const acceptCount = Object.values(result.results || {}).filter(status => status === 'accept').length;
        if (acceptCount > 0) {
          wx.showToast({
            title: `已重新订阅${acceptCount}类警报通知`,
            icon: 'success',
            duration: 2000
          });
        } else {
          wx.showToast({
            title: '订阅失败，请稍后重试',
            icon: 'none'
          });
        }
      } else {
        wx.showToast({
          title: '订阅失败，请稍后重试',
          icon: 'none'
        });
      }
    }).catch(err => {
      wx.hideLoading();
      wx.showToast({
        title: '订阅失败，请稍后重试',
        icon: 'none'
      });
    });
  },

  // 导航到位置
  navigateToLocation(e) {
    const location = e.currentTarget.dataset.location;
    if (!location) {
      wx.showToast({
        title: '暂无位置信息',
        icon: 'none'
      });
      return;
    }
    
    wx.openLocation({
      latitude: parseFloat(location.latitude),
      longitude: parseFloat(location.longitude),
      name: '预警位置',
      address: ''
    });
  },

  // 一键处理所有警告
  handleAllAlerts() {
    if (this.data.pendingCount === 0) {
      wx.showToast({
        title: '没有待处理的警告',
        icon: 'none'
      });
      return;
    }

    wx.showModal({
      title: '确认处理',
      content: `确定要处理全部 ${this.data.pendingCount} 个待处理警告吗？`,
      confirmText: '确定处理',
      confirmColor: '#4A90E2',
      success: (res) => {
        if (res.confirm) {
          wx.showLoading({
            title: '处理中...',
            mask: true
          });

          app.request({
            url: '/alerts/handle_all/',
            method: 'POST',
            data: {
              note: '一键批量处理'
            }
          }).then(result => {
            wx.hideLoading();
            const message = result.message || `成功处理 ${result.count || 0} 个警告`;
            wx.showToast({
              title: message,
              icon: 'success',
              duration: 2000
            });
            this.loadAlerts();
            
            // 批量处理成功后，提示用户重新订阅消息
            setTimeout(() => {
              wx.showModal({
                title: '提示',
                content: '为了及时接收新的警报通知，建议重新订阅消息',
                confirmText: '重新订阅',
                cancelText: '稍后',
                success: (modalRes) => {
                  if (modalRes.confirm) {
                    this.resubscribeMessages();
                  }
                }
              });
            }, 2000);
          }).catch(err => {
            wx.hideLoading();
            wx.showToast({
              title: err.message || '处理失败，请重试',
              icon: 'none'
            });
          });
        }
      }
    });
  },

  // 清理已处理警告
  clearHandledAlerts() {
    const count = this.data.alerts.length;
    if (count === 0) {
      wx.showToast({
        title: '没有可清理的警告',
        icon: 'none'
      });
      return;
    }

    wx.showModal({
      title: '确认清理',
      content: `确定要清理全部 ${count} 个已处理警告吗？此操作不可恢复。`,
      confirmText: '确定清理',
      confirmColor: '#E74C3C',
      success: (res) => {
        if (res.confirm) {
          wx.showLoading({
            title: '清理中...',
            mask: true
          });

          app.request({
            url: '/alerts/clear_handled/',
            method: 'POST'
          }).then(result => {
            wx.hideLoading();
            const message = result.message || `成功清理 ${result.count || 0} 个警告`;
            wx.showToast({
              title: message,
              icon: 'success',
              duration: 2000
            });
            this.loadAlerts();
          }).catch(err => {
            wx.hideLoading();
            wx.showToast({
              title: err.message || '清理失败，请重试',
              icon: 'none'
            });
          });
        }
      }
    });
  }
});

