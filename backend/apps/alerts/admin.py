"""
预警管理后台
"""
from django.contrib import admin
from .models import Alert


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'device', 'alert_type', 'severity', 'status', 'escalation_level', 'created_at']
    list_filter = ['alert_type', 'severity', 'status', 'escalation_level', 'created_at']
    search_fields = ['title', 'message', 'device__device_id']
    readonly_fields = ['created_at', 'updated_at']

