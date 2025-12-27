// pages/admin/config/config.js - 系统配置
const app = getApp();

Page({
  data: {
    configs: [],
    loading: true,
    showAddForm: false,
    editingConfig: null,
    formData: {
      key: '',
      value: '',
      value_type: 'string',
      description: '',
      is_public: false
    }
  },

  onLoad() {
    this.checkPermissionAndLoad();
  },

  onShow() {
    this.loadConfigs();
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

    this.loadConfigs();
  },

  // 加载配置列表
  loadConfigs() {
    this.setData({ loading: true });

    app.request({
      url: '/system/configs/',
      method: 'GET'
    }).then(result => {
      this.setData({
        configs: result.results || result || [],
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

  // 显示添加表单
  showAddForm() {
    this.setData({
      showAddForm: true,
      editingConfig: null,
      formData: {
        key: '',
        value: '',
        value_type: 'string',
        description: '',
        is_public: false
      }
    });
  },

  // 显示编辑表单
  showEditForm(e) {
    const config = e.currentTarget.dataset.config;
    this.setData({
      showAddForm: true,
      editingConfig: config,
      formData: {
        key: config.key,
        value: config.value,
        value_type: config.value_type,
        description: config.description || '',
        is_public: config.is_public
      }
    });
  },

  // 取消编辑
  cancelEdit() {
    this.setData({
      showAddForm: false,
      editingConfig: null
    });
  },

  // 输入处理
  onKeyInput(e) {
    this.setData({ 'formData.key': e.detail.value });
  },

  onValueInput(e) {
    this.setData({ 'formData.value': e.detail.value });
  },

  onDescriptionInput(e) {
    this.setData({ 'formData.description': e.detail.value });
  },

  onTypeChange(e) {
    const types = ['string', 'integer', 'float', 'boolean', 'json'];
    this.setData({ 'formData.value_type': types[e.detail.value] });
  },

  onPublicChange(e) {
    this.setData({ 'formData.is_public': e.detail.value });
  },

  // 提交表单
  submitForm() {
    const { formData, editingConfig } = this.data;

    if (!formData.key || !formData.value) {
      wx.showToast({
        title: '请填写配置键和值',
        icon: 'none'
      });
      return;
    }

    wx.showLoading({
      title: editingConfig ? '保存中...' : '添加中...',
      mask: true
    });

    const url = editingConfig ? `/system/configs/${editingConfig.id}/` : '/system/configs/';
    const method = editingConfig ? 'PUT' : 'POST';

    app.request({
      url: url,
      method: method,
      data: formData
    }).then(() => {
      wx.hideLoading();
      wx.showToast({
        title: editingConfig ? '保存成功' : '添加成功',
        icon: 'success'
      });
      this.cancelEdit();
      this.loadConfigs();
    }).catch(err => {
      wx.hideLoading();
      wx.showToast({
        title: err.message || '操作失败',
        icon: 'none'
      });
    });
  },

  // 删除配置
  deleteConfig(e) {
    const config = e.currentTarget.dataset.config;

    wx.showModal({
      title: '确认删除',
      content: `确定要删除配置"${config.key}"吗？`,
      confirmColor: '#FF5252',
      success: (res) => {
        if (res.confirm) {
          wx.showLoading({
            title: '删除中...',
            mask: true
          });

          app.request({
            url: `/system/configs/${config.id}/`,
            method: 'DELETE'
          }).then(() => {
            wx.hideLoading();
            wx.showToast({
              title: '删除成功',
              icon: 'success'
            });
            this.loadConfigs();
          }).catch(err => {
            wx.hideLoading();
            wx.showToast({
              title: err.message || '删除失败',
              icon: 'none'
            });
          });
        }
      }
    });
  },

  // 刷新
  refresh() {
    this.loadConfigs();
  }
});

