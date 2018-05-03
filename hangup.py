# -*- coding: UTF-8 -*-
import ccutils
import math
import datetime
from mysql_wrapper import Conf
import re


db = ccutils.db
getInfoByStaffId = ccutils.getInfoByStaffId
microtime = ccutils.microtime


def hangup(con, ev):
	'''
	:param info:
	:param call_type:
	:return:
	对应于agi_hangup.php
	'''
	id1 = id2 = id3 = None
	cdrs = ccutils.gen_cdrs(ev)
	# 呼叫记录插入
	customerid = cdrs[18] #这一句加上是为了倒数第二行的customerid赋值的时候有值
	id1 = ccutils.cdr_insert(ev, *cdrs)

	#下面部分的代码设置CallResult字段(此字段是asrcall表的字段增加到cdr字段里)来表示普通呼入呼出成功还是失败
	if re.search('Normal_Clearing', ev.getHeader('Hangup-Cause'), re.I):
		call_result = 'success'
	else:
		call_result = ev.getHeader('Hangup-Cause')
	sql = 'update cdr set CallResult = "{}" where id={}'.format(call_result, id1)
	db.execute(sql)
	DIALSTATUS = ev.getHeader('variable_CDR(DIALSTATUS)')
	if DIALSTATUS and 'answer' in DIALSTATUS.lower():
		# 获取通话时长
		answeredtime = ev.getHeader('Caller-Channel-Answered-Time')
		if not answeredtime:
			queue_start_time = int(ev.getHeader('QUEUETIME_START'))
			if queue_start_time:
				answeredtime = microtime(True) - queue_start_time
			else:
				# 通话保持后，恢复通话
				answeredtime = ev.getHeader('variable_billsec')

		recordfile = ev.getHeader('variable_record_file')
		if recordfile and answeredtime:
			caller = ev.getHeader('Caller-Caller-ID-Number')
			calltype = cdrs[21]
			if calltype == '0' or calltype == 0:
				caller = ev.getHeader('variable_OUTLINE')
			extenNum = ev.getHeader('variable_my_caller')
			CodeId_1 = ev.getHeader('variable_CodeId_1')
			CodeId_2 = ev.getHeader('variable_CodeId_2')
			ast_recordfile = recordfile
			PROID = cdrs[16]
			StaffId = cdrs[17]
			customerid = cdrs[18]
			callee = cdrs[2]
			uuid = cdrs[14]
			ClassifId = cdrs[19]
			CompanyId = cdrs[20]
			now = datetime.datetime.now()
			endtime = now.strftime('%Y-%m-%d %H:%M:%S')
			reply = con.api('global_getvar', 'recordings_dir')
			path = reply.getBody()
			hold_sec = int(answeredtime)/1000000
			sql = '''insert into {} (Type, StaffId, CustomerId, ProjectId, ClassifId, CallType, CallerNum, CalleeNum, Uniqueid, FileName, Path, HoldSec, CreateTime, CompanyId, exten, codeid_1, codeid_2) values (0, {}, {}, {}, {}, {}, {}, {}, '{}', '{}','{}',{}, '{}', {}, {}, {}, {})
						  '''.format(Conf.L_RECORD, StaffId, customerid, PROID, ClassifId, calltype, caller, callee, uuid, ast_recordfile,path, hold_sec, endtime, CompanyId, extenNum, CodeId_1, CodeId_2)
			sql = sql.replace('None', '0')
			id2 = db.execute(sql)
			# 如果来电转接号码为外线号码，生成CDR
			TRFER_PHONE = ev.getHeader('TRFER_PHONE')
			if TRFER_PHONE:
				DIALEDTIME = ev.getHeader('DIALEDTIME')
				sql = '''
							insert into {table} (clid, src, dst, calldate, answertime, endtime, duration, billsec, duration_int, billsec_int, dcontext, disposition, uniqueid, linkedid, projectid, StaffId, customerid, ClassifId, calltype, CompanyId)
							values ({callee1}, {callee1},{TRFER_PHONE1}, DATE_ADD({endtime1}, INTERVAL-{DIALEDTIME1}SECOND), DATE_ADD({endtime1}, INTERVAL,-{answeredtime1}SECOND), {endtime1}, {DIALEDTIME1}, {answeredtime1}, {DIALEDTIME1}, {answeredtime1}, '','ANSWERED', {uuid1}, {uuid1},
							{PROID1}, '', {customerid1}, {ClassifId1}, '0', {CompanyId1})
						'''.format(table = Conf.CDR,callee1=callee, TRFER_PHONE1=TRFER_PHONE,
							   endtime1=endtime,
							   DIALEDTIME1=DIALEDTIME,
							   answeredtime1=answeredtime, uuid1=uuid, PROID1=PROID,
							   customerid1=customerid,
							   ClassifId1=ClassifId, CompanyId1=CompanyId)
				id3 = db.execute(sql)
	type = ev.getHeader('variable_Type')
	if type == 2:
		sql = 'update {} set CallResult  = {} where id = {}'.format(Conf.T_BASEINFO, DIALSTATUS, customerid)
		db.execute(sql)
	ccutils.cdr_complement(ev, id1)
	return (id1,id2, id3)
