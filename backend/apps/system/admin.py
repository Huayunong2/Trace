"""
系统管理Admin配置
"""
from django.contrib import admin
from .models import SystemConfig


@admin.register(SystemConfig)
class SystemConfigAdmin(admin.ModelAdmin):
    list_display = ['key', 'value', 'value_type', 'is_public', 'description', 'updated_at']
    list_filter = ['value_type', 'is_public', 'created_at']
    search_fields = ['key', 'description']
    readonly_fields = ['created_at', 'updated_at']

