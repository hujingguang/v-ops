import logging
from django.utils import timezone
import pytz
import simplejson as json
from django.http import HttpResponse
from django.shortcuts import render
from django.contrib.auth.decorators import permission_required
from .models import AppInfo, AppRelationShip, DeployAppRecord, DeployAppRecordDetail, DeployAppPublishRecord
from .models import AppVersionRecord, DeployAppPublishRecordDetail
from .models import DeployAppEnv, AppVersionHistory, AppBranchStatus
from common.utils.public import remove_str_space, ExtendJSONEncoder, send_message
from common.utils.public import check_upper_and_underline
from datetime import datetime
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from common.utils.git_utils import GitParser
from common.utils.jenkins_utils import JenkinsParser
from django.db.models import Q
from usermanage.models import Users
from django.db import transaction
from common.config import SysConfig
from django_q.tasks import async_task


logger = logging.getLogger('default')

TEST_DINGTALK_WEB_HOOK = 'https://oapi.dingtalk.com/robot/send?access_token=fcaaa7cdb9eda262e5d1ce510e415fdf238565b8d6ad13e6a7a91116188aabe0'
PUBLISH_DINGTALK_WEB_HOOK = 'https://oapi.dingtalk.com/robot/send?access_token=d52dfc61c083c386c8234b556f2e1d74a7416ff23633e76190794eb060f48ec1'


def check_apps(withApps):
    """check_apps. 检测依赖包是否已经存在

    Args:
        withApps: 依赖包信息
    """
    with_apps = remove_str_space(withApps).replace('\n', '').split(',')
    no_find_apps = list()
    find_apps = list()
    for _app in with_apps:
        if not _app:
            continue
        elif AppInfo.objects.filter(app_name=_app).exists():
            find_apps.append(_app)
        else:
            no_find_apps.append(_app)
    return find_apps, no_find_apps


def check_apps_interdependence(be_add, current):
    """check_apps_interdependence. 检查依赖关系包中是否互相依赖

    Args:
        be_add:   添加的依赖包
        current: 当前添加的服务
    """
    if AppRelationShip.objects.filter(app_name=be_add).exists():
        apps = AppRelationShip.objects.get(app_name=be_add).with_apps
        if current in remove_str_space(apps).split(','):
            return True
    return False

@permission_required('usermanage.menu_deploymanage_servicemanage', raise_exception=True)
def service_readme(request):
    return render(request, 'serviceRead.html',context={})


@permission_required('usermanage.menu_deploymanage_servicemanage', raise_exception=True)
def service_manage(request):
    """service_manage. 微服务管理页面

    Args:
        request:
    """
    app_info_list = AppInfo.objects.all().order_by('-create_time')
    for app in app_info_list:
        try:
            app_relation = AppRelationShip.objects.get(app_name=app.app_name)
            app.relation_info = app_relation
        except:
            app.relation_info = None

    paginator = Paginator(app_info_list, 20)
    page = request.GET.get('page')
    try:
        svc = paginator.page(page)
    except PageNotAnInteger:
        svc = paginator.page(1)
    except EmptyPage:
        svc = paginator.page(paginator.num_pages)
    return render(request, 'serviceList.html',
                  context={'app_info_list': svc})




@permission_required('usermanage.menu_deploymanage_bindservice',
                     raise_exception=True)
def bind_service(request):
    """bind_service. 服务绑定接口

    Args:
        request:
    """
    result = {'status': 1, 'msg': '提交失败,请重试', 'data': []}
    app_name = request.POST.get('app_name', '')
    with_apps = request.POST.get('with_apps', '')
    with_apps = ','.join(json.loads(with_apps))
    create_user = request.user.username
    find_apps, no_find_apps = check_apps(with_apps)
    if find_apps:
        for app in find_apps:
            if check_apps_interdependence(app, app_name):
                result['msg'] = '服务： {0} 不能和 {1} 互相依赖'.format(app,
                                                              app_name)
                return HttpResponse(json.dumps(result), content_type='application/json')
    if no_find_apps:
        result['msg'] = '请先创建这些不存在的服务：' + ','.join(no_find_apps)
    elif app_name in find_apps:
        result['msg'] = '创建失败,不能依赖自己'
    elif AppRelationShip.objects.filter(app_name=app_name).exists():
        result['msg'] = '该服务已存在依赖绑定信息'
    else:
        with_apps = ','.join(list(set(find_apps)))
        #create_time = datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S')
        create_time = datetime.now(pytz.timezone('Asia/Shanghai'))
        #create_time = datetime.now()
        update_time = create_time
        r = AppRelationShip(
                app_name=app_name,
                create_time=create_time,
                update_time=update_time,
                create_user=create_user,
                with_apps=with_apps
                )
        r.save()
        result['status'] = 0
        result['msg'] = '添加成功'
    return HttpResponse(json.dumps(result), content_type='application/json')


@permission_required('usermanage.menu_deploymanage_bindservice',raise_exception=True)
def get_relation_service_list(request):
    app_name = request.POST.get('app_name','')
    result = {'status':1,'msg':'参数错误','data':[]}
    if app_name:
        relation_app = AppInfo.objects.exclude(app_name='nextop-base-parent').exclude(app_name=app_name).filter(app_type=2).values('app_name')
        apps = list()
        for app in relation_app:
            apps.append(app['app_name'])
        result['status']  = 0
        result['data']  = apps
    return HttpResponse(json.dumps(result), content_type='application/json')




@permission_required('usermanage.menu_deploymanage_bindservice',
                     raise_exception=True)
def get_bind_service_select(request):
    """get_bind_service_select. 获取服务绑定选项接口

    Args:
        request:
    """
    app_name_list = AppInfo.objects.exclude(app_name='nextop-base-parent').exclude(app_type=0).all().values('app_name')
    name_list = list()
    for appName in app_name_list:
        if not AppRelationShip.objects.filter(app_name=appName['app_name']).exists():
            name_list.append(appName["app_name"])
    return HttpResponse(json.dumps({'status': 0, 'msg': 'ok', 'data': name_list}), content_type="application/json")


@permission_required('usermanage.menu_deploymanage_versiontest',
                     raise_exception=True)
def get_add_version_service_select(request):
    """get_add_version_service_select. 版本提测获取服务选项接口

    Args:
        request:
    """
    app_name_list = AppInfo.objects.filter(
        Q(app_type=0) | Q(app_type=1)).values('app_name')
    name_list = list()
    for appName in app_name_list:
        # 必须已经绑定了服务依赖的才能提测
        if AppRelationShip.objects.filter(app_name=appName['app_name']).exists():
            name_list.append(appName["app_name"])
        if AppInfo.objects.filter(app_name=appName['app_name'],app_type=0).exists():
            name_list.append(appName["app_name"])
    return HttpResponse(json.dumps({'status': 0, 'msg': 'ok', 'data': name_list}), content_type="application/json")


@permission_required('usermanage.menu_deploymanage_versiontest',
                     raise_exception=True)
def get_add_version_branch_select(request):
    app_name = request.POST.get('app_name','')
    result = {'status':1,'msg':'branches get failed','data':[]}
    if app_name:
        app_info = AppInfo.objects.get(app_name=app_name.replace(' ',''))
        git_parser= GitParser()
        result = git_parser.get_service_branch_list(app_info.git_repo_address,prefix='feature')
        if app_info.app_type == 0:
            result = git_parser.get_service_branch_list(app_info.git_repo_address,prefix='feature',app_type=0)
        else:
            result = git_parser.get_service_branch_list(app_info.git_repo_address,prefix='feature')
    return HttpResponse(json.dumps(result), content_type="application/json")





@permission_required('usermanage.menu_deploymanage_versiontest',
                     raise_exception=True)
def get_add_version_user_select(request):
    """get_add_version_user_select. 版本提测获取测试人员接口

    Args:
        request:
    """
    test_users = Users.objects.filter(
        groups__name='测试组').values('username', 'display')
    user_list = {}
    for user in test_users:
        user_list[user['username']] = user['display']
    return HttpResponse(json.dumps({'status': 0, 'msg': 'ok', 'data':
                                    user_list}), content_type="application/json")


@permission_required('usermanage.menu_deploymanage_versiontest',
                     raise_exception=True)
def get_add_version_env_select(request):
    """get_add_version_env_select. 版本提测获取环境选项接口

    Args:
        request:
    """
    env_all = DeployAppEnv.objects.filter(can_select=1).all().values('env_id', 'env_name')
    env_list = {}
    for env in env_all:
        env_list[env['env_id']] = env['env_name']
    return HttpResponse(json.dumps({'status': 0, 'msg': 'ok', 'data':
                                    env_list}), content_type="application/json")


@permission_required('usermanage.menu_deploymanage_versionpublish',
                     raise_exception=True)
def get_add_publish_env_select(request):
    """get_add_version_env_select. 版本上线获取环境选项接口

    Args:
        request:
    """
    env_all = DeployAppEnv.objects.filter(can_select=0).all().values('env_id', 'env_name')
    env_list = {}
    for env in env_all:
        env_list[env['env_id']] = env['env_name']
    return HttpResponse(json.dumps({'status': 0, 'msg': 'ok', 'data':
                                    env_list}), content_type="application/json")



