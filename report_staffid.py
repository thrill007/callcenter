# -*- coding: UTF-8 -*-

import ccutils
from mysql_wrapper import Conf
db = ccutils.db
my_queue = {}
def report_staffid(con, *args):
        global my_queue
        if not args:  # 外联情况
                info = con.getInfo()
        else:
                info = args[0]  # 这里用info命名不太恰当但是历史原因就暂时info(时间上是ev--event)
                return
        caller = info.getHeader('caller-caller-id-number')
        callee = info.getHeader('variable_sip_to_user')  # 或者caller-destination-number
        uuid = info.getHeader('variable_uuid')


        # 获取分机
        member = info.getHeader('variable_MEMBERINTERFACE')
        ccutils.set_variable(con,'CDR(Exten)', member)

        # 获取工号
        sql = 'select StaffId from' + Conf.R_STAFFIDEXTEN_SHARE + 'where Exten = {}'.format(member)
        row = db.get(sql)
        StaffId = row.StaffId if row else 0
        if StaffId: ccutils.multiset(con, ['StaffId',StaffId,'CDR(StaffId)',StaffId])

        # 插入录音记录时会用到
        ccutils.multiset(con, ['CDR(DIALSTATUS)','ANSWER','QUEUETIME_START',ccutils.microtime(True)])

        return (StaffId,member)


