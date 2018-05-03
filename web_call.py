# -*- coding: UTF-8 -*-

from ccutils import *
from mysql_wrapper import Conf

def web_call(con, *args):
        if not args:  # 外联情况
                info = con.getInfo()
        else:
                info = args[0]  # 这里用info命名不太恰当但是历史原因就暂时info(时间上是ev--event)

        caller = info.getHeader('caller-caller-id-number')
        callee = info.getHeader('variable_sip_to_user')
        uuid = info.getHeader('Unique-ID')

        ProjectId = info.getHeader('variable_PROID')  #获得归属项目id
        con.execute('answer', uuid)
        # 呼入类型
        multiset(con, ['CDR(calltype)',1,'CALLTYPE',1])
        # 黑名单判断，如果是，则自动挂机
        is_black(caller, True)
        # 通过外线号码获取其所属于的项目(正常运行的项目)
        sql = "select QueueName, ClassifId from"+Conf.K_PROJECTINFO +"where id='{}'".format(ProjectId)
        row = db.get(sql)
        # 归属分类id
        ClassifId = row.ClassifId if row else 0
        # 归属项目id
        ProjectId = row.Id if row else 0
        # 队列名称
        queue_name = row.QueueName if row else ''
        multiset(con, ['CDR(ClassifId)',ClassifId,'CDR(ProjectId)',ProjectId,'PROID',ProjectId])
        # 检查该客户是否是服务客户，如果是，则获取其相应的资料
        sql = 'select Id,StaffId from'+Conf.CUSTOMER_BASEINFO+'where DelBatchId=0  and  phone={} and ProjectId="{}" limit 1;'.format(caller,ProjectId)
        row = db.get(sql)
        if row and row.Id > 0:
                set_variable(con, 'CUSID', row.Id)
        set_variable(con, 'U_QUEUE', queue_name)
        # exit(0) todo 原来的php代码里有这一句不知道啥意思
