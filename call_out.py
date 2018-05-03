# -*- coding: UTF-8 -*-

from ccutils import *
from mysql_wrapper import Conf

def call_out(con, *args):
	if not args:  #外联情况
		info = con.getInfo()
	else:
		info = args[0]  #这里用info命名不太恰当但是历史原因就暂时info(时间上是ev--event)
	if not info: return None
	# 软电话外呼情况
	caller = info.getHeader('variable_my_caller') #主叫
	PROID = info.getHeader('variable_CDR(PROID)')  # 获取归属项目Id
	callee = info.getHeader('variable_my_callee') #被叫
	uuid = info.getHeader('Unique-ID')
	# 非国际 本地判断
	if callee[0:2] != '00':
		callee = get_num(callee)
	#分机通过软电话直接外呼
	if PROID == '0' and len(caller) == 4:
	# 通过分机获取工号
		sql = 'select StaffId from {} where Exten = {}'.format(Conf.R_STAFFIDEXTEN_SHARE, caller)
		StaffId = db.get(sql).StaffId if db.get(sql) else 0
		# 如果没有绑定坐席或者坐席未在线
		if not StaffId or not is_online(StaffId): return None

		set_variable(con, 'CDR(StaffId)', StaffId)
		sql = "select a.Id,a.ClassifId,b.CompanyId from"+Conf.K_PROJECTINFO +"a join" + Conf.CRM_DEPARTMENT + "b on a.DepartmentId=b.Id join"+Conf.CRM_USERINFO+"c on b.Id=c.DepartmentId where a.`Status`=1 and c.StaffId={};".format(StaffId)
		row = db.get(sql)
		if row:
			PROID = row.Id
			ClassifId = row.ClassifId
			CompanyId = row.CompanyId
			multiset(con, ['CDR(CcompanyId)',CompanyId,'CDR(projectid)',PROID, 'CDR(ClassifId)', ClassifId])
		else:
			# todo 原来基于AS的逻辑是跳到dialplan的nonproject去执行, 但是nonproject没有找到，所以fs的dialplan里也暂时是个空的extension没做啥动作,并且后续如果有动作都要挪到outbound server里做不再转到dialplan(否则有些乱)
			# con.executeAsync('execute_extension', 'noproject')
			con.executeAsync('transfer', 'noproject')
			return None

		sql = "select id from {} where DelBatchId=0 and phone={} and projectid='{}' ;".format(Conf.CUSTOMER_BASEINFO, callee, PROID)
		row = db.get(sql)
		customerid = row.id if row else 0
		if not customerid:
			customerid = get_generator_id(callee, PROID)
		vars = ['CDR(customerid)',customerid,'CompanyId',CompanyId,'PROID',PROID,'StaffId',StaffId,'CUSID',customerid,'ClassifId',ClassifId]
		multiset(con, vars)
		###############################
		# 外呼号码
		sql = "select a.Num from {} a join {} b on a.Num=b.Num where  a.staffid={}  and b.Enabled=1 and a.type=0;".format(Conf.R_STAFFIDNUM_SHARE, Conf.K_NUMINFO_SHARE, StaffId)
		row = db.get(sql)
		Sysnum = row.Num if row else 0
		if not Sysnum:
			con.executeAsync('playback', Conf.SOUND_PATH + 'Ivr_010.wav')
			dial_str = None
		else:
			set_variable(con, 'Sysnum', Sysnum)
			dial_str = info.getHeader('variable_dial_str')
	else: #web 外呼
		CompanyId = info.getHeader('variable_CDR(CompanyId)')
		StaffId = info.getHeader('variable_CDR(StaffId)')  # 获取工号
		customerid = info.getHeader('variable_CDR(customerid)')  # 获取客户ID
		ClassifId = info.getHeader('variable_CDR(ClassifId)')
		call_type = info.getHeader('variable_CDR(calltype)')
		dcontext = info.getHeader('variable_CDR(dcontext)')
		dial_str = info.getHeader('variable_dial_str')
		Sysnum = info.getHeader('variable_Sysnum')  # 获取系统号码
		vars = ['CompanyId', CompanyId, 'CDR(StaffId)', StaffId, 'CDR(ClassifId)', ClassifId, 'CDR(projectid)',
			PROID, 'CDR(customerid)', customerid, 'CDR(calltype)', 0, 'CDR(Exten)', caller, 'calltype', 0]
		multiset(con, vars)

	# 外线号码
	set_variable(con,'OUTLINE',Sysnum)
	return (dial_str, callee, caller, StaffId, uuid)