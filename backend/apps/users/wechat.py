"""
微信API工具
"""
import requests
from django.conf import settings
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)


def get_wechat_openid_and_session_key(code):
    """
    调用微信API获取openid和session_key
    
    Args:
        code: 微信小程序wx.login()获取的code
        
    Returns:
        tuple: (openid, session_key) 或 (None, None) 如果失败
    """
    appid = settings.WECHAT_APPID
    secret = settings.WECHAT_SECRET
    
    if not appid or not secret:
        logger.error('微信AppID或Secret未配置')
        return None, None
    
    url = 'https://api.weixin.qq.com/sns/jscode2session'
    params = {
        'appid': appid,
        'secret': secret,
        'js_code': code,
        'grant_type': 'authorization_code'
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if 'errcode' in data:
            logger.error(f'微信API错误: {data.get("errcode")} - {data.get("errmsg")}')
            return None, None
        
        openid = data.get('openid')
        session_key = data.get('session_key')
        
        if openid and session_key:
            # 缓存session_key（微信建议缓存，不要频繁请求）
            # session_key有效期较长，可以缓存一段时间
            cache_key = f'wechat_session_key_{openid}'
            cache.set(cache_key, session_key, timeout=7200)  # 缓存2小时
            
            return openid, session_key
        else:
            logger.error(f'微信API返回数据异常: {data}')
            return None, None
            
    except requests.RequestException as e:
        logger.error(f'请求微信API失败: {e}')
        return None, None
    except Exception as e:
        logger.error(f'获取微信openid失败: {e}')
        return None, None


def get_cached_session_key(openid):
    """获取缓存的session_key"""
    cache_key = f'wechat_session_key_{openid}'
    return cache.get(cache_key)

