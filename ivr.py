# -*- coding: UTF-8 -*-
from ccutils import *
from report_staffid import *
from check_miss_call import *


def statis_presskey(con,ivr_layer, row, key):
	info = con.getInfo()
	uuid = info.getHeader('Unique-ID')
	node_id = -1
	if key == 0:
		node_id = row.Key_0
	elif key == 1:
		node_id = row.Key_1
	elif key == 2:
		node_id = row.Key_2
	elif key == 3:
		node_id = row.Key_3
	elif key == 4:
		node_id = row.Key_4
	elif key == 5:
		node_id = row.Key_5
	elif key == 6:
		node_id = row.Key_6
	elif key == 7:
		node_id = row.Key_7
	elif key == 8:
		node_id = row.Key_8
	elif key == 9:
		node_id = row.Key_9
	elif key == -3:
		node_id = row.Key_Pound # '#'键
		key = '#'
	else:
		return

	sql = "select id from {} where id={}".format(Conf.IVR_MENU, node_id)
	row = db.get(sql)
	if not row:
		return False

	if ivr_layer < 4:
		press_key = info.getHeader('KEY{}'.format(ivr_layer))
		if press_key == '':
                        set_variable(con,'KEY{}',ivr_layer,key)

	return True


def get_datakey(con, file, escape_digits='',retry = 1, offset = 0):
	i = 0
	while True:
		i += 1
		result = con.stream_file(file, escape_digits, offset)
		datakey = chr(result['result']) if result['result'] else -1
		datakey = '-2' if datakey == '*' else datakey
		datakey = '-3' if datakey == '#' else datakey
		if datakey != -1:
			break
		if i == retry:
			break

	return datakey


def ivr_exec(con, num):
	uuid = con.getInfo().getHeader('Unique-ID')
	# IVRj进入时间
	result = 0
	weekday = datetime.today().weekday()
	weekday = weekday if weekday else 7
	sql = "select IVRTreeId from {} where Num='{}' and  substring(WeekDayStr,{},1)=1 and CURRENT_TIME() between StartTime and EndTime limit 1;".format(Conf.IVR_TOD, num, weekday)
	row = db.get(sql)
	node_id = row.IVRTreeId if row else 0
	if not node_id:	return
	# 如果有放音信号，则必须摘机
	con.execute('answer', uuid)
	tree_arr = []
	ivr_menu(con, node_id, tree_arr)


