"""
围栏检测工具函数（复用代码）
"""
from django.conf import settings
from apps.fences.models import Fence, FenceViolationLog
from apps.locations.models import Location
from apps.alerts.models import Alert


def check_fence_violation_sync(location_id):
    """
    同步检查围栏越界（公共函数，可被异步任务和同步调用复用）
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        location = Location.objects.get(id=location_id)
        device = location.device
        
        if not device:
            logger.warning(f'位置记录 {location_id} 没有关联设备，跳过围栏检查')
            return
        
        # 获取设备的所有激活围栏
        fences = Fence.objects.filter(device=device, is_active=True)
        
        if not fences.exists():
            logger.debug(f'设备 {device.device_id} 没有激活的围栏，跳过检查')
            return
        
        logger.info(f'开始检查设备 {device.device_id} 的位置 {location.latitude},{location.longitude}，共有 {fences.count()} 个围栏')
        
        for fence in fences:
            is_violation, distance = fence.check_violation(
                location.latitude,
                location.longitude
            )
            
            logger.info(f'围栏 {fence.name} (中心: {fence.center_latitude},{fence.center_longitude}, 半径: {fence.radius}米): 距离={distance:.2f}米, 越界={is_violation}')
            
            # 记录越界日志
            violation_log = FenceViolationLog.objects.create(
                fence=fence,
                location=location,
                is_violation=is_violation,
                distance=distance,
            )
            
            if is_violation:
                # 越界处理
                fence.violation_count += 1
                fence.last_violation_time = location.recorded_at
                fence.save()
                
                logger.info(f'围栏 {fence.name} 越界，当前连续越界次数: {fence.violation_count}')
                
                # 如果连续越界次数达到阈值，触发报警（首次越界即报警）
                if fence.violation_count >= getattr(settings, 'FENCE_VIOLATION_THRESHOLD', 1):
                    # 创建预警（发送给监护人）
                    alert = Alert.objects.create(
                        device=device,
                        alert_type='fence_violation',
                        title='围栏越界预警',
                        message=f'老人已离开围栏"{fence.name}"范围，距离围栏中心{distance:.0f}米',
                        location=location,
                        severity='high',
                        is_handled=False,
                    )
                    
                    logger.info(f'创建围栏越界警报 {alert.id}: {alert.message}')
                    
                    # 尝试异步发送通知（如果Celery可用），否则同步执行
                    try:
                        from apps.fences.tasks import send_alert_notification
                        send_alert_notification.delay(device.id, 'fence_violation')
                        logger.info(f'已发送围栏越界通知任务（异步）')
                    except Exception as e:
                        logger.warning(f'Celery不可用，使用同步方式发送通知: {e}')
                        try:
                            from apps.fences.tasks import _send_alert_notification_sync
                            _send_alert_notification_sync(device.id, 'fence_violation')
                            logger.info(f'已发送围栏越界通知（同步）')
                        except Exception as sync_err:
                            logger.error(f'同步发送通知失败: {sync_err}', exc_info=True)
            else:
                # 回到围栏内，重置计数
                if fence.violation_count > 0:
                    logger.info(f'围栏 {fence.name} 回到范围内，重置越界计数')
                    fence.violation_count = 0
                    fence.save()
                    
                    violation_log.violation_count = 0
                    violation_log.save()
    
    except Location.DoesNotExist:
        logger.error(f'位置记录 {location_id} 不存在')
    except Exception as e:
        # 记录错误但不抛出异常，避免影响位置上传
        logger.error(f'围栏检查失败: {e}', exc_info=True)

