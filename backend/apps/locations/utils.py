"""
定位工具函数
"""
import requests
from django.conf import settings
from django.core.cache import cache


def reverse_geocode(latitude, longitude):
    """
    逆地理编码：将经纬度转换为地址
    使用高德地图API
    """
    if not settings.AMAP_KEY:
        return ''
    
    url = 'https://restapi.amap.com/v3/geocode/regeo'
    params = {
        'key': settings.AMAP_KEY,
        'location': f'{longitude},{latitude}',
        'output': 'json',
    }
    
    try:
        response = requests.get(url, params=params, timeout=5)
        data = response.json()
        
        if data.get('status') == '1' and data.get('regeocode'):
            return data['regeocode'].get('formatted_address', '')
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f'逆地理编码失败: {e}', exc_info=True)
    
    return ''


def calculate_distance(lat1, lon1, lat2, lon2):
    """
    计算两点之间的距离（米）
    使用Haversine公式
    """
    from math import radians, cos, sin, asin, sqrt
    
    # 将十进制度数转化为弧度
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    
    # Haversine公式
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    r = 6371000  # 地球平均半径，单位为米
    
    return c * r


def is_point_in_circle(point_lat, point_lon, center_lat, center_lon, radius):
    """
    判断点是否在圆形围栏内
    point_lat, point_lon: 点的经纬度
    center_lat, center_lon: 圆心经纬度
    radius: 半径（米）
    """
    distance = calculate_distance(point_lat, point_lon, center_lat, center_lon)
    return distance <= radius


def cache_location(device_id, location_data):
    """
    缓存位置数据到Redis
    """
    cache_key = f'device_location:{device_id}'
    cache.set(cache_key, location_data, timeout=300)  # 5分钟过期


def get_cached_location(device_id):
    """
    从Redis获取缓存的位置数据
    """
    cache_key = f'device_location:{device_id}'
    return cache.get(cache_key)

