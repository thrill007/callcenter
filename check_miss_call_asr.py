# -*- coding: UTF-8 -*-

import ccutils
from mysql_wrapper import Conf
db = ccutils.db

def check_miss_call_asr(con, *args):
        if not args:  # 外联情况
                info = con.getInfo()
        else:
                info = args[0]  # 这里用info命名不太恰当但是历史原因就暂时info(时间上是ev--event)


        caller_id = info.getHeader('caller-caller-id-number')
        callee = info.getHeader('variable_sip_to_user')  # 或者caller-destination-number
        if 'gw+' in callee: callee = callee[3:]
        uuid = info.getHeader('variable_uuid')


        classif_id = info.getHeader('variable_CDR(ClassifId)')
        company_id = info.getHeader('variable_CDR(CompanyId)')
        project_id = info.getHeader('variable_CDR(PROID)')
        batch_id = 0 #todo 这个变量不知道如何构造
        name = info.getHeader('variable_CDR(name)') #todo 也可以通过customer_baseinfo where id=customerid来得到name，这里选择originate通过通道变量直接传送
        phone = info.getHeader('variable_CDR(phone)') #todo 可以通过customer_baseinfo where id=customerid来得到
        address = info.getHeader('variable_CDR(address)') #todo 也可以通过customer_baseinfo/FORECAST_DATA_TEMP(这是什么鬼?) where id=customerid来得到
        sex = info.getHeader('variable_CDR(sex)')
        email = info.getHeader('variable_CDR(email)')
        call_out_status = info.getHeader('variable_CDR(CallOutStataus)')
        call_result = info.getHeader('variable_CDR(CallResult)')
        update_time = info.getHeader('variable_CDR(UpdateTime)')
        create_time = info.getHeader('varialbe_CDR(CreateTime)')


        StaffId = info.getHeader('variable_StaffId')
        DIALSTATUS = info.getHeader('variable_CDR(DIALSTATUS)')
        customerid = info.getHeader('variable_CUSID')
        customerid = customerid if customerid else 0
        PROID = info.getHeader('variable_PROID')

        # 未接来电记录
        # 如果没有接通才进行记录
        if not DIALSTATUS or 'answer' not in DIALSTATUS.lower():
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
                        sql = 'insert into' + Conf.ASRCALL_NOANSWER + '(ClassifId, CompanyId, ProjectId, callerid, BatchId, Name, Phone, Address, Sex, Email, CallOutStatus, CallResult, UpdateTime, CreateTime) values'
                        sql += "({},{},{},{},{},{},{},{},{}, {}, {}, {}, now(),now())".format(classif_id, company_id, project_id, caller_id, batch_id, name, phone, address, sex, email, call_out_status, call_result, update_time, create_time)
                        db.execute(sql)

        return True


