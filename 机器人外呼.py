# -*- coding: UTF-8 -*-

# originate.py -- a python wrapper of originate() for making a outbound call via esl

import sys
import ESL
from optparse import OptionParser
import pdb
import datetime
ar = {'caller_name': '8803<lifeng>',
      'caller': 8803,
      'callee': "1234_123456",
      'CompanyId': 3,
      'linkedid': 5,
      'PROID': 0,
      'customerid': 4,
      'StaffId': 8803,
      'ClassifId': 10,
      'calltype': 6,  #机器人外呼
      
      'batchid':0,
      'name':'lifeng',
      'address':'闵行区图书馆',
      'sex': 0,
      'email':'lifengxxxx@139.com',
      'CallOutStatus':0,
      'CallResult':'sucess',
      'UpdateTime':'{}'.format(datetime.datetime.now()),
      'CreateTime':'{}'.format(datetime.datetime.now()),
      'dcontext': 'call_out',
      'Sysnum': 1000,
      'CDR(DIALSTATUS)': 'online',
      'extension': 'from-asrcall',
      'gateway': '88851063331',
      'host': '192.168.0.114'}


def originate(**args):
        con = ESL.ESLconnection('localhost', '8021', 'ClueCon')
        if con.connected():

                '''
                其实originate命令很强大，这里不必须非要用channel variable:sip_callee_id_number, 任意变量都可以传入dialplan， 例如originate {x=1000,...} ... 在dialplan中就可以像获取channel variable一样获取到x, 就是说originate {}... 命令中, {}里的变量自动是全局变量/(或者说是自定义通道变量??)!!!
                '''
                '''下面是web click-to-dial功能调用python的时候应该传递的参数，包括
                自定义的通话参数
                CRM方面的参数
                。。。
                '''
                # 注意originate里传参数的时候，各个参数之间不能有空格！！！！
                # 注意连字符后面不能有空格....!!!!!
                cmd = 'originate ' \
                      '{{caller_id_name={},' \
                      'sip_callee_id_number={},' \
                      'CDR(CompanyId)={},' \
                      'CDR(PROID)={},' \
                      'CDR(StaffId)={},' \
                      'CDR(customerid)={},' \
                      'CDR(ClassifId)={},' \
                      'CDR(calltype)={},' \
                      'CALLTYPE={},'  \
                      'CDR(dcontext)={},' \
                      'Sysnum={},' \
                      'CDR(callerid)={},'\
                      'CDR(batchid)={},'\
                      'CDR(name)={},'\
                      'CDR(phone)={},' \
                      'CDR(address)={},' \
                      'CDR(sex)={},' \
                      'CDR(email)={},' \
                      'CDR(CallOutStatus)={},' \
                      'CDR(CallResult)={},' \
                      'CDR(UpdateTime)={},' \
                      'CDR(CreateTime)={},'.format(
                                args['caller_name'],
                                args['callee'],
                                args['CompanyId'],
                                args['PROID'],
                                args['StaffId'],
                                args['customerid'],
                                args['ClassifId'],
                                args['calltype'],
                                args['calltype'],
                                args['dcontext'],
                                args['Sysnum'],
                                args['gateway'],
                                args['batchid'],
                                args['name'],
                                args['caller'],
                                args['address'],
                                args['sex'],
                                args['email'],
                                args['CallOutStatus'],
                                args['CallResult'],
                                "'"+args['UpdateTime']+"'",
                                "'"+args['CreateTime']+"'"
                        )
                if args.has_key('gateway') and args.get('gateway'):
                        cmd += 'gateway={},'.format(args['gateway'])
                        cmd += 'dial_str={{origination_caller_id_number=8800200}}sofia/gateway/{}/{},'.format(args['gateway'], args['callee'])
                else:
                        cmd += 'dial_str=sofia/internal/{},'.format(args['callee'])

                cmd += 'CDR(DIALSTATUS)={}}}'.format(args['CDR(DIALSTATUS)'])
                cmd += 'sofia/internal/{}%{} {} XML call_out'.format(args['caller'], args['host'], args['extension'])

                print ("originate command is: ", cmd)

                con.bgapi(cmd)
        else:
                print ('fs的esl socket未能连接')


if __name__ == '__main__':
        # pdb.set_trace()
        originate(**ar)