def ivr_menu(con, node_id, tree_arr):
        dial_str = None
        info = con.getInfo()
        if not info: return True
        uuid = info.getHeader('Unique-ID')
        domain_name = get_domain(info)

        p_tree_ar = tree_arr
        parent_id = tree_arr[len(tree_arr) - 1] if len(tree_arr) > 0 else node_id
        tree_arr.append(node_id)
        result = True
        sql = "select * from {} where id={}".format(Conf.IVR_MENU, node_id)
        row = db.get(sql)
        if not row: return result
        # 节点类型:1 放音节点 2人工节点 3挂机节点 4来电转接
        type = row.Type
        if type == 1:  # 放音节点
                sound_id = row.SoundId
                if sound_id < 0: con.execute('hangup', uuid)
                # 重复播放次数
                replay_count = row.ReplayCount
                # 有效按键字符串
                escape_digits = ''
                escape_digits += ('0' if row.Key_0 != -1 else '')
                escape_digits += ('1' if row.Key_1 != -1 else '')
                escape_digits += ('2' if row.Key_2 != -1 else '')
                escape_digits += ('3' if row.Key_3 != -1 else '')
                escape_digits += ('4' if row.Key_4 != -1 else '')
                escape_digits += ('5' if row.Key_5 != -1 else '')
                escape_digits += ('6' if row.Key_6 != -1 else '')
                escape_digits += ('7' if row.Key_7 != -1 else '')
                escape_digits += ('8' if row.Key_8 != -1 else '')
                escape_digits += ('9' if row.Key_9 != -1 else '')
                escape_digits += ('*' if row.Key_Asterisk != -1 else '')
                escape_digits += ('#' if row.Key_Pound != -1 else '')
                sql = "select FileName from {} where id={}".format(Conf.IVR_SOUND, sound_id)
                row1 = db.get(sql)
                sound_file = row1.FileName if row1 else ''
                sound_file += '.wav'
                # data = get_datakey(Conf.SOUND_PATH+sound_file, escape_digits, replay_count)
                args = '1 1 {} 5000 # {} {} mykey [\\d+,*,#]'.format(replay_count,
                                                                     Conf.SOUND_PATH + sound_file.encode('utf-8'),
                                                                     Conf.SOUND_PATH + 'empty.gsm')
                ret = con.execute('play_and_get_digits', args)
                con.setEventLock('1')
                data = get_variable(con, 'play_and_get_digits', 'mykey')
                # 按键统计
                # 只记录0-9 #这些按键
                if data and data != '*' and data != '#':
                        data = int(data)

                if data >= 0 or data == -3:
                        # 语音层
                        ivr_layer = len(tree_arr)
                        statis_presskey(con, ivr_layer, row, data)
                if data == 0:
                        result = ivr_menu(con, row.Key_0, tree_arr)
                elif data == 1:
                        result = ivr_menu(con, row.Key_1, tree_arr)
                elif data == 2:
                        result = ivr_menu(con, row.Key_2, tree_arr)
                elif data == 3:
                        result = ivr_menu(con, row.Key_3, tree_arr)
                elif data == 4:
                        result = ivr_menu(con, row.Key_4, tree_arr)
                elif data == 5:
                        result = ivr_menu(con, row.Key_5, tree_arr)
                elif data == 6:
                        result = ivr_menu(con, row.Key_6, tree_arr)
                elif data == 7:
                        result = ivr_menu(con, row.Key_7, tree_arr)
                elif data == 8:
                        result = ivr_menu(con, row.Key_8, tree_arr)
                elif data == 9:
                        result = ivr_menu(con, row.Key_9, tree_arr)
                elif data == None:
                        # 放音结束
                        if row.EndEvent == -1:
                                con.execute('hangup', uuid)
                        ivr_menu(con, row.EndEvent, tree_arr)
                        return result
                elif data == '*':
                        # 用户按返回上一层
                        ret = tree_arr.pop()
                        # tree_arr.pop()
                        result = ivr_menu(con, parent_id, tree_arr)
                        return result
                elif data == '#':
                        result = ivr_menu(con, row.Key_Pound, tree_arr)
                        return result
                else:
                        return result
                # 如果是无效按键
                if not result:
                        ivr_menu(con, node_id, p_tree_ar)
        elif type == 2:  # 人工台节点
                queue_name = row.QueueName
                if queue_name:
                        set_variable(con, 'U_QUEUE', queue_name)
                        duration = info.getHeader('variable_CDR(duration)')
                        set_variable(con, 'AGITIME', duration)
                        staff_id, exten = report_staffid(con)
                        caller = info.getHeader('Caller-Caller-ID-Number')
                        records(con, exten, caller, staff_id, uuid) #todo 录音必须放在bridge之前否则没作用，为何？
                        queue_bridge(con.execute, staff_id, domain_name, queue_name)
                exit(0)
        elif type == 3:  # 挂机节点
                con.execute('hangup', uuid)
                return True
        elif type == 4:  # 来电转接
                # 工号
                exten_num = row.ExtenNum
                ##通过公司获取第一下外呼号码
                company_id = row.CompanyId
                sys_num = 0
                # 如果是工号
                if len(exten_num) == 4:
                        # 获取此工号绑定的分机
                        sql = 'select Exten from {} where staffid="{}"'.format(Conf.R_STAFFIDEXTEN_SHARE, exten_num)
                        row2 = db.get(sql)
                        exten = row2.Exten if row2 else 0
                        if exten:
                                exten_status = get_extension_state(exten)
                                # 分机空闲时进行呼叫
                                if not exten_status:
                                        duration = info.getHeader('variable_CDR(duration)')
                                        multiset(con, ['CDR(Exten)',exten,'StaffId',exten_num,'CDR(StaffId)',exten_num,'AGITIME',duration,'CALL_STR','SIP/{}'.format(exten)])
                                        dial_str = 'sofia/internal/{}%{}'.format(exten_num, domain_name)
                                elif exten_status == 4 or exten_status == -1:
                                        con.execute('playback', Conf.SOUND_PATH + 'Ivr_012.wav')  # 分机未登录
                                else:
                                        con.execute('playback', Conf.SOUND_PATH + 'Ivr_021.wav')  # 坐席正忙请稍后再拨
                        else:
                                # 分机未登录
                                con.execute('playback', Conf.SOUND_PATH + 'Ivr_012.wav', uuid)
                                pass
                else:
                        sys_num = info.getHeader('variable_EXTE')
                        if sys_num:
                                exten_num = get_num(exten_num)
                                duration = info.getHeader('variable_CDR(duration)')
                                multiset(con, ['TRFER_PHONE',exten_num, 'AGITIME',duration,'CALL_STR','SIP{}/{}'.format(sys_num, exten_num)])
                                dial_str = 'sofia/internal/{}%{}'.format(exten_num, domain_name)
        elif type == 5:
                dial_str = None
                # 转接分机
                # 总机工号
                exten_num = row.ExtenNum
                sys_num = 0
                args = '1 5 3 5000 # ' + Conf.SOUND_PATH + 'Ivr_022.wav ' + Conf.SOUND_PATH + 'empty.gsm staffid \\d+'
                ret = con.execute('play_and_get_digits', args)
                StaffId = get_variable(con, 'play_and_get_digits', 'staffid')
                if StaffId == '0':
                        # 转总机
                        if len(exten_num) == 4:
                                # todo 获取此分机绑定的工号(应该是工号绑定的分机吧??)
                                sql = 'select Exten from {} where StaffId={}'.format(Conf.R_STAFFIDEXTEN_SHARE, exten_num)
                                row = db.get(sql)
                                exten = row.Exten if row else 0
                                if exten:
                                        multiset(con, ['CDR(Exten)',exten,'StaffId',exten_num,'CDR(StaffId)',exten_num])
                                        exten_status = get_extension_state(exten)  # 取当前分机状态
                                        if exten_status:
                                                con.execute('playback', Conf.SOUND_PATH + 'Ivr_021.wav', uuid)  # 坐席正忙请稍后再拨
                                        else:
                                                duration = info.getHeader('variable_CDR(duration)')
                                                multiset(con, ['AGITIME',duration,'CALL_STR','SIP/{}'.format(exten)])
                                                # con.execute('Goto', 'transfer', uuid)
                                                dial_str = 'sofia/internal/{}%{}'.format(exten_num, domain_name)
                                else:
                                        # 分机未登录
                                        con.execute('playback', Conf.SOUND_PATH + 'Ivr_012.wav', uuid)
                        else:
                                # 以呼入号码作为处呼主叫
                                sys_num = info.getHeader('variable_EXTE')
                                if sys_num:
                                        exten_num = get_num(exten_num)
                                        duration = info.getHeader('variable_CDR(duration)')
                                        multiset(con, ['TRFER_PHONE',exten_num,'AGITIME',duration,'CALL_STR','SIP/{}/{}'.format(sys_num,exten_num)])
                                        dial_str = 'sofia/internal/{}%{}'.format(exten_num, domain_name)
                                        # con.execute('Goto', 'transfer', uuid)
                elif len(StaffId) == 4:
                        sql = 'select Exten from {} where StaffId = {} limit 1'.format(Conf.R_STAFFIDEXTEN_SHARE, StaffId)
                        row = db.get(sql)
                        exten_num = row.Exten if row else 0
                        if exten_num:
                                duration = info.getHeader('variable_CDR(duration')
                                multiset(con,['CDR(Exten)',exten_num,'StaffId',StaffId,'CDR(StaffId)',StaffId,'AGITIME',duration,'CALL_STR','SIP/{}'.format(exten_num)])
                                exten_status = get_extension_state(exten_num)
                                if not exten_status:
                                        dial_str = 'sofia/internal/{}%{}'.format(exten_num, domain_name)
                                elif exten_status == 4 or exten_status == -1:
                                        con.execute('playback', Conf.SOUND_PATH + 'Ivr_012.wav')  # 分机未登录
                                else:
                                        con.execute('playback', Conf.SOUND_PATH + 'Ivr_021.wav')  # 坐席正忙请稍后再拨
                                # con.execute('Goto', 'transfer', uuid)
                        else:
                                # 分机未登录
                                con.execute('playback', Conf.SOUND_PATH + 'Ivr_012.wav', uuid)
        else:
                duration = info.getHeader('variable_CDR(duration)')
                set_variable(con,'AGITIME', duration)
                con.execute('hangup', uuid)
        if dial_str:
                set_variable(con, 'CDR(DIALSTATUS)', 'answered')
                con.execute('bridge', dial_str)
                exit(0)
                return True
        else:
                set_variable(con, 'DIASTATUS123', 'missed')
                return False