"""
预警模型
"""
from django.db import models
from django.utils import timezone
from apps.devices.models import Device
from apps.locations.models import Location


class Alert(models.Model):
    """
    预警模型
    """
    ALERT_TYPE_CHOICES = [
        ('fence_violation', '围栏越界'),
        ('device_offline', '设备离线'),
        ('low_battery', '低电量'),
        ('sos', '主动求救'),
        ('other', '其他'),
    ]
    
    SEVERITY_CHOICES = [
        ('low', '低'),
        ('medium', '中'),
        ('high', '高'),
        ('critical', '紧急'),
    ]
    
    STATUS_CHOICES = [
        ('pending', '待处理'),
        ('handled', '已处理'),
        ('ignored', '已忽略'),
    ]
    
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='alerts', verbose_name='设备')
    alert_type = models.CharField('预警类型', max_length=20, choices=ALERT_TYPE_CHOICES)
    title = models.CharField('标题', max_length=100)
    message = models.TextField('消息内容')
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, blank=True, related_name='alerts', verbose_name='位置')
    severity = models.CharField('严重程度', max_length=20, choices=SEVERITY_CHOICES, default='medium')
    status = models.CharField('状态', max_length=20, choices=STATUS_CHOICES, default='pending')
    is_handled = models.BooleanField('是否已处理', default=False)
    handled_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='handled_alerts', verbose_name='处理人')
    handled_at = models.DateTimeField('处理时间', null=True, blank=True)
    handled_note = models.TextField('处理备注', blank=True)
    escalation_level = models.IntegerField('升级级别', default=1)  # 1:监护人, 2:社区管理员
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        db_table = 'alerts'
        verbose_name = '预警'
        verbose_name_plural = '预警'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['device', '-created_at']),
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['alert_type', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.device.device_id}"
    
    def handle(self, user, note=''):
        """处理预警"""
        self.is_handled = True
        self.status = 'handled'
        self.handled_by = user
        self.handled_at = timezone.now()
        self.handled_note = note
        self.save()
    
    def escalate(self):
        """升级预警"""
        from django.conf import settings
        from datetime import timedelta
        
        # 如果超过升级时间仍未处理，自动升级
        if not self.is_handled:
            elapsed = (timezone.now() - self.created_at).total_seconds()
            if elapsed > settings.ALERT_ESCALATION_TIME:
                self.escalation_level = 2
                self.save()
                return True
        return False

