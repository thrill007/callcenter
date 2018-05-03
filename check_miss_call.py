# -*- coding: UTF-8 -*-

import ccutils
from mysql_wrapper import Conf
db = ccutils.db

def check_miss_call(con, *args):
        if not args:  # 外联情况
                info = con.getInfo()
        else:
                info = args[0]  # 这里用info命名不太恰当但是历史原因就暂时info(实际上是ev--event)

        caller = info.getHeader('caller-caller-id-number')
        callee = info.getHeader('caller-destination-number')  # 或者caller-destination-number
        if 'gw+' in callee: callee = callee[3:]
        uuid = info.getHeader('variable_uuid')

        StaffId = info.getHeader('variable_StaffId')
        DIALSTATUS = info.getHeader('variable_CDR(DIALSTATUS)')
        customerid = info.getHeader('variable_CUSID')
        customerid = customerid if customerid else 0
        PROID = info.getHeader('variable_PROID')

        # 未接来电记录
        # 如果没有接通才进行记录
        if not DIALSTATUS or ('answer' not in DIALSTATUS.lower()):
        # 新客户
                if not StaffId:
                        sql = "select StaffId from" + Conf.R_STAFFIDNUM_SHARE + "where num={} and type=1  order by rand() limit 1".format(callee)
                        row = db.get(sql)
                        StaffId = row.StaffId if row else 0

                # 如果有工号 说明是记忆轮回
                if StaffId:
                        sql = "select CompanyId,DepartmentId from" + Conf.CRM_USERINFO + "where staffid = {};".format(StaffId)
                        row = db.get(sql)
                        CompanyID = row.CompanyId if row else 0
                        DepartmentId = row.DepartmentId if row else 0
                        sql = " select name from" + Conf.CUSTOMER_BASEINFO + "where id={} ".format(customerid)
                        row = db.get(sql)
                        name = row.name if row else 0
                        sql = 'insert into' + Conf.L_MISSEDCALL + '(`CompanyID`, `DepartmentID`, `GroupID`, `StaffId`,`CustomerName`, `PhoneNum`,  `CalleeNum`, `Status`, `UpdateTime`, `CreateTime`)values'
                        sql += "({},{},0,{},{},{},{},'0',now(),now())".format(CompanyID, DepartmentId, StaffId, name, caller, callee)
                        db.execute(sql)

        return True