@permission_required('usermanage.menu_deploymanage_addversion')
def add_version(request):
    """add_version. 添加版本提测接口

    Args:
        request:
    """
    msg_tmp = '''
    >提测服务：<font color="comment"> {0} </font>*
    >提测功能：<font color="comment"> {1}.... </font>*
    >提测人： <font color="comment"> {2} </font>*
    >分配测试：<font color="comment"> {3} </font>*
    >提测feature分支：<font color="comment"> {4} </font>*
    >自动生成分支: <font color="comment"> {5} </font>*
    >提测时间：<font color="comment"> {6} </font>*
    '''
    app_name = request.POST.get('app_name', '')
    feature_branch = request.POST.get('feature_branch', '')
    description = request.POST.get('description', '')
    test_user = request.POST.get('test_user', '')
    deploy_env = request.POST.get('deploy_env', '')
    is_sync = request.POST.get('is_sync',0)
    data = remove_str_space([app_name, feature_branch, test_user, deploy_env])
    result = {'status': 1, 'msg': '提交失败', 'data': []}
    if not AppInfo.objects.filter(Q(app_type=0) |
                                  Q(app_type=1)).filter(app_name=data[0]).exists():
        result['msg'] = '提测服务不存在,请先创建'
    elif not DeployAppEnv.objects.filter(env_name=data[3]).exists():
        result['msg'] = '部署环境不存在,请先创建'
    elif DeployAppRecord.objects.filter(app_name=data[0],
                                        feature_branch=data[1]).exists():
        result['msg'] = '已存在该提测版本'
    elif check_upper_and_underline(feature_branch):
        result['msg'] = '功能分支命名不规范,不能包含下划线和大写字母'
    else:
        app = AppInfo.objects.get(app_name=data[0])
        branch_prefix='feature'
        is_java = True
        if app.app_type == 0:
            branch_prefix = 'feature/'
            is_java = False
        git_parser = GitParser()
        _r = git_parser.check_repo_is_valid(app.git_repo_address,
                                            pom_file=app.pom_xml_path,
                                            branch=feature_branch,
                                            is_java=is_java)
        if _r['status'] != 0:
            return HttpResponse(json.dumps(_r), content_type="application/json")
        else:
            result = git_parser.get_branch_commit_uuid(
                app.git_repo_address, 
                feature_branch,
                auto_create_test_branch=True,
                prefix=branch_prefix)
            env = DeployAppEnv.objects.get(env_name=deploy_env)
            create_time = datetime.now(pytz.timezone('Asia/Shanghai'))
            update_time = create_time
            if isinstance(result, list):
                try:
                    with transaction.atomic():
                        app_record = DeployAppRecord.objects.create(
                                app_name=data[0],
                                feature_branch=data[1],
                                create_time=create_time,
                                update_time=update_time,
                                feature_branch_uuid=result[1],
                                auto_test_branch=result[0],
                                auto_test_branch_uuid=result[1],
                                deploy_status='Pending',
                                test_status='WaitTest',
                                publish_status=0,
                                test_user=data[2],
                                create_user=request.user.username,
                                description=description,
                                is_sync =is_sync
                                )
                        app_record.deploy_env.add(env)
                        DeployAppRecordDetail.objects.create(
                                compile_log="init\n",
                                deploy_log="init\n",
                                update_log="init\n",
                                deploy_app_record=app_record
                                )
                        desc = '-'
                        if len(description) > 10:
                            desc = description[:10]
                        else:
                            desc = description
                        # 发送通知消息
                        t_user = Users.objects.get(username=data[2])
                        msg_tmp = '''>提测服务：<font color="green">{0}</font>*>提测功能：<font color="comment">{1}....</font>*>提测人：<font color="red">{2}</font>*>分配测试：<font color="red">{3}</font>*>提测feature分支：<font color="comment"> {4} </font>*>自动生成分支: <font color="comment"> {5} </font>*>提测时间：<font color="comment"> {6} </font>*'''.format(data[0],
                                                                                                                                                                                                                                                                                                                                          desc,
                                                                                                                                                                                                                                                                                                                                          request.user.username,
                                                                                                                                                                                                                                                                                                                                          t_user.display,
                                                                                                                                                                                                                                                                                                                                          data[
                                                                                                                                                                                                                                                                                                                                              1],
                                                                                                                                                                                                                                                                                                                                          result[
                                                                                                                                                                                                                                                                                                                                              0],
                                                                                                                                                                                                                                                                                                                                          datetime.strftime(
                                                                                                                                                                                                                                                                                                                                              datetime.now(), '%Y-%m-%d %H:%M:%S')
                                                                                                                                                                                                                                                                                                                                          )
                        tel_list = list()
                        if request.user.tel_num:
                            tel_list.append(request.user.tel_num)
                        if t_user.tel_num:
                            tel_list.append(t_user.tel_num)
                        send_at = ''
                        for phone in tel_list:
                            send_at = send_at + '@' + phone
                        msg_tmp = msg_tmp + send_at
                        send_message('版本提测通知', msg_tmp,
                                     TEST_DINGTALK_WEB_HOOK, tel_list)
                        result = {'status': 0, 'msg': '添加成功', 'data': []}
                except Exception as e:
                    logger.error(str(e))
                    result = {'status': 1, 'msg': '数据库连接失败', 'data': []}
    return HttpResponse(json.dumps(result), content_type="application/json")


@permission_required('usermanage.menu_deploymanage_addservice', raise_exception=True)
def add_service(request):
    """add_service. 添加服务接口

    Args:
        request:
    """
    app_name = request.POST.get('app_name', None)
    git_addr = request.POST.get('git_addr', None)
    deploy_branch = request.POST.get('deploy_branch', 'master')
    pom_file_path = request.POST.get('pom_file_path', '')
    app_type = request.POST.get('app_type', 1)
    try:
        app_type = int(app_type)
        if app_type not in [0, 1, 2]:
            raise Exception('未知服务类型')
    except:
        app_type = 0
    app_function = request.POST.get('app_function', '其他')
    result = {'status': 1, 'msg': '添加失败', 'data': []}
    data = remove_str_space([app_name, git_addr, pom_file_path, deploy_branch])
    if not app_name or not git_addr:
        result['msg'] = '代码仓库地址或服务名不能为空,请重新输入'
    elif (not git_addr.startswith('http://') and not git_addr.startswith('https://')) or not git_addr.endswith('.git'):
        result['msg'] = '代码仓库地址格式不正确,请重新输入'
    elif AppInfo.objects.filter(app_name=app_name).exists():
        result['msg'] = '该服务名已存在,请重新修改'
    else:
        git_parser = GitParser()
        is_java = True
        if app_type == 0:
            is_java = False
        result = git_parser.check_repo_is_valid(data[1],
                pom_file=data[2],is_java=is_java)
        if result['status'] == 0:
            try:
                #create_time = datetime.strftime(datetime.now(pytz.timezone('Asia/Shanghai')), '%Y-%m-%d %H:%M:%S')
                create_time = datetime.now(pytz.timezone('Asia/Shanghai'))
                update_time = create_time
                app = AppInfo(
                        app_name=data[0],
                        git_repo_address=data[1],
                        deploy_branch=data[3], pom_xml_path=data[2],
                        create_time=timezone.now(),
                        app_type=app_type,
                        create_user=request.user.username,
                        app_function=app_function,
                        update_time=update_time
                        )
                app.save()
                result['status'] = 0
                result['msg'] = '添加成功'
            except Exception as e:
                result['msg'] = '添加失败,请联系管理员'
                result['status'] = 1
                logging.error(str(e))
    return HttpResponse(json.dumps(result), content_type="application/json")


@permission_required('usermanage.menu_deploymanage_resetservice', raise_exception=True)
def reset_service(request):
    """reset_service. 服务依赖重置接口

    Args:
        request:
    """
    username = request.user.username
    app_name = remove_str_space(request.POST.get('app_name', None))
    result = {'status': 1, 'msg': '重置失败', 'data': []}
    if app_name and AppInfo.objects.filter(app_name=app_name).exists():
        if AppRelationShip.objects.filter(app_name=app_name).exists():
            relation = AppRelationShip.objects.get(app_name=app_name)
            if relation.create_user == username or request.user.is_superuser:
                relation.delete()
                result = {'status': 0, 'msg': '已重置', 'data': []}
            else:
                return HttpResponse(json.dumps({'status': 1, 'msg':
                                                '只有创建人才能清除依赖', "data": []}),
                                    content_type='application/json')
        result = {'status': 0, 'msg': '已重置', 'data': []}

    return HttpResponse(json.dumps(result), content_type="application/json")


@permission_required('usermanage.menu_deploymanage_delservice',
                     raise_exception=True)
def del_service(request):
    """del_service. 删除服务信息接口

    Args:
        request:
    """
    username = request.user.username
    app_name = remove_str_space(request.POST.get('app_name', None))
    result = {'status': 1, 'msg': '删除失败', 'data': []}
    if app_name and AppInfo.objects.filter(app_name=app_name).exists():
        app = AppInfo.objects.get(app_name=app_name)
        if app.create_user == username or request.user.is_superuser:
            pass
        else:
            return HttpResponse(json.dumps({'status': 1, 'msg': '只能创建人才能删除该记录', "data": []}),
                                content_type='application/json')

        if AppRelationShip.objects.filter(app_name=app_name).exists():
            relation = AppRelationShip.objects.get(app_name=app_name)
            if relation.create_user != username or not request.user.is_superuser:
                return HttpResponse(json.dumps({'status': 1, 'msg': '请先找创建人清除依赖', "data": []}),
                                    content_type='application/json')
        app.delete()
        result = {'status': 0, 'msg': '已删除', 'data': []}
    return HttpResponse(json.dumps(result), content_type="application/json")


@permission_required('usermanage.menu_deploymanage_getservice', raise_exception=True)
def get_service(request):
    """get_service. 获取服务信息接口

    Args:
        request:
    """
    app_name = remove_str_space(request.POST.get("app_name", None))
    if app_name and AppInfo.objects.filter(app_name=app_name).exists():
        app = AppInfo.objects.filter(app_name=app_name).values(
            'app_name', 'git_repo_address', 'deploy_branch', 'pom_xml_path', 'app_type',
            'app_function', 'create_user', 'create_time', 'update_time')[0]
        with_apps = ''
        if AppRelationShip.objects.filter(app_name=app_name).exists():
            with_apps = AppRelationShip.objects.get(
                app_name=app_name).with_apps
        app.update({'with_apps': with_apps})
        result = {'status': 0, 'msg': 'ok', 'data': [app]}
    else:
        result = {'status': 1, 'msg': '服务不存在', 'data': []}
    return HttpResponse(json.dumps(result, cls=ExtendJSONEncoder,
                                   bigint_as_string=True), content_type="application/json")


