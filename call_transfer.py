# -*- coding: UTF-8 -*-

import ccutils
from mysql_wrapper import Conf
db = ccutils.db
def call_transfer(con, *args):
        if not args:  # 外联情况
                info = con.getInfo()
        else:
                info = args[0]  # 这里用info命名不太恰当但是历史原因就暂时info(时间上是ev--event)
                return

        # print('info.serialize() is {}'.format(info.serialize()))
        caller = info.getHeader('caller-caller-id-number')
        callee = info.getHeader('variable_sip_to_user')  # 或者caller-destination-number
        uuid = info.getHeader('variable_uuid')
        domain_name = info.getHeader('variable_domain_name')
        if not domain_name:
                domain_name = info.getHeader('variable_sip_to_host')
        elif not domain_name:
                domain_name = info.getHeader('channel-network-addr')
        ccutils.multiset(con,['CDR(calltype)',1,'CALLTYPE',1])
        sql = 'select StaffId from '+Conf.R_STAFFIDEXTEN_SHARE + 'where Exten = {}'.format(callee)
        row = db.get(sql)
        trans_staffid = row.StaffId if row else 0
        if trans_staffid:
                ccutils.multiset(con, ['StaffId',trans_staffid,'CDR(StaffId)',trans_staffid])

                sql = "select a.Id ,a.ClassifId from {} a join crm_department b on a.DepartmentId=b.Id " \
                      "join {} c on b.Id=c.DepartmentId where a.`Status`=1 and c.StaffId={};".format(Conf.K_PROJECTINFO, Conf.CRM_USERINFO, trans_staffid)
                row = db.get(sql)
                # 此外线号码没有绑定项目
                if row:
                        # 归属分类Id
                        ClassifId = row.ClassifId
                        # 归属项目Id
                        ProjectId = row.Id
                        ccutils.multiset(con, ['CDR(ClassifId)',ClassifId,'CDR(projectid)',ProjectId,'PROID',ProjectId,'ClassifId',ClassifId])
        ccutils.set_variable(con, 'CDR(DIALSTATUS)', 'answered')
        con.executeAsync('bridge','sofia/internal/${}%${}/'.format(callee, domain_name), uuid)

        # $agi->agi_exec('Dial', "SIP/$callee,30");

        return True


