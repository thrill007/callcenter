# -*- coding: UTF-8 -*-

import ccutils
from mysql_wrapper import Conf
import datetime
import time
import math
from queue_save_number import *
db = ccutils.db

def queue_hangup(con, ev):
        sys_mode = ccutils.read_configuration('sys_mode')
        caller = ev.getHeader('caller-caller-id-number')
        callee = ev.getHeader('channel-caller-id-number')
        uuid = ev.getHeader('Unique-ID')
        channel = ev.getHeader('Other-Leg-Channel-Name')
        # CustomId = ev.getHeader('variable_CustomId)') #todo 这是原来的php对应的但是获取不到这个变量所以用下面一句代替
        CustomId = ev.getHeader('variable_CDR(customerid)')
        # 如果客户ID不存在 直接退出
        if not CustomId: return True
        ClassifId = ev.getHeader('variable_ClassifId')
        StaffId = ev.getHeader('variable_StaffId')
        REASON = ev.getHeader('variable_REASON')
        REASON = REASON if REASON else ''
        CompanyId = ev.getHeader('variable_CompanyId')
        IsAnswer = ev.getHeader('variable_IsAnswer')
        calltype = ev.getHeader('variable_CALLTYPE')
        PROID = ev.getHeader('variable_PROID')
        recordfile = ev.getHeader('variable_record_file')
        now = datetime.datetime.now()
        endtime = now.strftime('%Y-%m-%d %H:%M:%S')
        if StaffId and not PROID:
                result = ccutils.getInfoByStaffId(StaffId)
                if result:
                        CompanyId = result['CompanyId']
                        ClassifId = result['ClassifId']
                        PROID = result['ProjectId']
                        ccutils.multiset(con, ['CDR(CompanyId)',CompanyId,'CDR(ClassifId)',ClassifId,'CDR(projectid)', PROID])

        if IsAnswer == 1 or not len(REASON):
        # 排队的
                if not  IsAnswer and not len(REASON):
                        REASON = '100'
                        ccutils.set_variable(con, 'CDR(customerid)', CustomId)
                # 呼叫记录插入
                cdrs = ccutils.gen_cdrs(ev)
                ccutils.cdr_insert(ev, *cdrs)
                # 获取通话时常
                answeredtime = 0
                queue_start_time = int(float(ev.getHeader('variable_QUEUETIME_START')))
                if queue_start_time:
                        answeredtime = ccutils.microtime(True) - queue_start_time
                else:
                        answeredtime = ev.getHeader('variable_CDR(billsec)')
                if not answeredtime:
                        answeredtime = '0000-00-00 00:00:00'
                # 接通
                # 号码呼叫状态置为通话结束
                # 关机、停机、拒接、无效号码、无应答插入到回收池
                sql = 'insert ignore into' + Conf.FORECAST_DATA_SHARE_LOG + '(Id,ClassifId,ProjectId,CompanyId,BatchId,StaffId,Name,Phone,Address,Sex,Email,CallOutStatus,CallResult,AnswerTime,UpdateTime,CreateTime)'
                sql += "select Id, ClassifId,ProjectId,CompanyId,BatchId,'{}',Name,Phone,Address,Sex,Email,3,'{}','{}','{}',CreateTime from {} where id='{}' ;".format(StaffId, REASON, answeredtime, endtime, Conf.FORECAST_DATA_TEMP, CustomId)
                db.execute(sql)
                # 从预测池中删除
                sql = "delete from {} where id='{}';".format(Conf.FORECAST_DATA_TEMP, CustomId)
                db.execute(sql)
                if recordfile:
                        extenNum = ev.getHeader('variable_CDR(Exten)')
                        ast_recodefile = recordfile
                        sql = 'insert into' + Conf.L_RECORD + '(Type,StaffId,CustomerId,ProjectId,ClassifId,CallType,CallerNum,CalleeNum,Uniqueid,FileName,Path,HoldSec,CreateTime,CompanyId,exten)values'
                        sql += "(0,'{}','{}','{}','{}',{},'{}','{}',{},'','{}','{}','{}','{}','{}');".format(StaffId, CustomId, PROID, ClassifId, calltype, caller, callee, uuid, ast_recodefile, answeredtime, endtime, CompanyId, extenNum)
                        db.execute(sql)

        else:
                sql = "select  Id, ClassifId,ProjectId,CompanyId,BatchId,Name,Phone,Address,Sex,Email,CreateTime from"+Conf.FORECAST_DATA_TEMP + "where id={} ;".format(CustomId)
                row = db.get(sql)
                if not row:
                        return True
                Id = row.Id
                ClassifId = row.ClassifId
                CompanyId = row.CompanyId
                ProjectId = row.ProjectId
                BatchId = row.BatchId
                Name = row.Name
                Phone = row.Phone
                Address = row.Address
                Sex = row.Sex
                Email = row.Email
                CreateTime = row.CreateTime
                # 关机。停机。拒接。无效号码。无应答 插入 到回收池
                sql = 'insert ignore into'+Conf.FORECAST_DATA_SHARE_LOG + '( Id,ClassifId,ProjectId,CompanyId,BatchId,StaffId,Name,Phone,Address,Sex,Email,CallOutStatus,CallResult,AnswerTime,UpdateTime,CreateTime)values'
                sql += "({}, '{}','{}','{}','{}',0,'{}','{}','{}','{}','{}',0,'{}',0,'{}','{}');".format(Id, ClassifId, ProjectId, CompanyId, BatchId, Name, Phone, Address, Sex, Email, REASON, endtime, CreateTime)
                db.execute(sql)
                # 插入cdr
                # 呼叫发起时间戳
                orig_time = ev.getHeader('variable_Origtime')
                duration = time.time() - orig_time
                call_date = orig_time.strftime('%Y-%m-%d %H:%M:%S')
                duration_int = math.ceil(duration)
                disposition = 'NO ANSWER'
                # 托管用户预测未接通不计话单
                if not sys_mode:
                        sql = 'INSERT INTO'+Conf.CDR+ '(`clid`, `src`, `dst`, `calldate`, `answertime`, `endtime`, `duration`, `billsec`,`duration_int`,`billsec_int`, `dcontext`, `disposition`, `uniqueid`, `linkedid`, `projectid`, `StaffId`, `customerid`, `ClassifId`, `calltype`,`channel`,`dstchannel`,CompanyId)values'
                        sql += "('{}', '{}','{}','{}', '0000-00-00 00:00:00','{}', {}, 0,{},0, 'from-autocall', '{}', '{}', '{}','{}', 0, '{}', '{}', 3,'{}','','$CompanyId');".format(caller, caller, Phone, call_date, endtime, duration, duration_int, disposition, uuid, uuid, ProjectId, CustomId, ClassifId, channel)
                        db.execute(sql)

        return True