@permission_required('usermanage.menu_deploymanage_updateservice', raise_exception=True)
def update_service(request):
    """update_service. 更新服务接口

    Args:
        request:
    """
    app_name = request.POST.get('app_name', None)
    git_addr = request.POST.get('git_addr', None)
    deploy_branch = request.POST.get('deploy_branch', 'master')
    pom_file_path = request.POST.get('pom_file_path', './')
    app_type = request.POST.get('app_type', 1)
    try:
        app_type = int(app_type)
        if app_type not in [0, 1, 2]:
            raise Exception('未知服务类型')
    except:
        app_type = 0
    app_function = request.POST.get('app_function', '其他')
    result = {'status': 1, 'msg': '添加失败', 'data': []}
    data = remove_str_space([app_name, git_addr, pom_file_path, deploy_branch])
    if not app_name or not git_addr:
        result['msg'] = '代码地址或服务名不能为空,请重新输入'
    elif (not git_addr.startswith('http://') and not git_addr.startswith('https://')) or not git_addr.endswith('.git'):
        result['msg'] = '代码地址格式不正确,请重新输入'
    else:
        git_parser = GitParser()
        result = git_parser.check_repo_is_valid(data[1],
                                                pom_file=data[2], branch=data[3])
        if result['status'] == 0:
            try:
                #update_time = datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S')
                update_time = datetime.now(pytz.timezone('Asia/Shanghai'))
                #update_time = datetime.now()
                AppInfo.objects.filter(app_name=app_name).update(
                    git_repo_address=data[1],
                    deploy_branch=data[3],
                    pom_xml_path=data[2],
                    update_time=update_time,
                    app_function=app_function,
                    app_type=app_type
                )
                result['status'] = 0
                result['msg'] = '保存成功'
            except Exception as e:
                result['msg'] = '保存失败,请联系管理员'
                logging.error(str(e))
    return HttpResponse(json.dumps(result), content_type="application/json")


@permission_required('usermanage.menu_deploymanage_versiontest',
                     raise_exception=True)
def version_test(request):
    """version_test. 获取提测版本列表

    Args:
        request:
    """
    username = request.user.username
    records = DeployAppRecord.objects.filter(Q(create_user=username) |
                                             Q(test_user=username)).all().order_by('-create_time')

    if request.user.is_superuser:
        records = DeployAppRecord.objects.all().order_by('-create_time')
    for record in records:
        try:
            #env = DeployAppEnv.objects.filter('deploy_app_record')
            env = record.deploy_env.get()
            record.env_obj = env
        except:
            record.env = None

    paginator = Paginator(records, 20)
    page = request.GET.get('page')
    try:
        r = paginator.page(page)
    except PageNotAnInteger:
        r = paginator.page(1)
    except EmptyPage:
        r = paginator.page(paginator.num_pages)
    return render(request, 'versionTest.html',
                  context={'version_records': r})


@permission_required('usermanage.menu_deploymanage_getversion',
                     raise_exception=True)
def get_version(request):
    """get_version. 获取版本记录详情接口

    Args:
        request:
    """
    deploy_id = remove_str_space(request.POST.get('deploy_id', None))
    result = {'status': 1, 'msg': '内部错误', 'data': []}
    if not deploy_id:
        result['msg'] = '不存在此记录'
    else:
        deploy_id = int(deploy_id)
        if not DeployAppRecord.objects.filter(deploy_id=deploy_id).exists():
            result['msg'] = '不存在此记录'
        else:
            record = DeployAppRecord.objects.get(deploy_id=deploy_id)
            env = None
            record_detail = None
            try:
                env = record.deploy_env.get()
            except Exception as e:
                logger.error(str(e))
            try:
                record_detail = DeployAppRecordDetail.objects.get(
                    deploy_app_record=record)
            except Exception as e:
                logger.error(str(e))
            r = DeployAppRecord.objects.filter(deploy_id=deploy_id).values(
                    'app_name',
                    'feature_branch',
                    'is_sync',
                    'feature_branch_uuid',
                    'auto_test_branch',
                    'auto_test_branch_uuid',
                    'publish_time',
                    'create_time',
                    'update_time',
                    'create_user',
                    'test_user',
                    'description')[0]
            r.update({'env_name': env.env_name,
                      'image_url': record_detail.test_image_url})
            result = {'status': 0, 'msg': 'ok', 'data': r}
    return HttpResponse(json.dumps(result, cls=ExtendJSONEncoder), content_type='application/json')


@permission_required('usermanage.menu_deploymanage_updateversion')
def update_version(request):
    """update_version. 更新版本详细接口

    Args:
        request:
    """
    deploy_env = request.POST.get('deploy_env', '')
    test_user = request.POST.get('test_user', '')
    app_name = request.POST.get('app_name', '')
    deploy_id = request.POST.get('deploy_id', '')
    data = remove_str_space([deploy_env, test_user, app_name])
    if not Users.objects.filter(username=data[1]).exists() or \
       not DeployAppEnv.objects.filter(env_name=data[0]).exists() or \
       not DeployAppRecord.objects.filter(app_name=data[2],
                                          deploy_id=int(deploy_id)).exists():
        result = {'status': 1, 'msg': '数据错误', 'data': []}
    else:
        try:
            with transaction.atomic():
                new_env = DeployAppEnv.objects.get(env_name=data[0])
                record = DeployAppRecord.objects.filter(
                    app_name=data[2],
                    deploy_id=int(deploy_id)).all()[0]
                try:
                    old_env = record.deploy_env.all()[0]
                    record.deploy_env.remove(old_env)
                except Exception as e:
                    logger.error(str(e))
                    pass
                record.test_user = data[1]
                # record.deploy_env.remove(old_env)
                record.deploy_env.add(new_env)
                record.save()
                result = {'status': 0, 'msg': '更新成功', 'data': []}
        except Exception as e:
            logger.error(str(e))
            result = {'status': 1, 'msg': '数据库连接错误', 'data': []}
    return HttpResponse(json.dumps(result), content_type='application/json')


@permission_required('usermanage.menu_deploymanage_passversion')
def pass_version(request):
    deploy_id = remove_str_space(request.POST.get('deploy_id', None))
    result = {'status': 1, 'msg': '参数错误', 'data': []}
    user = request.user
    git_parser = GitParser()
    if not DeployAppRecord.objects.filter(deploy_id=int(deploy_id)).exists():
        result['版本不存在']
    else:
        record = DeployAppRecord.objects.get(deploy_id=int(deploy_id))
        if record.test_user == user.username or user.is_superuser:
            app_info = AppInfo.objects.get(app_name=record.app_name)
            publish_commit_id = git_parser.get_branch_commit_uuid(
                    app_info.git_repo_address,
                    record.auto_test_branch)[0]
            create_user_phone = Users.objects.get(
                username=record.create_user).tel_num
            test_user_phone = Users.objects.get(
                username=record.test_user).tel_num
            send_list = list()
            if create_user_phone:
                send_list.append(create_user_phone)
            if test_user_phone:
                send_list.append(test_user_phone)
            msg_tmp = '''>提测服务：<font color="green">{0}</font>*>测试人：<font color="red">{1}</font>*>提测人：<font color="red">{2}</font>*>测试分支: <font color="comment"> {3} </font>*>测试结果：<font color="green">已通过</font>*'''.format(
                app_info.app_name, record.test_user, record.create_user, record.auto_test_branch)
            send_at = ''
            for phone in send_list:
                send_at = send_at + '@' + phone
            msg_tmp = msg_tmp + send_at
            send_message('提测通知', msg_tmp, TEST_DINGTALK_WEB_HOOK, send_list)
            try:
                with transaction.atomic():
                    record.test_status = 'TestPass'
                    record.auto_test_branch_uuid = publish_commit_id
                    record.save()
                result['msg'] = '操作成功'
                result['status'] = 0
            except Exception as e:
                logger.error(str(e))
                result['msg'] = '数据库连接失败'
        else:
            result['无权限操作']
    return HttpResponse(json.dumps(result), content_type='application/json')


