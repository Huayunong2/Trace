// pages/track/track.js
const app = getApp();

Page({
  data: {
    deviceId: null,
    trackData: null,
    selectedDate: '',
    markers: [],
    polyline: []
  },

  onLoad(options) {
    if (options.deviceId) {
      this.setData({ deviceId: options.deviceId });
      const today = new Date().toISOString().split('T')[0];
      this.setData({ selectedDate: today });
      this.loadTrack();
    }
  },

  // 选择日期
  onDateChange(e) {
    this.setData({ selectedDate: e.detail.value });
    this.loadTrack();
  },

  // 加载轨迹数据
  loadTrack() {
    const { deviceId, selectedDate } = this.data;
    const startTime = `${selectedDate}T00:00:00`;
    const endTime = `${selectedDate}T23:59:59`;
    
    app.request({
      url: `/locations/track/?device_id=${deviceId}&start_time=${startTime}&end_time=${endTime}`,
      method: 'GET'
    }).then(result => {
      this.setData({ trackData: result });
      this.updateMap();
    });
  },

  // 更新地图
  updateMap() {
    const locations = this.data.trackData?.locations || [];
    
    if (locations.length === 0) {
      return;
    }
    
    // 设置标记点
    const markers = locations.map((loc, index) => ({
      id: index,
      latitude: parseFloat(loc.latitude),
      longitude: parseFloat(loc.longitude),
      iconPath: '',
      width: 30,
      height: 30
    }));
    
    // 设置路线
    const points = locations.map(loc => ({
      latitude: parseFloat(loc.latitude),
      longitude: parseFloat(loc.longitude)
    }));
    
    const polyline = [{
      points: points,
      color: '#4A90E2',
      width: 4
    }];
    
    this.setData({ markers, polyline });
  }
});

