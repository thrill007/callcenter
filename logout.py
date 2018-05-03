# -*- coding: UTF-8 -*-

from mysql_wrapper import *
import  base
from ccutils import *

def logout(con, *args):
        """ 'handler' is the default function name for apps.   It can be overridden with <modname>::<function>   `session` is a session object `args` is a string with all the args passed after the module name   """
        # freeswitch.consoleLog('info', 'Answering call from Python.\n')
        # freeswitch.consoleLog('info', 'Arguments: %s\n' % args)
        if not args:  # 外联情况
                info = con.getInfo()
        else:
                info = args[0]  # 这里用info命名不太恰当但是历史原因就暂时info(时间上是ev--event)

        exten = info.getHeader('channel-caller-id-number')
        uuid = info.getHeader('Unique-ID')
        # 退出删除登录信息
        sql = 'delete from {} where Exten={}'.format(Conf.R_STAFFIDEXTEN_SHARE, exten.strip())
        print('sql is>>>>>>>>>>>>>>>{}'.format(sql))
        count = db.execute(sql)
        # 移出队列
        sql = 'select name from {}'.format(Conf.CFG_QUEUE)
        rows = db.get_all(sql)
        for row in rows:
                base.remove_queue_member(exten, row.name)
        # 退出成功
        con.executeAsync('playback', Conf.SOUND_PATH + 'Ivr_007.wav', uuid)
        return True




