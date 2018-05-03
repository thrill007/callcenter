# -*- coding: UTF-8 -*-
import ccutils
from mysql_wrapper import Conf
import datetime
db = ccutils.db
now = datetime.datetime.now
def queue_answer(con, *args):
        # IsForeCSave = GLOBALS['IsForeCSave']
        info = args[0]
        callee = info.getHeader('variable_sip_from_user')
        uuid = info.getHeader('variable_uuid')
        CustomId = info.getHeader('variable_CDR(customerid)') #获取客户ID
        CustomId = CustomId if CustomId else 0
        QueueName = info.getHeader('variable_QueueName')
        '''
        这里要通过MEMBERINTERFACE获取坐席分机，但是在呼入情况下info是针对客户那一端的channel的不是针对坐席这一端的
        所以通过info.getHeader()来获取是'牛头不对马尾'，呼出应该没问题
        '''
        member = info.getHeader('variable_MEMBERINTERFACE') #获取分机
        starttime = ccutils.microtime(True)
        # 获取工号
        sql = 'select StaffId from' + Conf.R_STAFFIDEXTEN_SHARE + 'where Exten = {}'.format(member)
        row = db.get(sql)
        StaffId = row.StaffId if row else 0
        vars = ['CDR(Exten)', member, 'IsAnswer',1,'QUEUETIME_START',ccutils.microtime(True)]
        ccutils.multiset(con, vars)
        isIvrLogin = '0'
        if not StaffId:
                # 如果staffid为空有可能是座席F5刷新导致的，临时的解决为从登录日志表中获取最新的一次登录绑定
                sql = "select UserName from {} where exten={} and IsSuccess=1 order by id desc limit 1;".format(Conf.l_CRM_LOGIN, member)
                row = db.get(sql)
                StaffId = row.StaffId if row else 0
                if StaffId:
                        ccutils.set_variable(con,'StaffId', 0)
        online_time = 0
        if StaffId:
                ccutils.multiset(con, ['StaffId',StaffId, 'CDR(StaffId)',StaffId])
                sql = 'select UpdateTime from' + Conf.R_STAFFIDEXTEN_SHARE + 'where StaffId={} limit 1'.format(StaffId)
                row = db.get(sql)
                online_time = row.UpdateTime if row else 0
                if online_time == 1:
                        # 如果是语音登录则记录最后一次接通的被叫号码
                        isIvrLogin = 1
                        sql = "update {} set lastnum={} where queue_name='{}' and staffid={};".format(Conf.FORECAST_QUEUE,callee, QueueName,StaffId)
                        db.execute(sql)
            # 摘机标识
        if isIvrLogin and online_time==1:
                ccutils.set_variable(con, 'SHARED(SRC_IsSave, {})', member, isIvrLogin)
                # 参数字符串
                ccutils.set_variable(con, 'SHARED(SHARE_STRING, {})',member, int(CustomId)*int(StaffId))
        ccutils.set_variable(con, 'CDR(customerid)', CustomId)
        # 号码呼叫状态置为通话中
        sql = "update"+Conf.FORECAST_DATA_TEMP+"set calloutStatus=2,updatetime='{}' where id={};".format(now(), CustomId)
        db.execute(sql)
        return (StaffId,)
