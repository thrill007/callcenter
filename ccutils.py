# -*- coding: UTF-8 -*-
# import freeswitch
import json
from mysql_wrapper import Connection as SQLdb, Row, Conf
import time
from ipaddress import *
import math
from datetime import datetime, date
from base import *
import re
'''表的结构是 StaffId | Exten | State | CompanyId | IPAddr | UpdateTime | CreateTime'''


# db_parms = {'host':'10.10.10.100','user':'root', 'passwd':'', 'db':'u_crm_db', 'port':3306}
# try:
# 	conn = MySQLdb.connect(**db_parms)
# 	cursor = conn.cursor()
# except Exception as e:
# 	freeswitch.consoleLog('NOTICE', '获取数据失败')

# table = 'r_staffidexten_share'
from mysql_wrapper import Conf

cursor = None
g_online_time = 0
db = None


def records(con, callee, caller, staff_id, uuid):
	set_variable(con, 'RECORD_STEREO', 'false')
	reply = con.api('global_getvar', 'recordings_dir')
	rec_dir = reply.getBody()
	rec_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
	rec_file = callee + '_' + caller + '_' + staff_id + '_' + uuid + '.wav'
	rec_fullname = rec_dir + '/' + rec_date + '/' + rec_file
	con.executeAsync('record_session', '{}'.format(rec_fullname))
	set_variable(con, 'record_file', rec_file)


def get_domain(info):
	domain_name = info.getHeader('variable_domain_hame')
	if not domain_name:
		domain_name = info.getHeader('variable_sip_to_host')
	elif not domain_name:
		domain_name = info.getHeader('channel-network-addr')
	return domain_name

def queue_bridge(func, staff_id, domain, queue_name):
	sql = 'select Exten from' + Conf.R_STAFFIDEXTEN_SHARE + 'where StaffId = "{}"'.format(staff_id)
	row = db.get(sql)
	Exten = row.Exten if row else '0'
	dial_str = 'sofia/internal/{}%{}'.format(Exten, domain)
	set_var(func, 'CDR(DIALSTATUS)', 'answered')
	func('bridge', dial_str)


# set_variable = lambda c,x,y:c.executeAsync('set','{}={}'.format(x, y))
def set_variable(*args):
	con = args[0]
	ar = args[1] + '={}'
	con.executeAsync('set', ar.format(*args[2:]))
def set_var(func, *args):
	ar = args[0] + '={}'
	func('set', ar.format(*args[1:]))


def list2dict(*lst):
	d = {}
	for i in range(0, len(lst), 2):
		d[lst[i]] = lst[i+1]
	return d

def str2list(str):
	lst = str.split(' ')

def multiset(con, lst):
	parms = ''
	while len(lst):
		parms += '{}={}'.format(lst.pop(0), lst.pop(0))
		parms += ' '
	con.executeAsync('multiset', parms)


def multiset_s(con, **args):
	parms = ''
	for arg in args.items():
		parms += '{}={}'.format(arg[0], arg[1])
		parms += ' '
	con.executeAsync('multiset', parms)

def get_variable(con, *args):
	'''
	获取名字为args[0]的app执行后的变量值
	:param con:
	:return:
	'''
	index = 0
	while True:
		ev = con.recvEvent()
		if ev.getHeader('event-name') == 'CHANNEL_EXECUTE_COMPLETE' and \
			ev.getHeader('variable_current_application') == args[0] and \
			ev.getHeader('variable_{}'.format(args[1])):
			my_var = (ev.getHeader('variable_{}'.format(args[1])))
			return my_var
		index += 1
		if index >= 20: break


def is_black(con, phone, hangup=True):
	uuid = con.getInfo().getHeader('Unique-ID')
	sql = 'select id from'+Conf.K_BLACKLIST_SHARE+'where num={}'.format(phone)
	row = db.get(sql)
	id1 = row.id if row else -1
	if id1 > 0:
		result = True
	else:
		result = False
		# 直接挂机
	if result and hangup:
		con.execute('hangup', uuid)
	return result

