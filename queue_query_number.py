# -*- coding: UTF-8 -*-

import ccutils
from mysql_wrapper import Conf
db = ccutils.db
def get_queue_name(staff_id):
        return 'lifeng'

def queue_query_number(con, *args):
        if not args:  # 外联情况
                info = con.getInfo()
        else:
                info = args[0]  # 这里用info命名不太恰当但是历史原因就暂时info(时间上是ev--event)

        caller = info.getHeader('caller-caller-id-number')
        callee = info.getHeader('variable_sip_to_user')  # 或者caller-destination-number
        uuid = info.getHeader('Unique-ID')
        con.setEventLock('1')
        con.execute('answer', uuid)

    # 通过分机获取工号
        sql = 'select StaffId from ' + Conf.R_STAFFIDEXTEN_SHARE + ' where Exten = {}'.format(caller)
        row = db.get(sql)
        StaffId = row.StaffId if row else 0

        if not StaffId:
                isOutline = ccutils.is_online(StaffId)
                # 此分机不在线，请重新输入。
                if not isOutline:
                        # 分机未登录
                        con.execute('playback', Conf.SOUND_PATH+'Ivr_012.wav', uuid)
                        con.execute('say', 'en number iterated StaffId', uuid)
                        return True


        queue_name = get_queue_name(StaffId)
        if queue_name:
                sql = "select Lastnum from  {} where Queue_Name='{}' and StaffId={}".format(Conf.FORECAST_QUEUE, queue_name, StaffId)
                row = db.get(sql)
                lastnum = row.Lastnum if row else 0
                if not lastnum:
                        lastnum = 0
                index = 0
                data = '1'
                while True:
                        if data == '1':
                                con.execute('playback', Conf.SOUND_PATH+'Ivr_013.wav', uuid)
                                con.execute('say', 'en number iterated {}'.format(lastnum), uuid)
                        con.execute('play_and_get_digits','1 1 3 5000 # {}Ivr_014.wav {} empty.gsm data \\d+'.format(Conf.SOUND_PATH, Conf.SOUND_PATH))
                        data = ccutils.get_variable(con, 'play_and_get_digits', 'data')
                        index += 1
                        if index == 30:
                                break


