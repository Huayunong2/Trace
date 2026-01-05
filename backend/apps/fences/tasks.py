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
        
        # 检查用户订阅状态（仅用于日志记录，不影响推送）
        subscribe_record = SubscribeMessage.objects.filter(
            user=guardian,
            template_id=template_id
        ).first()
        
        # 无论订阅状态如何，都尝试推送（因为微信订阅状态可能已更新，但数据库中记录未更新）
        # 这样即使订阅状态被误标记为False，也能继续尝试推送
        if subscribe_record and not subscribe_record.subscribe_status:
            logger.info(f'监护人 {guardian.username} 订阅状态为False，但仍尝试推送（可能已重新订阅）')
        elif not subscribe_record:
            logger.info(f'监护人 {guardian.username} 无订阅记录，尝试推送（用户可能已订阅但记录丢失）')
        
        # 格式化消息数据（传入alert_type以使用正确的模板格式）
        message_data = WeChatPushService.format_alert_message(latest_alert, device, elderly, alert_type)
        
        # 确定跳转页面
        page = 'pages/alert/alert'  # 跳转到警报页面
        
        # 发送订阅消息（无论订阅状态如何都尝试推送）
        result = WeChatPushService.send_subscribe_message(
            openid=guardian.openid,
            template_id=template_id,
            page=page,
            data=message_data
        )
        
        if result.get('success'):
            # 推送成功，更新订阅状态为True（无论之前状态如何）
            SubscribeMessage.objects.update_or_create(
                user=guardian,
                template_id=template_id,
                defaults={
                    'subscribe_status': True
                    # updated_at 字段使用 auto_now=True，Django会自动更新，无需手动设置
                }
            )
            logger.info(f'成功发送警报推送: 设备={device_id}, 类型={alert_type}, 监护人={guardian.username}, openid={guardian.openid[:10]}...')
        else:
            errcode = result.get('errcode')
            errmsg = result.get('error', '未知错误')
            need_resubscribe = result.get('need_resubscribe', False)
            
            # 45009: 频率限制（同一用户同一模板每天最多发送一次）
            # 这是微信订阅消息的限制，需要用户重新订阅才能再次发送
            if errcode == 45009 or need_resubscribe:
                logger.warning(f'用户 {guardian.username} 订阅消息频率限制 (errcode={errcode}, errmsg={errmsg})，需要重新订阅才能继续接收推送')
                # 不更新订阅状态，因为用户仍然订阅，只是需要重新授权
            # 只有在明确返回43101（用户未订阅）或43104（用户拒绝接收）时才标记为False
            elif errcode is not None and errcode in [43101, 43104]:
                # 用户明确未订阅或拒绝接收，标记为False
                SubscribeMessage.objects.update_or_create(
                    user=guardian,
                    template_id=template_id,
                    defaults={
                        'subscribe_status': False
                        # updated_at 字段使用 auto_now=True，Django会自动更新，无需手动设置
                    }
                )
                logger.warning(f'用户 {guardian.username} 未订阅或拒绝接收消息 (errcode={errcode}, errmsg={errmsg})，已标记为未订阅，请提醒用户重新订阅')
            else:
                # 其他错误（网络错误、token过期等）不更新订阅状态
                # 因为这些错误可能是临时的，订阅状态仍然有效
                logger.warning(f'发送警报推送失败（非订阅错误）: 设备={device_id}, 类型={alert_type}, 监护人={guardian.username}, errcode={errcode}, errmsg={errmsg}，订阅状态保持不变')
        
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