@permission_required('usermanage.menu_deploymanage_deployversion')
def deploy_version(request):
    """deploy_version. 发布提测版本接口

    Args:
        request:
    """
    deploy_id = request.POST.get('deploy_id', '')
    user = request.user
    result = {'status': 1, 'msg': '非法参数', 'data': ''}
    try:
        deploy_id = int(deploy_id)
    except Exception as e:
        deploy_id = None
    if not deploy_id:
        return HttpResponse(json.dumps(result), content_type='application/json')
    if not DeployAppRecord.objects.filter(deploy_id=deploy_id).exists():
        result['msg'] = '不存在此记录'
        return HttpResponse(json.dumps(result), content_type='application/json')
    if DeployAppRecord.objects.filter(Q(create_user=user.username) | Q(test_user=user.username)).exists() or user.is_superuser:
        record = DeployAppRecord.objects.get(deploy_id=deploy_id)
        env = record.deploy_env.all()[0]
        if not env.jenkins_url:
            result['msg'] = '缺少发布环境,请联系管理员配置'
        else:
            sys_conf = SysConfig()
            j_url = env.jenkins_url
            j_user = sys_conf.get('git_username')
            j_passwd = sys_conf.get('git_password')
            job_prefix = env.project_prefix
            job_sufix = env.project_sufix
            folder_name = env.jenkins_folder.rstrip('/').lstrip('/')
            folder_depth = env.jenkins_folder_depth
            app_name = record.app_name
            job_name = app_name
            full_name = ''
            if not j_url or not j_passwd or not j_user:
                result['msg'] = '发布环境缺少认证用户'
            else:
                if job_prefix:
                    job_name = job_prefix.replace(' ','') + job_name
                if job_sufix:
                    job_name = job_name + job_sufix.replace(' ','')
                if folder_depth == 0:
                    full_name = job_name
                elif folder_depth == 1:
                    full_name = folder_name.replace(' ','') + '/' + job_name
                git_parser = GitParser()
                git_address = AppInfo.objects.get(app_name=app_name).git_repo_address
                now_feature_uuid = git_parser.get_branch_commit_uuid(git_address,record.feature_branch)[0]
                #是否进行代码同步到测试分支
                if record.is_sync == 1 and record.feature_branch_uuid != now_feature_uuid:
                    print('触发代码同步')
                    _r = git_parser.merge_branch_to_other(git_address,record.auto_test_branch,record.feature_branch)
                    if _r['status'] == 1:
                        return HttpResponse(json.dumps(_r), content_type='application/json')
                    else:
                        record.auto_test_branch_uuid = git_parser.get_branch_commit_uuid(git_address, record.auto_test_branch)[0]
                        record.feature_branch_uuid = now_feature_uuid
                        record.save()
                jenkins_parser = JenkinsParser(j_user, j_passwd, j_url)
                # job_info = jenkins_parser.get_job_info(job_name,folderName=folder_name,depth=folder_depth)
                params = {'BRANCH': record.auto_test_branch}
                # 直接执行
                #jenkins_parser.start_job(deploy_id, full_name, parameters=params,depth=folder_depth)
                task_name = 'Version_Test_Record_ID: ' + str(deploy_id)
                async_task(jenkins_parser.start_job, deploy_id=deploy_id,
                           job_full_name=full_name,
                           parameters=params,
                           depth=folder_depth,
                           timeout=3600,
                           task_name=task_name)
                return HttpResponse(json.dumps({'status': 0, 'msg': '正在部署', 'data': []}),
                                    content_type='application/json')
    else:
        result['msg'] = '无权限'
    return HttpResponse(json.dumps(result), content_type='application/json')



@permission_required('usermanage.menu_deploymanage_versionpublish')
def deploy_publish(request):
    """deploy_publish. 发布上线版本接口

    Args:
        request:
    """
    publish_id = request.POST.get('publish_id', '')
    user = request.user
    result = {'status': 1, 'msg': '非法参数', 'data': ''}
    try:
        publish_id = int(publish_id)
    except Exception as e:
        publish_id = None
    if not publish_id:
        return HttpResponse(json.dumps(result), content_type='application/json')
    if not DeployAppPublishRecord.objects.filter(publish_id=publish_id).exists():
        result['msg'] = '不存在此记录'
        return HttpResponse(json.dumps(result), content_type='application/json')
    if Users.objects.filter(username=request.user.username,groups__name='发布组').exists() or user.is_superuser:
        record = DeployAppPublishRecord.objects.get(publish_id=publish_id)
        env = record.publish_env.filter(can_select=0).all()[0]
        if not env.jenkins_url:
            result['msg'] = '缺少发布环境,请联系管理员配置'
        else:
            sys_conf = SysConfig()
            j_url = env.jenkins_url
            j_user = sys_conf.get('git_username')
            j_passwd = sys_conf.get('git_password')
            job_prefix = env.project_prefix
            job_sufix = env.project_sufix
            folder_name = env.jenkins_folder.rstrip('/').lstrip('/')
            folder_depth = env.jenkins_folder_depth
            app_name = record.app_name
            job_name = app_name
            full_name = ''
            version = AppVersionRecord.objects.get(publish_id=publish_id,app_name=app_name)
            if not j_url or not j_passwd or not j_user:
                result['msg'] = '发布环境缺少认证用户'
            else:
                if job_prefix:
                    job_name = job_prefix.replace(' ','') + job_name
                if job_sufix:
                    job_name = job_name + job_sufix.replace(' ','')
                if folder_depth == 0:
                    full_name = job_name
                elif folder_depth == 1:
                    full_name = folder_name.replace(' ','') + '/' + job_name
                jenkins_parser = JenkinsParser(j_user, j_passwd, j_url)
                # job_info = jenkins_parser.get_job_info(job_name,folderName=folder_name,depth=folder_depth)
                params = {'BRANCH': version.release_branch}
                # 直接执行
                #jenkins_parser.start_job(publish_id, full_name,
                #        parameters=params,depth=folder_depth,publish=True)
                task_name = 'Version_Publish_Record_ID: ' + str(publish_id)
                async_task(jenkins_parser.start_job, deploy_id=publish_id,
                           job_full_name=full_name,
                           publish=True,
                           parameters=params,
                           depth=folder_depth,
                           timeout=3600,
                           task_name=task_name)
                return HttpResponse(json.dumps({'status': 0, 'msg': '正在部署', 'data': []}),
                                    content_type='application/json')
    else:
        result['msg'] = '无权限'
    return HttpResponse(json.dumps(result), content_type='application/json')





@permission_required('usermanage.menu_deploymanage_versionpublish',
                     raise_exception=True)
def version_publish(request):
    """version_publish. 版本上线列表获取接口

    Args:
        request:
    """
    username = request.user.username
    records = DeployAppPublishRecord.objects.filter(
        Q(create_user=username)).all().order_by('-create_time')
    if request.user.is_superuser or Users.objects.filter(username=username, groups__name="测试组").exists():
        records = DeployAppPublishRecord.objects.all().order_by('-create_time')
    for record in records:
        try:
            #env = DeployAppEnv.objects.filter('deploy_app_record')
            deploy_records = list()
            env = record.publish_env.all()[0]
            if AppVersionHistory.objects.filter(publish_id=record.publish_id, app_name=record.app_name).exists():
                app_version = AppVersionHistory.objects.get(
                    publish_id=record.publish_id, app_name=record.app_name)
            else:
                app_version = None
            for _id in record.deploy_ids.split(','):
                deploy_records.append(DeployAppRecord.objects.get(
                    deploy_id=int(_id)).auto_test_branch)
            record.env_obj = env
            record.deploy_records = ','.join(deploy_records)
            record.app_version = app_version
        except Exception as e:
            print(123)
            logger.error(str(e))
            record.env_obj = None
            record.deploy_records = None
            app_version = None

    paginator = Paginator(records, 20)
    page = request.GET.get('page')
    try:
        r = paginator.page(page)
    except PageNotAnInteger:
        r = paginator.page(1)
    except EmptyPage:
        r = paginator.page(paginator.num_pages)
    return render(request, 'versionPublish.html',
                  context={'publish_records': r})


@permission_required('usermanage.menu_deploymanage_versionpublish', raise_exception=True)
def get_deploy_versions_select(request):
    """get_deploy_versions_select. 服务上线获取服务可提测版本接口

    Args:
        request:
    """
    app_name = request.POST.get('app_name', '')
    result = {'status': 0, 'msg': '无该服务提测通过版本', 'data': []}
    if not app_name:
        if not DeployAppRecord.objects.filter(deploy_status="DeployPass", test_status='TestPass', publish_status=0).exists():
            result['msg'] = '没有可以上线的服务'
            return HttpResponse(json.dumps(result), content_type='application/json')
        else:
            apps = list()
            for app in DeployAppRecord.objects.filter(deploy_status="DeployPass", test_status='TestPass', publish_status=0).values('app_name').distinct():
                apps.append(app['app_name'])
            result = {'status': 0, 'msg': 'ok', 'data': apps}
            return HttpResponse(json.dumps(result, cls=ExtendJSONEncoder), content_type='application/json')
    if not DeployAppRecord.objects.filter(app_name=app_name,
                                          deploy_status="DeployPass", test_status='TestPass', publish_status=0).exists():
        return HttpResponse(json.dumps(result), content_type='application/json')
    else:
        versions = list()
        for version in DeployAppRecord.objects.filter(app_name=app_name,
                                                      deploy_status="DeployPass", test_status='TestPass',
                                                      publish_status=0).values('auto_test_branch'):
            versions.append(version['auto_test_branch'])
        result = {'status': 0, 'msg': 'ok', 'data': versions}
        return HttpResponse(json.dumps(result, cls=ExtendJSONEncoder), content_type='application/json')


def format_relation(app, action=0):
    """format_relation. 格式化依赖包字符串数据,废弃

    Args:
        app:
        action:
    """
    label_list = list()
    app_list = list()
    if action == 0:
        if AppRelationShip.objects.filter(app_name=app).exists():
            relations = AppRelationShip.objects.get(
                app_name=app).with_apps.split(',')
            for r in relations:
                label_list.append(app + '__' + r)
                app_list.append(r)
    elif action == 1:
        app = app.split('')
        return label_list


def get_relation(app):
    """get_relation. 获取服务依赖字符串

    Args:
        app:
    """
    if AppRelationShip.objects.filter(app_name=app).exists():
        return AppRelationShip.objects.get(app_name=app).with_apps.split(',')
    return []


@permission_required('usermanage.menu_deploymanage_versionpublish', raise_exception=True)
def get_deploy_relation_select(request):
    """get_deploy_relation_select. 服务上线接口获取依赖服务列表

    Args:
        request:
    """
    app_name = request.POST.get('app_name', '')
    result = {'status': 0, 'msg': '无该服务提测通过版本', 'data': []}
    if not app_name:
        if not DeployAppRecord.objects.filter(deploy_status="DeployPass", test_status='TestPass', publish_status=0).exists():
            result['msg'] = '没有可以上线的服务'
            return HttpResponse(json.dumps(result), content_type='application/json')
    if not DeployAppRecord.objects.filter(app_name=app_name,
                                          deploy_status="DeployPass", test_status='TestPass', publish_status=0).exists():
        return HttpResponse(json.dumps(result), content_type='application/json')
    else:
        first_apps = get_relation(app_name)
        second_apps = list()
        for app in first_apps:
            second_apps.append(
                [app + '__' + base_app for base_app in get_relation(app)])
        search_apps = [app_name + '__' +
                       app for app in first_apps] + second_apps
        all_apps = list()
        for x in search_apps:
            if x and isinstance(x, list):
                all_apps = all_apps + x
            elif x and isinstance(x, str):
                all_apps.append(x)
        result = {'status': 0, 'msg': 'ok', 'data': all_apps}
        return HttpResponse(json.dumps(result, cls=ExtendJSONEncoder), content_type='application/json')


