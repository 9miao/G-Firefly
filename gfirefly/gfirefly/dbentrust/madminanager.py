#coding:utf8
'''
Created on 2013-5-22

@author: lan (www.9miao.com)
'''
from gfirefly.utils.singleton import Singleton
from gevent_zeromq import zmq 
import gevent
from util import excuteSQL
# import marshal
from util import ToDBAddress,M2DB_PORT
from gtwisted.utils import log
import traceback

class MAdminManager:
    """一个单例管理器。作为所有madmin的管理者
    """
    __metaclass__ = Singleton
    
    def __init__(self):
        """初始化所有管理的的madmin的集合，放在self.admins中
        """
        self.isStart = False
        self.to_db_port = None
        
    def registe(self,admin):
        """注册一个madmin对象到管理中.
        >>> madmin = MAdmin('tb_registe','characterId',incrkey='id')
        >>> MAdminManager().registe(madmin)
        """
        pass
#         self.admins[admin._name] = admin

    def _run(self):
        """执行协议
        """
        while True:
#             msg = self.sock.recv()
            try:
                pyobj = self.sock.recv_pyobj()
                tablename,sql = pyobj
                excuteSQL(tablename, sql)
            except Exception,e:
                log.err(_stuff=e,_why=traceback.format_exc())
    
    def checkAdmins(self,port=M2DB_PORT):
        """遍历所有的madmin，与数据库进行同步。

        >>>MAdminManager().checkAdmins(port=M2DB_PORT)
        """
        if self.isStart:
            return
        self.isStart=True
        context = zmq.Context()
        self.sock = context.socket(zmq.SUB)
        
        if port==M2DB_PORT:
            port = ToDBAddress().m2db_port
        address = 'tcp://*:%s'%port
        self.sock.bind(address)
        self.sock.setsockopt(zmq.SUBSCRIBE, "")
        gevent.spawn(self._run)
        

        
