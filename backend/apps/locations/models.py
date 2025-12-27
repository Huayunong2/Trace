"""
定位服务模型
"""
from django.db import models
from django.utils import timezone
from django.conf import settings
from apps.devices.models import Device


class Location(models.Model):
    """
    位置记录模型
    """
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='locations', verbose_name='设备')
    latitude = models.DecimalField('纬度', max_digits=10, decimal_places=7)
    longitude = models.DecimalField('经度', max_digits=10, decimal_places=7)
    address = models.CharField('地址', max_length=200, blank=True)
    accuracy = models.FloatField('精度（米）', null=True, blank=True)
    altitude = models.FloatField('海拔（米）', null=True, blank=True)
    speed = models.FloatField('速度（米/秒）', null=True, blank=True)
    heading = models.FloatField('方向角', null=True, blank=True)
    location_type = models.CharField('定位类型', max_length=20, choices=[
        ('gps', 'GPS'),
        ('lbs', '基站定位'),
        ('wifi', 'WiFi定位'),
    ], default='gps')
    recorded_at = models.DateTimeField('记录时间', default=timezone.now)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    
    class Meta:
        db_table = 'locations'
        verbose_name = '位置记录'
        verbose_name_plural = '位置记录'
        ordering = ['-recorded_at']
        indexes = [
            models.Index(fields=['device', '-recorded_at']),
            models.Index(fields=['-recorded_at']),
        ]
    
    def __str__(self):
        return f"{self.device.device_id} - {self.latitude}, {self.longitude} - {self.recorded_at}"
    
    def save(self, *args, **kwargs):
        # 自动获取地址（逆地理编码）
        if not self.address:
            self.address = self._reverse_geocode()
        super().save(*args, **kwargs)
    
    def _reverse_geocode(self):
        """逆地理编码：将经纬度转换为地址"""
        from .utils import reverse_geocode
        try:
            return reverse_geocode(float(self.latitude), float(self.longitude))
        except Exception:
            return ''


class LocationCache(models.Model):
    """
    位置缓存模型（Redis缓存，此模型用于记录缓存键）
    """
    device = models.OneToOneField(Device, on_delete=models.CASCADE, related_name='location_cache', verbose_name='设备')
    latitude = models.DecimalField('纬度', max_digits=10, decimal_places=7)
    longitude = models.DecimalField('经度', max_digits=10, decimal_places=7)
    address = models.CharField('地址', max_length=200, blank=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        db_table = 'location_cache'
        verbose_name = '位置缓存'
        verbose_name_plural = '位置缓存'