@permission_required('usermanage.menu_deploymanage_versionpublish', raise_exception=True)
def add_publish(request):
    """add_publish. 添加服务上线表单接口

    Args:
        request:
    """
    app_name = request.POST.get('app_name', '')
    description = request.POST.get('description', '')
    deploy_env = request.POST.get('deploy_env', '')
    deploy_versions = request.POST.get('deployVersions', [])
    dependences = request.POST.get('dependences', {})
    data = remove_str_space([app_name, deploy_env])
    format_dependences = list()
    result = {'status': 1, 'msg': 'error', 'data': []}
    if DeployAppPublishRecord.objects.filter(app_name=data[0], publish_status=0).exists():
        result['msg'] = '该服务存在上线未完成版本,暂时无法提交'
        return HttpResponse(json.dumps(result, cls=ExtendJSONEncoder), content_type='application/json')
    if dependences:
        dependences = json.loads(dependences)
        for k, v in dependences.items():
            app_keys = k.replace('-value', '')
            check_app = app_keys.split('__')[-1]
            if not AppInfo.objects.filter(app_name=check_app).exists():
                result['msg'] = '依赖包：{0} 不存在'.format(check_app)
                return HttpResponse(json.dumps(result, cls=ExtendJSONEncoder), content_type='application/json')
            obj = AppInfo.objects.get(app_name=check_app)
            v = v.replace(' ', '')  # 清除空格
            if len(v) == 0:
                # 先使用上次成功发布版本分支,否则使用master分支
                if AppVersionRecord.objects.filter(service_relation=app_name+"__"+check_app).exists():
                    v = AppVersionRecord.objects.filter(
                        service_relation=app_name+"__"+check_app)[0].release_branch
                else:
                    v = 'master'
            git_parser = GitParser()
            result = git_parser.check_repo_is_valid(
                obj.git_repo_address, pom_file=None, branch=v)
            if result['status'] != 0:
                result['msg'] = '依赖包：{0}   '.format(app_keys) + result['msg']
                return HttpResponse(json.dumps(result, cls=ExtendJSONEncoder), content_type='application/json')
            else:
                format_dependences.append(app_keys + ':' + v)
    deploy_versions = json.loads(deploy_versions)
    if len(deploy_versions) < 1:
        result['msg'] = '参数错误,必须提供提测版本'
        return HttpResponse(json.dumps(result, cls=ExtendJSONEncoder), content_type='application/json')
    deploy_ids = list()
    versions_obj = list()
    for version in deploy_versions:
        if DeployAppRecord.objects.filter(
                app_name=data[0],
                auto_test_branch=version,
                test_status="TestPass",
                publish_status=0,
                deploy_status="DeployPass").exists():
            record = DeployAppRecord.objects.filter(
                    app_name=data[0],
                    auto_test_branch=version,
                    test_status="TestPass",
                    publish_status=0,
                    deploy_status="DeployPass")[0]
            versions_obj.append(record)
            deploy_ids.append(str(record.deploy_id))
        else:
            result['msg'] = '版本：{0} 不符合上线规范,状态必须满足：部署成功,测试通过, 未上线'.format(
                version)
            return HttpResponse(json.dumps(result, cls=ExtendJSONEncoder), content_type='application/json')
    try:
        with transaction.atomic():
            create_time = datetime.now(pytz.timezone('Asia/Shanghai'))
            publish_record = DeployAppPublishRecord.objects.create(
                app_name=data[0],
                deploy_ids=','.join(deploy_ids),
                create_time=create_time,
                create_user=request.user.username,
                deploy_status='Pending',
                description=description,
                dependence_str=','.join(format_dependences))
            env = DeployAppEnv.objects.get(env_name=deploy_env)
            publish_record.publish_env.add(env)
            DeployAppPublishRecordDetail.objects.create(
                deploy_app_publish_record=publish_record)
            flag = False
            for version in versions_obj:
                # 提交上线单锁定测试分支代码uuid位置
                version_info = AppInfo.objects.get(app_name=version.app_name)
                version.publish_status = 2
                git_parser = GitParser()
                try:
                    version.auto_test_branch_uuid = git_parser.get_branch_commit_uuid(
                    version_info.git_repo_address, version.auto_test_branch)[0]
                except Exception as e:
                    result['msg'] = '无法获取提测分支信息: ' + version.auto_test_branch
                    flag = True
                    break
                version.save()
            if flag:
                raise Exception(result['msg'])
            result['status'] = 0
            result['msg'] = '添加成功'
            msg_tmp = '''
            >上线服务：<font color="comment"> {0} </font>*
            >上线功能：<font color="comment"> {1}.... </font>*
            >上线人： <font color="comment"> {2} </font>*
            >上线版本：<font color="comment"> {3} </font>*
            >提测时间：<font color="comment"> {6} </font>*
            '''
    except Exception as e:
        logger.error(str(e))
        result['status'] = 1
        if not flag:
            result['msg'] = '数据库连接失败'
    return HttpResponse(json.dumps(result, cls=ExtendJSONEncoder), content_type='application/json')

@permission_required('usermanage.menu_deploymanage_versionpublish', raise_exception=True)
def merge_conflict_publish(request):
    publish_id = request.POST.get('publish_id','')
    result = {'status':1,'msg': '撤销失败','data':''}
    if not publish_id:
        result['msg'] = '无效提交数据'
    else:
        publish_id = int(publish_id)
        if not DeployAppPublishRecord.objects.filter(publish_id=publish_id).exists():
            result['msg'] = '不存在该上线记录'
        else:
            publish_record = DeployAppPublishRecord.objects.get(publish_id=publish_id)
            publish_record.merge_status=0
            publish_record.save()
            result['status'] = 0
            result['msg'] = '确认成功'
    return HttpResponse(json.dumps(result),content_type="application/json")





@permission_required('usermanage.menu_deploymanage_versionpublish', raise_exception=True)
def delete_publish(request):
    publish_id = request.POST.get('publish_id','')
    result = {'status':1,'msg': '撤销失败','data':''}
    if not publish_id:
        result['msg'] = '无效提交数据'
    else:
        publish_id = int(publish_id)
        if not DeployAppPublishRecord.objects.filter(publish_id=publish_id).exists():
            result['msg'] = '不存在该上线记录'
        else:
            publish_record = DeployAppPublishRecord.objects.get(publish_id=publish_id)
            app_info = AppInfo.objects.get(app_name=publish_record.app_name)
            app_record = None
            if AppVersionRecord.objects.filter(publish_id=publish_id).exists():
                app_record = AppVersionRecord.objects.get(app_name=publish_record.app_name, publish_id=publish_id)
                if app_record.release_branch:
                    logger.info('撤销发布分支: '+app_record.release_branch)
                    print('撤销发布分支: '+app_record.release_branch)
                    git_parser = GitParser()
                    _r = git_parser.delete_remote_branch(app_info.git_repo_address,app_record.release_branch)
                    if _r['status'] != 0:
                        return HttpResponse(json.dumps(result),content_type="application/json")
            test_records = list()
            for record_id in publish_record.deploy_ids.split(','):
                if DeployAppRecord.objects.filter(deploy_id=record_id).exists():
                    test_records.append(DeployAppRecord.objects.get(deploy_id=record_id))
            try:
                with transaction.atomic():
                    if app_record:
                        app_record.delete()
                    for _record in test_records:
                        _record.publish_status = 0
                        _record.save()
                    publish_record.delete()
            except Exception as e:
                logger.error(str(e))
                print(str(e))
                result['msg'] = '撤销失败: ' + str(e)
            result['status'] = 0
            result['msg'] = '已撤销'
        return HttpResponse(json.dumps(result, cls=ExtendJSONEncoder), content_type='application/json')




@permission_required('usermanage.menu_deploymanage_versionpublish', raise_exception=True)
def pass_publish(request):
    """pass_publish. 服务上线通过接口

    Args:
        request:
    """
    publish_id = request.POST.get('publish_id', '')
    result = {'status': 1, 'msg': '无权限操作', 'data': []}
    if not DeployAppPublishRecord.objects.filter(publish_id=int(publish_id)).exists():
        result['msg'] = '记录不存在'
    else:
        if request.user.is_superuser or Users.objects.filter(username=request.user.username, groups__name="测试组").exists():
            update_time = datetime.now(pytz.timezone('Asia/Shanghai'))
            try:
                with transaction.atomic():
                    publish_record = DeployAppPublishRecord.objects.get(
                        publish_id=int(publish_id))
                    publish_record.update_time = update_time
                    publish_record.publish_status = 1
                    publish_record.publish_user = request.user.username
                    publish_record.save()
                    for _id in publish_record.deploy_ids.split(','):
                        deploy_record = DeployAppRecord.objects.get(
                            deploy_id=int(_id))
                        deploy_record.publish_status = 1
                        deploy_record.publish_time = update_time
                        deploy_record.save()
                    result['status'] = 0
                    result['msg'] = '操作成功'
            except Exception as e:
                logger.error(str(e))
                result['msg'] = '数据库操作报错'
    return HttpResponse(json.dumps(result, cls=ExtendJSONEncoder), content_type='application/json')


@permission_required('usermanage.menu_deploymanage_versionpublish',
                     raise_exception=True)
