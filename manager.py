# -*- coding: UTF-8 -*-

from ccutils import *
from mysql_wrapper import Conf

def manager(con, *args):
        if not args:  # 外联情况
                info = con.getInfo()
        else:
                info = args[0]  # 这里用info命名不太恰当但是历史原因就暂时info(时间上是ev--event)

        exten = info.getHeader('caller-caller-id-number')
        callee = info.getHeader('variable_sip_to_user')  # 或者caller-destination-number
        uuid = info.getHeader('variable_uuid')
        con.execute('answer', uuid)
        # 通过分机获取工号
        sql = 'select StaffId from' + Conf.R_STAFFIDEXTEN_SHARE + 'where Exten = {}'.format(exten)
        row = db.get(sql)
        StaffId = row.StaffId if row else 0
        # 预测队列加入
        if callee == '010':
                # 如果号码未绑定或者分机不在线
                if not StaffId or not is_online(StaffId):
                        # 分机未登录
                        con.execute('playback', Conf.SOUND_PATH+'Ivr_012.wav', uuid)
                        return True
                sql = 'select ForecastId from' + Conf.FORECAST_IVRLOGOUT + 'where StaffId = {}'.format(StaffId)
                row = db.get(sql)
                forecast_id = row.ForecastId if row else 0
                if not forecast_id:
                        sql = "select ForecastId from" + Conf.FORECAST_QUEUE + "where staffid='{}' limit 1;".format(StaffId)
                        row = db.get(sql)
                        forecast_id = row.ForecastId if row else 0
                        if not forecast_id:
                                # 队列加入失败
                                con.execute('playback', Conf.SOUND_PATH+'Ivr_016.wav', uuid)
                                return  True

                queue_name = 'autocall_' + str(forecast_id)
                # 加入预测队列
                add_queue(exten, queue_name)
                # sql = "insert into" + Conf.FORECAST_QUEUE +"(ForecastId,Queue_Name,StaffId) values({},'{}','{}') ON DUPLICATE KEY UPDATE Queue_Name='{}';".format(forecast_id, queue_name, StaffId, queue_name)
                sql = 'insert into forecast_queue (ForecastId, Queue_Name, StaffId, LastNum) values ({}, "{}", "{}", "") ON DUPLICATE KEY UPDATE Queue_name = "{}"'.format(forecast_id, queue_name, StaffId, queue_name)
                db.execute(sql)
                sql = "delete from"+Conf.FORECAST_IVRLOGOUT + "where StaffId='{}' ;".format(StaffId)
                db.execute(sql)
                # 队列加入成功
                con.execute('playback', Conf.SOUND_PATH+'Ivr_015.wav', uuid)
                return True
        elif callee == '011':
                # 如果号码未绑定或者分机不在线
                if not StaffId or not is_online(StaffId):
                        # 分机未登录
                        con.execute('playback', Conf.SOUND_PATH+'Ivr_012.wav', uuid)
                        return True
                sql = "select ForecastId from"+Conf.FORECAST_QUEUE + "where StaffId='{}' limit 1;".format(StaffId)
                row = db.get(sql)
                forecast_id = row.ForecastId if row else 0
                if not forecast_id:
                        # 队列退出成功
                        con.execute('playback', Conf.SOUND_PATH+'Ivr_017.wav', uuid)
                        return True
                remove_queue_member(exten, 'autocall_'+str(forecast_id))
                sql = "insert into"+Conf.FORECAST_IVRLOGOUT+"(ForecastId,StaffId) values('{}','{}') ON DUPLICATE KEY UPDATE ForecastId='{}' ;".format(forecast_id, StaffId, forecast_id)
                db.execute(sql)
                sql = "delete from"+Conf.FORECAST_QUEUE+"where StaffId='{}' ;".format(StaffId)
                db.execute(sql)
                # 队列退出成功
                con.execute('playback', Conf.SOUND_PATH+'Ivr_017.wav', uuid)
                return True
        elif callee == '007':
                con.execute('say', 'en number iterated ' + str(exten), uuid)
                return True

        return True
