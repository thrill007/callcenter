# -*- coding: UTF-8 -*-

import ccutils
from mysql_wrapper import Conf
db = ccutils.db

def queue_groupcall_answer(con, *args):
        if not args:  # 外联情况
                ev = con.getInfo()
        else:
                ev = args[0]  # 这里用info命名不太恰当但是历史原因就暂时info(时间上是ev--event)
                return

        # $IsForeCSave = & $GLOBALS['IsForeCSave'];  #todo 不知道这个变量何用??
        callee = ev.getHeader('variable_sip_to_user')  # 或者caller-destination-number
        CustomId = ev.getHeader('variable_CustomId')
        QueueName = ev.getHeader('QueueName')
        memberinterface = ev.getHeader('variable_MEMBERINTERFACE')  #获取分机
        member = memberinterface[:4]
        start_time = ccutils.microtime(True)
        # 获取工号
        sql = 'select StaffId from {} where Exten={} limit 1'.format(Conf.R_STAFFIDEXTEN_SHARE, member)
        row = db.get(sql)
        StaffId = row.StaffId if row else 0
        ccutils.multiset(con, ['CDR(Exten)',member,'IsAnswer',1])
        isIvrLogin = '0'
        if not StaffId:
                # 如果staffid为空 有可能 是座席F5刷新导致的，临时的解决为从登录日志表中获取最新的一次登录绑定
                sql = "select UserName from {} where exten='{}' and IsSuccess=1 order by id desc limit 1;".format(Conf.l_CRM_LOGIN, member)
                row = db.get(sql)
                StaffId = row.StaffId if row else 0
                if not StaffId:
                        ccutils.set_variable(con,'StaffId', 0)

        if StaffId:
                ccutils.multiset(con, ['StaffId',StaffId,'CDR(StaffId)',StaffId])
                sql = 'select UpdateTime from {} where StaffId={} limit 1'.format(Conf.R_STAFFIDEXTEN_SHARE, StaffId)
                row = db.get(sql)
                online_time = row.UpdateTime if row else 0
        ccutils.set_variable(con,'CDR(customerid)',CustomId)
        return True