def get_publish(request):
    """get_publish. 获取服务上线详情接口

    Args:
        request:
    """
    publish_id = remove_str_space(request.POST.get('publish_id', None))
    result = {'status': 1, 'msg': '内部错误', 'data': []}
    if not publish_id:
        result['msg'] = '不存在此记录'
    else:
        publish_id = int(publish_id)
        if not DeployAppPublishRecord.objects.filter(publish_id=publish_id).exists():
            result['msg'] = '不存在此记录'
        else:
            record = DeployAppPublishRecord.objects.get(publish_id=publish_id)
            env = None
            record_detail = None
            release_branch = None
            deploy_branches = list()
            deploy_features = list()
            try:
                env = record.publish_env.get()
            except Exception as e:
                logger.error(str(e))
            try:
                record_detail = DeployAppPublishRecordDetail.objects.get(
                    deploy_app_publish_record=record)
            except Exception as e:
                logger.error(str(e))
            try:
                for _id in record.deploy_ids.split(','):
                    deploy_branches.append(DeployAppRecord.objects.get(
                        deploy_id=int(_id)).auto_test_branch)
                    deploy_features.append(DeployAppRecord.objects.get(
                        deploy_id=int(_id)).feature_branch)
            except Exception as e:
                logger.error(str(e))

            try:
                release_branch = AppVersionHistory.objects.get(
                    publish_id=publish_id, app_name=record.app_name).release_name
            except Exception as e:
                logger.error(str(e))

            r = DeployAppPublishRecord.objects.filter(publish_id=publish_id).values(
                    'app_name',
                    'dependence_str',
                    'create_time',
                    'update_time',
                    'create_user',
                    'publish_user',
                    'description')[0]
            r.update({'env_name': env.env_name,
                      'image_url': record_detail.release_image_url,
                      'deploy_ids': ','.join(deploy_branches),
                      'release_branch': release_branch,
                      'deploy_features':','.join(deploy_features),
                      })
            result = {'status': 0, 'msg': 'ok', 'data': r}
    return HttpResponse(json.dumps(result, cls=ExtendJSONEncoder), content_type='application/json')





@permission_required('usermanage.menu_deploymanage_versionpublish')
def clear_and_merge_branch(request):
    publish_id =  request.POST.get('publish_id','')
    check_box = request.POST.get('check_box','')
    check_box = json.loads(check_box)
    #action = ['release','test','feature']
    result = {'status':1,'msg':'参数错误','data':[]}
    if publish_id:
        publish_id = int(publish_id)
        if DeployAppPublishRecord.objects.filter(publish_id=publish_id,create_user=request.user.username).exists() or request.user.is_superuser:
            pass
        else:
            result = {'status':1,'msg':'只有上线人和管理员才能进行合并','data':[]}
            return HttpResponse(json.dumps(result), content_type='application/json')
        if DeployAppPublishRecord.objects.filter(publish_id=publish_id,publish_status=1).exists():
            test_branches = list()
            feature_branches = list()
            publish_record = DeployAppPublishRecord.objects.get(publish_id=publish_id,publish_status=1)
            for _id in publish_record.deploy_ids.split(','):
                _r = DeployAppRecord.objects.get(deploy_id=int(_id))
                test_branches.append(_r.auto_test_branch)
                feature_branches.append(_r.feature_branch)
            app_info = AppInfo.objects.get(app_name=publish_record.app_name)
            for _action  in check_box:
                git_parser = GitParser()
                if _action == 'release':
                    app_version = AppVersionRecord.objects.get(app_name=app_info.app_name,publish_id=publish_id)
                    print(app_version.release_branch)
                elif _action == "test":
                    for t in test_branches:
                        do_delete = True
                        if AppBranchStatus.objects.filter(app_name=app_info.app_name,branch_name=t).exists():
                            if AppBranchStatus.objects.filter(app_name=app_info.app_name,branch_name=t,is_deleted=1).exists():
                                do_delete = False
                        else:
                            AppBranchStatus.objects.create(
                                    app_name=app_info.app_name,
                                    branch_name=t,
                                    branch_type=1,
                                    create_by=request.user.username
                                    )
                        if do_delete:
                            _r = git_parser.delete_remote_branch(app_info.git_repo_address,t)
                            if _r['status'] == 0:
                                branch_status = AppBranchStatus.objects.get(app_name=app_info.app_name,branch_name=t)
                                branch_status.is_deleted = 1
                                branch_status.save()
                            else:
                                return HttpResponse(json.dumps(result), content_type='application/json')
                elif _action == "feature":
                    for t in feature_branches:
                        print(t)
            result = {'status':0,'msg':'操作成功','data':[]}
        else:
            result['msg'] = '记录不存在或版本未上线'
    return HttpResponse(json.dumps(result), content_type='application/json')
    


def check_base_and_update(base_name):
    """check_base_and_update. 检测所有服务的父包是否有更新，直接从master获取

    Args:
        base_name:  父工程名,默认为： nextop-base-parent
    """
    maven_path = SysConfig().get('maven_bin_path', '')
    result = {'status': 1, 'msg': '公共包 {0} 未定义不存在'.format(
        base_name), 'data': []}
    create_time = datetime.strftime(datetime.now(), '%Y%m%d.%H%M%S')
    release_name = 'auto.release.' + create_time+'-RELEASE'
    if not AppInfo.objects.filter(app_name=base_name).exists():
        return result
    else:
        base_app = AppInfo.objects.get(app_name=base_name)
        base_app_version = None
        if AppVersionRecord.objects.filter(app_name=base_name).exists():
            base_app_version = AppVersionRecord.objects.filter(app_name=base_name)[
                0]
        git_parser = GitParser()
        master_uuid = git_parser.get_branch_commit_uuid(
            base_app.git_repo_address, 'master')[0]
        if base_app_version and base_app_version.release_branch_uuid == master_uuid:
            # 返回空表示无变化
            return dict()
        else:
            logger.info('开始更新基础包代码')
            git_parser = GitParser()
            r = git_parser.deploy_jar_to_repo(
                    base_name,
                    base_app.git_repo_address,
                    'master',
                    release_name,
                    base_app.pom_xml_path,
                    maven_path
                    )
            r['data'] = r['data'] + [master_uuid]
            return r


def resolve_dependence_str(dependence_str, app_name):
    """resolve_dependence_str. 处理依赖字符串,只支持处理两层依赖关系

    Args:
        dependence_str: 依赖关系及分支数据
        app_name: 主服务名

    Returns:
        first:  第一层依赖及其分支 {'project':'branch_name'}
        second: 第二层依赖及其分支列表 {'project':['branch_name']}
    """
    de_list = dependence_str.split(',')
    first = list()
    second = list()
    for de in de_list:
        if de.startswith(app_name+'__'):
            first.append(de)
        else:
            second.append(de)
    second_project_branches = dict()
    first_project_branches = dict()
    if second:
        for s in second:
            project_branch = s.split('__')
            p_b = project_branch[-1].split(':')
            if p_b[0] not in second_project_branches:
                second_project_branches[p_b[0]] = [p_b[1]]
            else:
                if p_b[1] not in second_project_branches[p_b[0]]:
                    second_project_branches[p_b[0]].append(p_b[1])
    if first:
        for f in first:
            project_branch = f.split('__')
            p_b = project_branch[-1].split(':')
            first_project_branches[p_b[0]] = p_b[1]
    return first_project_branches, second_project_branches


