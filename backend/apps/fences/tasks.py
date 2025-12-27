"""
围栏检查异步任务
"""
try:
    from celery import shared_task
    CELERY_AVAILABLE = True
except ImportError:
    CELERY_AVAILABLE = False
    # 定义一个假装饰器，避免导入错误
    def shared_task(func):
        return func

from apps.fences.utils import check_fence_violation_sync

# 导出同步函数，供其他模块直接调用
__all__ = ['send_alert_notification', '_send_alert_notification_sync', 'check_fence_violation']


@shared_task
def check_fence_violation(location_id):
    """
    异步检查围栏越界（复用同步函数）
    """
    check_fence_violation_sync(location_id)


def _send_alert_notification_sync(device_id, alert_type):
    """
    同步发送预警通知（微信订阅消息推送）- 内部函数，可被异步任务和同步调用复用
    """
    from apps.devices.models import Device
    from apps.alerts.models import Alert
    from apps.users.models import User, SubscribeMessage
    from apps.users.wechat_push import WeChatPushService
    from django.conf import settings
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        device = Device.objects.get(id=device_id)
        latest_alert = Alert.objects.filter(device=device, alert_type=alert_type).latest('created_at')
        
        # 获取监护人信息
        if not device.elderly or not device.elderly.guardian:
            logger.warning(f'设备 {device_id} 未关联老人或监护人，跳过推送')
            return
        
        guardian = device.elderly.guardian
        elderly = device.elderly
        
        # 检查监护人是否有openid
        if not guardian.openid:
            logger.warning(f'监护人 {guardian.username} 没有openid，无法推送')
            return
        
        # 获取对应的模板ID
        template_map = settings.WECHAT_SUBSCRIBE_TEMPLATES
        template_id = template_map.get(alert_type)
        
        if not template_id:
            logger.warning(f'警报类型 {alert_type} 未配置模板ID，跳过推送')
            return
        
        # 检查用户是否订阅了该模板（如果未订阅，也尝试发送，因为用户可能之前订阅过但记录丢失）
        subscribe_record = SubscribeMessage.objects.filter(
            user=guardian,
            template_id=template_id,
            subscribe_status=True
        ).first()
        
        if not subscribe_record:
            logger.info(f'监护人 {guardian.username} 未订阅模板 {template_id}，但尝试发送推送（用户可能已订阅但记录丢失）')
            # 继续执行，因为用户可能之前订阅过但记录丢失
        
        # 格式化消息数据（传入alert_type以使用正确的模板格式）
        message_data = WeChatPushService.format_alert_message(latest_alert, device, elderly, alert_type)
        
        # 确定跳转页面
        page = 'pages/alert/alert'  # 跳转到警报页面
        
        # 发送订阅消息
        result = WeChatPushService.send_subscribe_message(
            openid=guardian.openid,
            template_id=template_id,
            page=page,
            data=message_data
        )
        
        if result.get('success'):
            if not subscribe_record:
                SubscribeMessage.objects.update_or_create(
                    user=guardian,
                    template_id=template_id,
                    defaults={'subscribe_status': True}
                )
            logger.info(f'成功发送警报推送: 设备={device_id}, 类型={alert_type}, 监护人={guardian.username}, openid={guardian.openid[:10]}...')
        else:
            errcode = result.get('errcode')
            errmsg = result.get('error', '未知错误')
            
            if errcode in [43101, 43104]:
                SubscribeMessage.objects.update_or_create(
                    user=guardian,
                    template_id=template_id,
                    defaults={'subscribe_status': False}
                )
                logger.warning(f'用户 {guardian.username} 未订阅或拒绝接收消息 (errcode={errcode}, errmsg={errmsg})，请提醒用户重新订阅')
            else:
                logger.warning(f'发送警报推送失败: 设备={device_id}, 类型={alert_type}, 监护人={guardian.username}, errcode={errcode}, errmsg={errmsg}')
        
    except Device.DoesNotExist:
        logger.error(f'设备不存在: device_id={device_id}')
    except Alert.DoesNotExist:
        logger.error(f'警报不存在: device_id={device_id}, alert_type={alert_type}')
    except Exception as e:
        logger.error(f'发送通知异常: {e}', exc_info=True)


@shared_task
def send_alert_notification(device_id, alert_type):
    """
    发送预警通知（微信订阅消息推送）- 异步任务
    """
    _send_alert_notification_sync(device_id, alert_type)
