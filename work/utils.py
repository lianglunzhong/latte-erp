# coding:utf-8
import sys
import time
import gc

from django.db import connection

from lib.models import ScriptLog
from lib.utils import get_now
from script_configs import ScriptTimings


# 定时器
def timing_start(times):
    while True:
        now_minute = get_now().minute
        now_hour = get_now().hour

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
    # 通过在shell命令行增加参数, 来确定脚本是立刻执行还是定时执行
    # upervisor中默认没有参数, 所以supervisor始终为定时执行
    start_now = False
    if len(sys.argv) == 2 and sys.argv[1] == 'now':
        start_now = True

    # 脚本的执行时间, 保存在our_config中, key为方法名称
    timings = ScriptTimings.script_dict[fun.__name__]['timings']

    while True:
        # 如果不是立刻开始, 说明是需要进行循环跑的
        if not start_now:
            timing_start(timings)

        # 在方法执行之前, 进行脚本创建
        script_log = ScriptLog.objects.create(process=fun.__name__, date_from=get_now(), running_status=2)

        connection.close()

        # 执行方法, 如果发生异常, 则捕获异常, 并结束循环
        try:
            fun()
        except Exception, e:
            script_log.date_to = get_now()
            script_log.running_status = 0
            script_log.content = e
            script_log.save()
            break

        # 方法执行结束, 进行善后处理
        script_log.date_to = get_now()
        script_log.running_status = 1
        script_log.run_time = round((script_log.date_to - script_log.date_from).total_seconds() / 60.0, 2)
        script_log.save()

        connection.close()
        sys.stdout.flush()
        gc.collect()

        # 如果是要立刻开始的, 说明是手动跑的, 这次跑完, 则中断循环
        if start_now:
            break
        time.sleep(60)