def deploy_dependence_jar_and_push(dependence_str, app_name, publish_id, release_name):
    """deploy_dependence_jar_and_push. 
    编译依赖包deploy到maven仓库并将pom文件修改push到git仓库
    先处理第二层依赖，然后处理第一层依赖。

    Args:
        dependence_str: 依赖包关系数据
        app_name:  主服务名
        publish_id:  上线记录id
        release_name: 主服务生成的release版本名

    Returns:
        result: {'status':0,'msg':'','data':[]}
    """
    maven_path = SysConfig().get('maven_bin_path', '')
    first, second = resolve_dependence_str(dependence_str, app_name)
    do_app = dict()
    for k in dependence_str.split(','):
        if app_name != k.split('__')[0]:
            k = k.split('__')
            if k[0] not in do_app:
                do_app[k[0]] = [k[1].split(':')[0]]
            else:
                _v = k[1].split(':')[0]
                if _v not in do_app[k[0]]:
                    do_app[k[0]].append(_v)

    for k, v in second.items():
        service_relation = app_name + '__' + k
        reset = True  # 是否需要重写版本标记
        have_history = True
        if AppVersionHistory.objects.filter(app_name=k,
                                            service_relation=service_relation).exists():
            # 如果存在该服务对应依赖包发布记录版本,则获取版本历史最近的一个记录,对比是否需要更新
            app_version = AppVersionHistory.objects.filter(app_name=k,
                                                           service_relation=service_relation).order_by('-create_time')[0]
            app_info = AppInfo.objects.filter(app_name=app_version.app_name)[0]
            if len(v) == 1 and v[0] == app_version.release_name:
                # 如果版本未变,且代码位置一样
                git_parser = GitParser()
                release_uuid = git_parser.get_branch_commit_uuid(
                    app_info.git_repo_address, v[0])[0]
                if release_uuid == app_version.release_uuid:
                    have_history = False
                    if not AppVersionRecord.objects.filter(release_branch=app_version.release_name, app_name=k, service_relation=service_relation).exists():
                        # 不存在版本则创建,存在则更新publish_id
                        AppVersionRecord.objects.create(
                                release_branch=app_version.release_name,
                                release_branch_uuid=release_uuid,
                                app_name=k,
                                publish_id=publish_id,
                                service_relation=service_relation
                                )
                    else:
                        new_version = AppVersionRecord.objects.get(
                            release_branch=app_version.release_name, app_name=k, service_relation=service_relation)
                        new_version.publish_id = publish_id
                        new_version.save()
                    reset = False
                    print('二层依赖服务已存在且代码未发生改变并生成了jar 包则不再编译')
                    # 处理完毕,继续处理依赖包
        if AppVersionRecord.objects.filter(publish_id=publish_id, app_name=k, service_relation=service_relation).exists() and have_history:
            # 如果已经deploy,则不再进行二次编译deploy
            _record = AppVersionRecord.objects.filter(
                publish_id=publish_id, app_name=k, service_relation=service_relation)[0]
            if len(_record.maven_jar_version) > 5:
                logger.info('已存在该上线版本记录并生成了jar 包则不再编译')
                print('已存在该上线版本记录并生成了jar 包则不再编译')
                reset = False
        if reset:
            jarName = release_name + '-RELEASE'
            project, versions = k, v
            project_info = AppInfo.objects.get(app_name=project)
            pom_path = project_info.pom_xml_path
            repoName = project_info.git_repo_address
            git_parser = GitParser()
            base_app = AppVersionRecord.objects.get(
                app_name='nextop-base-parent')
            # 合并代码并生成依赖包release分支
            _r = git_parser.merge_branch_and_create_release(
                    repoName,
                    versions,
                    release_name,
                    project_info.app_name
                    )
            if _r['status'] != 0:
                return _r
            git_parser = GitParser()
            # 设置parent并提交
            _r = git_parser.deploy_jar_to_repo(
                    project_info.app_name,
                    repoName,
                    release_name,
                    jarName,
                    pom_path,
                    maven_path,
                    action=1,
                    push=True,
                    parent=base_app.app_name,
                    parent_jar_version=base_app.maven_jar_version,
                    is_deploy=False
                    )
            logger.info('替换parent完毕不编译')
            if _r['status'] != 0:
                return _r
            git_parser = GitParser()
            # 设置自己的服务版本并提交和deploy
            _r = git_parser.deploy_jar_to_repo(
                    project_info.app_name,
                    repoName,
                    release_name,
                    jarName,
                    pom_path,
                    maven_path,
                    action=0,
                    push=True,
                    )
            logger.info('生成服务版本并编译和入库')
            if _r['status'] != 0:
                return _r
            else:
                try:
                    create_time = datetime.now(pytz.timezone('Asia/Shanghai'))
                    git_parser = GitParser()
                    new_uuid = git_parser.get_branch_commit_uuid(
                        repoName, release_name)[0]
                    # 如果版本记录不存在，则创建该服务版本
                    if not AppVersionRecord.objects.filter(
                            app_name=project_info.app_name,
                            publish_id=publish_id,
                            # release_branch=release_name,
                            service_relation=service_relation
                    ).exists():
                        with transaction.atomic():
                            AppVersionRecord.objects.create(
                                app_name=project_info.app_name,
                                create_time=create_time,
                                publish_id=publish_id,
                                maven_jar_version=jarName,
                                service_relation=service_relation,
                                release_branch=release_name,
                                release_branch_uuid=new_uuid
                            )
                    else:
                        a = AppVersionRecord.objects.filter(
                            app_name=project_info.app_name,
                            publish_id=publish_id,
                            release_branch=release_name,
                            service_relation=service_relation
                        )[0]
                        a.release_branch_uuid = new_uuid
                        a.release_branch = release_name
                        a.service_relation = service_relation
                        a.publish_id = publish_id
                        a.save()
                    # 如果历史记录不存在,则创建此记录
                    if not AppVersionHistory.objects.filter(
                            app_name=project_info.app_name,
                            publish_id=publish_id,
                            release_name=release_name,
                            service_relation=service_relation
                    ).exists():
                        with transaction.atomic():
                            AppVersionHistory.objects.create(
                                app_name=project_info.app_name,
                                create_time=create_time,
                                publish_id=publish_id,
                                maven_jar_version=jarName,
                                service_relation=service_relation,
                                release_name=release_name,
                                release_uuid=new_uuid
                            )
                    else:
                        with transaction.atomic():
                            h = AppVersionHistory.objects.get(
                                app_name=project_info.app_name,
                                publish_id=publish_id,
                                service_relation=service_relation,
                                release_name=release_name
                            )
                            h.release_uuid = new_uuid
                            h.save()
                    print('保存版本信息')
                except Exception as e:
                    print(str(e))
                    logger.error(str(e))
                # 保存版本信息

    # 生成第一层依赖包版本
    for k, v in first.items():
        service_relation = app_name + '__' + k
        reset = True  # 是否需要重写版本标记
        have_history = True
        v = [v]  # 此处版本需为list类型
        if AppVersionHistory.objects.filter(app_name=k,
                                            service_relation=service_relation).exists():
            # 如果存在该服务对应依赖包发布记录版本,则获取版本历史最近的一个记录,对比是否需要更新
            app_version = AppVersionHistory.objects.filter(app_name=k,
                                                           service_relation=service_relation).order_by('-create_time')[0]
            app_info = AppInfo.objects.filter(app_name=app_version.app_name)[0]
            if len(v) == 1 and v[0] == app_version.release_name:
                # 如果版本未变,且代码位置一样
                git_parser = GitParser()
                release_uuid = git_parser.get_branch_commit_uuid(
                    app_info.git_repo_address, v[0])[0]
                if release_uuid == app_version.release_uuid:
                    if not AppVersionRecord.objects.filter(release_branch=app_version.release_name, app_name=k, service_relation=service_relation).exists():
                        # 不存在版本则创建,存在则更新publish_id
                        AppVersionRecord.objects.create(
                                release_branch=app_version.release_name,
                                release_branch_uuid=release_uuid,
                                app_name=k,
                                publish_id=publish_id,
                                service_relation=service_relation
                                )
                    else:
                        new_version = AppVersionRecord.objects.get(
                            release_branch=app_version.release_name, app_name=k, service_relation=service_relation)
                        new_version.publish_id = publish_id
                        new_version.save()
                    reset = False
                    have_history = False
                    # 处理完毕,继续处理依赖包
        if AppVersionRecord.objects.filter(publish_id=publish_id, app_name=k, service_relation=service_relation).exists() and have_history:
            # 如果已经deploy,则不再进行二次编译deploy
            _rcd = AppVersionRecord.objects.filter(
                publish_id=publish_id, app_name=k, service_relation=service_relation)[0]
            if len(_rcd.maven_jar_version) > 5:
                logger.info('已存在该上线版本记录并生成了jar 包则不再编译')
                reset = False
        if reset:
            jarName = release_name + '-RELEASE'
            project, versions = k, v[0]  # 此处版本需为str类型
            project_info = AppInfo.objects.get(app_name=project)
            pom_path = project_info.pom_xml_path
            repoName = project_info.git_repo_address
            git_parser = GitParser()
            base_app = AppVersionRecord.objects.get(
                app_name='nextop-base-parent')
            # 合并代码并生成依赖包release分支
            _r = git_parser.merge_branch_and_create_release(
                repoName,
                [versions],
                release_name,
                project_info.app_name
            )
            if _r['status'] != 0:
                return _r
            git_parser = GitParser()
            # 设置parent并提交
            _r = git_parser.deploy_jar_to_repo(
                    project_info.app_name,
                    repoName,
                    release_name,
                    jarName,
                    pom_path,
                    maven_path,
                    action=1,
                    push=True,
                    parent=base_app.app_name,
                    parent_jar_version=base_app.maven_jar_version,
                    is_deploy=False
                    )
            logger.info('替换parent完毕不编译')
            if _r['status'] != 0:
                return _r

            # 如果存在二层依赖，则设置依赖包版本并提交
            if k in do_app:
                second_apps = dict()
                for s_app in do_app[k]:
                    s_obj = AppVersionRecord.objects.get(
                        app_name=s_app, publish_id=publish_id, service_relation=app_name+'__'+s_app)
                    second_apps[s_app] = s_obj.maven_jar_version
                git_parser = GitParser()
                _r = git_parser.deploy_jar_to_repo(
                        project_info.app_name,
                        repoName,
                        release_name,
                        jarName,
                        pom_path,
                        maven_path,
                        action=2,
                        push=True,
                        is_deploy=False,
                        relation_project=second_apps
                        )
                if _r['status'] != 0:
                    return _r

            # 设置自己的服务版本并提交和deploy
            git_parser = GitParser()
            _r = git_parser.deploy_jar_to_repo(
                    project_info.app_name,
                    repoName,
                    release_name,
                    jarName,
                    pom_path,
                    maven_path,
                    action=0,
                    push=True,
                    )
            logger.info('生成服务版本并编译和入库')
            if _r['status'] != 0:
                return _r
            else:
                try:
                    create_time = datetime.now(pytz.timezone('Asia/Shanghai'))
                    git_parser = GitParser()
                    new_uuid = git_parser.get_branch_commit_uuid(
                        repoName, release_name)[0]
                    # 如果版本记录不存在，则创建该服务版本
                    if not AppVersionRecord.objects.filter(
                            app_name=project_info.app_name,
                            publish_id=publish_id,
                            # release_branch=release_name,
                            service_relation=service_relation
                    ).exists():
                        with transaction.atomic():
                            AppVersionRecord.objects.create(
                                app_name=project_info.app_name,
                                create_time=create_time,
                                publish_id=publish_id,
                                maven_jar_version=jarName,
                                service_relation=service_relation,
                                release_branch=release_name,
                                release_branch_uuid=new_uuid
                            )
                    else:
                        a = AppVersionRecord.objects.filter(
                            app_name=project_info.app_name,
                            publish_id=publish_id,
                            release_branch=release_name,
                            service_relation=service_relation
                        )[0]
                        a.release_branch_uuid = new_uuid
                        a.release_branch = release_name
                        a.service_relation = service_relation
                        a.publish_id = publish_id
                        a.save()
                    # 如果历史记录不存在,则创建此记录
                    if not AppVersionHistory.objects.filter(
                            app_name=project_info.app_name,
                            publish_id=publish_id,
                            release_name=release_name,
                            service_relation=service_relation
                    ).exists():
                        with transaction.atomic():
                            AppVersionHistory.objects.create(
                                app_name=project_info.app_name,
                                create_time=create_time,
                                publish_id=publish_id,
                                maven_jar_version=jarName,
                                service_relation=service_relation,
                                release_name=release_name,
                                release_uuid=new_uuid
                            )
                    else:
                        with transaction.atomic():
                            h = AppVersionHistory.objects.get(
                                app_name=project_info.app_name,
                                publish_id=publish_id,
                                service_relation=service_relation,
                                release_name=release_name
                            )
                            h.release_uuid = new_uuid
                            h.save()
                    print('保存版本信息')
                except Exception as e:
                    print(str(e))
                    logger.error(str(e))
                # 保存版本信息

    return {'status': 0, 'msg': 'ok', 'data': []}