def get_generator_id(project_id, new_number = 0):
	sql = "select NewId from {} where num={} and projectid='{}'; ".format(Conf.TEMP_NEWNUM, new_number, project_id)
	row = db.get(sql)
	id1 = row.NewId if row else 0
	if id1:
		return id1
	sql = 'insert into {} (Id) values (NULL)'.format(Conf.B_ID_GENERATOR)
	db.execute(sql)
	id1 = db.insert_id()
	if id1:
		sql = "insert into {}(NewId,Num,Projectid) values ({},'{}','{}')".format(Conf.TEMP_NEWNUM, id1, new_number, project_id)
		db.execute(sql)
		return id1
	else:
		return 0

def remove_queue_member(exten, forecast_id):
	pass
def add_queue(exten, queue_name):
	pass
def gen_cdrs(ev):
	call_type = ev.getHeader('variable_CDR(calltype)')
	if call_type == '0':  #呼出
		caller = ev.getHeader('variable_my_caller')
		callee = ev.getHeader('variable_my_callee')  # 或者caller-destination-number
		clid = ev.getHeader('variable_my_caller_name')
	elif call_type == '1': #呼入
		caller = ev.getHeader('caller-caller-id-number')
		callee = ev.getHeader('caller-destination-number')
		clid = ev.getHeader('caller-caller-id-name')
	elif call_type == '3': #预测外呼
		caller = ev.getHeader('caller-caller-id-number')
		callee = ev.getHeader('variable_sip_to_user')  # 或者caller-destination-number
		clid = ev.getHeader('variable_caller_id_name')
	else:
		caller = ev.getHeader('caller-caller-id-number')
		callee = ev.getHeader('variable_sip_to_user')  # 或者caller-destination-number
		clid = ev.getHeader('variable_caller_id_name')

	uuid = ev.getHeader('variable_uuid')
	CompanyId = ev.getHeader('variable_CDR(CompanyId)')
	PROID = ev.getHeader('variable_CDR(PROID)')
	StaffId = ev.getHeader('variable_CDR(StaffId)')
	customerid = ev.getHeader('variable_CDR(customerid)')
	if customerid == '-1': customerid = 0		#todo customerd及其类似的实在是太乱了，目前发现了就有四种方式似乎就为了传递一个变量?!
	ClassifId = ev.getHeader('variable_CDR(ClassifId)')
	DIALSTATUS = ev.getHeader('variable_CDR(DIALSTATUS)')
	now = datetime.now()
	# 转换为指定的格式
	endtime = now.strftime('%Y-%m-%d %H:%M:%S')
	if not StaffId and callee and len(callee) == 4:
		sql = 'select StaffId from {} where Exten = {} limit 1;'.format(Conf.R_STAFFIDEXTEN_SHARE, callee.strip())
		# print('the sql is: {}'.format(sql))
		row = db.get(sql)
		StaffId = row.StaffId if row else 0

	if not StaffId:
		StaffId = 0

	if not customerid:
		customerid = 0
	if not PROID:
		PROID = 0
	if not ClassifId:
		ClassifId = 0

	if StaffId and not PROID:
		result = getInfoByStaffId(StaffId)
		if result:
			CompanyId = result['CompanyId']
			ClassifId = result['ClassifId']
			PROID = result['ProjectId']

	dst = ev.getHeader('Caller-Destination-Number')[:4]  # variable_CDR(dst)-->Caller-Destination-Number
	#todo 不管那么多，就用event里的date相关字段来指代calldate
	# calldate = ev.getHeader('variable_CDR(start)')
	# calldate = calldate if calldate else '0001-01-01 00:00:00'
	calldate = ev.getHeader('variable_start_stamp')
	answeredtime = ev.getHeader('variable_answer_stamp')
	answeredtime = answeredtime if answeredtime else '0001-01-01 00:00:00'
	hangup_time = ev.getHeader('Caller-Channel-Hangup-Time')
	hangup_time = hangup_time if hangup_time else '0001-01-01 00:00:00'
	endtime = ev.getHeader('variable_end_stamp')
	endtime = endtime if endtime else '0001-01-01 00:00:00'
	duration = ev.getHeader('variable_duration')
	duration = duration if duration else '0.00'
	duration_int = math.ceil(float(duration))

	billsec = ev.getHeader('variable_billsec')
	billsec = billsec if billsec else '0.00'
	billsec_int = math.ceil(float(billsec))

	if call_type == '0': #呼出
		dcontext = ev.getHeader('variable_CDR(dcontext)')
	else: #呼入
		dcontext = ev.getHeader('caller-context')
	channel = ev.getHeader('Other-Leg-Channel-Name')
	dstchannel = ev.getHeader('variable_channel_name')
	disposition = ev.getHeader('variable_originate_disposition') if billsec_int else 'ANSWERED'

	linkedid = ev.getHeader('variable_CDR(linkedid)')

	StaffId = ev.getHeader('variable_CDR(StaffId)')
	ClassifId = ev.getHeader('variable_CDR(ClassifId)')
	# extenNum = ev.getHeader('variable_CDR(Exten)')
	extenNum = caller
	CodeId_1 = ev.getHeader('variable_CodeId_1')
	CodeId_2 = ev.getHeader('variable_CodeId_2')

	if dst == 's':
		dst = ev.getHeader('variable_EXTE')
	if not caller:
		caller = ev.getHeader('Caller-Caller-ID-Number')
	if not call_type:
		caller = ev.getHeader('Caller-Caller-ID-Number')  # OUTLINE-->originator

	if not dst:
		dst = ev.getHeader('variable_EXTE')

	if not PROID:
		PROID = ev.getHeader('variable_CDR(PROID)')

	PROID = PROID if PROID else 0
	StaffId = StaffId if StaffId else 0
	customerid = customerid if customerid else 0
	ClassifId = ClassifId if ClassifId else 0
	CompanyId = CompanyId if CompanyId else 0
	call_type = call_type if call_type else 0
	extenNum = extenNum if extenNum else 0
	CodeId_1 = CodeId_1 if CodeId_1 else 0
	CodeId_2 = CodeId_2 if CodeId_2 else 0
	return (clid, caller, callee, calldate, answeredtime, endtime, duration, duration_int, billsec,
		billsec_int, dcontext, channel, dstchannel, disposition, uuid, linkedid, PROID,
		StaffId, customerid, ClassifId, CompanyId, call_type, extenNum, CodeId_1, CodeId_2)

