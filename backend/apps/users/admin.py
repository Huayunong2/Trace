"""
用户管理后台
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, ElderlyProfile, SubscribeMessage


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """用户管理"""
    list_display = ['id', 'username', 'phone', 'role', 'openid', 'is_active', 'created_at']
    list_filter = ['role', 'is_active', 'created_at']
    search_fields = ['username', 'phone', 'openid']
    fieldsets = BaseUserAdmin.fieldsets + (
        ('扩展信息', {'fields': ('role', 'phone', 'openid', 'avatar')}),
    )


@admin.register(ElderlyProfile)
class ElderlyProfileAdmin(admin.ModelAdmin):
    """老人档案管理"""
    list_display = ['id', 'name', 'age', 'gender', 'guardian', 'emergency_contact', 'emergency_phone', 'is_active', 'created_at']
    list_filter = ['gender', 'is_active', 'created_at']
    search_fields = ['name', 'emergency_contact', 'emergency_phone']
    raw_id_fields = ['user', 'guardian']


@admin.register(SubscribeMessage)
class SubscribeMessageAdmin(admin.ModelAdmin):
    """订阅消息管理"""
    list_display = ['id', 'user', 'template_id', 'subscribe_status', 'subscribed_at', 'updated_at']
    list_filter = ['subscribe_status', 'template_id', 'subscribed_at']
    search_fields = ['user__username', 'template_id']
    raw_id_fields = ['user']
