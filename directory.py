#!/usr/bin/python3.6
import sys
import freeswitch
# sys.path.append('/Library/Python/2.7/site-packages')
import MySQLdb


print '********************************>>>>>'

def fsapi(session, stream, env, args):
    """ Handles API calls (from fs_cli, dialplan HTTP, etc.).   Default name is 'fsapi', but it can be overridden with <modname>::<function>   `session` is a session object when called from the dial plan or the string "na" when not. `stream` is a switch_stream. Anything written with stream.write() is returned to the caller. `env` is a switch_event. `args` is a string with all the args passed after the module name.   """
    if args == '':
        stream.write("fsapi called with no arguments2.\n")
    else:
        stream.write("fsapi called with these arguments1: %s\n" % args)
    stream.write(env.serialize())
def handler(session, args):
    """ 'handler' is the default function name for apps.   It can be overridden with <modname>::<function>   `session` is a session object `args` is a string with all the args passed after the module name   """
    # freeswitch.consoleLog('info', 'Answering call from Python.\n')
    # freeswitch.consoleLog('info', 'Arguments: %s\n' % args)
  
    # session.answer()
    # session.setHangupHook(hangup_hook)
    # session.setInputCallback(input_callback)
    # session.execute("playback", session.getVariable("hold_music"))
    freeswitch.consoleLog("NOTICE","hereherehereherehereherehereherehereherehereherehereherehereherehereherehereherehere\r\n")
    if args == '':
    	freeswitch.consoleLog('info', 'hanlder called with no arguments')
    else:
    	freeswitch.consoleLog('info', 'handler called with arguments: %s' % args)

def xml_fetch(params,params1):
	""" Bind to an XML lookup.   `params` is a switch_event with all the relevant data about what is being searched for in the XML registry.   """
	freeswitch.consoleLog("NOTICE","the event is: ..... %s " % params.serialize())
	# print ('the event is: %s' % params.serialize())
	user = params.getHeader('sip_auth_username')
	domain_name = params.getHeader('sip_auth_realm')
	got = get_user(user)
	if got is not ():
		xml = '''
			<document type="freeswitch/xml"> 
			  <section name="directory"> 
			    <domain name="%s"> 
			      <params> 
			        <param name="dial-string" value="{presence_id=${dialed_user}@${dialed_domain}}${sofia_contact(${dialed_user}@${dialed_domain})}"/> 
			      </params> 
			      <groups> 
			        <group name="default"> 
			          <users> 
			            <user id="%s"> 
			              <params> 
			                <param name="password" value="%s"/> 
			                </params> 
			              <variables> 
			                <variable name="user_context" value="%s"/> 
			              </variables> 
			            </user> 
			          </users> 
			        </group> 
			      </groups> 
			    </domain> 
			  </section>
			</document>
			''' % (domain_name, user, got[0], got[1])
	else:
		xml = ''
	freeswitch.consoleLog('NOTICE', 'the final xml is: %s' % xml)	
	return xml

def runtime(args):
    """ Run a function in a thread (eg.: when called from fs_cli `pyrun`).   `args` is a string with all the args passed after the module name.   """
    print args + "\n"

def get_user(user, tbl = 'cfg_sip', db = 'u_crm_db'):
	if user is None:
		return ()
	result = ()
	try:
		conn = MySQLdb.connect(host = 'localhost', user = 'root', passwd = '', db = 'u_crm_db', port = 3306)
		cur = conn.cursor()
		sql = 'select secret,context from %s where name = %s' % (tbl, user)
		freeswitch.consoleLog('NOTICE', 'sql is: %s\n' % sql)
		rows = cur.execute(sql)
		freeswitch.consoleLog('NOTICE', 'the rows is:-------->{}'.format(rows))
		if rows > 0:
			result = cur.fetchone()
		cur.close()
		conn.close()
		return result
	except MySQLdb.Error as e:
		print ("Mysql Error %d: %s" % (e.args[0], e.args[1]))
		return result


	
