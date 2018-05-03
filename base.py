# -*- coding: UTF-8 -*-
# /**
#  * 获取分机状态及通话时的被叫号码
#  *=================================================
#  * @param	$exten	  	(string)		分机号
#  * @param	$queuename	 (string)		队列名称
#  *=================================================
#  *@Return:
#  *-1 =扩展找不到
#  * 0=空闲
#  * 1=静态座席 通话中
#  * 2=忙（paused）
#  * 4 =不可用
#  * 8 =振铃
#  * 9 =振铃(通话中时 如果还有其它客户呼入的情况)
#  * 16 =正等待
#  * 17=动态座席 通话中
#  * 18=小休
#  * 19=正忙（分机处于队列中
#  */

def get_extension_state(exten):
	#todo asterisk中是向agi框架请求分机状态(参数带在request的url当中), fs如何实现?
	return 0

def remove_queue_member(exten, forecast_id):
	pass


def DBGet(family, key):
	pass