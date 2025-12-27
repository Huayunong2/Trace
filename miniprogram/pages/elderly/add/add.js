// pages/elderly/add.js
const app = getApp();

Page({
  data: {
    formData: {
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

  // 表单输入
  onInput(e) {
    const field = e.currentTarget.dataset.field;
    this.setData({
      [`formData.${field}`]: e.detail.value
    });
  },

  // 性别选择
  onGenderChange(e) {
    this.setData({
      'formData.gender': e.detail.value
    });
  },

  // 选择照片
  choosePhoto() {
    wx.chooseImage({
      count: 1,
      success: (res) => {
        wx.showToast({
          title: '图片选择成功',
          icon: 'success'
        });
      }
    });
  },

  // 提交表单
  submit() {
    const { formData } = this.data;
    
    // 验证必填项
    if (!formData.name || !formData.name.trim()) {
      wx.showToast({
        title: '请输入姓名',
        icon: 'none'
      });
      return;
    }
    
    if (!formData.emergency_contact || !formData.emergency_contact.trim()) {
      wx.showToast({
        title: '请输入紧急联系人',
        icon: 'none'
      });
      return;
    }
    
    if (!formData.emergency_phone || !formData.emergency_phone.trim()) {
      wx.showToast({
        title: '请输入紧急联系电话',
        icon: 'none'
      });
      return;
    }

    // 验证手机号格式
    if (formData.emergency_phone && !/^1[3-9]\d{9}$/.test(formData.emergency_phone)) {
      wx.showToast({
        title: '请输入正确的手机号',
        icon: 'none'
      });
      return;
    }
    
    wx.showLoading({
      title: '添加中...',
      mask: true
    });
    
    app.request({
      url: '/auth/elderly/',
      method: 'POST',
      data: {
        name: formData.name.trim(),
        age: formData.age ? parseInt(formData.age) : null,
        gender: formData.gender || null,
        medical_history: formData.medical_history || '',
        emergency_contact: formData.emergency_contact.trim(),
        emergency_phone: formData.emergency_phone.trim(),
        address: formData.address || '',
        notes: formData.notes || ''
      }
    }).then(() => {
      wx.hideLoading();
      wx.showToast({
        title: '添加成功',
        icon: 'success'
      });
      setTimeout(() => {
        wx.navigateBack();
      }, 1500);
    }).catch(err => {
      wx.hideLoading();
      wx.showToast({
        title: err.message || '添加失败',
        icon: 'none',
        duration: 2000
      });
    });
  }
});

