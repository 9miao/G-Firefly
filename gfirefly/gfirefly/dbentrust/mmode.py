#coding:utf8
'''
Created on 2013-5-8

@author: lan (www.9miao.com)
'''
from memobject import MemObject,CACHE_TIMEOUT
import util
from gevent import Greenlet,queue
from gevent_zeromq import zmq
from gfirefly.utils.singleton import Singleton
from util import ToDBAddress
import traceback
from gtwisted.utils import log

MMODE_STATE_NEW = 1     #创建
MMODE_STATE_UPDATE = 2  #更新
MMODE_STATE_DEL = 3     #删除


class PKValueError(ValueError): 
    """
    """
    def __init__(self, data):
        ValueError.__init__(self)
        self.data = data
    def __str__(self):
        return "new record has no 'PK': %s" % (self.data)
    
class DBPub(Greenlet):
    """
    """
    __metaclass__ = Singleton
    
    def __init__(self, run=None, *args, **kwargs):
        Greenlet.__init__(self)
        self.isStart = False
        self.inbox = queue.Queue()
        context = zmq.Context()
        self.sock = context.socket(zmq.PUB)
        self.to_db_address = (ToDBAddress().m2db_host,ToDBAddress().m2db_port)
        
    def send(self,message):
        """
        """
        if not self.isStart:
            self.start()
        self.isStart=True
        self.inbox.put(message)
        
    def _run(self):
        """执行协议
        """
        address = 'tcp://%s:%s'%self.to_db_address
        self.sock.connect(address)
        while True:
            try:
                message = self.inbox.get()
                self.sock.send_pyobj(message)
            except Exception as e:
                log.err(_stuff=e,_why=traceback.format_exc())
                log.msg(str(message))

class MMode(MemObject):
    """内存数据模型，最终对应到的是表中的一条记录
    """
    def __init__(self, name,pk,data={},fk=None,**kw):
        """
        """
        MemObject.__init__(self, name,**kw)
        self._pk = pk
        self._fk = fk
        self.data = data
        
    def _update_fk(self,pk,old_fk_value,fk_value):
        """
        """
        tb_name = self._name.split(":")[0]
        old_name = '%s_fk:%s'%(tb_name,old_fk_value)
        old_fkmm = MFKMode(old_name)
        old_pklist = old_fkmm.get('pklist')
        if old_pklist is None:#如果外键列表没有生成,则重新生成
            props = {self._fk:old_fk_value}
            old_pklist = util.getAllPkByFkInDB(tb_name, self._pk, props)
        if old_pklist and pk in old_pklist:#清理原有的外键
            old_pklist.remove(pk)
            old_fkmm.update('pklist', old_pklist)
        if fk_value is None:
            return
        new_name = '%s_fk:%s'%(tb_name,fk_value)
        new_fkmm = MFKMode(new_name)
        new_pklist = new_fkmm.get('pklist')
        if new_pklist is None:
            props = {self._fk:fk_value}
            new_pklist=util.getAllPkByFkInDB(tb_name,self._pk, props)
        if pk not in new_pklist:
            new_pklist.append(pk)
            new_fkmm.update('pklist', new_pklist)
        
    def update(self, key, values):
        data = self.getData()
        if self._fk and self._fk==key:#判断外键是否更新
            fk = data.get(self._fk,"")
            pk = data.get(self._pk)
            self._update_fk(pk, fk, values)#更新外键
        data.update({key:values})
        result = MemObject.update(self, 'data',data)
        self.syncDB()
        return result
    
    def update_multi(self, mapping):
        data = self.getData()
        if self._fk and self._fk in mapping.keys():#查看外键是否在更新的map中
            fk = data.get(self._fk,"")
            new_fk = mapping.get(self._fk,fk)
            if new_fk!=fk:#查看外键的值是否发生了变化
                pk = data.get(self._pk)
                self._update_fk(pk, fk, new_fk)#更新外键
        data.update(mapping)
        result = MemObject.update(self, 'data',data)
        self.syncDB()
        return result
    
    def get_multi(self, keys):
        return MemObject.get_multi(self, keys)
    
    def getData(self):
        """获取data数据
        """
        data = self.get('data')
        if data:
            return data
        tablename,pk_value = self._name.split(':')
        props = {self._pk:int(pk_value)}
        record = util.GetOneRecordInfo(tablename,props)
        if record:
            self.data = record
            self.insert()
            return self.data
        return None
    
    def delete(self):
        """清理对象
        """
        self.syncDB(state=MMODE_STATE_DEL)
        if self._fk:
            data = self.getData()
            if data:
                fk = data.get(self._fk,"")
                pk = data.get(self._pk)
                self._update_fk(pk, fk, None)
        self.mdelete()
    
    def IsEffective(self):
        '''检测对象是否有效
        '''
        return True
        
    def syncDB(self,state=MMODE_STATE_UPDATE):
        """同步到数据库
        """
        tablename = self._name.split(':')[0]
        if state==MMODE_STATE_NEW:
            props = self.getData()
            pk = self._pk
            result = util.InsertIntoDB(tablename, props)
        elif state==MMODE_STATE_UPDATE:
            props = self.getData()
            pk = self._pk
            prere = {pk:props.get(pk)}
            sql = util.UpdateWithDictSQL(tablename, props, prere)
            DBPub().send((tablename,sql))
            result = True
        else:
            pk = self._pk
            props = self.getData()
            prere = {pk:props.get(pk)}
            result = util.DeleteFromDB(tablename,prere)
        return result
            
        
