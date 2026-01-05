/**
 * 微信订阅消息工具
 */
const app = getApp();

let templateIdsCache = null;

/**
 * 获取模板ID配置（从后端获取）
 */
async function getTemplateIds() {
  if (templateIdsCache) {
    return templateIdsCache;
  }
  
  try {
    const result = await app.request({
      url: '/auth/subscribe/template_ids/',
      method: 'GET'
    });
    
    templateIdsCache = result.templates || {};
    return templateIdsCache;
  } catch (err) {
    return {};
  }
}

/**
 * 引导用户订阅消息
 * @param {string} alertType 警报类型
 * @param {object} options 选项
 */
async function subscribeMessage(alertType, options = {}) {
  try {
    const templateIds = await getTemplateIds();
    const templateId = templateIds[alertType];
    
    if (!templateId) {
      return { success: false, reason: 'template_not_configured' };
    }
    
    return new Promise((resolve, reject) => {
      wx.requestSubscribeMessage({
        tmplIds: [templateId],
        success: async (res) => {
          const status = res[templateId];
          const subscribeStatus = status === 'accept';
          
          try {
            await app.request({
              url: '/auth/subscribe/subscribe/',
              method: 'POST',
              data: {
                template_id: templateId,
                subscribe_status: subscribeStatus
              }
            });
          } catch (err) {
            // 静默失败，不影响用户操作
            console.error('订阅状态更新失败:', err);
          }
          
          if (subscribeStatus && options.showToast !== false) {
            wx.showToast({
              title: '订阅成功',
              icon: 'success',
              duration: 1500
            });
          }
          
          resolve({ success: true, status: subscribeStatus });
        },
        fail: reject
      });
    });
  } catch (err) {
    return { success: false, error: err };
  }
}

/**
 * 订阅所有警报类型的消息
 * @param {object} options 选项
 */
async function subscribeAllAlerts(options = {}) {
  try {
    const templateIds = await getTemplateIds();
    const templateIdList = Object.values(templateIds).filter(id => id);
    
    if (templateIdList.length === 0) {
      return { success: false, reason: 'no_templates_configured' };
    }
    
    return new Promise((resolve, reject) => {
      wx.requestSubscribeMessage({
        tmplIds: templateIdList,
        success: async (res) => {
          const promises = Object.entries(templateIds).map(([alertType, templateId]) => {
            const status = res[templateId];
            const subscribeStatus = status === 'accept';
            
            return app.request({
              url: '/auth/subscribe/subscribe/',
              method: 'POST',
              data: {
                template_id: templateId,
                subscribe_status: subscribeStatus
              }
            }).catch((err) => {
              // 静默失败，不影响整体流程
              console.error('订阅状态更新失败:', err);
            });
          });
          
          await Promise.all(promises);
          
          const acceptCount = templateIdList.filter(id => res[id] === 'accept').length;
          if (acceptCount > 0 && options.showToast !== false) {
            wx.showToast({
              title: `已订阅${acceptCount}类警报通知`,
              icon: 'success',
              duration: 2000
            });
          }
          
          resolve({ success: true, results: res });
        },
        fail: reject
      });
    });
  } catch (err) {
    return { success: false, error: err };
  }
}

module.exports = {
  subscribeMessage,
  subscribeAllAlerts,
  getTemplateIds
};
