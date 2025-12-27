// pages/elderly/detail.js
const app = getApp();
const subscribe = require('../../../utils/subscribe.js');

Page({
  data: {
    elderlyId: null,
    elderly: null,
    device: null,
    userRole: 'guardian',
    showEditForm: false,
    editForm: {
      name: '',
      age: '',
      gender: '',
      medical_history: '',
      emergency_contact: '',
      emergency_phone: '',
      address: '',
      notes: ''
    }
  },

  onLoad(options) {
    if (options.id) {
      this.setData({ 
        elderlyId: options.id,
        userRole: app.globalData.userRole || 'guardian'
      });
      this.loadDetail();
    }
  },

  // 加载详情
  loadDetail() {
    wx.showLoading({ title: '加载中...', mask: true });
    
    app.request({
      url: `/auth/elderly/${this.data.elderlyId}/`,
      method: 'GET'
    }).then(result => {
      wx.hideLoading();
      this.setData({ 
        elderly: result,
        editForm: {
          name: result.name || '',
          age: result.age || '',
          gender: result.gender || '',
          medical_history: result.medical_history || '',
          emergency_contact: result.emergency_contact || '',
          emergency_phone: result.emergency_phone || '',
          address: result.address || '',
          notes: result.notes || ''
        }
      });
      if (result.device) {
        // 确保设备信息完整，补充默认值
        const device = {
          ...result.device,
          status: result.device.status || 'offline',
          battery_level: result.device.battery_level !== undefined && result.device.battery_level !== null 
            ? result.device.battery_level 
            : 100,
          device_type: result.device.device_type || 'smart_bracelet',
          name: result.device.name || '定位设备'
        };
        this.setData({ device });
        
        // 如果有设备ID，更新设备状态
        if (device.device_id) {
          this.updateDeviceStatus(device.device_id);
        }
      }
    }).catch(err => {
      wx.hideLoading();
      let errorMsg = '加载失败';
      if (err.message) {
        if (err.message.includes('404') || err.message.includes('未找到')) {
          errorMsg = '老人档案不存在或已被删除';
          // 404错误，返回上一页
          setTimeout(() => {
            wx.navigateBack();
          }, 1500);
        } else {
          errorMsg = err.message;
        }
      }
      wx.showToast({
        title: errorMsg,
        icon: 'none'
      });
    });
  },

  // 更新设备状态（从后端获取最新状态）
  updateDeviceStatus(deviceId) {
    app.request({
      url: `/devices/?device_id=${deviceId}`,
      method: 'GET'
    }).then(result => {
      const devices = result.results || result;
      if (devices.length > 0) {
        const device = devices[0];
        this.setData({ device });
      }
    }).catch(err => {
    });
  },

  // 绑定设备
  bindDevice() {
    const userRole = this.data.userRole || app.globalData.userRole || 'guardian';
    
    if (userRole === 'elderly') {
      // 老人角色：生成设备ID
      this.generateDeviceId();
    } else {
      // 监护人角色：绑定设备
      if (this.data.device && this.data.device.device_id) {
        // 如果已有设备ID，可以选择更换或查看设备信息
        wx.showModal({
          title: '设备已绑定',
          content: '该老人已绑定设备，是否要更换设备？',
          confirmText: '更换设备',
          cancelText: '取消',
          success: (res) => {
            if (res.confirm) {
              this.showBindDeviceModal();
            }
          }
        });
      } else {
        // 没有设备ID，绑定设备（需要输入老人生成的设备ID）
        this.showBindDeviceModal();
      }
    }
  },

  // 显示绑定设备输入框（仅监护人角色使用）
  showBindDeviceModal() {
    this.inputDeviceId();
  },

  // 生成设备ID（老人角色）
  generateDeviceId() {
    // 如果没有设备，先选择设备类型再创建
    if (!this.data.device) {
      wx.showActionSheet({
        itemList: ['智能手环', '手机'],
        success: (res) => {
          const deviceTypes = ['smart_bracelet', 'phone'];
          const deviceType = deviceTypes[res.tapIndex];
          
          wx.showLoading({ title: '生成中...', mask: true });
          
          app.request({
            url: '/devices/',
            method: 'POST',
            data: {
              elderly_id: this.data.elderlyId,
              name: '定位设备',
              device_type: deviceType
            }
          }).then(result => {
            wx.hideLoading();
            const deviceId = result.device_id || '生成中...';
            wx.showModal({
              title: '设备ID已生成',
              content: `设备ID: ${deviceId}\n\n请将此ID告知监护人，由监护人完成绑定。`,
              showCancel: false,
              confirmText: '知道了'
            });
            this.loadDetail();
          }).catch(err => {
            wx.hideLoading();
            wx.showToast({
              title: err.message || '生成失败',
              icon: 'none'
            });
          });
        }
      });
    } else {
      // 已有设备，直接显示设备ID
      wx.showModal({
        title: '设备ID',
        content: `设备ID: ${this.data.device.device_id || '未生成'}\n\n请将此ID告知监护人，由监护人完成绑定。`,
        showCancel: false,
        confirmText: '知道了'
      });
    }
  },

  // 输入设备ID
  inputDeviceId() {
    wx.showModal({
      title: '输入设备ID',
      editable: true,
      placeholderText: '请输入设备ID或扫描码',
      success: (res) => {
        if (res.confirm && res.content) {
          const deviceId = res.content.trim();
          if (deviceId) {
            this.createOrBindDevice(deviceId);
          } else {
            wx.showToast({
              title: '设备ID不能为空',
              icon: 'none'
            });
          }
        }
      }
    });
  },

  // 创建或绑定设备（监护人角色通过设备ID绑定）
  createOrBindDevice(deviceId) {
    const userRole = this.data.userRole;
    const elderlyId = this.data.elderlyId;
    
    if (userRole === 'guardian') {
      // 监护人角色：通过设备ID绑定到老人
      if (!deviceId || !deviceId.trim()) {
        wx.showToast({
          title: '设备ID不能为空',
          icon: 'none'
        });
        return;
      }
      
      wx.showLoading({
        title: '绑定中...',
        mask: true
      });
      
      app.request({
        url: '/devices/bind_by_device_id/',
        method: 'POST',
        data: {
          device_id: deviceId.trim(),
          elderly_id: elderlyId
        }
      }).then(result => {
        wx.hideLoading();
        wx.showToast({
          title: '绑定成功',
          icon: 'success'
        });
        // 绑定成功后，引导用户订阅消息通知
        this.subscribeAlerts();
        // 重新加载详情
        this.loadDetail();
      }).catch(err => {
        wx.hideLoading();
        let errorMsg = err.message || '绑定失败';
        if (errorMsg.includes('设备ID不存在')) {
          errorMsg = '设备ID不存在，请确认设备ID是否正确';
        } else if (errorMsg.includes('已绑定')) {
          errorMsg = '该设备已被其他老人绑定，或该老人已绑定其他设备';
        } else if (errorMsg.includes('权限')) {
          errorMsg = '无权限绑定此设备';
        }
        wx.showToast({
          title: errorMsg,
          icon: 'none',
          duration: 2500
        });
      });
      return;
    }
    
    // 老人角色不应该调用此方法，应该使用generateDeviceId
    wx.showToast({
      title: '老人角色应使用"生成设备ID"功能',
      icon: 'none'
    });
  },

  // 显示编辑表单（仅监护人角色）
  showEditForm() {
    const userRole = this.data.userRole || app.globalData.userRole || 'guardian';
    if (userRole !== 'guardian') {
      wx.showToast({
        title: '只有监护人可以编辑',
        icon: 'none'
      });
      return;
    }
    this.setData({ showEditForm: true });
  },

  // 取消编辑
  cancelEdit() {
    this.setData({ showEditForm: false });
    // 重新加载数据，恢复原始值
    this.loadDetail();
  },

  // 表单输入
  onEditInput(e) {
    const field = e.currentTarget.dataset.field;
    this.setData({
      [`editForm.${field}`]: e.detail.value
    });
  },

  // 性别选择
  onGenderChange(e) {
    this.setData({
      'editForm.gender': e.detail.value
    });
  },

  // 提交编辑
  submitEdit() {
    const { editForm, elderlyId } = this.data;
    
    // 验证必填项
    if (!editForm.name || !editForm.name.trim()) {
      wx.showToast({
        title: '请输入姓名',
        icon: 'none'
      });
      return;
    }
    
    if (!editForm.emergency_contact || !editForm.emergency_contact.trim()) {
      wx.showToast({
        title: '请输入紧急联系人',
        icon: 'none'
      });
      return;
    }
    
    if (!editForm.emergency_phone || !editForm.emergency_phone.trim()) {
      wx.showToast({
        title: '请输入紧急联系电话',
        icon: 'none'
      });
      return;
    }

    wx.showLoading({
      title: '保存中...',
      mask: true
    });

    app.request({
      url: `/auth/elderly/${elderlyId}/`,
      method: 'PUT',
      data: editForm
    }).then(() => {
      wx.hideLoading();
      wx.showToast({
        title: '保存成功',
        icon: 'success'
      });
      this.setData({ showEditForm: false });
      this.loadDetail();
    }).catch(err => {
      wx.hideLoading();
      wx.showToast({
        title: err.message || '保存失败',
        icon: 'none'
      });
    });
  },

  // 删除老人（仅监护人角色）
  deleteElderly() {
    const userRole = this.data.userRole || app.globalData.userRole || 'guardian';
    if (userRole !== 'guardian') {
      wx.showToast({
        title: '只有监护人可以删除',
        icon: 'none'
      });
      return;
    }

    const elderly = this.data.elderly;
    wx.showModal({
      title: '确认删除',
      content: `确定要删除老人"${elderly.name}"吗？此操作不可恢复，关联的设备将被解除绑定。`,
      confirmColor: '#FF5252',
      success: (res) => {
        if (res.confirm) {
          wx.showLoading({
            title: '删除中...',
            mask: true
          });

          app.request({
            url: `/auth/elderly/${this.data.elderlyId}/`,
            method: 'DELETE'
          }).then((result) => {
            wx.hideLoading();
            wx.showToast({
              title: '删除成功',
              icon: 'success'
            });
            setTimeout(() => {
              wx.navigateBack();
            }, 1500);
          }).catch(err => {
            wx.hideLoading();
            let errorMsg = '删除失败';
            if (err.message) {
              if (err.message.includes('权限') || err.message.includes('无权限')) {
                errorMsg = '无权限删除此老人档案';
              } else if (err.message.includes('ngrok') || err.message.includes('连接异常')) {
                errorMsg = '网络连接异常，请稍后重试';
              } else if (!err.message.includes('204')) {
                errorMsg = err.message;
              } else {
                // 204状态码表示成功
                wx.showToast({
                  title: '删除成功',
                  icon: 'success'
                });
                setTimeout(() => {
                  wx.navigateBack();
                }, 1500);
                return;
              }
            }
            wx.showToast({
              title: errorMsg,
              icon: 'none',
              duration: 2500
            });
          });
        }
      }
    });
  },

  // 订阅警报通知（在绑定设备或设置围栏后调用）
  subscribeAlerts() {
    subscribe.subscribeAllAlerts().catch(err => {
      // 订阅失败不影响主流程，静默处理
    });
  }
});

