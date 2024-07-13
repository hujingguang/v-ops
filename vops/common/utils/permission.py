from django.http import HttpResponse
import simplejson as json
from django.shortcuts import render


def superuser_required(func):
    """superuser_required. 判断是否为超级管理员

    Args:
        func:
    """
    def wrapper(request, *args, **kw):
        user = request.user
        if user.is_superuser is False:
            if request.is_ajax():
                result = {'status': 1, 'msg': '只有管理员才能修改该页面', 'data': []}
                return HttpResponse(json.dumps(result), content_type='application/json')
            else:
                context = {'errMsg': 'No permission'}
                return render(request, '403.html', context=context)
        return func(request, *args, **kw)
    return wrapper


def role_required(roles=()):
    """role_required. 判断角色组装饰器

    Args:
        role:
    """
    def _role(func):
        def wrapper(request, *args, **kw):
            user = request.user
            if user.role not in roles and user.is_superuser is False:
                if user.is_ajax():
                    result = {'status': 1,
                              'msg': 'No Permission', 'data': []}
                    return HttpResponse(json.dumps(result), content_type='application/json')
                else:
                    context = {'errMsg': 'No Permission'}
                    return render(request, '403.html', context=context)
            return func(request, *args, **kw)
        return wrapper
    return _role
