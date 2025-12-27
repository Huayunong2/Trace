"""
Django Admin 自定义配置
"""
from django.contrib import admin

# 美化admin界面
admin.site.site_header = '老年痴呆防走失系统管理后台'
admin.site.site_title = '防走失系统'
admin.site.index_title = '欢迎使用防走失预警与跟踪系统'

