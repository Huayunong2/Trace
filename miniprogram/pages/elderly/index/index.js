// pages/elderly/index/index.js - 老人角色首页
const app = getApp();

Page({
  data: {
    deviceId: null,
    device: null,
    location: null,
    loading: true,
    userInfo: null,
    _creatingDevice: false, // 防止重复创建设备的标志
    _deviceChecked: false, // 标记是否已检查过设备（避免每次onShow都检查）
    locationUpdateStarted: false, // 标记是否已开始后台定位更新
    lastUploadTime: null, // 上次上传位置的时间（用于控制上传频率）
  },

  onLoad() {
    // 首次加载时重置设备检查标志
    this.setData({ _deviceChecked: false, _creatingDevice: false });
    this.checkLoginAndLoad();
  },

  onShow() {
    // onShow时不重置_deviceChecked，避免重复检查设备
    // 只刷新数据，不重新创建设备
    this.checkLoginAndLoad();
    
    // 如果设备已绑定且定位更新未启动，重新启动
    if (this.data.deviceId && this.data.device && this.data.device.is_active && !this.data.locationUpdateStarted) {
      this.startLocationUpload();
    }
  },

  onHide() {
    // 页面隐藏时，不停止定位更新（保持后台定位）
    // 使用 wx.startLocationUpdate() 后，小程序在后台时也能继续获取位置
    
    // 如果使用后台定位API，则继续运行
    // 如果使用传统方式，定时器可能会被暂停（这是正常的，因为传统方式不支持后台）
    if (this.data.locationUpdateStarted) {
    }
  },

  // 检查登录并加载数据
  checkLoginAndLoad() {
    if (!app.globalData.token) {
      // 未登录，跳转到登录页
      wx.reLaunch({
        url: '/pages/login/login'
      });
      return;
    }

    if (!app.globalData.userInfo) {
      app.getUserInfo().then(userInfo => {
        this.setData({ userInfo });
        // 重置设备检查标志，重新加载设备
        this.setData({ _deviceChecked: false });
        this.loadDevice();
      }).catch(() => {
        // 如果获取用户信息失败，跳转到登录页
        wx.reLaunch({
          url: '/pages/login/login'
        });
      });
    } else {
      this.setData({ userInfo: app.globalData.userInfo });
      // onShow时不重置_deviceChecked，避免重复检查
      // 只在onLoad时重置，确保首次加载会检查设备
      this.loadDevice();
    }
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
          wx.removeStorageSync('userRole');
          wx.removeStorageSync('userProfile');
          wx.reLaunch({
            url: '/pages/login/login'
          });
        }
      }
    });
  },

  // 加载设备信息
  loadDevice() {
    // 如果正在创建设备，不重复加载
    if (this.data._creatingDevice) {
      return;
    }
    
    this.setData({ loading: true });

    // 老人角色直接查询与自己关联的设备
    const userId = app.globalData.userInfo?.id;
    if (!userId) {
      app.getUserInfo().then(() => {
        this.loadDevice();
      });
      return;
    }

    // 直接查询设备（后端已支持elderly__user查询）
    app.request({
      url: `/devices/`,
      method: 'GET'
    }).then(result => {
      const devices = result.results || result;
      
      if (devices.length > 0) {
        const device = devices[0];
        this.setData({
          device: device,
          deviceId: device.device_id,
          _deviceChecked: true // 已检查过设备
        });
        
        // 如果设备已绑定到老人档案且有监护人，说明已绑定，开始上传位置
        if (device.elderly && device.device_id && device.is_active && device.elderly.guardian) {
          this.loadLocation();
          this.startLocationUpload();
        } else {
          // 未绑定监护人，但已有设备ID，等待监护人绑定
          this.setData({ loading: false });
        }
      } else {
        // 没有设备，且之前没有尝试过创建，才创建设备
        if (!this.data._deviceChecked && !this.data._creatingDevice) {
          this.createDeviceAndGenerateQR();
        } else {
          // 已经检查过但没有设备，可能是设备创建中或失败，不重复创建
          this.setData({ loading: false });
        }
      }
    }).catch(err => {
      this.setData({ loading: false, _deviceChecked: true });
    });
  },

  // 创建设备并生成设备ID（老人角色）
  createDeviceAndGenerateQR() {
    // 防止重复调用
    if (this._creatingDevice) {
      return;
    }
    this._creatingDevice = true;
    
    wx.showActionSheet({
      itemList: ['智能手环', '手机'],
      success: (res) => {
        const deviceTypes = ['smart_bracelet', 'phone'];
        const deviceType = deviceTypes[res.tapIndex];
        
        wx.showLoading({ title: '生成设备中...', mask: true });
        
        // 老人角色先获取或创建自己的老人档案（仅用于设备关联，但设备可以被其他监护人绑定）
        app.request({
          url: '/auth/elderly/',
          method: 'GET'
        }).then(elderlyResult => {
          const elderlyList = elderlyResult.results || elderlyResult;
          let elderlyId = null;
          
          if (elderlyList.length > 0) {
            // 已有老人档案，直接使用
            elderlyId = elderlyList[0].id;
            // 创建设备
            return app.request({
              url: '/devices/',
              method: 'POST',
              data: {
                elderly_id: elderlyId,
                name: '定位设备',
                device_type: deviceType
              }
            });
          } else {
            // 如果没有老人档案，创建一个临时档案（关联到当前用户）
            const userInfo = app.globalData.userInfo || {};
            return app.request({
              url: '/auth/elderly/',
              method: 'POST',
              data: {
                name: userInfo.username || '老人',
                emergency_contact: '未设置',
                emergency_phone: userInfo.phone || '00000000000',
                address: '未设置地址'
              }
            }).then(newElderly => {
              elderlyId = newElderly.id;
              if (!elderlyId) {
                throw new Error('无法获取老人档案ID');
              }
              // 创建设备（设备ID由后端自动生成UUID）
              // 设备初始关联到老人的ElderlyProfile，但可以被监护人重新绑定
              return app.request({
                url: '/devices/',
                method: 'POST',
                data: {
                  elderly_id: elderlyId,
                  name: '定位设备',
                  device_type: deviceType
                }
              });
            });
          }
        }).then(device => {
          wx.hideLoading();
          this._creatingDevice = false;
          this.setData({ creatingDevice: false });
          // 设备创建成功，重新加载设备信息
          this.loadDevice();
        }).catch(err => {
          wx.hideLoading();
          this._creatingDevice = false;
          this.setData({ creatingDevice: false });
          let errorMsg = '创建设备失败';
          if (err.message) {
            if (err.message.includes('已绑定设备')) {
              errorMsg = '您已有设备，请刷新页面查看';
            } else {
              errorMsg = err.message;
            }
          }
          wx.showToast({
            title: errorMsg,
            icon: 'none',
            duration: 2500
          });
          this.setData({ loading: false });
        });
      },
      fail: () => {
        this._creatingDevice = false;
        this.setData({ creatingDevice: false, loading: false });
      }
    });
  },

  // 加载当前位置
  loadLocation() {
    // 先检查定位权限
    wx.getSetting({
      success: (res) => {
        if (res.authSetting['scope.userLocation']) {
          // 已授权，直接获取位置
          this.doGetLocation();
        } else if (res.authSetting['scope.userLocation'] === false) {
          // 用户之前拒绝了授权，需要引导开启
          wx.showModal({
            title: '需要定位权限',
            content: '为了提供定位服务，需要获取您的位置信息。请在设置中开启定位权限。',
            confirmText: '去设置',
            cancelText: '取消',
            success: (modalRes) => {
              if (modalRes.confirm) {
                wx.openSetting({
                  success: (settingRes) => {
                    if (settingRes.authSetting['scope.userLocation']) {
                      this.doGetLocation();
                    }
                  }
                });
              }
            }
          });
        } else {
          // 未授权，请求授权
          wx.authorize({
            scope: 'scope.userLocation',
            success: () => {
              this.doGetLocation();
            },
            fail: () => {
              wx.showModal({
                title: '需要定位权限',
                content: '为了提供定位服务，需要获取您的位置信息。请允许定位权限。',
                confirmText: '去设置',
                cancelText: '取消',
                success: (modalRes) => {
                  if (modalRes.confirm) {
                    wx.openSetting();
                  }
                }
              });
            }
          });
        }
      },
      fail: () => {
        // 获取设置失败，直接尝试获取位置
        this.doGetLocation();
      }
    });
  },

  // 执行获取位置
  doGetLocation() {
    wx.getLocation({
      type: 'gcj02',
      altitude: false,
      isHighAccuracy: true,  // 高精度定位
      success: (res) => {
        // 格式化经纬度显示（保留6位小数）
        const latitude = parseFloat(res.latitude);
        const longitude = parseFloat(res.longitude);
        
        this.setData({
          location: {
            latitude: latitude,
            longitude: longitude,
            latitudeStr: latitude.toFixed(6),
            longitudeStr: longitude.toFixed(6)
          }
        });
        
        // 上传位置到服务器
        if (this.data.deviceId) {
          this.uploadLocation(res);
        }
        
        this.setData({ loading: false });
      },
      fail: (err) => {
        this.setData({ loading: false });
        
        // 根据错误类型提供更友好的提示
        let errorMsg = '获取位置失败';
        let needOpenSetting = false;
        
        if (err.errMsg) {
          if (err.errMsg.includes('auth deny') || err.errMsg.includes('permission denied')) {
            errorMsg = '定位权限被拒绝，请在设置中允许定位权限';
            needOpenSetting = true;
          } else if (err.errMsg.includes('ERROR_NOCELL&WIFI_LOCATIONSWITCHOFF') || 
                     err.errMsg.includes('locationSwitchOff')) {
            errorMsg = '定位服务未开启，请在系统设置中开启定位服务';
          } else if (err.errMsg.includes('timeout')) {
            errorMsg = '定位超时，请重试';
          } else if (err.errMsg.includes('fail')) {
            errorMsg = '定位失败，请检查定位服务是否开启';
          }
        }
        
        wx.showModal({
          title: '定位失败',
          content: errorMsg + '\n\n提示：确保已开启系统定位服务和微信定位权限。',
          confirmText: needOpenSetting ? '去设置' : '知道了',
          cancelText: '取消',
          success: (modalRes) => {
            if (needOpenSetting && modalRes.confirm) {
              wx.openSetting();
            }
          }
        });
      }
    });
  },

  // 获取电池电量（返回Promise，统一异步处理）
  getBatteryLevel() {
    return new Promise((resolve) => {
      // 先尝试使用同步API（更快）
      try {
        const batteryInfo = wx.getBatteryInfoSync();
        if (batteryInfo && batteryInfo.level !== undefined && batteryInfo.level !== null) {
          const level = parseInt(batteryInfo.level);
          if (!isNaN(level) && level >= 0 && level <= 100) {
            resolve(level);
            return;
          }
        }
      } catch (err) {
        // 同步API失败，继续尝试异步API
      }
      
      // 如果同步API失败，尝试异步API
      wx.getBatteryInfo({
        success: (res) => {
          if (res && res.level !== undefined && res.level !== null) {
            const level = parseInt(res.level);
            if (!isNaN(level) && level >= 0 && level <= 100) {
              resolve(level);
            } else {
              resolve(null);
            }
          } else {
            resolve(null);
          }
        },
        fail: (err) => {
          resolve(null);
        }
      });
    });
  },

  // 上传位置
  async uploadLocation(location) {
    if (!this.data.deviceId) return;

    // 限制经纬度精度到7位小数（符合后端DecimalField定义）
    const latitude = parseFloat(location.latitude).toFixed(7);
    const longitude = parseFloat(location.longitude).toFixed(7);

    // 获取电池电量
    let batteryLevel = null;
    try {
      const level = await this.getBatteryLevel();
      if (level !== null && level !== undefined) {
        batteryLevel = Math.max(0, Math.min(100, parseInt(level))); // 确保在0-100范围内
      }
    } catch (err) {
    }
    
    // 如果获取失败，尝试使用设备当前电量（如果有）
    if (batteryLevel === null && this.data.device && this.data.device.battery_level !== undefined) {
      batteryLevel = this.data.device.battery_level;
    }
    
    // 如果还是没有，使用默认值100（表示电量正常）
    if (batteryLevel === null) {
      batteryLevel = 100;
    }

    // 准备上传数据
    const uploadData = {
      device_id: this.data.deviceId,
      latitude: latitude,
      longitude: longitude,
      address: location.address || ''
    };
    
    // 如果成功获取到电量，添加到上传数据中
    if (batteryLevel !== null) {
      uploadData.battery_level = batteryLevel;
    }

    app.request({
      url: '/locations/upload/',
      method: 'POST',
      data: uploadData
    }).then(result => {
      // 上传成功后，更新本地设备电量显示
      if (batteryLevel !== null && this.data.device) {
        this.setData({
          'device.battery_level': batteryLevel
        });
      }
    }).catch(err => {
    });
  },

  // 开始后台定位更新（使用微信小程序后台定位API）
  startLocationUpload() {
    // 如果已经启动，先停止
    if (this.data.locationUpdateStarted) {
      this.stopLocationUpload();
    }

    // 检查设备状态
    if (!this.data.device || !this.data.device.is_active || !this.data.deviceId) {
      return;
    }

    // 先检查定位权限
    wx.getSetting({
      success: (res) => {
        if (res.authSetting['scope.userLocation'] === false) {
          // 用户拒绝了授权，提示开启
          wx.showModal({
            title: '需要定位权限',
            content: '为了在后台持续追踪位置，需要您授权定位权限。请在设置中开启定位权限（建议选择"使用小程序期间和离开小程序后"）。',
            confirmText: '去设置',
            cancelText: '取消',
            success: (modalRes) => {
              if (modalRes.confirm) {
                wx.openSetting({
                  success: (settingRes) => {
                    if (settingRes.authSetting['scope.userLocation']) {
                      // 授权成功，重新启动定位
                      this.startLocationUpload();
                    }
                  }
                });
              }
            }
          });
          return;
        }

        // 开始后台定位更新
        wx.startLocationUpdate({
          success: () => {
            this.setData({ locationUpdateStarted: true });
            
            // 监听位置变化事件（全局监听器，页面隐藏后仍然有效）
            // 注意：onLocationChange是全局监听器，不需要在每个页面单独设置
            // 但如果多次调用startLocationUpdate，可能会创建多个监听器
            // 为了避免重复监听，需要在调用前检查是否已设置
            if (!this.locationChangeHandler) {
              this.locationChangeHandler = (res) => {
                // 控制上传频率：每30秒上传一次
                const now = Date.now();
                const lastUploadTime = this.data.lastUploadTime || 0;
                const timeSinceLastUpload = now - lastUploadTime;
                
                // 如果距离上次上传超过30秒，或者首次上传，则上传位置
                if (timeSinceLastUpload >= 30000 || lastUploadTime === 0) {
                  // 更新位置显示
                  const latitude = parseFloat(res.latitude);
                  const longitude = parseFloat(res.longitude);
                  this.setData({
                    location: {
                      latitude: latitude,
                      longitude: longitude,
                      latitudeStr: latitude.toFixed(6),
                      longitudeStr: longitude.toFixed(6)
                    },
                    lastUploadTime: now
                  });
                  
                  // 上传位置到服务器
                  this.uploadLocationFromChange(res);
                } else {
                  // 只更新显示，不上传（节省流量和服务器资源）
                  const latitude = parseFloat(res.latitude);
                  const longitude = parseFloat(res.longitude);
                  this.setData({
                    location: {
                      latitude: latitude,
                      longitude: longitude,
                      latitudeStr: latitude.toFixed(6),
                      longitudeStr: longitude.toFixed(6)
                    }
                  });
                }
              };
              
              wx.onLocationChange(this.locationChangeHandler);
            }

            // 立即获取一次位置（用于显示）
            this.loadLocation();
          },
          fail: (err) => {
            this.setData({ locationUpdateStarted: false });
            
            // 如果启动失败，回退到传统的定位方式
            wx.showModal({
              title: '定位启动失败',
              content: '后台定位启动失败，将使用普通定位模式。可能需要在设置中允许后台定位权限。',
              showCancel: false,
              success: () => {
                // 回退到传统方式（仅在前台时定位）
                this.startLocationUploadFallback();
              }
            });
          }
        });
      },
      fail: (err) => {
        // 直接尝试启动（可能已经授权）
        wx.startLocationUpdate({
          success: () => {
            this.setData({ locationUpdateStarted: true });
            // 使用已创建的监听器（避免重复创建）
            if (!this.locationChangeHandler) {
              this.locationChangeHandler = (res) => {
                // 控制上传频率：每30秒上传一次
                const now = Date.now();
                const lastUploadTime = this.data.lastUploadTime || 0;
                const timeSinceLastUpload = now - lastUploadTime;
                
                // 如果距离上次上传超过30秒，或者首次上传，则上传位置
                if (timeSinceLastUpload >= 30000 || lastUploadTime === 0) {
                  // 更新位置显示
                  const latitude = parseFloat(res.latitude);
                  const longitude = parseFloat(res.longitude);
                  this.setData({
                    location: {
                      latitude: latitude,
                      longitude: longitude,
                      latitudeStr: latitude.toFixed(6),
                      longitudeStr: longitude.toFixed(6)
                    },
                    lastUploadTime: now
                  });
                  
                  // 上传位置到服务器
                  this.uploadLocationFromChange(res);
                } else {
                  // 只更新显示，不上传
                  const latitude = parseFloat(res.latitude);
                  const longitude = parseFloat(res.longitude);
                  this.setData({
                    location: {
                      latitude: latitude,
                      longitude: longitude,
                      latitudeStr: latitude.toFixed(6),
                      longitudeStr: longitude.toFixed(6)
                    }
                  });
                }
              };
              
              wx.onLocationChange(this.locationChangeHandler);
            }
            // 立即获取一次位置（用于显示）
            this.loadLocation();
          },
          fail: (startErr) => {
            this.setData({ locationUpdateStarted: false });
          }
        });
      }
    });
  },

  // 回退方案：使用传统定位方式（仅在前台有效）
  startLocationUploadFallback() {
    if (this.locationTimer) {
      clearInterval(this.locationTimer);
    }
    
    // 立即获取一次位置
    this.loadLocation();
    
    // 每30秒获取一次位置（仅在前台有效）
    this.locationTimer = setInterval(() => {
      if (this.data.device && this.data.device.is_active) {
        this.loadLocation();
      }
    }, 30000);
    
  },

  // 停止后台定位更新
  stopLocationUpload() {
    // 停止后台定位
    if (this.data.locationUpdateStarted) {
      wx.stopLocationUpdate({
        success: () => {
        },
        fail: (err) => {
        }
      });
      this.setData({ locationUpdateStarted: false });
    }

    // 清除传统定时器（如果有）
    if (this.locationTimer) {
      clearInterval(this.locationTimer);
      this.locationTimer = null;
    }

    // 注意：wx.onLocationChange() 是全局监听器
    // 调用 wx.stopLocationUpdate() 后，位置变化监听会自动停止
    // 但是为了确保完全清理，我们可以清除handler引用
    // 注意：微信小程序不支持手动移除onLocationChange监听器，只能通过stopLocationUpdate停止
    this.locationChangeHandler = null;
  },

  // 从位置变化事件上传位置（用于后台定位）
  async uploadLocationFromChange(locationRes) {
    if (!this.data.deviceId) return;

    // 限制经纬度精度到7位小数
    const latitude = parseFloat(locationRes.latitude).toFixed(7);
    const longitude = parseFloat(locationRes.longitude).toFixed(7);

    // 获取电池电量
    let batteryLevel = null;
    try {
      const level = await this.getBatteryLevel();
      if (level !== null && level !== undefined) {
        batteryLevel = Math.max(0, Math.min(100, parseInt(level)));
      }
    } catch (err) {
    }
    
    // 如果获取失败，尝试使用设备当前电量
    if (batteryLevel === null && this.data.device && this.data.device.battery_level !== undefined) {
      batteryLevel = this.data.device.battery_level;
    }
    
    // 如果还是没有，使用默认值100
    if (batteryLevel === null) {
      batteryLevel = 100;
    }

    // 准备上传数据
    const uploadData = {
      device_id: this.data.deviceId,
      latitude: latitude,
      longitude: longitude,
      address: locationRes.address || ''
    };
    
    // 如果成功获取到电量，添加到上传数据中
    if (batteryLevel !== null) {
      uploadData.battery_level = batteryLevel;
    }

    app.request({
      url: '/locations/upload/',
      method: 'POST',
      data: uploadData
    }).then(result => {
      // 上传成功后，更新本地设备电量显示
      if (batteryLevel !== null && this.data.device) {
        this.setData({
          'device.battery_level': batteryLevel
        });
      }
    }).catch(err => {
    });
  },

  // 主动发送SOS报警
  sendSOS() {
    if (!this.data.deviceId) {
      wx.showToast({
        title: '设备未绑定',
        icon: 'none'
      });
      return;
    }

    // 检查设备是否已绑定监护人
    const device = this.data.device;
    if (!device || !device.elderly || !device.elderly.guardian) {
      wx.showModal({
        title: '无法发送求救',
        content: '设备尚未绑定监护人，请先让监护人绑定设备后再使用紧急求救功能。',
        showCancel: false,
        confirmText: '知道了'
      });
      return;
    }

    wx.showModal({
      title: '紧急求救',
      content: '确定要发送SOS求救信号吗？',
      confirmText: '确定发送',
      confirmColor: '#E74C3C',
      success: (res) => {
        if (res.confirm) {
          wx.showLoading({ title: '发送中...', mask: true });
          
          app.request({
            url: '/alerts/sos/',
            method: 'POST',
            data: {
              device_id: this.data.deviceId
            }
          }).then(() => {
            wx.hideLoading();
            wx.showToast({
              title: '求救信号已发送',
              icon: 'success'
            });
          }).catch(err => {
            wx.hideLoading();
            let errorMsg = err.message || '发送失败';
            if (errorMsg.includes('尚未绑定监护人')) {
              errorMsg = '设备尚未绑定监护人，请先让监护人绑定设备';
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

  // 查看位置
  viewLocation() {
    if (!this.data.location) {
      wx.showToast({
        title: '暂无位置信息',
        icon: 'none'
      });
      return;
    }

    // 从后端获取最新位置信息（包含地址）
    app.request({
      url: `/locations/latest/?device_id=${this.data.deviceId}`,
      method: 'GET',
      silent: true
    }).then(locationData => {
      const address = locationData.address || '';
      wx.openLocation({
        latitude: this.data.location.latitude,
        longitude: this.data.location.longitude,
        name: '我的位置',
        address: address
      });
    }).catch(() => {
      // 如果获取失败，仍然打开地图（不带地址）
      wx.openLocation({
        latitude: this.data.location.latitude,
        longitude: this.data.location.longitude,
        name: '我的位置',
        address: ''
      });
    });
  },


  // 刷新数据
  refresh() {
    this.loadDevice();
    if (this.data.device && this.data.device.is_active) {
      this.loadLocation();
    }
    wx.showToast({
      title: '已刷新',
      icon: 'success',
      duration: 1500
    });
  },

  // 复制设备ID
  copyDeviceId(e) {
    const deviceId = e.currentTarget.dataset.id || this.data.device?.device_id;
    if (!deviceId) {
      wx.showToast({
        title: '设备ID不存在',
        icon: 'none'
      });
      return;
    }
    
    wx.setClipboardData({
      data: deviceId,
      success: () => {
        wx.showToast({
          title: '设备ID已复制',
          icon: 'success'
        });
      },
      fail: () => {
        wx.showToast({
          title: '复制失败',
          icon: 'none'
        });
      }
    });
  },

  onUnload() {
    // 页面卸载时，停止定位更新
    // 注意：对于后台定位，即使页面卸载，定位也可能继续（取决于小程序生命周期）
    // 但为了资源管理，我们仍然在这里停止定位
    this.stopLocationUpload();
  }
});

