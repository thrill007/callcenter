# -*- coding: UTF-8 -*-
import ccutils
from mysql_wrapper import Conf
from base import *
from ivr import *

db = ccutils.db
getInfoByStaffId = ccutils.getInfoByStaffId


def call_in(con, *args):
	'''
	:param info:
	:return:
	此函数对应于agi_call_in.php
	'''
	if not args:  #外联情况
		info = con.getInfo()
	else:
		info = args[0]  #这里用info命名不太恰当但是历史原因就暂时info(时间上是ev--event)
		return
	caller = info.getHeader('variable_sip_from_user')
	callee = info.getHeader('channel-destination-number')
        if 'gw+' in callee: callee = callee[3:]
	uuid = info.getHeader('variable_uuid')
	domain_name = info.getHeader('variable_domain_hame')
	if not domain_name: domain_name = info.getHeader('variable_sip_to_host')
	elif not domain_name: domain_name = info.getHeader('channel-network-addr')
	dial_str = None
	# 通过外线号码获得其所属的项目(正常进行的项目)
	sql = 'select b.id as ClassifId, a.CompanyId, a.Type from {} a join {} b on a.CompanyId = b.CompanyId ' \
	      'where a.Num = "{}" order by b.Id limit 1'.format(Conf.K_NUMINFO_SHARE, Conf.K_PROJECT_CLASSIFICATION, callee)
	row = db.get(sql)
	if not row:
		print('#########未绑定项目#############')
		return dial_str
	# 判断是否为语音识别的呼入号码
	# row.Type = 3
	if row.Type == 3:
		sql = 'select asrnumber, CompanyId from' + Conf.ASRCALL_CONFIG +'where CallerID = "{}"'.format(callee)
		asrrow = db.get(sql)
		if asrrow:
			CustomerId = 0       #todo 原来php里直接出现此变量，python会报错如果没有实现定义的话，所以这里添加个定义，具体php为何这样有待进一步理解
			vars = ['asrnumber',asrrow.asrnumber,'CompanyId',asrrow.CompanyId,'CDR(CompanyId)',asrrow.CompanyId,'CDR(calltype)',6,'CUSID',CustomerId,'CustomId',CustomerId,'CDR(customerid)',CustomerId]
			ccutils.multiset(con, vars)
			# ###todo:transfer好像执行完不会返回，这里似乎应该调用execute_extension更合适,待确认...
			con.executeAsync('transfer', 'from-asrcall', uuid)
			return dial_str
	# 归属分类id
	ClassifId = row.ClassifId
	# 队列名称:队列到名字和呼入到外线一致
	QueueName = callee

	CompanyId = row.CompanyId
	vars = ['CompanyId',CompanyId,'ClassifId',ClassifId,'CDR(calltype)',1,'CDR(ClassifId)',ClassifId,'CDR(CompanyId)',CompanyId]
	ccutils.multiset(con, vars)
	# 黑名单
	sql = 'select id from' + Conf.K_BLACKLIST_SHARE  + 'where Num = "{}" and CompanyId = {} limit 1'.format(caller, CompanyId)
	blacklist = db.get(sql).id if db.get(sql) else None
	if blacklist:
		print('已经加入黑名单')
		return dial_str
	sql = "select IVR_IsStaffFirst,IsRecord from {} where Enabled=1 and Id={} ;".format(Conf.CRM_COMPANYINFO, CompanyId)
	row = db.get(sql)
	if not row:
		# 公司账户已经禁用
		con.execute('playback', 'ccos_company_disabled')
		return dial_str

	staff_first = row.IVR_IsStaffFirst
	#  $agi->set_variable('ISRECORD',$row['IsRecord']);
	# 检查应该客户是否为服务客户  如果是   则获取其相应资料
	sql = "select Id,StaffId,ProjectId from" + Conf.CUSTOMER_BASEINFO +"where CompanyId={} and  DelBatchId=0  and  phone='{}' limit 1;".format(CompanyId, caller)

	row = db.get(sql)
	CustomerId = row.Id if row else 0
	StaffId = row.StaffId if row else 0

	###
	if not CustomerId and staff_first:
		sql = "select id, StaffId,customerid from {} where ClassifId={} and  dst={} and StaffId>0 union all select id,  " \
		      "StaffId,customerid from {} where ClassifId={} and  src ={} and StaffId>0 order by id  desc limit 1;".format(Conf.CDR, ClassifId, caller, Conf.CDR, ClassifId, caller)
		row = db.get(sql)
		CustomerId = row.customerid if row else 0
		StaffId = row.StaffId if row else 0

	###
	if not CustomerId:
		CustomerId = ccutils.get_generator_id(0, caller)

	vars = ['CUSID',CustomerId, 'CDR(customerid)',CustomerId]
	ccutils.multiset(con, vars)
	# 语音导航
	ivr_exec(con, callee)
	# 直属号码
	if not staff_first or not StaffId:
		sql = "select StaffId,count(*) as CountNum  from" + Conf.R_STAFFIDNUM_SHARE + "where num='{}' and type=1 ;".format(callee)
		row = db.get(sql)
		# 如果没有呼入绑定 则挂机
		if row and not row.CountNum:
			return None

		# 如果有呼入绑定 且只有一个座席
		if row.CountNum == 1:
			StaffId = row.StaffId
			staff_first = 1

	# 呼叫归属客服
	if staff_first and StaffId:
		sql = 'select Exten from' + Conf.R_STAFFIDEXTEN_SHARE + 'where StaffId = "{}"'.format(StaffId)
		row = db.get(sql)
		Exten = row.Exten if row else ''
		vars = ['StaffId',StaffId,'CDR(Exten)',Exten,'CDR(StaffId)',StaffId]
		ccutils.multiset(con, vars)
		ExtenStatus = -4
		if Exten: ExtenStatus = get_extension_state(Exten) #取当前分机状态
		# 分机空闲时进行呼叫
		if not ExtenStatus:
			sql = "select c.id,b.IsHiddenNum from" + Conf.CRM_USERINFO + "a  join crm_role b on a.RoleId=b.Id join " \
			      "k_projectinfo c on a.DepartmentId=c.DepartmentId and c.`Status`=1 where a.StaffId='{}';".format(StaffId)
			row = db.get(sql)
			isHiddenNum = row.IsHiddenNum
			if not isHiddenNum:
				ccutils.set_variable(con,'CALLERID(num-pres)','prohib')

			# ccutils.set_variable(con,'CALL_STR','SIP/{}'.format(Exten))
			# con.executeAsync('set', 'CALL_STR=SIP/{}'.format(Exten), uuid)
			# con.executeAsync('Goto', 'transfer', uuid)
			dial_str = 'sofia/internal/{}%{}'.format(Exten, domain_name)
		elif staff_first == 1:
			con.execute('playback', Conf.SOUND_PATH + 'Ivr_021.wav')  # 坐席正忙请稍后再拨
			return dial_str

		if not QueueName:
			return dial_str
		# 如果列队中有部门经理 且号码显示 没全部为可显示
		sql = "select a.Id from" + Conf.R_STAFFIDNUM_SHARE +"a join {} b  on a.StaffId=b.StaffId join {} c on b.RoleId=c.Id and c.`Type`=3 and c.IsHiddenNum=1 where  a.Num ='{}' limit 1 ;".format(Conf.CRM_USERINFO, Conf.CRM_ROLE, callee)
		row = db.get(sql)
		isHiddenNum = row.Id if row else 0
		if not isHiddenNum:
			# 查看座席权限是否 是隐藏
			sql = "select Id  from" + Conf.CRM_ROLE + "where CompanyId={} and type=4 and  ISHiddenNum=0 limit 1;".format(CompanyId)
			row = db.get(sql)
			isHiddenNum = row.Id if row else 0
			if isHiddenNum:
				ccutils.set_variable(con, 'CALLERID(num-pres)','prohib')
		ccutils.set_variable(con, 'U_QUEUE', QueueName)
		return (dial_str, QueueName)