def cdr_insert(ev, *args):
	clid = args[0]
	caller = args[1]
	dst = args[2]
	calldate = args[3]
	answeredtime = args[4]
	endtime = args[5]
	duration = args[6]
	duration_int = args[7]
	billsec = args[8]
	billsec_int = args[9]
	dcontext = args[10]
	channel = args[11]
	dstchannel = args[12]
	disposition = args[13]
	uuid = args[14]
	linkedid = args[15]
	PROID = args[16]
	StaffId = args[17]
	customerid = args[18]
	ClassifId = args[19]
	CompanyId = args[20]
	call_type = args[21]
	extenNum = args[22]
	CodeId_1 = args[23]
	CodeId_2 = args[24]
	sql = "insert into {}  (clid, src, dst, calldate, answertime, endtime, duration, duration_int, billsec, billsec_int, dcontext, channel, dstchannel, disposition, uniqueid, linkedid, projectid, StaffId, customerid, Classifid, CompanyId, calltype, exten, codeid_1, codeid_2) values ('{}', '{}', '{}', '{}', '{}', '{}',{}, {}, {}, {}, '{}', '{}', '{}', '{}', '{}', '{}', {}, {}, {}, {}, {}, {}, '{}', '{}', '{}');".format(Conf.CDR, clid, caller, dst, calldate, answeredtime, endtime, duration, duration_int, billsec, billsec_int, dcontext, channel, dstchannel, disposition, uuid, linkedid, PROID, StaffId, customerid, ClassifId, CompanyId, call_type, extenNum, CodeId_1, CodeId_2)
	sql = sql.replace('None', '0')
	print('the sql######################## {}'.format(sql))
	r = db.execute(sql)
	return r


