"""
预警相关异步任务
"""
import logging
from celery import shared_task
from django.conf import settings
from apps.alerts.models import Alert
from apps.devices.models import Device

logger = logging.getLogger(__name__)


@shared_task
def check_device_status():
    """
    定期检查设备状态（离线、低电量等）
    """
    from django.utils import timezone
    from datetime import timedelta
    
    devices = Device.objects.filter(is_active=True)
    now = timezone.now()
    
    for device in devices:
        # 检查离线状态
        if device.last_online_time:
            offline_seconds = (now - device.last_online_time).total_seconds()
            if offline_seconds > settings.DEVICE_OFFLINE_THRESHOLD:
                # 检查是否已有未处理的离线预警
                existing_alert = Alert.objects.filter(
                    device=device,
                    alert_type='device_offline',
                    is_handled=False
                ).first()
                
                if not existing_alert:
                    alert = Alert.objects.create(
                        device=device,
                        alert_type='device_offline',
                        title='设备离线预警',
                        message=f'设备已离线超过{int(offline_seconds/60)}分钟',
                        severity='high',
                        is_handled=False,
                    )
                    # 发送通知
                    try:
                        from apps.fences.tasks import send_alert_notification
                        send_alert_notification.delay(device.id, 'device_offline')
                    except Exception as e:
                        # Celery不可用时，使用同步方式发送
                        logger.warning(f'Celery不可用，使用同步方式发送离线通知: {e}')
                        try:
                            from apps.fences.tasks import _send_alert_notification_sync
                            _send_alert_notification_sync(device.id, 'device_offline')
                        except Exception as sync_err:
                            logger.error(f'同步发送离线通知失败: {sync_err}', exc_info=True)
        
        # 检查低电量（只检查在线设备且有电量信息）
        # 设备状态为online或low_battery时才检查，离线设备不检查低电量
        if (device.battery_level is not None and 
            device.status in ['online', 'low_battery'] and 
            device.battery_level < settings.DEVICE_LOW_BATTERY_THRESHOLD):
            # 检查是否已有未处理的低电量预警
            existing_alert = Alert.objects.filter(
                device=device,
                alert_type='low_battery',
                is_handled=False
            ).first()
            
            if not existing_alert:
                alert = Alert.objects.create(
                    device=device,
                    alert_type='low_battery',
                    title='设备低电量预警',
                    message=f'设备电量仅剩{device.battery_level}%',
                    severity='medium',
                    is_handled=False,
                )
                # 发送通知
                try:
                    from apps.fences.tasks import send_alert_notification
                    send_alert_notification.delay(device.id, 'low_battery')
                except Exception as e:
                    # Celery不可用时，使用同步方式发送
                    logger.warning(f'Celery不可用，使用同步方式发送低电量通知: {e}')
                    try:
                        from apps.fences.tasks import _send_alert_notification_sync
                        _send_alert_notification_sync(device.id, 'low_battery')
                    except Exception as sync_err:
                        logger.error(f'同步发送低电量通知失败: {sync_err}', exc_info=True)


@shared_task
def escalate_alerts():
    """
    升级未处理的预警
    """
    from django.utils import timezone
    
    unhandled_alerts = Alert.objects.filter(is_handled=False)
    
    for alert in unhandled_alerts:
        alert.escalate()

