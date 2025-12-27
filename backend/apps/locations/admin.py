"""
定位管理后台 - 增强版，带地图可视化
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import path
from django.shortcuts import render
from django.http import JsonResponse
from .models import Location, LocationCache
from apps.devices.models import Device
from apps.users.models import ElderlyProfile


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ['id', 'device_link', 'latitude', 'longitude', 'address', 'recorded_at', 'map_link']
    list_filter = ['location_type', 'recorded_at']
    search_fields = ['device__device_id', 'address']
    readonly_fields = ['created_at']
    # date_hierarchy = 'recorded_at'  # 暂时禁用，避免时区问题
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('map-view/', self.admin_site.admin_view(self.map_view), name='locations_location_map'),
        ]
        return custom_urls + urls
    
    def map_view(self, request):
        """地图视图"""
        # 获取所有有位置信息的设备
        devices = Device.objects.filter(is_active=True).select_related('elderly')
        locations_data = []
        
        for device in devices:
            latest_location = Location.objects.filter(device=device).order_by('-recorded_at').first()
            if latest_location and latest_location.latitude and latest_location.longitude:
                locations_data.append({
                    'id': device.id,
                    'name': device.elderly.name if device.elderly else device.name,
                    'latitude': float(latest_location.latitude),
                    'longitude': float(latest_location.longitude),
                    'address': latest_location.address,
                    'status': device.status,
                    'battery': device.battery_level,
                    'time': latest_location.recorded_at.strftime('%Y-%m-%d %H:%M:%S'),
                })
        
        context = {
            'locations': locations_data,
            'amap_key': settings.AMAP_KEY or 'YOUR_AMAP_KEY',
            'opts': self.model._meta,
            'has_view_permission': True,
        }
        return render(request, 'admin/locations/map_view.html', context)
    
    def device_link(self, obj):
        if obj.device and obj.device.elderly:
            return format_html(
                '<a href="/admin/devices/device/{}/change/">{}</a>',
                obj.device.id,
                obj.device.elderly.name
            )
        return '-'
    device_link.short_description = '关联老人'
    
    def map_link(self, obj):
        if obj.latitude and obj.longitude:
            return format_html(
                '<a href="https://uri.amap.com/marker?position={},{}" target="_blank">查看地图</a>',
                obj.longitude,
                obj.latitude
            )
        return '-'
    map_link.short_description = '地图'
    


@admin.register(LocationCache)
class LocationCacheAdmin(admin.ModelAdmin):
    list_display = ['device', 'latitude', 'longitude', 'address', 'updated_at']
    readonly_fields = ['updated_at']


# 自定义管理视图 - 地图可视化
class LocationMapAdmin(admin.ModelAdmin):
    """地图可视化管理页面"""
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('map-view/', self.admin_site.admin_view(self.map_view), name='locations_location_map'),
        ]
        return custom_urls + urls
    
    def map_view(self, request):
        """地图视图"""
        # 获取所有有位置信息的设备
        devices = Device.objects.filter(is_active=True).select_related('elderly')
        locations_data = []
        
        for device in devices:
            latest_location = Location.objects.filter(device=device).order_by('-recorded_at').first()
            if latest_location and latest_location.latitude and latest_location.longitude:
                locations_data.append({
                    'id': device.id,
                    'name': device.elderly.name if device.elderly else device.name,
                    'latitude': float(latest_location.latitude),
                    'longitude': float(latest_location.longitude),
                    'address': latest_location.address,
                    'status': device.status,
                    'battery': device.battery_level,
                    'time': latest_location.recorded_at.strftime('%Y-%m-%d %H:%M:%S'),
                })
        
        context = {
            'locations': locations_data,
            'amap_key': 'YOUR_AMAP_KEY',  # 需要替换为实际的key
        }
        return render(request, 'admin/locations/map_view.html', context)