def cdr_complement(*args):
	'''
	为了统一cdr表格，将asrcall的cdr部分合并入传统的坐席cdr表，这里就是在普通的Hangup()处理后再补充设置增加的字段
	:param args:
	:return:
	'''
	ev = args[0]
	id1 = args[1]
	caller_id_group = ev.getHeader('variable_CDR(callerid)')
	batch_id = ev.getHeader('variable_CDR(batchid)')
	name = ev.getHeader('variable_CDR(name)')
	phone = ev.getHeader('variable_CDR(phone)')
	address = ev.getHeader('variable_CDR(address)')
	sex = ev.getHeader('variable_CDR(sex)')
	email = ev.getHeader('variable_CDR(email)')
	if re.search('Normal_Clearing', ev.getHeader('Hangup-Cause'), re.I):
		call_result = 'success'
	else:
		call_result = 'failure'

	call_out_status = ev.getHeader('variable_CDR(CallOutStatus')
	update_time = ev.getHeader('variable_CDR(UpdateTime)')
	if not update_time: update_time = datetime.now()
	create_time = ev.getHeader('variable_CDR(CreateTime)')
	if not create_time: create_time = datetime.now()

	sql = 'update {} set CallerId={},BatchId={}, Name="{}", Phone={}, Address="{}", Sex={}, Email="{}", CallOutStatus={}, CallResult="{}", UpdateTime="{}", CreateTime="{}" where id={}'.format(
		Conf.CDR, caller_id_group, batch_id, name, phone, address, sex, email, call_out_status, call_result,
		update_time, create_time, id1)
	sql = sql.replace('None', '0')
	db.execute(sql)


def read_configuration(key):
	with open(Conf.CONFIG_FILE, 'r') as f:
		config_lines = f.readlines()
		if key == 'all':
			return config_lines
		else:
			lst = [x for x in config_lines if key in x][0]
			return lst.split('=')[1] if lst else None

def del_RSE_Data(where):
	sql = 'delete  from {} where {}'.format(Conf.R_STAFFIDEXTEN_SHARE, where)
	db.execute(sql)

def microtime(get_as_float = False):
	if get_as_float:
		return time.time()
	else:
		r = math.modf(time.time())
		return '{:f} {:d}'.format(r[0], int(r[1]))
def get_rse_data(where, myreturn):
	try:
		sql = 'select %s from %s where %s limit 1; % (myreturn, table, where)'
		if cursor.execute(sql) > 0:
			return cursor.fetchone()
		else:
			return False
	except:
		cursor.rollback()


def is_online(staffid):
	global g_online_time
	online_time = 0
	query = 'select UpdateTime from {} where StaffId = {} limit 1'.format(Conf.R_STAFFIDEXTEN_SHARE, staffid)
	rows = db.get(query)
	if rows: online_time = db.get(query).UpdateTime

	# 值为1时候，是语音登录，如果是web登录，则online_time是时间戳,即使是异常退出,time()-online_time > 31超时总是成立
	if g_online_time == 0:
		g_online_time = 31
	# 已经语音登录或者web登录过了
	if online_time == 1 or time.time() - online_time < g_online_time:
		return True
	return False

def get_num(callee):
	# num = callee + 0
	# todo这里为了调试先固定一个号码
	num = callee
	#外地手机号码加拨零
	if num[0] == '1' and num[0:2] != '10' and len(num) == 11:
		# 转换为数值类型
		hcode = num[0:7]
		sql = "select areacode from {} where hcode={}".format(Conf.B_HCODE_SHARE, hcode)
		row = db.get(sql)
		areacode = row.areacode if row else 0

		if areacode and areacode != Conf.local_areacode:
			# 长途
			callee = '0'+num
		elif areacode and areacode == Conf.local_areacode:
		    # 市话
		    callee = num
	return callee

