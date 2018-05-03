# -*- coding: UTF-8 -*-

import ccutils
from mysql_wrapper import Conf


db = ccutils.db
def login(con, *args):
        if not args:  # 外联情况
                info = con.getInfo()
        else:
                info = args[0]  # 这里用info命名不太恰当但是历史原因就暂时info(时间上是ev--event)

        con.setEventLock('1')
        """ 'handler' is the default function name for apps.   It can be overridden with <modname>::<function>   
        `session` is a session object `args` is a string with all the args passed after the module name   """
        # get caller number

        exten = info.getHeader('channel-caller-id-number')
        uuid = info.getHeader('Unique-ID')
        isOutline = 0

        query = 'select StaffId from {} where Exten = {} limit 1'.format(Conf.R_STAFFIDEXTEN_SHARE, exten.strip())
        print('sql is : {}'.format(query))

        StaffId = 0
        row = db.get(query)
        if row:
                StaffId = row.StaffId
        if StaffId:
                # 此分机被别的工号绑定过，要确定这个工号是不是正在线？
                isOutline = ccutils.is_online(StaffId)
                if isOutline:
                        # 此工号已经在线(表示你想要用的分机已经被占用)，你需要换一个分机继续输入你的工号，不过在分机之前先听听系统告诉你哪个工号占有了此分机,
                        # 播放语音提示绑定的工号为
                        data = con.execute('playback', Conf.SOUND_PATH + 'Ivr_005.wav')
                        # con.setEventLock('1')
                        con.execute('say', 'en number iterated ' + str(StaffId))
                        # con.setEventLock('1')
                        return True

        # 没有绑定的情况(包括1.查到了此分机曾经被绑定过但是绑定的工号目前不在线 2.压根没有查到有工号绑定过此分机;反正1，2都说明此分机可用)
        index = 0
        id1 = 0
        while True:
                index += 1
                # 请输入工号并以'#'号结束
                args = '3 21 3 5000 # '+Conf.SOUND_PATH+'Ivr_001.wav '+Conf.SOUND_PATH+'empty.gsm data1 \\d+'
                ret = con.execute('play_and_get_digits', args)
                StaffId = ccutils.get_variable(con, 'play_and_get_digits', 'data1')
                # 如果工号前缀与分机前缀不一致，则不允许绑定
                if StaffId[0] != exten[0]:
                        print('输入了非法的工号后的语音提示 {}'.format(StaffId))
                        # 播放分机未登录
                        con.execute('playback', Conf.SOUND_PATH + 'Ivr_012.wav')
                        # con.setEventLock('1')
                        return True

                # 此工号已经在线，请重新输入
                # 这里似乎少了一句判断刚刚输入的工号是否已经被占用了???
                isOutline = ccutils.is_online(StaffId)
                if isOutline:
                        # 这里面的处理是:你想要用的工号已经被人用了，语音播报这个工号目前绑定的分机
                        query = 'select Exten from {} where StaffId = {} limit 1'.format(Conf.R_STAFFIDEXTEN_SHARE, StaffId)
                        o_exten = db.get(query).Exten
                        con.execute('playback', Conf.SOUND_PATH + 'Ivr_008.wav')
                        # con.setEventLock('1')
                        con.execute('say', 'en number iterated {}'.format(str(o_exten)))
                        # con.setEventLock('1')
                        print('想用的工号已经被占用了的语音提示{}'.format(StaffId))
                        continue

                # 请输入密码并以'#'结束
                con.execute('play_and_get_digits', '3 21 3 5000 "#" '+Conf.SOUND_PATH+'Ivr_002.wav '+Conf.SOUND_PATH+'empty.gsm data2 \\d+')
                passwd = ccutils.get_variable(con, 'play_and_get_digits', 'data2')
                sql = '''select a.Id, a.CompanyId from {} a
                 join {} b on a.RoleId=b.Id and b.`Type` in (3,4)
                 join {} c on a.CompanyId = c.Id
                 where c.Enabled=1 and a.Enabled=1 and StaffId = {}
                 and Password = Password({})'''.format(Conf.CRM_USERINFO, Conf.CRM_ROLE, Conf.CRM_COMPANYINFO, StaffId, passwd)
                id1 = 0
                CompanyId = 0
                r = db.get(sql)
                if r:
                        id1 = r.Id
                        CompanyId = r.CompanyId
                if id1:
                        if not ccutils.isAuthIP(CompanyId, exten):
                                # IP地址验证错误
                                con.execute('playback', Conf.SOUND_PATH + 'Ivr_010.wav', uuid)
                                # con.setEventLock('1')
                        else:
                                break
                                # 密码错误请重新输入
                print('密码错误的语音提示{}'.format(StaffId))
                con.execute('playback', Conf.SOUND_PATH + 'Ivr_004.wav', uuid)
                # con.setEventLock('1')
                if index == 3:
                        break


        # 如果没有此工号则退出
        if id1 == 0:
                return True

        # 工号必须为4位数字
        if not StaffId.isdigit() or not len(StaffId) == 4:
                return True
        r = ccutils.ivr_rse_login(StaffId, exten, CompanyId)

        if r:
                '''此分机或者工号已被占用(在你通过语音登录的同时，有人比你手快已经抢先通过另外的分机语音登录了相同的工号，或者通过web登录了相同的工号，或者是绑定了相同的分机)
                语音播报被抢先绑定的工号为或者分机是:...'''
                con.execute('playback', Conf.SOUND_PATH + 'Ivr_005.wav', uuid)
                # con.setEventLock('1')
                con.execute('say', 'en number iterated ' + str(exten), uuid)
                # con.setEventLock('1')
                con.execute('say', 'en number iterated ' + str(StaffId), uuid)
                # con.setEventLock('1')
                return True

        # 登录成功
        con.execute('playback', Conf.SOUND_PATH + 'Ivr_006.wav', uuid)
        return True
