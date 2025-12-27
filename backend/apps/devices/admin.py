"""
设备管理后台
"""
from django.contrib import admin
from .models import Device


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ['device_id', 'name', 'elderly', 'status', 'battery_level', 'last_online_time', 'is_active']
    list_filter = ['status', 'device_type', 'is_active', 'created_at']
    search_fields = ['device_id', 'name', 'qr_code']

