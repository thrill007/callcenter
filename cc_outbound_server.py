# -*- coding: UTF-8 -*-
import ESL
import SocketServer
import socket
from imp import reload
from call_in import *
from call_out import *
from report_staffid import *
from check_miss_call import *
from call_quality import *
from call_wisper import *
from call_transfer import *
from call_onhold import *
from hangup import *
from login import *
from logout import *
from queue_query_number import *
from manager import *
from web_call import *
from queue_answer import *
from queue_save_number import *
from queue_hangup import *
import socket
import threading
import re

db = ccutils.db
getInfoByStaffId = ccutils.getInfoByStaffId




class ESLRequestHandler(SocketServer.BaseRequestHandler):

	def setup(self):
		# self.request.sendall(bytes('welcome'.encode('utf-8')))
		print (self.client_address, 'connected!')
		fd = self.request.fileno()
		print fd
		self.con = ESL.ESLconnection(fd)
		if self.con.connected():
			self.info = self.con.getInfo()

		print 'Connected: ', self.con.connected()
		# print('当前正在运行的线程:{}'.format(threading.enumerate()))

	def handle(self):
		con = self.con
		info = self.info
		try:
			uuid = info.getHeader('Unique-ID')
			dial_str = info.getHeader('variable_dial_str')
			context = info.getHeader('caller-context')
			dest = info.getHeader('channel-destination-number')
			domain = get_domain(info)
			con.events('plain', 'all')
			con.filter('Unique-ID', uuid)
			# con.send('myevents plain {}'.format(uuid))
			ev = con.recvEventTimed(2000)
			if ev and uuid != ev.getHeader('Unique-ID'): print('#######不一样的event')
			'''
			按照wiki所说，context是系统的通道变量，它对应于info变量是caller-context,但是dialplan里设置了context=internal,
			发出的事件里的caller-context没变，而是多了一个caller-context自定义的event字段。
			程序里先获取caller-context字段，如果能获取到，说明拨号计划里期望更改默认的context，则使用获取到的值
			否则再获取caller-context并使用之
			'''
			if context == 'call_out':
				if dest in ['000', 'login']:
					login(con)
				elif dest in ['001', 'logout']:
					logout(con)
				elif dest == '002':
					queue_query_number(con)
				elif len(dest) == 3:
					manager(con)
				# 下面这条测试，通过web originate(...)外呼或者软电话外呼
				elif (dest.isdigit() and 8 < len(dest)  < 13 and dest[0:3] != '888') or dest in ['call-out']:
					dial_str, callee, caller, staff_id, uuid = call_out(con)
					if dial_str:
						set_variable(con, 'CDR(DIALSTATUS)', 'answered')
						con.executeAsync('bridge', dial_str)
						records(con, callee, caller, staff_id, uuid)
				elif dest in ['003', 'onhold']:
					call_onhold(con)
				elif dest in map(str, range(8800, 8819)) + ['internal', '88851063330', '88851063331']:
					dial_str, queue_name = call_in(con)
					if dial_str or queue_name: set_variable(con, 'CDR(DIALSTATUS)', 'answered')
					if dial_str:
						con.executeAsync('bridge', dial_str)
					elif queue_name:
						staff_id, member = report_staffid(con)
						queue_bridge(con.executeAsync, staff_id, domain, queue_name)

				# 下面是呼入的场景(呼入到web端坐席?)
				elif dest in ['004', 'from-web']:
					u_queue = web_call(con)
					if u_queue:
						staff_id, member = report_staffid(con)
						queue_bridge(con.executeAsync, staff_id, domain, u_queue)
				elif dest == 'from-ivr': #这里是web originate发起后走到到流程，originate必须设置参数my_caller, my_callee
					caller = info.getHeader('variable_my_caller')
					callee = info.getHeader('variable_my_callee')
					records(con, callee, caller, domain, uuid)
					u_queue = info.getHeader('variable_U_QUEUE')
					if u_queue:
						staff_id, member = report_staffid(con)
						queue_bridge(con.executeAsync, staff_id, domain, u_queue)
				elif dest in ['006', 'from-autocall']:
					caller = info.getHeader('variable_my_caller')
					callee = info.getHeader('variable_my_callee')
					records(con,callee, caller, domain, uuid)
					queue_name = info.getHeader('variable_QueueName')
					if queue_name:
						staff_id = queue_answer(con, info)
						queue_bridge(con.executeAsync, staff_id, domain, queue_name)
				elif dest == '_asr':
					dial_str, queue_name = call_in(con)
					if dial_str or queue_name: set_variable(con, 'CDR(DIALSTATUS)', 'answered')
					if dial_str:
						con.executeAsync('bridge', dial_str)
					elif queue_name:
						staff_id, member = report_staffid(con)
						queue_bridge(con.executeAsync, staff_id, domain, queue_name)

				elif dest in ['postprocess-after-autocall', '678']:
					callee = info.getHeader('variable_my_callee')
					share_string = info.getHeader('SHARED(SHARE_STRING)')
					queue_save_number(con, callee, share_string)
		except SystemExit:
			print('调用了exit(0)')
		except Exception as e:
			print('e')
		finally:
			# con.execute('sleep', '20000')
			# con.setEventLock('1')
			con.disconnect()


# server host is a tuple ('host', port)
if __name__ == '__main__':
	server = SocketServer.ThreadingTCPServer(('', 8040), ESLRequestHandler)
	server.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
	if 'MainThread' in threading.currentThread().name:
		server.serve_forever()