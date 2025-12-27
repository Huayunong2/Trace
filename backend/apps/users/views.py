from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.conf import settings
from .models import User, ElderlyProfile, SubscribeMessage
from .serializers import UserSerializer, ElderlyProfileSerializer, LoginSerializer, SubscribeMessageSerializer
from .authentication import generate_jwt_token
from .wechat import get_wechat_openid_and_session_key


class UserViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """根据用户角色返回不同的用户列表"""
        user = self.request.user
        
        # 系统管理员：可以查看所有用户
        if user.role == 'system_admin':
            return User.objects.all()
        # 社区管理员：可以查看监护人、老人和管理员用户
        elif user.role == 'community_admin':
            return User.objects.filter(role__in=['guardian', 'elderly', 'community_admin', 'system_admin'])
        else:
            # 其他角色：只能查看自己的信息
            return User.objects.filter(id=user.id)
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def login(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        code = serializer.validated_data.get('code')
        selected_role = serializer.validated_data.get('role', 'guardian')  # 默认监护人
        avatar_url = request.data.get('avatar_url', '')  # 头像URL（从登录表单获取）
        nickname = request.data.get('nickname', '')  # 昵称（从登录表单获取）
        
        openid, session_key = get_wechat_openid_and_session_key(code)
        
        if not openid:
            if settings.DEBUG and code and code.lower().startswith('test'):
                openid = 'mock_test123'
            else:
                return Response({'error': '微信登录失败'}, status=status.HTTP_401_UNAUTHORIZED)
        
        user, created = User.objects.get_or_create(
            openid=openid,
            defaults={
                'username': nickname if nickname else (f'user_{openid[-6:]}' if openid.startswith('mock_') else f'wx_{openid[-8:]}'),
                'is_active': True,
                'role': selected_role  # 设置选择的角色
            }
        )
        if created:
            user.set_unusable_password()
        
        # 处理已存在用户的角色切换逻辑（必须在更新昵称之前验证）
        is_super_admin = False
        role_updated = False
        
        if not created:
            # 超级管理员账号：允许切换角色（用于测试）
            # 通过环境变量配置超级管理员的openid列表
            super_admin_openids = settings.SUPER_ADMIN_OPENIDS if hasattr(settings, 'SUPER_ADMIN_OPENIDS') else []
            
            # 判断是否为超级管理员（允许切换角色）：
            # 1. 开发环境下：所有用户都可以切换角色（方便测试）
            # 2. 生产环境：需要在配置的超级管理员列表中
            # 3. openid包含test/admin/mock关键词（开发/测试账号）
            # 4. 用户名包含test/admin/system关键词或角色为system_admin
            is_super_admin = (
                settings.DEBUG or  # 开发环境：所有用户都可以切换角色（仅用于开发测试）
                openid in super_admin_openids or  # 生产环境：需要在配置列表中
                (openid and (
                    openid.startswith('mock_') or 
                    'test' in openid.lower() or
                    'admin' in openid.lower()
                )) or
                (user.username and (
                    'test' in user.username.lower() or
                    'admin' in user.username.lower() or
                    'system' in user.username.lower() or
                    user.role == 'system_admin'  # 系统管理员角色也可以切换
                ))
            )
            
            # 如果用户已存在且不是超级管理员，必须验证角色是否匹配（严格隔离）
            if user.role != selected_role and not is_super_admin:
                role_display_map = dict(User.ROLE_CHOICES)
                current_role_display = role_display_map.get(user.role, user.role)
                selected_role_display = role_display_map.get(selected_role, selected_role)
                return Response({
                    'error': f'身份验证失败：您的账号已注册为{current_role_display}，不能使用{selected_role_display}身份登录。如需切换身份，请联系系统管理员。'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # 超级管理员可以切换角色（更新角色）
            if is_super_admin and user.role != selected_role:
                user.role = selected_role
                role_updated = True
        
        # 更新用户信息（昵称）- 角色验证通过后统一更新
        # 无论是新用户还是已存在用户，只要提供了新昵称就更新
        nickname_updated = False
        if nickname and nickname.strip() and user.username != nickname.strip():
            user.username = nickname.strip()
            nickname_updated = True
        
        # 如果用户信息有变更，统一保存一次
        if nickname_updated or role_updated:
            user.save()
        
        return Response({
            'token': generate_jwt_token(user),
            'user': UserSerializer(user).data
        })
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        return Response(UserSerializer(request.user).data)


class SubscribeMessageViewSet(viewsets.ModelViewSet):
    """订阅消息管理"""
    from .serializers import SubscribeMessageSerializer
    serializer_class = SubscribeMessageSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return SubscribeMessage.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def template_ids(self, request):
        """获取订阅消息模板ID列表"""
        from django.conf import settings
        
        template_map = settings.WECHAT_SUBSCRIBE_TEMPLATES
        templates = {
            alert_type: template_id 
            for alert_type, template_id in template_map.items() 
            if template_id
        }
        
        return Response({
            'templates': templates,
            'alert_types': {
                'fence_violation': '围栏越界',
                'device_offline': '设备离线',
                'low_battery': '低电量',
                'sos': '紧急求救'
            }
        })
    
    @action(detail=False, methods=['post'])
    def subscribe(self, request):
        """订阅消息（接收前端传来的订阅结果）"""
        from .models import SubscribeMessage
        import logging
        
        logger = logging.getLogger(__name__)
        
        try:
            template_id = request.data.get('template_id')
            subscribe_status = request.data.get('subscribe_status', True)
            
            if not template_id:
                return Response({'error': 'template_id参数必填'}, status=status.HTTP_400_BAD_REQUEST)
            
            # 确保 subscribe_status 是布尔类型
            if isinstance(subscribe_status, str):
                subscribe_status = subscribe_status.lower() in ('true', '1', 'yes', 'accept')
            elif isinstance(subscribe_status, int):
                subscribe_status = bool(subscribe_status)
            else:
                subscribe_status = bool(subscribe_status)
            
            subscribe_msg, created = SubscribeMessage.objects.update_or_create(
                user=request.user,
                template_id=template_id,
                defaults={'subscribe_status': subscribe_status}
            )
            
            return Response({
                'message': '订阅状态已更新',
                'template_id': template_id,
                'subscribe_status': subscribe_status
            })
        except Exception as e:
            logger.error(f'订阅消息失败: {e}', exc_info=True)
            return Response({
                'error': f'订阅消息失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ElderlyProfileViewSet(viewsets.ModelViewSet):
    serializer_class = ElderlyProfileSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        # 如果是老人角色，返回与自己用户直接关联的档案（应该能看到自己的档案，无论是否绑定监护人）
        if user.role == 'elderly':
            return ElderlyProfile.objects.filter(user=user)
        elif user.role == 'guardian':
            # 监护人角色：查看自己管理的老人档案（guardian不为null且等于当前用户）
            return ElderlyProfile.objects.filter(guardian=user)
        elif user.role in ['community_admin', 'system_admin']:
            # 社区管理员和系统管理员：可以查看所有档案
            return ElderlyProfile.objects.all()
        else:
            # 其他角色：返回空查询集
            return ElderlyProfile.objects.none()
    
    def perform_create(self, serializer):
        user = self.request.user
        
        # 如果创建者是老人角色，只关联user，不设置guardian（等待监护人绑定）
        if user.role == 'elderly':
            serializer.save(user=user, guardian=None)
        else:
            # 监护人角色：创建老人档案时，设置自己为监护人
            serializer.save(guardian=user)
    
    def perform_destroy(self, instance):
        """
        删除老人档案时，需要处理关联的设备
        设备会通过on_delete=models.SET_NULL自动设置为null
        """
        user = self.request.user
        
        # 权限检查
        if user.role == 'elderly':
            # 老人角色：只能删除自己的档案
            if instance.user != user:
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied('无权限删除此老人档案')
        elif user.role == 'guardian':
            # 监护人角色：只能删除自己管理的老人档案
            if instance.guardian != user:
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied('无权限删除此老人档案')
        elif user.role in ['community_admin', 'system_admin']:
            # 社区管理员和系统管理员：可以删除任何档案
            pass
        else:
            # 其他角色：无删除权限
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('无权限删除老人档案')
        
        # 删除老人档案（关联的设备会自动设置为null，因为有on_delete=models.SET_NULL）
        instance.delete()

