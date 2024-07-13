import simplejson as json
from decimal import Decimal
from datetime import datetime, date, timedelta
from functools import singledispatch
import requests
from datetime import datetime
import logging

logger = logging.getLogger('default')


@singledispatch
def convert(o):
    raise TypeError('can not convert type')


@convert.register(datetime)
def _(o):
    return o.strftime('%Y-%m-%d %H:%M:%S')


@convert.register(date)
def _(o):
    return o.strftime('%Y-%m-%d')


@convert.register(timedelta)
def _(o):
    return o.__str__()


@convert.register(Decimal)
def _(o):
    return float(o)


class ExtendJSONEncoder(json.JSONEncoder):
    """ExtendJSONEncoder. json处理类
    """

    def default(self, obj):
        try:
            return convert(obj)
        except TypeError:
            return super(ExtendJSONEncoder, self).default(obj)


class ExtendJSONEncoderFTime(json.JSONEncoder):
    def default(self, obj):
        try:
            if isinstance(obj, datetime):
                return obj.isoformat(' ')
            else:
                return convert(obj)
        except TypeError:
            return super(ExtendJSONEncoderFTime, self).default(obj)


def remove_str_space(data):
    """remove_str_space. 去除入参中字符串包含的空格

    Args:
        data: 字符串或列表
    """
    if isinstance(data, str):
        return data.replace(' ', '')
    elif isinstance(data, list):
        _data = list()
        for _d in data:
            if isinstance(_d, str):
                _d = _d.replace(' ', '')
            _data.append(_d)
        data = _data
    return data


def send_message(title, message, webhook, telList):
    headers = {"Content-Type": "application/json;charset=utf-8"}
    message = message.replace('*', '\n\n')
    data = {
        "msgtype": "markdown",
        "markdown": {
            "title": title,
            "text": message
        },
        "at": {
            "atMobiles": telList,
            "isAtAll": 'false'

        }
    }
    try:
        rsp = requests.post(url=webhook, headers=headers,
                            data=json.dumps(data))
        _r = json.loads(rsp.text)
        if _r['errcode'] != 0:
            logger.error(str(_r))
    except Exception as e:
        logger.error(str(e))


def check_upper_and_underline(data: str):
    CAPITAL = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L",
               "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z"]
    def _isupper(s):
        return True if s in CAPITAL else False

    if "_" in data:
        return True
    return True if len(list(filter(_isupper, data))) > 0 else False



if __name__ == "__main__":
    #data = [1, 'hello world', 0, True]
    #print(remove_str_space(data))
    s = 'helloworldX'
    print(check_upper_and_underline(s))
