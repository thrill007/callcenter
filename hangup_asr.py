# -*- coding: UTF-8 -*-
import ccutils
import math
import datetime
from mysql_wrapper import Conf
import re
from hangup import *

db = ccutils.db
getInfoByStaffId = ccutils.getInfoByStaffId
microtime = ccutils.microtime

def hangup_asr(con,ev):

        '''
	:param info:
	:param call_type:
	:return:
	对应于agi_hangup.php
	'''
        #目前，对于机器人外呼的cdr，采用了两步写的方式：先是坐席方式cdr字段的写入, 然后是新增的asrcall_xxx表的相关字段的更新
        (id1, id2, id3) = hangup(con,ev)

        ccutils.cdr_complement(ev, id1)