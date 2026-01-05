from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.utils import timezone
from datetime import timedelta
from apps.users.models import ElderlyProfile
from apps.devices.models import Device
from .models import Location
from .serializers import LocationSerializer, LocationCreateSerializer
from .utils import get_cached_location


class LocationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = LocationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        # 如果是老人角色，查看与自己用户直接关联的设备位置
        if user.role == 'elderly':
            devices = Device.objects.filter(elderly__user=user)
        else:
            # 监护人角色：查看自己管理的老人设备位置
            elderly_profiles = ElderlyProfile.objects.filter(guardian=user)
            devices = Device.objects.filter(elderly__in=elderly_profiles)
        
        # 使用select_related优化查询，减少N+1问题
        queryset = Location.objects.select_related(
            'device', 'device__elderly', 'device__elderly__guardian'
        ).filter(device__in=devices)
        
        days = self.request.query_params.get('days')
        if days:
            try:
                start_date = timezone.now() - timedelta(days=int(days))
                queryset = queryset.filter(recorded_at__gte=start_date)
            except ValueError:
                pass
        
        device_id = self.request.query_params.get('device_id')
        if device_id:
            queryset = queryset.filter(device__device_id=device_id)
        
        return queryset.order_by('-recorded_at')
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def upload(self, request):
        serializer = LocationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        location = serializer.save()
        
        # 更新设备状态：设备上传位置时，标记为在线
        if location.device:
            from django.utils import timezone
            from django.conf import settings
            from apps.alerts.models import Alert
            
            location.device.last_online_time = timezone.now()
            location.device.last_location_time = timezone.now()
            
            # 根据电量决定设备状态
            low_battery_threshold = getattr(settings, 'DEVICE_LOW_BATTERY_THRESHOLD', 20)
            
            if location.device.battery_level is not None:
                if location.device.battery_level < low_battery_threshold:
                    # 电量低于阈值，设置为低电量状态
                    location.device.status = 'low_battery'
                    
                    # 检查是否已有未处理的低电量预警
                    existing_alert = Alert.objects.filter(
                        device=location.device,
                        alert_type='low_battery',
                        is_handled=False
                    ).first()
                    
                    # 如果没有未处理的低电量警报，创建新的警报
                    if not existing_alert:
                        alert = Alert.objects.create(
                            device=location.device,
                            alert_type='low_battery',
                            title='设备低电量预警',
                            message=f'设备电量仅剩{location.device.battery_level}%',
                            severity='medium',
                            is_handled=False,
                        )
                        
                        # 发送推送通知
                        try:
                            from apps.fences.tasks import send_alert_notification
                            send_alert_notification.delay(location.device.id, 'low_battery')
                        except Exception as e:
                            # Celery不可用时，使用同步方式发送
                            import logging
                            logger = logging.getLogger(__name__)
                            logger.warning(f'Celery不可用，使用同步方式发送低电量通知: {e}')
                            try:
                                from apps.fences.tasks import _send_alert_notification_sync
                                _send_alert_notification_sync(location.device.id, 'low_battery')
                            except Exception as sync_err:
                                logger.error(f'同步发送低电量通知失败: {sync_err}', exc_info=True)
                else:
                    # 电量正常，设置为在线状态
                    if location.device.status == 'low_battery':
                        # 如果之前是低电量状态，现在电量恢复了，更新状态为在线
                        location.device.status = 'online'
            else:
                # 没有电量信息，默认设置为在线
                location.device.status = 'online'
            
            location.device.save()
        
        # 检查围栏越界（优先使用异步，否则同步执行）
        if location.device:
            try:
                from apps.fences.tasks import check_fence_violation
                check_fence_violation.delay(location.id)
            except Exception:
                # Celery不可用时，同步执行
                try:
                    from apps.fences.utils import check_fence_violation_sync
                    check_fence_violation_sync(location.id)
                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f'围栏检查失败: {e}', exc_info=True)
        
        return Response(LocationSerializer(location).data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['get'])
    def latest(self, request):
        from .utils import reverse_geocode, cache_location, get_cached_location
        from .serializers import LocationSerializer
        
        device_id = request.query_params.get('device_id')
        if not device_id:
            return Response({'error': 'device_id参数必填'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 优先从数据库获取
        try:
            device = Device.objects.get(device_id=device_id)
            location = Location.objects.filter(device=device).latest('recorded_at')
            
            # 如果地址为空，触发反向地理编码
            if not location.address or location.address.strip() == '':
                address = reverse_geocode(float(location.latitude), float(location.longitude))
                if address:
                    location.address = address
                    location.save(update_fields=['address'])
                    location.refresh_from_db()
                
                # 更新缓存（无论是否成功）
                cache_location(device_id, {
                    'latitude': float(location.latitude),
                    'longitude': float(location.longitude),
                    'address': location.address or '',
                    'recorded_at': location.recorded_at.isoformat() if hasattr(location.recorded_at, 'isoformat') else str(location.recorded_at),
                })
            
            return Response(LocationSerializer(location).data)
            
        except (Device.DoesNotExist, Location.DoesNotExist):
            # 如果数据库中没有，尝试从缓存获取
            cached_location = get_cached_location(device_id)
            if cached_location:
                # 确保address字段存在
                if 'address' not in cached_location:
                    cached_location['address'] = ''
                
                # 如果缓存中地址为空，尝试反向地理编码
                if not cached_location.get('address') or cached_location.get('address', '').strip() == '':
                    if cached_location.get('latitude') and cached_location.get('longitude'):
                        address = reverse_geocode(
                            float(cached_location['latitude']), 
                            float(cached_location['longitude'])
                        )
                        if address:
                            cached_location['address'] = address
                            # 更新缓存
                            cache_location(device_id, cached_location)
                        else:
                            cached_location['address'] = ''
                
                return Response(cached_location)
            
            return Response({'error': '未找到位置信息'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=False, methods=['get'])
    def track(self, request):
        device_id = request.query_params.get('device_id')
        if not device_id:
            return Response({'error': 'device_id参数必填'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            device = Device.objects.get(device_id=device_id)
        except Device.DoesNotExist:
            return Response({'error': '设备不存在'}, status=status.HTTP_404_NOT_FOUND)
        
        queryset = Location.objects.filter(device=device)
        start_time = request.query_params.get('start_time')
        end_time = request.query_params.get('end_time')
        
        if start_time:
            queryset = queryset.filter(recorded_at__gte=start_time)
        if end_time:
            queryset = queryset.filter(recorded_at__lte=end_time)
        
        locations = queryset.order_by('recorded_at')
        return Response({
            'device_id': device_id,
            'count': locations.count(),
            'locations': LocationSerializer(locations, many=True).data
        })

