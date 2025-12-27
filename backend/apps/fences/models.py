"""
电子围栏模型
"""
from django.db import models
from django.utils import timezone
from apps.devices.models import Device


class Fence(models.Model):
    """
    电子围栏模型（圆形围栏）
    """
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='fences', verbose_name='设备')
    name = models.CharField('围栏名称', max_length=50)
    center_latitude = models.DecimalField('中心纬度', max_digits=10, decimal_places=7)
    center_longitude = models.DecimalField('中心经度', max_digits=10, decimal_places=7)
    radius = models.IntegerField('半径（米）', default=500)
    address = models.CharField('围栏地址', max_length=200, blank=True)
    is_active = models.BooleanField('是否启用', default=True)
    violation_count = models.IntegerField('越界次数', default=0)  # 连续越界计数
    last_violation_time = models.DateTimeField('最后越界时间', null=True, blank=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        db_table = 'fences'
        verbose_name = '电子围栏'
        verbose_name_plural = '电子围栏'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.device.device_id}"
    
    def check_violation(self, latitude, longitude):
        """
        检查是否越界
        返回: (is_violation, distance)
        """
        from apps.locations.utils import is_point_in_circle, calculate_distance
        
        distance = calculate_distance(
            float(latitude), float(longitude),
            float(self.center_latitude), float(self.center_longitude)
        )
        
        is_violation = not is_point_in_circle(
            float(latitude), float(longitude),
            float(self.center_latitude), float(self.center_longitude),
            self.radius
        )
        
        return is_violation, distance


class FenceViolationLog(models.Model):
    """
    围栏越界日志
    """
    fence = models.ForeignKey(Fence, on_delete=models.CASCADE, related_name='violation_logs', verbose_name='围栏')
    location = models.ForeignKey('locations.Location', on_delete=models.CASCADE, related_name='fence_violations', verbose_name='位置')
    is_violation = models.BooleanField('是否越界', default=True)
    distance = models.FloatField('距离（米）', null=True, blank=True)
    violation_count = models.IntegerField('连续越界次数', default=1)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    
    class Meta:
        db_table = 'fence_violation_logs'
        verbose_name = '围栏越界日志'
        verbose_name_plural = '围栏越界日志'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['fence', '-created_at']),
        ]

