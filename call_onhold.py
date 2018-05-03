# -*- coding: UTF-8 -*-
import ccutils
from mysql_wrapper import Conf
db = ccutils.db
def call_onhold(con, *args):
	# 播放等待音
	index = 0
	if not args:  #外联情况
		info = con.getInfo()
	else:
		info = args[0]  #这里用info命名不太恰当但是历史原因就暂时info(时间上是ev--event)
		return #目前inbound模式只处理hangup后的cdr，其余的情况放在outbound模式处理

	uuid = info.getHeader('Unique-ID')
	while index < 3:
		con.executeAsync('playback', Conf.SOUND_PATH + 'ringMusic.wav', uuid)
		index += 1
	return True
