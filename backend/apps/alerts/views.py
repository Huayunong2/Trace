from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from apps.users.models import ElderlyProfile
from apps.devices.models import Device
from apps.locations.models import Location
from .models import Alert
from .serializers import AlertSerializer, AlertHandleSerializer


class AlertViewSet(viewsets.ModelViewSet):
    serializer_class = AlertSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        # 管理员角色：可以查看所有警告
        if user.role in ['community_admin', 'system_admin']:
            queryset = Alert.objects.select_related(
                'device', 'device__elderly', 'device__elderly__guardian',
                'location', 'handled_by'
            ).all()
        # 老人角色：查看与自己用户直接关联的设备报警
        elif user.role == 'elderly':
            devices = Device.objects.filter(elderly__user=user)
            queryset = Alert.objects.select_related(
                'device', 'device__elderly', 'device__elderly__guardian',
                'location', 'handled_by'
            ).filter(device__in=devices)
        else:
            # 监护人角色：查看自己管理的老人设备报警（guardian不为null且等于当前用户）
            elderly_profiles = ElderlyProfile.objects.filter(guardian=user)
            devices = Device.objects.filter(elderly__in=elderly_profiles)
            queryset = Alert.objects.select_related(
                'device', 'device__elderly', 'device__elderly__guardian',
                'location', 'handled_by'
            ).filter(device__in=devices)
        
        status_filter = self.request.query_params.get('status')
        alert_type = self.request.query_params.get('type')
        severity = self.request.query_params.get('severity')
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if alert_type:
            queryset = queryset.filter(alert_type=alert_type)
        if severity:
            queryset = queryset.filter(severity=severity)
        
        return queryset.order_by('-created_at')
    
    @action(detail=True, methods=['post'])
    def handle(self, request, pk=None):
        alert = self.get_object()
        serializer = AlertHandleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        alert.handle(request.user, serializer.validated_data.get('note', ''))
        return Response(AlertSerializer(alert).data)
    
    @action(detail=False, methods=['get'])
    def unhandled_count(self, request):
        """获取待处理警告数量"""
        count = self.get_queryset().filter(status='pending').count()
        return Response({'count': count})
    
    @action(detail=False, methods=['post'])
    def handle_all(self, request):
        """批量处理所有待处理的警告"""
        queryset = self.get_queryset().filter(status='pending')
        note = request.data.get('note', '批量处理')
        
        count = 0
        for alert in queryset:
            alert.handle(request.user, note)
            count += 1
        
        return Response({
            'success': True,
            'message': f'成功处理 {count} 个警告',
            'count': count
        })
    
    @action(detail=False, methods=['post'])
    def clear_handled(self, request):
        """清理所有已处理的警告"""
        queryset = self.get_queryset().filter(status='handled')
        count = queryset.count()
        queryset.delete()
        
        return Response({
            'message': f'成功清理 {count} 个已处理警告',
            'count': count
        })
    
    @action(detail=False, methods=['post'])
    def sos(self, request):
        device_id = request.data.get('device_id')
        if not device_id:
            return Response({'error': 'device_id参数必填'}, status=status.HTTP_400_BAD_REQUEST)
        
        user = request.user
        
        # 根据角色查找设备并验证权限
        try:
            device = Device.objects.get(device_id=device_id, is_active=True)
        except Device.DoesNotExist:
            return Response({'error': '设备不存在'}, status=status.HTTP_404_NOT_FOUND)
        
        # 确保设备已关联到老人档案
        if not device.elderly:
            return Response({'error': '设备未绑定到老人档案'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 验证权限：老人角色需要验证设备是否已绑定监护人，并且设备必须是当前用户创建的
        if user.role == 'elderly':
            # 检查设备是否是当前用户创建的
            # 优先检查 created_by 字段（如果数据库已迁移），否则检查 elderly.user
            is_owner = False
            try:
                # 尝试使用 created_by 字段判断（如果数据库已迁移）
                if hasattr(device, 'created_by') and device.created_by is not None:
                    is_owner = device.created_by == user
                else:
                    # 如果 created_by 为空或字段不存在，使用 elderly.user 判断
                    is_owner = device.elderly and device.elderly.user == user
            except (AttributeError, Exception):
                # 如果访问 created_by 字段出错（数据库字段可能不存在），使用 elderly.user 判断
                is_owner = device.elderly and device.elderly.user == user
            
            if not is_owner:
                return Response({'error': '设备不存在或无权限'}, status=status.HTTP_403_FORBIDDEN)
            
            # 检查设备的老人档案是否已绑定监护人（必须有监护人才能发送SOS）
            if not device.elderly or not device.elderly.guardian:
                return Response({'error': '设备尚未绑定监护人，请先让监护人绑定设备'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            # 监护人角色：验证设备是否绑定到自己管理的老人档案
            if not device.elderly:
                return Response({'error': '设备未关联到老人'}, status=status.HTTP_403_FORBIDDEN)
            elderly_profiles = ElderlyProfile.objects.filter(guardian=user)
            if not elderly_profiles.filter(id=device.elderly.id).exists():
                return Response({'error': '无权限访问该设备'}, status=status.HTTP_403_FORBIDDEN)
        
        try:
            location = Location.objects.filter(device=device).latest('recorded_at')
        except Location.DoesNotExist:
            location = None
        
        alert = Alert.objects.create(
            device=device,
            alert_type='sos',
            title='主动求救',
            message='老人主动触发SOS求救按钮',
            location=location,
            severity='critical',
            escalation_level=2,
        )
        
        # 发送推送通知
        try:
            from apps.fences.tasks import send_alert_notification
            send_alert_notification.delay(device.id, 'sos')
        except Exception as e:
            # Celery不可用时，使用同步方式发送
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f'Celery不可用，使用同步方式发送SOS通知: {e}')
            try:
                from apps.fences.tasks import _send_alert_notification_sync
                _send_alert_notification_sync(device.id, 'sos')
            except Exception as sync_err:
                logger.error(f'同步发送SOS通知失败: {sync_err}', exc_info=True)
        
        return Response(AlertSerializer(alert).data, status=status.HTTP_201_CREATED)