class MFKMode(MemObject):
    """外键内存数据模型
    """
    def __init__(self, name,pklist = []):
        MemObject.__init__(self, name)
        self.pklist = pklist
        
class MAdmin(object):
    """MMode对象管理，同一个MAdmin管理同一类的MMode，对应的是数据库中的某一种表
    """
    
    def __init__(self, name,pk,**kw):
        self._name = name
        self.pk = pk
        self._fk = kw.get('fk','')
        self.incrkey = kw.get('incrkey','')
        self.timeout = kw.get('timeout',CACHE_TIMEOUT)
        
    def load(self):
        '''读取数据到数据库中
        '''
        mmname = self._name
        recordlist = util.ReadDataFromDB(mmname)
        for record in recordlist:
            pk = record[self.pk]
            mm = MMode(self._name+':%s'%pk,self.pk,data=record,fk=self._fk,timeout=self.timeout)
            mm.insert()
    
    def getAllPkByFk(self,fk):
        '''根据外键获取主键列表
        '''
        name = '%s_fk:%s'%(self._name,fk)
        fkmm = MFKMode(name)
        pklist = fkmm.get('pklist')
        if pklist is not None:
            return pklist
        props = {self._fk:fk}
        dbkeylist = util.getAllPkByFkInDB(self._name, self.pk, props)
        name = '%s_fk:%s'%(self._name,fk)
        fkmm = MFKMode(name, pklist = dbkeylist)
        fkmm.insert()
        return dbkeylist
        
    def getObj(self,pk):
        '''根据主键，可以获得mmode对象的实例.\n
        >>> m = madmin.getObj(1)
        '''
        mm = MMode(self._name+':%s'%pk,self.pk,fk=self._fk,timeout=self.timeout)
        if mm.get('data'):
            return mm
        props = {self.pk:pk}
        record = util.GetOneRecordInfo(self._name,props)
        if not record:
            return None
        mm =  MMode(self._name+':%s'%pk,self.pk,data = record,fk=self._fk,timeout=self.timeout)
        mm.insert()
        return mm
    
    def getObjData(self,pk):
        '''根据主键，可以获得mmode对象的实例的数据.\n
        >>> m = madmin.getObjData(1)
        '''
        mm = MMode(self._name+':%s'%pk,self.pk,fk=self._fk,timeout=self.timeout)
        if not mm.IsEffective():
            return None
        data = mm.get('data')
        if data:
            return data
        props = {self.pk:pk}
        record = util.GetOneRecordInfo(self._name,props)
        if not record:
            return None
        mm =  MMode(self._name+':%s'%pk,self.pk,data = record,fk=self._fk,timeout=self.timeout)
        mm.insert()
        return record
        
    
    def getObjList(self,pklist):
        '''根据主键列表获取mmode对象的列表.\n
        >>> m = madmin.getObjList([1,2,3,4,5])
        '''
        _pklist = []
        objlist = []
        for pk in pklist:
            mm = MMode(self._name+':%s'%pk,self.pk,fk=self._fk,timeout=self.timeout)
            if not mm.IsEffective():
                continue
            if mm.get('data'):
                objlist.append(mm)
            else:
                _pklist.append(pk)
        if _pklist:
            recordlist = util.GetRecordList(self._name, self.pk,_pklist)
            for record in recordlist:
                pk = record[self.pk]
                mm =  MMode(self._name+':%s'%pk,self.pk,data = record,fk=self._fk,timeout=self.timeout)
                mm.insert()
                objlist.append(mm)
        return objlist
    
    def deleteMode(self,pk):
        '''根据主键删除内存中的某条记录信息，\n这里只是修改内存中的记录状态_state为删除状态.\n
        >>> m = madmin.deleteMode(1)
        '''
        mm = self.getObj(pk)
        if mm:
