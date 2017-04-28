# coding:utf-8
import csv
import sys
import pprint

import pytz
from dateutil.parser import parse
from django.utils import timezone
from django.http import HttpResponse

import datetime
import gc
import time
from django.db import connection


def pp(content):
    '''pprint的简单使用
    '''
    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(content)


def eparse(value, offset=None):
    '''将str类型的时间转化成: 含时区的datetime
    easy parse的简称 eparse
    
    value: str
    offset: str '+08:00' value是东八区时间, 但字符串中没有时区信息
                '+00:00' value是UTC时间, 但字符串中没有时区信息
    如果传的是date类型, 需要自己补足时分秒
            offset=" 00:00:00+08:00"
    
    有时区的字符串: '2016-01-01 12:59:12 +08:00'
    无时区的字符串: '2016-01-01 12:59:12'  这种类型需要手动传递后缀'+00:00'或对应时区
    '''
    try:
        if offset:
            value += offset
        t = parse(value)
    except Exception, e:
        t = None
    return t

def add8(value, microsecond=False):
    """接收utc时间, 返回东八区的字符串时间, 如果时间格式有误, 则返回空字符串"""
    try:
        if not microsecond:
            value = value.replace(microsecond=0)
        tz = pytz.timezone('Asia/Shanghai')
        t = value.astimezone(tz).strftime("%Y-%m-%d %H:%M:%S")
    except:
        t = ''
    return t


def get_now(microsecond=False, utc=False):
    '''获取东八区的时间, 包含时区信息, 默认不展示毫秒信息
    >>>print get_now()
    2016-05-19 15:07:36+08:00

    建议所有获取当前时间的方法都使用这个时间
    '''
    
    now = timezone.now()

    if not utc:
        tz = pytz.timezone('Asia/Shanghai')
        now = now.astimezone(tz)

    if not microsecond:
        now = now.replace(microsecond=0)
    return now

def ee(e):
    '''输出异常的信息, 建议使用这个来输出所有异常
    '''
    msg =  e.__class__.__name__ + ': ' + e.message
    return msg

#设置函数超时的装饰器
from functools import wraps
import signal
def set_timeout(seconds=10):
    def decorator(func):
        def _handle_timeout(signum, frame):
            raise Exception

        def wrapper(*args, **kwargs):
            signal.signal(signal.SIGALRM, _handle_timeout)
            signal.alarm(seconds)
            try:
                result = func(*args, **kwargs)
            finally:
                signal.alarm(0)
            return result
        return wraps(func)(wrapper)
    return decorator

def eu(content):
    """将传入的数据用utf-8编码"""
    if content:
        return content.encode('utf-8')
    else:
        return ''

def write_csv(filename):
    """简化csv文件的生成"""
    response = HttpResponse(content_type='text/csv')
    response.write('\xEF\xBB\xBF') 
    response['Content-Disposition'] = 'attachment; filename="%s.csv"' % filename
    writer = csv.writer(response)
    return response, writer


# 定时器
def timing_start(times):
    while True:
        now_minute = datetime.datetime.now().minute
        now_hour = datetime.datetime.now().hour

        if now_minute == 0:
            print 'Time is %s:00' % now_hour

        if type(times) == list:
            if time.strftime('%H:%M') in times:
                print '%s START' % time.strftime('%H:%M')
                break

        elif type(times) == dict:
            if (not (now_hour + times['start_hour']) % times['interval_hour']) and now_minute == times['start_minute']:
                print '%s START' % time.strftime('%H:%M')
                break
        sys.stdout.flush()

        time.sleep(45)
    return True

# 1.开始的时候就创建一个log记录 todo
# 2.根据在命令行执行的脚本, 确认是否需要立刻执行, python work_get_choies_item now #即可立刻执行脚本
# 3.结束的时候, 关闭数据库连接
# 4.脚本使用定时开始
def manage_script(fun):
    from work.script_configs import ScriptTimings
    #通过在shell命令行增加参数, 来确定脚本是立刻执行还是定时执行
    #upervisor中默认没有参数, 所以supervisor始终为定时执行
    start_now = False
    if len(sys.argv) == 2 and sys.argv[1] == 'now':
        start_now = True

    # 脚本的执行时间, 保存在our_config中, key为方法名称
    timings = ScriptTimings.script_dict[fun.__name__]['timings']

    while True:
        if start_now:
            #立刻执行, 只执行一次
            start_now = False
        else:
            #定时执行
            timing_start(timings)

        #在方法执行之前, 进行脚本创建,
        # script_log = ScriptLog.objects.create(process=fun.__name__, date_from=timezone.now(), running_status=2)

        connection.close()
        #执行方法
        fun()

        # script_log.date_to = timezone.now()
        # script_log.running_status = 1
        # script_log.run_time = round(float((script_log.date_to-script_log.date_from).total_seconds()) / 60, 2)
        # script_log.save()

        connection.close()
        sys.stdout.flush()
        gc.collect()
        time.sleep(60)