@permission_required('usermanage.menu_deploymanage_versionpublish',
                     raise_exception=True)
def create_release(request):
    """create_release. 生成版本接口

    Args:
        request:
    """
    publish_id = request.POST.get('publish_id', '')
    result = {'status': 1, 'msg': '操作失败,请联系管理员', 'data': []}
    create_time = datetime.now(pytz.timezone('Asia/Shanghai'))
    if not DeployAppPublishRecord.objects.filter(publish_id=int(publish_id)).exists():
        result['msg'] = '无该上线记录'
    else:
        publish_id = int(publish_id)
        publish_record = DeployAppPublishRecord.objects.get(
            publish_id=int(publish_id))
        username = request.user.username
        release_name = 'auto.release.' + \
            datetime.strftime(datetime.now(), '%Y%m%d.%H%M%S') + \
            '.'+publish_record.app_name.split('-')[-1]


        if publish_record.create_user == username or Users.objects.filter(username=username, groups__name="测试组").exists() or request.user.is_superuser:
            base_name = 'nextop-base-parent'
            # 检查基础包是否有更新
            r = check_base_and_update(base_name)
            if len(r) > 1 and r['status'] == 0:
                try:
                    with transaction.atomic():
                        if AppVersionRecord.objects.filter(app_name=base_name).exists():
                            old_v = AppVersionRecord.objects.get(
                                app_name=base_name)
                            # 保存版本历史
                            AppVersionHistory.objects.create(
                                    publish_id=old_v.publish_id,
                                    app_name=old_v.app_name,
                                    create_time=create_time,
                                    maven_jar_version=old_v.maven_jar_version,
                                    service_relation=old_v.service_relation,
                                    release_name=old_v.release_branch,
                                    release_uuid=old_v.release_branch_uuid
                                    )
                            old_v.delete()

                        AppVersionRecord.objects.update_or_create(
                            app_name=base_name,
                            publish_id=int(publish_id),
                            create_time=create_time,
                            feature_branch='master',
                            test_branch='master',
                            test_branch_uuid=r['data'][2],
                            release_branch=r['data'][0],
                            release_branch_uuid=r['data'][2],
                            publish_tag='',
                            maven_jar_version=r['data'][1]
                        )
                    result = r
                except Exception as e:
                    logger.error(str(e))
                    result['mesg'] = '基础包版本保存失败'
            elif len(r) == 0:
                # 基础包无变化,所有服务都用一个版本
                result = {'status': 0, 'msg': '处理成功', 'data': []}
            else:
                # 生成基础包报错
                return HttpResponse(json.dumps(r, cls=ExtendJSONEncoder), content_type='application/json')
            # 先生成服务release分支
            deploy_records = [DeployAppRecord.objects.get(
                deploy_id=id) for id in publish_record.deploy_ids.split(',')]
            branches_uuid = dict()
            branches = list()
            for _r in deploy_records:
                branches.append(_r.auto_test_branch)
                branches_uuid[_r.auto_test_branch] = _r.auto_test_branch_uuid
            app_info = AppInfo.objects.get(app_name=publish_record.app_name)
            merge_status = 0
            # 如果历史记录没有则生成该服务的发布分支
            if not AppVersionHistory.objects.filter(app_name=app_info.app_name, publish_id=publish_id).exists():
                print('开始创建发布分支')
                git_parser = GitParser()
                r = git_parser.merge_branch_and_create_release(
                    app_info.git_repo_address,
                    branches,
                    release_name,
                    app_name=app_info.app_name,
                    branches_uuid=branches_uuid)
                if r['status'] != 0:
                    #合并失败状态设置为1
                    merge_status = 1
                    #return HttpResponse(json.dumps(r, cls=ExtendJSONEncoder), content_type='application/json')
                AppVersionHistory.objects.create(
                        app_name=app_info.app_name,
                        publish_id=publish_id,
                        release_name=release_name,
                        create_time=create_time
                        )
            if not AppVersionRecord.objects.filter(app_name=app_info.app_name).exists():
                _release = release_name
                if AppVersionHistory.objects.filter(app_name=app_info.app_name, publish_id=publish_id).exists():
                    history = AppVersionHistory.objects.filter(
                        app_name=app_info.app_name, publish_id=publish_id)[0]
                    _release = history.release_name
                AppVersionRecord.objects.create(
                        app_name=app_info.app_name,
                        publish_id=publish_id,
                        release_branch=_release,
                        create_time=create_time
                        )
            else:
                new_app = AppVersionRecord.objects.get(
                    app_name=app_info.app_name)
                new_app.publish_id = publish_id
                #new_app.release_branch = release_name
                new_app.create_time = create_time
                new_app.save()

            #如果是前端工程则直接返回
            if app_info.app_type == 0:
                result = {'status':0, 'msg':'操作成功','data':[]}
                try:
                    with transaction.atomic():
                        publish_record = DeployAppPublishRecord.objects.get(publish_id=publish_id)
                        publish_record.release_status = 1
                        publish_record.merge_status = merge_status
                        print('分支合并状态：'+str(merge_status))
                        publish_record.save()
                except Exception as e:
                    result['status'] = 1
                    result['msg'] = '数据库保存失败'
                    logger.error(str(e))
                return HttpResponse(json.dumps(result, cls=ExtendJSONEncoder), content_type='application/json')
            current_app = AppVersionRecord.objects.get(
                app_name=app_info.app_name)

            jarName = current_app.release_branch + '-RELEASE'
            maven_path = SysConfig().get('maven_bin_path', '')
            #生成parent包版本
            base_app = AppVersionRecord.objects.get(app_name='nextop-base-parent')
            git_parser = GitParser()
            _r = git_parser.deploy_jar_to_repo(
                current_app.app_name,
                app_info.git_repo_address,
                current_app.release_branch,
                jarName,
                app_info.pom_xml_path,
                maven_path,
                action=1,
                push=True,
                parent=base_app.app_name,
                parent_jar_version=base_app.maven_jar_version,
                is_deploy=False
            )
            if _r['status'] != 0:
                return HttpResponse(json.dumps(_r, cls=ExtendJSONEncoder), content_type='application/json')
            
            # 生成依赖包版本,已生成的不会再进行打包push
            result = deploy_dependence_jar_and_push(
                publish_record.dependence_str, publish_record.app_name, publish_id, current_app.release_branch)

            if result['status'] == 0:
                # 最终修改服务的依赖包版并提交到release
                do_app = dict()
                _dependence_str = publish_record.dependence_str
                for d in _dependence_str.split(','):
                    d = d.split('__')
                    if current_app.app_name == d[0]:
                        be_add = d[1].split(':')[0]
                        if current_app.app_name not in do_app:
                            do_app[current_app.app_name] = [be_add]
                        else:
                            if be_add not in do_app[current_app.app_name]:
                                do_app[current_app.app_name].append(be_add)
                if len(do_app[current_app.app_name]) >= 1:
                    _apps = dict()
                    for a in do_app[current_app.app_name]:
                        s_obj = AppVersionRecord.objects.get(
                            app_name=a, publish_id=publish_id, service_relation=current_app.app_name+'__'+a)
                        _apps[a] = s_obj.maven_jar_version
                    git_parser = GitParser()
                    jarName = current_app.release_branch + '-RELEASE'
                    maven_path = SysConfig().get('maven_bin_path', '')

                     #修改依赖包
                    _r = git_parser.deploy_jar_to_repo(
                        current_app.app_name,
                        app_info.git_repo_address,
                        current_app.release_branch,
                        jarName,
                        app_info.pom_xml_path,
                        maven_path,
                        action=2,
                        push=True,
                        is_deploy=False,
                        relation_project=_apps
                    )
                    if _r['status'] != 0:
                        return HttpResponse(json.dumps(_r, cls=ExtendJSONEncoder), content_type='application/json')
                    else:
                        try:
                            with transaction.atomic():
                                publish_record = DeployAppPublishRecord.objects.get(publish_id=publish_id)
                                publish_record.release_status = 1
                                publish_record.save()
                                result['msg'] = '已生成'
                        except Exception as e:
                            result['msg'] = '数据库保存失败'
                            logger.error(str(e))
                        des = publish_record.description
                        if len(des) > 10:
                            des = des[:10]
                        send_user = Users.objects.get(
                            username=publish_record.create_user)
                        create_time = datetime.now(
                            pytz.timezone('Asia/Shanghai'))
                        msg_tmp = '''>上线服务：<font color="comment"> {0} </font>*>上线功能：<font color="comment"> {1}.... </font>*>上线人： <font color="comment"> {2} </font>*>上线分支：<font color="comment"> {3} </font>*>上线时间：<font color="comment"> {4} </font>*'''.format(current_app.app_name, des, send_user.display, current_app.release_branch, create_time)
                        tel_list = list()
                        if send_user.tel_num:
                            tel_list.append(send_user.tel_num)
                        send_at = ''
                        for phone in tel_list:
                            send_at = send_at + '@' + phone
                        msg_tmp = msg_tmp + send_at
                        send_message('版本上线通知', msg_tmp,
                                     PUBLISH_DINGTALK_WEB_HOOK, tel_list)
            return HttpResponse(json.dumps(result, cls=ExtendJSONEncoder), content_type='application/json')
        else:
            result['msg'] = '无操作权限'
    return HttpResponse(json.dumps(result, cls=ExtendJSONEncoder), content_type='application/json')