#             if self._fk:
#                 data = mm.get('data')
#                 if data:
#                     fk = data.get(self._fk,0)
#                     name = '%s_fk:%s'%(self._name,fk)
#                     fkmm = MFKMode(name)
#                     pklist = fkmm.get('pklist')
#                     if pklist and pk in pklist:
#                         pklist.remove(pk)
#                     fkmm.update('pklist', pklist)
            mm.delete()
        return True
    
#     def checkAll(self):
#         """同步内存中的数据到对应的数据表中。\n
#         >>> m = madmin.checkAll()
#         """
#         key = '%s:%s:'%(mclient._hostname,self._name)
#         _pklist = util.getallkeys(key, mclient.connection)
#         for pk in _pklist:
#             mm = MMode(self._name+':%s'%pk,self.pk,fk=self._fk)
#             if not mm.IsEffective():
#                 mm.mdelete()
#                 continue
#             if not mm.get('data'):
#                 continue
#             mm.checkSync(timeout=self._timeout)
#         self.deleteAllFk()
        
#     def deleteAllFk(self):
#         """删除所有的外键
#         """
#         key = '%s:%s_fk:'%(mclient._hostname,self._name)
#         _fklist = util.getallkeys(key, mclient.connection)
#         for fk in _fklist:
#             name = '%s_fk:%s'%(self._name,fk)
#             fkmm = MFKMode(name)
#             fkmm.mdelete()
        
    def new(self,data):
        """创建一个新的对象
        """
        incrkey = self.incrkey
        tablename = self._name
        if incrkey:
            result = util.InsertIntoDBAndReturnID(tablename, data)
            data[incrkey] = result[0]
            pk = data.get(self.pk)
            if pk is None:
                raise PKValueError(data)
            mm = MMode(self._name+':%s'%pk,self.pk,data=data,fk=self._fk,timeout=self.timeout)
        else:
            pk = data.get(self.pk)
            result = util.InsertIntoDB(tablename, data)
            if not result:
                raise util.SQLError()
            mm = MMode(self._name+':%s'%pk,self.pk,data=data,fk=self._fk,timeout=self.timeout)
        mm.insert()
        if self._fk:
            fk = data.get(self._fk,0)
            name = '%s_fk:%s'%(self._name,fk)
            fkmm = MFKMode(name)
            pklist = fkmm.get('pklist')
            pklist = self.getAllPkByFk(fk)
            pklist.append(pk)
            fkmm.update('pklist', pklist)
        return mm
    
    def insert(self):
        pass
    
        
if __name__=="__main__":
    from dbpool import dbpool
    from memclient import memcached_connect
    from madminanager import MAdminManager
    memcached_connect(["127.0.0.1:11211"])
    aa = {"default":{'host':"localhost",'user':'root',
        'passwd':'111',
        'db':'legend',
        'port':3306,
        'charset':'utf8'},
      "master":{'host':"localhost",'user':'root',
        'passwd':'111',
        'db':'test',
        'port':3306,
        'charset':'utf8'}
      }
    dbpool.initPool(aa)
    
    class router: 
        def db_for_read(self, **kw):
            return "master"
        def db_for_write(self, **kw):
            return "master"
    
    dbpool.bind_router(router)
    
    ma = MAdmin('tb_role_info','id',incrkey='id',fk="username")
    mm = ma.getObj(19)
    mm.update("username", "llllll")
    print ma.getAllPkByFk('lanjinmin')
    MAdminManager().checkAdmins()
    
    print "1111111111111111111"
    print ma.getAllPkByFk('lanjinmin')
    print ma.getAllPkByFk('llllll')
    import gevent
    
    gevent.sleep(100)
    
    

