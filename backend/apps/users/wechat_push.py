"""
微信订阅消息推送工具类
"""
import requests
import logging
import time
from django.conf import settings
from django.core.cache import cache
from datetime import datetime

logger = logging.getLogger(__name__)


class WeChatPushService:
    """微信订阅消息推送服务"""
    
    ACCESS_TOKEN_CACHE_KEY = 'wechat_access_token'
    ACCESS_TOKEN_EXPIRE = 7200  # access_token有效期2小时
    
    @staticmethod
    def get_access_token():
        """
        获取微信access_token（带缓存）
        """
        # 先从缓存获取
        access_token = cache.get(WeChatPushService.ACCESS_TOKEN_CACHE_KEY)
        if access_token:
            return access_token
        
        # 缓存中没有，重新获取
        appid = settings.WECHAT_APPID
        secret = settings.WECHAT_SECRET
        
        if not appid or not secret:
            logger.error('微信配置未设置：WECHAT_APPID 或 WECHAT_SECRET')
            return None
        
        url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={appid}&secret={secret}"
        
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if 'access_token' in data:
                access_token = data['access_token']
                expires_in = data.get('expires_in', 7200)
                # 缓存access_token，提前5分钟过期
                cache.set(WeChatPushService.ACCESS_TOKEN_CACHE_KEY, access_token, expires_in - 300)
                logger.info('成功获取微信access_token')
                return access_token
            else:
                logger.error(f'获取access_token失败: {data}')
                return None
        except Exception as e:
            logger.error(f'获取access_token异常: {e}')
            return None
    
    @staticmethod
    def send_subscribe_message(openid, template_id, page, data, retry_count=0):
        """
        发送微信订阅消息（带重试机制）
        
        Args:
            openid: 用户openid
            template_id: 模板ID
            page: 点击消息跳转的页面路径
            data: 模板数据（字典格式）
            retry_count: 重试次数
        
        Returns:
            dict: 发送结果
        """
        MAX_RETRY = 3
        RETRY_DELAY = 2
        
        access_token = WeChatPushService.get_access_token()
        if not access_token:
            return {'success': False, 'error': '获取access_token失败'}
        
        url = f"https://api.weixin.qq.com/cgi-bin/message/subscribe/send?access_token={access_token}"
        
        payload = {
            "touser": openid,
            "template_id": template_id,
            "page": page,
            "data": data
        }
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            result = response.json()
            
            errcode = result.get('errcode', 0)
            if errcode == 0:
                logger.info(f'订阅消息发送成功: openid={openid}, template_id={template_id}')
                return {'success': True, 'result': result}
            else:
                errmsg = result.get('errmsg', '未知错误')
                retryable_errors = [40001, 40014, 42001, 45011]
                
                # 45009: 频率限制（同一用户同一模板每天最多发送一次）
                # 这是微信订阅消息的限制，需要用户重新订阅才能再次发送
                if errcode == 45009:
                    logger.warning(f'订阅消息发送失败（频率限制）: errcode={errcode}, errmsg={errmsg}, openid={openid}')
                    return {'success': False, 'errcode': errcode, 'error': errmsg, 'need_resubscribe': True}
                
                if errcode in retryable_errors and retry_count < MAX_RETRY:
                    logger.warning(f'订阅消息发送失败，准备重试: errcode={errcode}, retry={retry_count+1}')
                    time.sleep(RETRY_DELAY)
                    cache.delete(WeChatPushService.ACCESS_TOKEN_CACHE_KEY)
                    return WeChatPushService.send_subscribe_message(
                        openid, template_id, page, data, retry_count + 1
                    )
                
                logger.warning(f'订阅消息发送失败: errcode={errcode}, errmsg={errmsg}, openid={openid}')
                return {'success': False, 'errcode': errcode, 'error': errmsg}
        except requests.RequestException as e:
            if retry_count < MAX_RETRY:
                logger.warning(f'订阅消息发送网络错误，准备重试: {e}, retry={retry_count+1}')
                time.sleep(RETRY_DELAY)
                return WeChatPushService.send_subscribe_message(
                    openid, template_id, page, data, retry_count + 1
                )
            
            logger.error(f'发送订阅消息异常: {e}, openid={openid}')
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def format_alert_message(alert, device, elderly, alert_type):
        """
        格式化警报消息为订阅消息数据格式
        
        Args:
            alert: Alert对象
            device: Device对象
            elderly: ElderlyProfile对象
            alert_type: 警报类型（用于确定使用哪个模板格式）
        
        Returns:
            dict: 订阅消息数据（根据不同模板返回不同格式）
        """
        # 格式化时间
        time_str = alert.created_at.strftime('%Y年%m月%d日 %H:%M')
        
        # 根据不同的警报类型，返回对应模板的数据格式
        if alert_type == 'sos':
            # SOS求救模板：thing1（老人姓名），time4（触发时间）
            return {
                "thing1": {"value": elderly.name[:20]},  # 老人姓名，最多20个字
                "time4": {"value": time_str},  # 触发时间
            }
        elif alert_type == 'fence_violation':
            # 围栏越界模板：time1（越界时间），thing2（越界地点）
            location_str = '未知位置'
            if alert.location:
                location_str = alert.location.address or f"{alert.location.latitude},{alert.location.longitude}"
            elif hasattr(elderly, 'address') and elderly.address:
                location_str = elderly.address
            
            return {
                "time1": {"value": time_str},  # 越界时间
                "thing2": {"value": location_str[:20]},  # 越界地点，最多20个字
            }
        elif alert_type in ['device_offline', 'low_battery']:
            # 设备状态异常通知模板：time1（时间），phrase2（异常状态）
            status_map = {
                'device_offline': '设备离线',
                'low_battery': '电量低'
            }
            status_text = status_map.get(alert_type, '状态异常')
            
            return {
                "time1": {"value": time_str},  # 时间
                "phrase2": {"value": status_text},  # 异常状态
            }
        else:
            # 其他类型，使用默认格式（兼容处理）
            location_str = '未知位置'
            if alert.location:
                location_str = alert.location.address or f"{alert.location.latitude},{alert.location.longitude}"
            elif hasattr(elderly, 'address') and elderly.address:
                location_str = elderly.address
            
            return {
                "time1": {"value": time_str},
                "phrase2": {"value": "状态异常"},
            }

