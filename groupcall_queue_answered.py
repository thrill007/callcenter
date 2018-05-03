# -*- coding: UTF-8 -*-

import ccutils
from mysql_wrapper import Conf
db = ccutils.db

def groupcall_queue_answered(con, ev):
        caller = ev.getHeader('caller-caller-id-number')
        callee = ev.getHeader('variable_sip_to_user')  # 或者caller-destination-number
        uuid = ev.getHeader('variable_uuid')

