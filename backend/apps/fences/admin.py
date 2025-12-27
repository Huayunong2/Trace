"""
围栏管理后台 - 增强版，带地图选点
"""
from django.contrib import admin
from django.utils.html import format_html
from django import forms
from django.conf import settings
from .models import Fence, FenceViolationLog


class FenceAdminForm(forms.ModelForm):
    """围栏表单，带地图选点"""
    
    class Meta:
        model = Fence
        fields = '__all__'
        widgets = {
            'center_latitude': forms.NumberInput(attrs={
                'class': 'vTextField',
                'step': '0.0000001',
                'id': 'id_center_latitude'
            }),
            'center_longitude': forms.NumberInput(attrs={
                'class': 'vTextField',
                'step': '0.0000001',
                'id': 'id_center_longitude'
            }),
            'radius': forms.NumberInput(attrs={
                'class': 'vTextField',
                'id': 'id_radius'
            }),
        }


@admin.register(Fence)
class FenceAdmin(admin.ModelAdmin):
    form = FenceAdminForm
    list_display = ['id', 'name', 'device_link', 'center_latitude', 'center_longitude', 'radius', 'is_active', 'map_preview']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'device__device_id']
    readonly_fields = ['violation_count', 'last_violation_time', 'created_at', 'updated_at', 'map_picker']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('device', 'name', 'is_active')
        }),
        ('围栏设置', {
            'fields': ('map_picker', 'center_latitude', 'center_longitude', 'radius', 'address')
        }),
        ('统计信息', {
            'fields': ('violation_count', 'last_violation_time'),
            'classes': ('collapse',)
        }),
        ('时间信息', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    class Media:
        css = {
            'all': ('admin/css/fence_admin.css',)
        }
        js = (
            f'https://webapi.amap.com/maps?v=2.0&key={settings.AMAP_KEY or "YOUR_AMAP_KEY"}',
            'admin/js/fence_admin.js',
        )
    
    def device_link(self, obj):
        if obj.device and obj.device.elderly:
            return format_html(
                '<a href="/admin/devices/device/{}/change/">{}</a>',
                obj.device.id,
                obj.device.elderly.name
            )
        return '-'
    device_link.short_description = '关联老人'
    
    def map_preview(self, obj):
        """地图预览"""
        if obj.center_latitude and obj.center_longitude:
            return format_html(
                '''
                <div id="fence_map_preview_{}" style="width:100%; height:300px; margin:10px 0;"></div>
                <script>
                    (function() {{
                        var map = new AMap.Map('fence_map_preview_{}', {{
                            zoom: 15,
                            center: [{}, {}]
                        }});
                        var circle = new AMap.Circle({{
                            center: [{}, {}],
                            radius: {},
                            fillColor: '#4A90E2',
                            fillOpacity: 0.3,
                            strokeColor: '#4A90E2',
                            strokeWeight: 2
                        }});
                        map.add(circle);
                        var marker = new AMap.Marker({{
                            position: [{}, {}],
                            title: '围栏中心'
                        }});
                        map.add(marker);
                    }})();
                </script>
                ''',
                obj.id, obj.id, obj.center_longitude, obj.center_latitude,
                obj.center_longitude, obj.center_latitude, obj.radius,
                obj.center_longitude, obj.center_latitude
            )
        return '请先设置围栏中心位置'
    map_preview.short_description = '围栏预览'
    map_preview.allow_tags = True
    
    def map_picker(self, obj):
        """地图选点器"""
        return format_html(
            '''
            <div style="margin: 20px 0;">
                <p><strong>在地图上点击选择围栏中心位置：</strong></p>
                <div id="fence_map_picker" style="width:100%; height:400px; border:1px solid #ddd; margin:10px 0;"></div>
                <p style="color: #666; font-size: 12px;">提示：点击地图设置中心点，拖动滑块调整半径</p>
            </div>
            <script>
                (function() {{
                    var map = new AMap.Map('fence_map_picker', {{
                        zoom: 13,
                        center: [116.397470, 39.908823]
                    }});
                    
                    var marker = new AMap.Marker({{
                        draggable: true,
                        cursor: 'move'
                    }});
                    
                    var circle = new AMap.Circle({{
                        fillColor: '#4A90E2',
                        fillOpacity: 0.3,
                        strokeColor: '#4A90E2',
                        strokeWeight: 2
                    }});
                    
                    var radius = document.getElementById('id_radius').value || 500;
                    var latInput = document.getElementById('id_center_latitude');
                    var lngInput = document.getElementById('id_center_longitude');
                    var radiusInput = document.getElementById('id_radius');
                    
                    // 如果有初始值，设置地图中心
                    if (latInput.value && lngInput.value) {{
                        var center = [parseFloat(lngInput.value), parseFloat(latInput.value)];
                        map.setCenter(center);
                        marker.setPosition(center);
                        circle.setCenter(center);
                        circle.setRadius(parseInt(radius));
                        map.add(marker);
                        map.add(circle);
                    }}
                    
                    // 地图点击事件
                    map.on('click', function(e) {{
                        var lng = e.lnglat.getLng();
                        var lat = e.lnglat.getLat();
                        latInput.value = lat;
                        lngInput.value = lng;
                        marker.setPosition([lng, lat]);
                        circle.setCenter([lng, lat]);
                        if (!marker.getMap()) {{
                            map.add(marker);
                            map.add(circle);
                        }}
                        
                        // 逆地理编码获取地址
                        AMap.plugin('AMap.Geocoder', function() {{
                            var geocoder = new AMap.Geocoder();
                            geocoder.getAddress([lng, lat], function(status, result) {{
                                if (status === 'complete' && result.info === 'OK') {{
                                    var addressInput = document.querySelector('[name="address"]');
                                    if (addressInput) {{
                                        addressInput.value = result.regeocode.formattedAddress;
                                    }}
                                }}
                            }});
                        }});
                    }});
                    
                    // 标记拖拽事件
                    marker.on('dragend', function(e) {{
                        var lng = e.lnglat.getLng();
                        var lat = e.lnglat.getLat();
                        latInput.value = lat;
                        lngInput.value = lng;
                        circle.setCenter([lng, lat]);
                    }});
                    
                    // 半径变化事件
                    radiusInput.addEventListener('input', function() {{
                        var newRadius = parseInt(this.value) || 500;
                        circle.setRadius(newRadius);
                    }});
                }})();
            </script>
            '''
        )
    map_picker.short_description = '地图选点'
    map_picker.allow_tags = True


@admin.register(FenceViolationLog)
class FenceViolationLogAdmin(admin.ModelAdmin):
    list_display = ['id', 'fence', 'is_violation', 'distance', 'violation_count', 'created_at']
    list_filter = ['is_violation', 'created_at']
    readonly_fields = ['created_at']
