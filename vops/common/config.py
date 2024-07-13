import logging
from django.http import HttpResponse
import traceback
import simplejson as json
from common.utils.permission import superuser_required
from django.db import transaction
from usermanage.models import Config


logger = logging.getLogger('default')


class SysConfig(object):
    def __init__(self):
        self.sys_config = {}
        self.get_all_config()

    def get_all_config(self):
        try:
            confs = Config.objects.all().values('item', 'value')
            sys_config = {}
            for items in confs:
                if items['value'] in ('false', 'False'):
                    items['value'] = False
                if items['value'] in ('true', 'True'):
                    items['value'] = True
                sys_config[items['item']] = items['value']
            self.sys_config = sys_config
        except Exception as m:
            logger.error(f"获取系统配置数据失败 {m}{traceback.format_exc()}")
            self.sys_config = {}

    def get(self, key, default_value=None):
        value = self.sys_config.get(key, default_value)
        if isinstance(value, str) and value.strip() == '':
            return default_value
        return value

    def set(self, key, value):
        if value is False:
            db_value = 'false'
        elif value is True:
            db_value = 'true'
        else:
            db_value = value
        obj, created = Config.objects.update_or_create(
            item=key, defaults={"value": db_value})
        if created:
            self.sys_config.update({key: value})

    def replace(self, configs):
        result = {'status': 0, 'msg': 'ok', 'data': []}
        try:
            with transaction.atomic():
                self.purge()
                Config.objects.bulk_create([Config(item=items['key'].strip(),
                                                   value=str(items['value']).strip()) for items in json.loads(configs)])

        except Exception as m:
            logger.error(traceback.format_exc())
            result['status'] = 1
            result['msg'] = str(m)
        finally:
            self.get_all_config()
        return result

    def purge(self):
        """purge. 清除所有系统配置缓存
        """
        try:
            with transaction.atomic():
                Config.objects.all().delete()
                self.sys_config = {}
        except Exception as m:
            logger.error(f"清除缓存失败 {m}{traceback.format_exc()}")


@superuser_required
def change_config(request):
    configs = request.POST.get('configs')
    vops_conf = SysConfig()
    result = vops_conf.replace(configs)
    return HttpResponse(json.dumps(result), content_type='application/json')
