// pages/fence/fence.js
const app = getApp();
const subscribe = require('../../utils/subscribe.js');

Page({
  data: {
    deviceId: null,
    fences: [],
    showAddForm: false,
    showEditForm: false,
    editingFenceId: null,
    formData: {
      name: '',
      center_latitude: '',
      center_longitude: '',
      radius: 500,
      address: ''
    }
  },

  onLoad(options) {
    if (options.deviceId) {
      this.setData({ deviceId: options.deviceId });
      this.checkLoginAndLoad();
    } else {
      wx.showToast({
        title: '缺少设备ID',
        icon: 'none'
      });
      setTimeout(() => {
        wx.navigateBack();
      }, 1500);
    }
  },

  // 检查登录并加载
  checkLoginAndLoad() {
    if (!app.globalData.token) {
      app.wxLogin().then(() => {
        this.loadFences();
      }).catch(() => {
        wx.showToast({
          title: '请先登录',
          icon: 'none'
        });
      });
    } else {
      this.loadFences();
    }
  },

  // 加载围栏列表
  loadFences() {
    if (!this.data.deviceId) {
      return;
    }
    // 先获取最新位置，用于判断是否越界
    app.request({
      url: `/locations/latest/?device_id=${this.data.deviceId}`,
      method: 'GET',
      silent: true
    }).then(locationResult => {
      // 再获取围栏列表
      return app.request({
        url: `/fences/?device_id=${this.data.deviceId}`,
        method: 'GET'
      }).then(result => {
        const fences = (result.results || result || []).map(fence => ({
          ...fence,
          center_latitude: fence.center_latitude ? parseFloat(fence.center_latitude) : null,
          center_longitude: fence.center_longitude ? parseFloat(fence.center_longitude) : null,
          radius: fence.radius ? parseInt(fence.radius) : 500
        }));
        
        // 如果有位置信息，检查每个围栏是否越界
        if (locationResult && locationResult.latitude && locationResult.longitude) {
          const locLat = parseFloat(locationResult.latitude);
          const locLng = parseFloat(locationResult.longitude);
          
          if (!isNaN(locLat) && !isNaN(locLng)) {
            fences.forEach(fence => {
              if (fence.center_latitude !== null && fence.center_longitude !== null) {
                const distance = this.calculateDistance(
                  locLat,
                  locLng,
                  fence.center_latitude,
                  fence.center_longitude
                );
                fence.is_violation = distance > fence.radius;
              } else {
                fence.is_violation = false;
              }
            });
          } else {
            fences.forEach(fence => {
              fence.is_violation = false;
            });
          }
        } else {
          // 没有位置信息，默认不越界
          fences.forEach(fence => {
            fence.is_violation = false;
          });
        }
        
        this.setData({ fences });
      });
    }).catch(err => {
        if (err.message && err.message.includes('认证')) {
          app.globalData.token = null;
          wx.removeStorageSync('token');
          this.checkLoginAndLoad();
        }
      });
  },

  // 显示添加表单
  showAdd() {
    this.setData({ 
      showAddForm: true,
      showEditForm: false,
      editingFenceId: null,
      formData: {
        name: '',
        center_latitude: '',
        center_longitude: '',
        radius: 500,
        address: ''
      }
    });
  },

  // 取消添加/编辑
  cancelAdd() {
    this.setData({ 
      showAddForm: false,
      showEditForm: false,
      editingFenceId: null,
      formData: {
        name: '',
        center_latitude: '',
        center_longitude: '',
        radius: 500,
        address: ''
      }
    });
  },

  // 输入处理
  onNameInput(e) {
    this.setData({
      'formData.name': e.detail.value
    });
  },

  onRadiusInput(e) {
    let value = e.detail.value;
    let radius = parseInt(value);
    
    // 如果输入为空，允许清空
    if (value === '') {
      this.setData({
        'formData.radius': ''
      });
      return;
    }
    
    // 如果无法解析为数字，不更新
    if (isNaN(radius)) {
      return;
    }
    
    // 限制范围：1-2000
    if (radius < 1) {
      radius = 1;
      wx.showToast({
        title: '半径最小为1米',
        icon: 'none',
        duration: 2000
      });
    } else if (radius > 2000) {
      radius = 2000;
      wx.showToast({
        title: '半径最大为2000米，已自动调整',
        icon: 'none',
        duration: 2000
      });
    }
    
    this.setData({
      'formData.radius': radius
    });
  },

  // 选择位置（使用地图API）
  chooseLocation() {
    // 始终使用真实地图选点API
    wx.chooseLocation({
      success: (res) => {
        this.setData({
          'formData.center_latitude': res.latitude.toString(),
          'formData.center_longitude': res.longitude.toString(),
          'formData.address': res.address || res.name || '未知地址'
        });
        wx.showToast({
          title: '位置选择成功',
          icon: 'success'
        });
      },
      fail: (err) => {
        // 如果选择失败，提供手动输入选项（开发者工具环境）
        if (err.errMsg && err.errMsg.includes('chooseLocation:fail')) {
          wx.showModal({
            title: '选择位置失败',
            content: '开发者工具中无法使用地图选点，请使用"输入坐标"功能',
            showCancel: false
          });
        } else {
          wx.showToast({
            title: '选择位置失败',
            icon: 'none'
          });
        }
      }
    });
  },

  // 显示手动输入位置对话框
  showLocationInput() {
    wx.showModal({
      title: '手动输入地址',
      editable: true,
      placeholderText: '请输入地址（如：北京市东城区天安门广场）',
      success: (res) => {
        if (res.confirm && res.content) {
          this.setData({
            'formData.address': res.content.trim(),
            'formData.center_latitude': this.data.formData.center_latitude || '39.908823', // 默认北京坐标
            'formData.center_longitude': this.data.formData.center_longitude || '116.397470'
          });
          wx.showToast({
            title: '地址已设置',
            icon: 'success'
          });
        }
      }
    });
  },

  // 显示手动输入坐标对话框
  showCoordinateInput() {
    const currentLat = this.data.formData.center_latitude || '';
    const currentLng = this.data.formData.center_longitude || '';
    
    wx.showModal({
      title: '输入经纬度坐标',
      content: `当前: 纬度 ${currentLat || '未设置'}, 经度 ${currentLng || '未设置'}\n\n格式: 纬度,经度\n示例: 39.908823,116.397470`,
      editable: true,
      placeholderText: '纬度,经度',
      success: (res) => {
        if (res.confirm && res.content) {
          const coords = res.content.trim().split(',');
          if (coords.length === 2) {
            const lat = parseFloat(coords[0].trim());
            const lng = parseFloat(coords[1].trim());
            
            if (!isNaN(lat) && !isNaN(lng) && lat >= -90 && lat <= 90 && lng >= -180 && lng <= 180) {
              this.setData({
                'formData.center_latitude': lat.toString(),
                'formData.center_longitude': lng.toString(),
                'formData.address': this.data.formData.address || `坐标位置 (${lat}, ${lng})`
              });
              wx.showToast({
                title: '坐标已设置',
                icon: 'success'
              });
            } else {
              wx.showToast({
                title: '坐标格式错误',
                icon: 'none'
              });
            }
          } else {
            wx.showToast({
              title: '请输入: 纬度,经度',
              icon: 'none'
            });
          }
        }
      }
    });
  },

  // 提交添加围栏
  submitAdd() {
    const { formData, deviceId } = this.data;
    // 验证必填项
    if (!formData.name || !formData.name.trim()) {
      wx.showToast({
        title: '请输入围栏名称',
        icon: 'none'
      });
      return;
    }
    
    if (!formData.center_latitude || !formData.center_longitude) {
      wx.showToast({
        title: '请选择围栏位置',
        icon: 'none'
      });
      return;
    }
    
    if (!deviceId) {
      wx.showToast({
        title: '缺少设备ID，请重新进入页面',
        icon: 'none',
        duration: 2000
      });
      return;
    }
    
    // 准备提交数据
    // 验证经纬度
    const lat = parseFloat(formData.center_latitude);
    const lng = parseFloat(formData.center_longitude);
    
    if (isNaN(lat) || isNaN(lng)) {
      wx.showToast({
        title: '经纬度格式错误',
        icon: 'none'
      });
      return;
    }
    
    if (lat < -90 || lat > 90) {
      wx.showToast({
        title: '纬度范围错误（-90到90）',
        icon: 'none'
      });
      return;
    }
    
    if (lng < -180 || lng > 180) {
      wx.showToast({
        title: '经度范围错误（-180到180）',
        icon: 'none'
      });
      return;
    }
    
    // 验证半径范围
    let radius = parseInt(formData.radius) || 500;
    if (radius < 1) {
      radius = 1;
      wx.showToast({
        title: '半径最小为1米，已自动调整',
        icon: 'none'
      });
    } else if (radius > 2000) {
      radius = 2000;
      wx.showToast({
        title: '半径最大为2000米，已自动调整',
        icon: 'none'
      });
    }
    
    const submitData = {
      device_id: deviceId,
      name: formData.name.trim(),
      center_latitude: lat,
      center_longitude: lng,
      radius: radius,
      address: formData.address || ''
    };
    
    wx.showLoading({
      title: '添加中...',
      mask: true
    });
    
    app.request({
      url: '/fences/',
      method: 'POST',
      data: submitData
    }).then(() => {
      wx.hideLoading();
      wx.showToast({
        title: '添加成功',
        icon: 'success'
      });
      // 创建围栏成功后，引导用户订阅消息通知
      subscribe.subscribeAllAlerts().catch(err => {
      });
      // 重置表单
      this.setData({ 
        showAddForm: false,
        formData: {
          name: '',
          center_latitude: '',
          center_longitude: '',
          radius: 500,
          address: ''
        }
      });
      this.loadFences();
    }).catch(err => {
      wx.hideLoading();
      const errorMsg = err.message || '添加失败，请重试';
      wx.showToast({
        title: errorMsg.length > 20 ? errorMsg.substring(0, 20) + '...' : errorMsg,
        icon: 'none',
        duration: 2500
      });
    });
  },

  // 编辑围栏
  editFence(e) {
    const id = e.currentTarget.dataset.id;
    const item = e.currentTarget.dataset.item;
    
    if (!item) {
      wx.showToast({
        title: '围栏数据错误',
        icon: 'none'
      });
      return;
    }
    
    // 填充表单数据
    this.setData({
      showEditForm: true,
      showAddForm: false,
      editingFenceId: id,
      formData: {
        name: item.name || '',
        center_latitude: item.center_latitude ? item.center_latitude.toString() : '',
        center_longitude: item.center_longitude ? item.center_longitude.toString() : '',
        radius: item.radius || 500,
        address: item.address || ''
      }
    });
  },

  // 提交编辑围栏
  submitEdit() {
    const { formData, deviceId, editingFenceId } = this.data;
    
    // 验证必填项
    if (!formData.name || !formData.name.trim()) {
      wx.showToast({
        title: '请输入围栏名称',
        icon: 'none'
      });
      return;
    }
    
    if (!formData.center_latitude || !formData.center_longitude) {
      wx.showToast({
        title: '请选择围栏位置',
        icon: 'none'
      });
      return;
    }
    
    if (!editingFenceId) {
      wx.showToast({
        title: '编辑ID错误',
        icon: 'none'
      });
      return;
    }
    
    // 验证经纬度
    const lat = parseFloat(formData.center_latitude);
    const lng = parseFloat(formData.center_longitude);
    
    if (isNaN(lat) || isNaN(lng)) {
      wx.showToast({
        title: '经纬度格式错误',
        icon: 'none'
      });
      return;
    }
    
    if (lat < -90 || lat > 90) {
      wx.showToast({
        title: '纬度范围错误（-90到90）',
        icon: 'none'
      });
      return;
    }
    
    if (lng < -180 || lng > 180) {
      wx.showToast({
        title: '经度范围错误（-180到180）',
        icon: 'none'
      });
      return;
    }
    
    // 验证半径范围
    let radius = parseInt(formData.radius) || 500;
    if (radius < 1) {
      radius = 1;
      wx.showToast({
        title: '半径最小为1米，已自动调整',
        icon: 'none'
      });
    } else if (radius > 2000) {
      radius = 2000;
      wx.showToast({
        title: '半径最大为2000米，已自动调整',
        icon: 'none'
      });
    }
    
    const submitData = {
      name: formData.name.trim(),
      center_latitude: lat,
      center_longitude: lng,
      radius: radius,
      address: formData.address || ''
    };
    
    wx.showLoading({
      title: '保存中...',
      mask: true
    });
    
    app.request({
      url: `/fences/${editingFenceId}/`,
      method: 'PUT',
      data: submitData
    }).then(() => {
      wx.hideLoading();
      wx.showToast({
        title: '保存成功',
        icon: 'success'
      });
      // 重置表单
      this.setData({ 
        showEditForm: false,
        editingFenceId: null,
        formData: {
          name: '',
          center_latitude: '',
          center_longitude: '',
          radius: 500,
          address: ''
        }
      });
      this.loadFences();
    }).catch(err => {
      wx.hideLoading();
      const errorMsg = err.message || '保存失败，请重试';
      wx.showToast({
        title: errorMsg.length > 20 ? errorMsg.substring(0, 20) + '...' : errorMsg,
        icon: 'none',
        duration: 2500
      });
    });
  },

  // 删除围栏
  deleteFence(e) {
    const id = e.currentTarget.dataset.id;
    const item = e.currentTarget.dataset.item || {};
    const fenceName = item.name || '该围栏';
    
    wx.showModal({
      title: '确认删除',
      content: `确定要删除"${fenceName}"吗？此操作不可恢复。`,
      confirmText: '删除',
      confirmColor: '#FF5252',
      success: (res) => {
        if (res.confirm) {
          wx.showLoading({
            title: '删除中...',
            mask: true
          });
          
          app.request({
            url: `/fences/${id}/`,
            method: 'DELETE'
          }).then(() => {
            wx.hideLoading();
            wx.showToast({
              title: '删除成功',
              icon: 'success'
            });
            // 重新加载围栏列表
            this.loadFences();
          }).catch(err => {
            wx.hideLoading();
            const errorMsg = err.message || '删除失败，请重试';
            wx.showToast({
              title: errorMsg.length > 20 ? errorMsg.substring(0, 20) + '...' : errorMsg,
              icon: 'none',
              duration: 2500
            });
          });
        }
      }
    });
  },

  // 切换围栏状态
  toggleFence(e) {
    const id = e.currentTarget.dataset.id;
    const isActive = e.detail.value;
    
    wx.showLoading({
      title: '更新中...',
      mask: true
    });
    
    app.request({
      url: `/fences/${id}/toggle/`,
      method: 'POST'
    }).then(() => {
      wx.hideLoading();
      wx.showToast({
        title: isActive ? '围栏已启用' : '围栏已禁用',
        icon: 'success',
        duration: 1500
      });
      // 重新加载围栏列表以更新状态
      this.loadFences();
    }).catch(err => {
      wx.hideLoading();
      wx.showToast({
        title: err.message || '操作失败',
        icon: 'none',
        duration: 2000
      });
      // 恢复开关状态
      this.loadFences();
    });
  },

  // 计算两点间距离（米）- 使用Haversine公式
  calculateDistance(lat1, lon1, lat2, lon2) {
    // 确保参数是数字类型
    lat1 = parseFloat(lat1);
    lon1 = parseFloat(lon1);
    lat2 = parseFloat(lat2);
    lon2 = parseFloat(lon2);
    
    if (isNaN(lat1) || isNaN(lon1) || isNaN(lat2) || isNaN(lon2)) {
      return Infinity;
    }
    
    const R = 6371000; // 地球半径（米）
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLon = (lon2 - lon1) * Math.PI / 180;
    const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
      Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
      Math.sin(dLon / 2) * Math.sin(dLon / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    const distance = R * c;
    
    return distance;
  }
});

