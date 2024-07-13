from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import permission_required
import logging
from common.utils.permission import superuser_required
from .models import Config




logger = logging.getLogger('default')


def index(request):
    """index. index页面导航

    Args:
        request:
    """
    return HttpResponseRedirect('/dashboard/')


def login(request):
    """login. 登陆处理方法

    Args:
        request:
    """
    if request.user and request.user.is_authenticated:
        return HttpResponseRedirect('/')
    return render(request, 'login.html', context={})


@permission_required('usermanage.menu_dashboard', raise_exception=True)
def dashboard(request):
    """dashboard. 管理面板

    Args:
        request:
    """
    return render(request, 'dashboard.html', {})


@permission_required('usermanage.menu_system_configure', raise_exception=True)
# @superuser_required
def sysconfig(request):
    """sysconfig. 系统配置请求处理方法

    Args:
        request: 
    """
    sys_confs = Config.objects.all().values('item', 'value')
    all_confs = {}
    for items in sys_confs:
        all_confs[items["item"]] = items["value"]
    context = {"sys_config": all_confs}
    return render(request, 'sysconfig.html', context)


