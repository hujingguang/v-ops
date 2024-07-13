from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Users

# Register your models here.


@admin.register(Users)
class UsersAdmin(UserAdmin):
    list_display = ('id', 'username', 'display', 'email',
                    'is_superuser', 'is_staff', 'is_active')
    search_fields = ('id', 'username', 'display', 'email','tel_num')
    list_display_link = ('id', 'username')
    ordering = ('id',)
    fieldsets = (
        ('认证信息', {'fields': ('username', 'password')}),
        ('个人信息', {'fields': ('display', 'email','tel_num',
                             'ding_user_id', 'wx_user_id', 'feishu_open_id')}),
        ('权限信息', {'fields': ('is_superuser', 'is_active',
                             'is_staff', 'groups', 'user_permissions')}),
        ('其他信息', {'fields': ('date_joined',)}),
    )
    # 添加页显示内容
    add_fieldsets = (
        ('认证信息', {'fields': ('username', 'password1', 'password2')}),
        ('个人信息', {'fields': ('display', 'email','tel_num',
                             'ding_user_id', 'wx_user_id', 'feishu_open_id')}),
        ('权限信息', {'fields': ('is_superuser', 'is_active',
                             'is_staff', 'groups', 'user_permissions')}),
    )
    filter_horizontal = ('groups', 'user_permissions',
                         )
    list_filter = ('is_staff', 'is_superuser',
                   'is_active', 'groups',)
