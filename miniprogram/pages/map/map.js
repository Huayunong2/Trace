// pages/map/map.js
const app = getApp();

Page({
  data: {
    deviceId: null,
    device: null,
    location: null,  // 设备位置数据
    fences: [],
    markers: [],
    polyline: [],
    circles: [],
    mapCenter: {
      latitude: 39.908823,
      longitude: 116.397470
    },
    mapScale: 16,
    loading: true
  },

  onLoad(options) {
    // switchTab 不支持参数传递，优先从全局数据获取
    let deviceId = options.deviceId || app.globalData.currentDeviceId;
    
    if (deviceId) {
      this.setData({ deviceId: deviceId });
      app.globalData.currentDeviceId = null;
      this.loadMapData();
    } else {
      this.loadFirstDevice();
    }
  },

  onShow() {
    // 每次显示时检查是否有新的设备ID
    if (app.globalData.currentDeviceId && app.globalData.currentDeviceId !== this.data.deviceId) {
      const deviceId = app.globalData.currentDeviceId;
      this.setData({ deviceId: deviceId });
      app.globalData.currentDeviceId = null;
      this.loadMapData();
    } else if (this.data.deviceId) {
      this.loadMapData();
      // 开始定时更新位置
      this.startLocationUpdate();
    }
  },



  onUnload() {
    // 停止定时更新
    if (this.updateTimer) {
      clearInterval(this.updateTimer);
    }
  },

  // 加载第一个设备
  loadFirstDevice() {
    this.setData({ loading: true });
    
    // 先检查登录
    if (!app.globalData.token) {
      app.wxLogin().then(() => {
        this.loadFirstDeviceInternal();
      }).catch(() => {
        this.setData({ loading: false });
        wx.showToast({
          title: '请先登录',
          icon: 'none'
        });
      });
    } else {
      this.loadFirstDeviceInternal();
    }
  },

  // 内部加载第一个设备方法
  loadFirstDeviceInternal() {
    app.request({
      url: '/auth/elderly/',
      method: 'GET'
    }).then(result => {
      const elderlyList = result.results || result;
      const elderlyWithDevice = elderlyList.find(elderly => elderly.device && elderly.device.device_id);
      
      if (elderlyWithDevice) {
        const deviceId = elderlyWithDevice.device.device_id;
        this.setData({ deviceId: deviceId });
        this.loadMapData();
      } else {
        wx.showToast({
          title: '暂无设备，请先添加',
          icon: 'none',
          duration: 2000
        });
        this.setData({ loading: false });
      }
    }).catch(() => {
      this.setData({ loading: false });
      wx.showToast({
        title: '加载失败',
        icon: 'none'
      });
    });
  },

  // 加载地图数据
  loadMapData() {
    this.setData({ loading: true });
    
    Promise.all([
      this.loadDeviceInfo(),
      this.loadLatestLocation(),
      this.loadFences()
    ]).finally(() => {
      this.setData({ loading: false });
    });
  },

  // 加载设备信息
  loadDeviceInfo() {
    if (!this.data.deviceId) return Promise.resolve();
    
    return app.request({
      url: `/devices/?device_id=${this.data.deviceId}`,
      method: 'GET'
    }).then(result => {
      const devices = result.results || result;
      if (devices.length > 0) {
        const device = devices[0];
        // 确保设备信息完整
        const deviceData = {
          ...device,
          status: device.status || 'offline',
          battery_level: device.battery_level !== undefined && device.battery_level !== null 
            ? device.battery_level 
            : 100,
          device_type: device.device_type || 'smart_bracelet',
          name: device.name || '定位设备'
        };
        this.setData({ device: deviceData });
      }
      }).catch((err) => {
        // 获取地址失败，静默处理，不影响地图显示
        console.error('获取地址失败:', err);
      });
  },

  // 加载最新位置
  loadLatestLocation() {
    if (!this.data.deviceId) return Promise.resolve();
    
    return app.request({
      url: `/locations/latest/?device_id=${this.data.deviceId}`,
      method: 'GET',
      silent: true  // 静默处理，不显示错误提示
    }).then(result => {
      if (result && result.latitude && result.longitude) {
        this.setData({
          location: result,
          mapCenter: {
            latitude: parseFloat(result.latitude),
            longitude: parseFloat(result.longitude)
          }
        });
        this.updateMarkers();
        this.updateCircles(); // 更新围栏圆圈（检查越界状态）
      } else {
        // 没有位置数据
        this.setData({ location: null });
        this.updateMarkers();
      }
    }).catch(err => {
      // 404错误（未找到位置信息）是正常情况，完全静默处理
      this.setData({ location: null });
      this.updateMarkers();
    });
  },

  // 加载围栏
  loadFences() {
    if (!this.data.deviceId) return Promise.resolve();
    
    return app.request({
      url: `/fences/?device_id=${this.data.deviceId}`,
      method: 'GET'
    }).then(result => {
      const fences = result.results || result;
      this.setData({ fences });
      this.updateCircles(); // 更新围栏圆圈
    });
  },

  // 更新标记点
  updateMarkers() {
    const markers = [];
    
    // 只添加设备位置标记（使用默认标记）
    if (this.data.location && this.data.location.latitude && this.data.location.longitude) {
      markers.push({
        id: 1,
        latitude: parseFloat(this.data.location.latitude),
        longitude: parseFloat(this.data.location.longitude),
        width: 40,
        height: 40,
        callout: {
          content: this.data.device?.elderly?.name || '设备位置',
          color: '#333',
          fontSize: 14,
          borderRadius: 5,
          bgColor: '#fff',
          padding: 5,
          display: 'ALWAYS'
        }
      });
    }
    
    this.setData({ markers });
  },

  // 更新围栏圆圈
  updateCircles() {
    const { fences, location } = this.data;
    
    // 检查每个围栏是否越界（如果有位置信息）
    const circles = fences
      .filter(fence => {
        // 只显示激活的围栏，且必须有有效的经纬度
        return fence.is_active && 
               fence.center_latitude !== null && 
               fence.center_latitude !== undefined &&
               fence.center_longitude !== null && 
               fence.center_longitude !== undefined &&
               !isNaN(parseFloat(fence.center_latitude)) &&
               !isNaN(parseFloat(fence.center_longitude));
      })
      .map(fence => {
        const centerLat = parseFloat(fence.center_latitude);
        const centerLng = parseFloat(fence.center_longitude);
        const radius = parseInt(fence.radius) || 500;
        
        // 检查是否越界
        let isViolation = false;
        if (location && location.latitude && location.longitude) {
          const locLat = parseFloat(location.latitude);
          const locLng = parseFloat(location.longitude);
          
          if (!isNaN(locLat) && !isNaN(locLng)) {
            const distance = this.calculateDistance(locLat, locLng, centerLat, centerLng);
            isViolation = distance > radius;
          }
        }
        
        // 根据是否越界设置颜色：绿色（正常）或红色（越界）
        const strokeColor = isViolation ? '#FF5252' : '#4CAF50';
        const fillColor = isViolation ? '#FF525240' : '#4CAF5040';
        
        return {
          latitude: centerLat,
          longitude: centerLng,
          radius: radius,
          strokeWidth: 3,
          strokeColor: strokeColor,
          fillColor: fillColor
        };
      });
    
    this.setData({ circles });
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
    
    const R = 6371000;
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLon = (lon2 - lon1) * Math.PI / 180;
    const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
      Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
      Math.sin(dLon / 2) * Math.sin(dLon / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return R * c;
  },

  // 开始定时更新位置
  startLocationUpdate() {
    // 每30秒更新一次位置
    this.updateTimer = setInterval(() => {
      this.loadLatestLocation();
    }, 30000);
  },

  // 导航到当前位置（使用微信内置地图）
  navigateToLocation() {
    if (!this.data.location) {
      wx.showToast({
        title: '暂无位置信息',
        icon: 'none'
      });
      return;
    }
    
    const latitude = parseFloat(this.data.location.latitude);
    const longitude = parseFloat(this.data.location.longitude);
    const elderlyName = this.data.device?.elderly?.name || '老人位置';
    
    // 使用微信内置地图打开位置
    wx.openLocation({
      latitude: latitude,
      longitude: longitude,
      name: elderlyName,
      address: '',
      scale: 18,
      fail: () => {
        wx.showToast({
          title: '打开地图失败，请检查权限',
          icon: 'none'
        });
      }
    });
  },

  // 添加围栏
  addFence() {
    if (!this.data.deviceId) {
      this.loadFirstDeviceInternal();
      wx.showToast({
        title: '设备ID不存在，正在加载...',
        icon: 'none',
        duration: 2000
      });
      return;
    }
    wx.navigateTo({
      url: `/pages/fence/fence?deviceId=${this.data.deviceId}`
    });
  },

});

