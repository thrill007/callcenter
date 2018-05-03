# -*- coding: UTF-8 -*-

import ccutils
from mysql_wrapper import Conf
import datetime
import re

db = ccutils.db


def queue_save_number(con, *args):
        ev = con.getInfo()
        StaffId = ev.getHeader('variable_StaffId')
        caller = ev.getHeader('caller-caller-id-number')
        # todo 对应于$callee = $agi->param['Exten'];--调用php的时候url传入一个字符串参数,通过*分割成CustomerId & StaffId
        # todo 但是对于fs版本的此函数，必须显示的分别传入CustomerId & StaffId
        callee = ev.getHeader('variable_sip_to_user')
        uuid = ev.getHeader('variable_uuid')

        CustomId = ev.getHeader('variable_CDR(customerid)')
        result = ccutils.getInfoByStaffId(StaffId)
        if not result:  return True
        ClassifId = result['ClassifId']
        PROID = result['ProjectId']
        # 通话结束，保存请按1，丢弃请挂机。
        args = '1 3 3 5000 # ' + Conf.SOUND_PATH + 'Ivr_018.wav ' + Conf.SOUND_PATH + 'empty.gsm data1 \\d+'
        ret = con.execute('play_and_get_digits', args)
        con.setEventLock('1')
        datakey = ccutils.get_variable(con, 'play_and_get_digits', 'data1')
        if datakey == '1':
                sql = "select CompanyId,phone,name,address from" + Conf.FORECAST_DATA_TEMP + "where id='{}';".format(CustomId)
                row = db.get(sql)
                CompanyId = row.CompanyId if row else 0
                phone = row.phone if row else 0
                name = row.name if row else ''
                address = row.address if row else ''
                if not CompanyId:
                        phone = callee
                        sql = "select CompanyId from {} where id='{}' ;".format(Conf.K_PROJECT_CLASSIFICATION, ClassifId)
                        row = db.get(sql)
                        CompanyId = row.CompanyId if row else 0
                # 获取归属部门ID
                sql = "select departmentid from" + Conf.CRM_USERINFO + "where staffid='{}' ;".format(StaffId)
                row = db.get(sql)
                DepartmentId = row.departmentid if row else 0
                sql = 'insert into' + Conf.CUSTOMER_BASEINFO + '(Id,AssignStatus,DepartmentId,CompanyId,StaffId,ProjectId,Name,Phone,Address,UpdateTime,CreateTime)'
                sql += "values('{}',1,'{}','{}','{}','{}','{}','{}','{}','{}','{}')".format(CustomId, DepartmentId,
                                                                                        CompanyId, StaffId,
                                                                                        PROID, name, phone,
                                                                                        address,
                                                                                        datetime.datetime.now(),
                                                                                        datetime.datetime.now())
                sql += 'ON DUPLICATE KEY UPDATE UpdateTime="{}"'.format(datetime.datetime.now())
                db.execute(sql)
                # 保存成功，用户号码为：
                con.executeAsync('playback', Conf.SOUND_PATH + 'Ivr_019.wav')
                con.execute('say', 'en number iterated {}'.format(phone))

        # if index == 3:
        #         break
        # index += 1

        return True