def filter_var(ipAddr):
	ip = IPv4Address(ipAddr)
	return ip.is_global


def array_intersect(old, new):
	# return reduce(set.intersection, map(set, [old, new]))
	#更简洁的实现方式
	return [x for x in old if x in new]



def isAuthIP(CompanyId, exten):
	sql = 'select ipaddr from {} where name = {} limit 1;'.format(Conf.CFG_SIP, exten)
	r = db.get(sql)
	if r:
		ipaddr = r.ipaddr
	else:
		ipaddr = ''

	if filter_var(ipaddr):	# todo 公网地址需要进行IP验证
		sql = 'select AuthIP from {} where id = {};'.format(Conf.CRM_COMPANYINFO, CompanyId)
		row = db.get(sql)
		if row and row.AuthIP != u'':
			old_authip = row.AuthIP
			old_authip = json.loads(old_authip)
			if ipaddr in old_authip:
				sql = 'select a.ipaddr,count(1) as counts from {} a join {} b on b.StaffId=a.name where b.CompanyId={} and a.ipaddr!= "" group by a.ipaddr order by counts desc'.format(Conf.CFG_SIP, Conf.CRM_USERINFO,CompanyId)
				rows = db.get_all(sql)
				if isinstance(rows, list):
					new_authip_most = rows[0].ipaddr
				elif isinstance(rows, Row):
					new_authip_most = rows.ipaddr
				else:
					new_authip_most = ''
				new_authip_list = []
				for row in rows:
					new_authip_list.append(row.ipaddr)
				authip_list = list(array_intersect(old_authip, new_authip_list))
				if new_authip_most not in authip_list:
					authip_list.append(new_authip_most)
				# sql = "update crm_companyinfo set AuthIP='".json_encode(authip)."' where Id=$companyid";
				sql = "update {} set AuthIP= '{}' where Id= {}".format(Conf.CRM_COMPANYINFO, json.dumps(authip_list), CompanyId)
				db.execute(sql)
				if ipaddr not in authip_list:
					return False
				else:
					return True
	return True


def getRow(sql, limited=False):
	pass


def getOne(sql):
	row = ()
	try:
		if cursor.execute(sql):
			row = cursor.fetchone()
			return row
	except:
		pass
		# freeswitch.consoleLog('notice', '获取数据失败')
	return row


def ivr_rse_login(staffid, exten, CompanyId=0):
	sql = "select StaffId from {} where (Exten={} or StaffId={} ) and (UpdateTime=1 or {} -UpdateTime<31 )  limit 1;".format(Conf.R_STAFFIDEXTEN_SHARE,
		exten, staffid, time.time())
	value = db.get(sql)
	# 如果已经登录在线  则返回分机绑定的工号
	# freeswitch.consoleLog('NOTICE', '>>>>>>>>>>>>.the value is:%s ' % value)
	if value:
		return value.StaffId

	# 删除离线
	sql = "delete from {} where exten={} or staffid= {} ;".format(Conf.R_STAFFIDEXTEN_SHARE, exten, staffid)
	db.execute(sql)
	if not CompanyId:
		sql = "select CompanyId from {} where StaffId= {} limit 1;".format(Conf.CRM_USERINFO, staffid)
		CompanyId = db.get(sql).CompanyId

	sql = "insert into {}(StaffId,Exten,CompanyId,State,IPAddr,UpdateTime)values({}, {}, {},0,'0.0.0.0',1);".format(
		Conf.R_STAFFIDEXTEN_SHARE, staffid, exten, CompanyId)
	db.execute(sql)
	return 0


if __name__ == '__main__':
	pass
else:
	db = SQLdb()


def getInfoByStaffId(staffid):
	sql = '''
		    select b.id ProjectId, b.ClassifId, a.CompanyId from {} a join {} b on a.DepartmentId = b.DepartmentId where b.`Status` = 1
		    and a.staffid = {}
		    '''.format(Conf.CRM_USERINFO, Conf.K_PROJECTINFO, staffid)
	result = db.get(sql)
	return result
