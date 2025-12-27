"""
系统管理模型
"""
from django.db import models
from django.utils import timezone


class SystemConfig(models.Model):
    """
    系统配置模型
    """
    key = models.CharField('配置键', max_length=100, unique=True)
    value = models.TextField('配置值')
    description = models.CharField('描述', max_length=200, blank=True)
    value_type = models.CharField('值类型', max_length=20, choices=[
        ('string', '字符串'),
        ('integer', '整数'),
        ('float', '浮点数'),
        ('boolean', '布尔值'),
        ('json', 'JSON'),
    ], default='string')
    is_public = models.BooleanField('是否公开', default=False)  # 是否允许普通用户查看
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        db_table = 'system_configs'
        verbose_name = '系统配置'
        verbose_name_plural = '系统配置'
        ordering = ['key']
    
    def __str__(self):
        return f"{self.key} = {self.value}"
    
    def get_typed_value(self):
        """获取类型转换后的值"""
        if self.value_type == 'integer':
            try:
                return int(self.value)
            except ValueError:
                return 0
        elif self.value_type == 'float':
            try:
                return float(self.value)
            except ValueError:
                return 0.0
        elif self.value_type == 'boolean':
            return self.value.lower() in ('true', '1', 'yes', 'on')
        elif self.value_type == 'json':
            import json
            try:
                return json.loads(self.value)
            except (json.JSONDecodeError, TypeError):
                return {}
        else:
            return self.value

