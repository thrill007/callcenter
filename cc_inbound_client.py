# -*- coding: UTF-8 -*-

from ESL import *
from call_transfer import *
from call_wisper import *
from call_quality import *
from queue_query_number import *
from report_staffid import *
from check_miss_call import *
from check_miss_call_asr import *
from queue_answer import *
from queue_hangup import *
from queue_groupcall_answer import *
from groupcall_queue_answered import *
from manager import *
from hangup import *
from hangup_asr import *
from base import *
from datetime import datetime,date
from call_in import *
from call_out import *
from call_onhold import *
from ivr import *
import time
import re

db = ccutils.db
microtime = ccutils.microtime
getInfoByStaffId = ccutils.getInfoByStaffId
con = ESLconnection("localhost", "8021", "ClueCon")
now = datetime.now()

if __name__ == '__main__':
        # are we connected?
        if con.connected():
                con.events("plain", "all")
                con.filter('Event-Name', 'CHANNEL_HANGUP_COMPLETE')
                con.filter('Event-Name', 'CHANNEL_CREATE')
                con.filter('Event-Name', 'CHANNEL_STATE')
                con.filter('Event-Name', 'CHANNEL_HANGUP')
                while True:
                        ev = con.recvEvent()
                        if ev:
                                event_name = ev.getHeader('Event-Name')
                                hit_dialplan = ev.getHeader('Channel-HIT-Dialplan')
                                channel_state = ev.getHeader('Channel-State')
                                if event_name == 'CHANNEL_CREATE':
                                        print('CHANNEL_CREATE..............................')
                                        pass
                                elif event_name == 'CHANNEL_STATE':
                                        if ev.getHeader('channel-State') == 'CS_EXECUTE':
                                                print('CS_EXECUTE..........................')
                                                if ev.getHeader('caller-context') == 'call_onhold':
                                                        call_onhold(con,ev)
                                                elif ev.getHeader('caller-context') == 'chan_transfer':
                                                        call_transfer(con,ev)
                                                        pass
                                                elif ev.getHeader('caller-context') == 'extenspy_whisper':
                                                        call_wisper(con, ev)
                                                        pass
                                                elif ev.getHeader('caller-context') == 'extenspy_silent':
                                                        call_quality(con, ev)
                                                        pass
                                                elif ev.getHeader('Caller-Context') in ['from-web','from-ivr']:
                                                        report_staffid(con, ev)
                                                elif ev.getHeader('caller-context') == 'from-ivr':
                                                        check_miss_call(con, ev)
                                                elif ev.getHeader('caller-context') == 'internal':
                                                        call_in(con,ev)
                                                        report_staffid(con, ev)
                                                        check_miss_call(con, ev)
                                                        pass
                                                elif ev.getHeader('caller-context') == 'from-autocall':
                                                        queue_answer(con, ev)
                                                        queue_hangup(con, ev)
                                                elif ev.getHeader('caller-context') == 'from-groupcall-queuenode':
                                                        queue_groupcall_answer(con, ev)
                                                        groupcall_queue_answered(con, ev)
                                                elif ev.getHeader('caller-context') == 'from-web':
                                                        pass
                                        elif ev.getHeader('channel-State') == 'CS_HANGUP':
                                                print("CS_HANGUP...............................")
                                        elif ev.getHeader('channel-State') == 'CS_DONE':
                                                print('CS_DONE.....................................')
                                elif event_name == 'CHANNEL_ANSWER':
                                        print('CHANNEL_ANSWER..............................')
                                elif event_name == 'CHANNEL_HANGUP':
                                        print('CHANNEL_HANGUP................................')
                                elif event_name == 'CHANNEL_HANGUP_COMPLETE':
                                        print('CHANNEL_HANGUP_COMPLETE......................................')
                                        # print (ev.serialize())
                                        # variable_CDR(calltype) fs在获取通道变量的是，key-value中的key 是大小写不敏感的，但是value是敏感的
                                        # 只是设置了calltype的那个channel生成cdr，这个channel也是走dialplan的channel
                                        #todo cdr生成部分的架构要再梳理下，结合传统(坐席)+机器人在同一个cdr表里生成呼叫成功和失败状况下的数据
                                        if hit_dialplan == 'true':
                                                if ev.getHeader('variable_CDR(calltype)') == '1': #呼入
                                                        dstatus = ev.getHeader('variable_CDR(DIALSTATUS)')
                                                        if re.search('Normal_Clearing', ev.getHeader('Hangup-Cause'),  re.I):
                                                                hangup(con, ev)
                                                                check_miss_call(con, ev)
                                                elif ev.getHeader('variable_CDR(calltype)') == '0': #呼出
                                                        '''
                                                        呼出情况比较复杂，简要总结如下(Event-Name:CHANNEL_HANGUP_COMPLETE):
                                                        1. 被叫不在线并且开启了voice mail, 则b-leg能成功接通(接通voicemail也算是接通), HANGUP-CAUSE='NORMAL_CLEARING', variable_DIALSTATUS='SUCCESS'???
                                                        2. 被叫不在线没有开启voicemail，则b-leg失败，HANGUP-CAUSE='NO_USER_RESPONSE', variable_DIALSTATUS='NO_USER_RESPONSE'
                                                        3. 被叫在线，并且开启了voicemail，但是拒绝接听, HANGUP-CAUSE='NORMAL_CLEARING', variable_DIALSTATUS='SUCCESS' 无法分别出拒绝接听
                                                        4. 被叫在线，没有开启voicemail, 拒绝接听,则hangup_cause='CALL_REJECTED', variable_DIALSTATUS='CALL_REJECTED'
                                                        '''
                                                        dial_status = ev.getHeader('variable_DIALSTATUS')
                                                        if dial_status == 'NO_USER_RESPONSE': #情况2
                                                                pass
                                                        elif dial_status in ['CANCEL', 'SUCCESS']:  #情况1,3
                                                                pass
                                                        elif ev.getHeader('variable_sip_hangup_phrase') == 'Decline': #情况4
                                                                pass
                                                        hangup(con, ev)
                                                elif ev.getHeader('variable_CDR(calltype)') == '3':
                                                        # 预测外呼情况下的呼通和未呼通的cdr都在这里处理(同上面，通过hangup-cause来判断)
                                                        queue_hangup(con, ev)
                                                elif ev.getHeader('variable_CDR(calltype)') == '6':
                                                        # 机器人外呼情况下的呼通和未呼通的cdr都在这里处理(同上面，通过hangup-cause来判断)
                                                        hangup(con, ev)
                                                        check_miss_call_asr(con, ev)
                                        else:
                                                # print('non-dialplan: {}, the state1 is {}'.format(event_name, channel_state))
                                                pass

