#coding:utf8
'''
Created on 2015-1-3

@author: root
'''
from memfields import MemObj,MemFields
import util

MMODE_STATE_ORI = 1     #未变更
MMODE_STATE_NEW = 2     #创建
MMODE_STATE_UPDATE = 3  #更新
MMODE_STATE_DEL = 4     #删除

class PKValueError(ValueError):
    """
    """
    def __init__(self, data):
        ValueError.__init__(self)
        self.data = data
    def __str__(self):
        return "new record has no 'PK': %s" % (self.data)
    
class MemModel(MemObj):
    
    def __init__(self,name,pk,data={},**kw):
        MemObj.__init__(self, name,**kw)
        self.pk = pk
        dataField = MemFields(data)
        self.data = dataField
        self.initFields()
        
    def __getattribute__(self, attr):
        _value = object.__getattribute__(self,attr)
        value = MemObj.__getattribute__(self, attr)
        if attr=="data":
            if not value:
                tablename,pid = self._name.split(':')
                props = {self.pk:int(pid)}
                record = util.GetOneRecordInfo(tablename,props)
                if record:
                    _value.setValue(record)
                    return record
        return value
    
    def delete(self):
        """
        """
        tablename,pid = self._name.split(':')
        pk = self.pk
        prere = {pk:int(pid)}
        result = util.DeleteFromDB(tablename,prere)
        self.mdelete()
        return result
        
    def syncDB(self):
        """同步到数据库
        """
        tablename = self._name.split(':')[0]
        data_item = self.__dict__.get("data")
        data_item.setValue(data_item.value)
        if self._cas:
            self.release()
        props = self.data
        pk = self.pk
        prere = {pk:props.get(pk)}
        result = util.UpdateWithDict(tablename, props, prere)
        return result
    
    save = syncDB
    
    def __repr__(self):
        """
        """
        return "<MemModel:(%s) %s>"%(self._name,self.data)
    
    def __str__(self):
        """
        """
        return "<MemModel:(%s) %s>"%(self._name,self.data)

class MemAdmin(object):
    
    def __init__(self, name,pk,**kw):
        self.name = name
        self.pk = pk
        self.kw = kw
        self.incrkey = kw.get('incrkey','')
        
    def load(self):
        '''读取数据到数据库中
        '''
        mmname = self.name
        recordlist = util.ReadDataFromDB(mmname)
        for record in recordlist:
            pk = record[self.pk]
            mm = MemModel(self.name+':%s'%pk,self.pk,data=record,**self.kw)
            mm.insert()
            
    def new(self,data):
        """创建一个新的对象
        """
        incrkey = self.incrkey
        tablename = self.name
        if incrkey:
            result = util.InsertIntoDBAndReturnID(tablename, data)
            data[incrkey] = result
            pk = data.get(self.pk)
            if pk is None:
                raise PKValueError(data)
            mm = MemModel(self.name+':%s'%pk,self.pk,data=data,**self.kw)
            setattr(mm,incrkey,pk)
        else:
            pk = data.get(self.pk)
            result = util.InsertIntoDB(tablename, data)
            if not result:
                raise util.SQLError()
            mm = MemModel(self.name+':%s'%pk,self.pk,data=data,**self.kw)
        mm.insert()
        return mm
        
    def getObj(self,pk):
        '''根据主键，可以获得mmode对象的实例.
        '''
        mm = MemModel(self.name+':%s'%pk,self.pk,**self.kw)
        if mm.data:
            return mm
        else:
            return None
    
    def getAllPkByFk(self,**kw):
        """
        """
        dbkeylist = util.getAllPkByFkInDB(self._name, self._pk, kw)
        return dbkeylist
    
    def getObjList(self,pklist):
        '''根据主键列表获取mmode对象的列表.\n
        >>> m = madmin.getObjList([1,2,3,4,5])
        '''
        objlist = []
        for pk in pklist:
            mm = MemModel(self.name+':%s'%pk,self.pk,**self.kw)
            objlist.append(mm)
        return objlist
    
        
if __name__=="__main__":
    from dbpool import dbpool
    from memclient import memcached_connect
    memcached_connect(["127.0.0.1:11222"])
    from memclient import mclient
    import time
    aa = {"default":{'host':"localhost",'user':'root',
            'passwd':'111',
            'db':'legend',
            'port':3306,
            'charset':'utf8'},
          }
    dbpool.initPool(aa)

    ma = MemAdmin('tb_role_info','id',incrkey='id',cas=True)
    ma.load()
    t1 = time.time()
    mm = ma.getObj(1)
    mm.data['vip_exp'] = 123
    print "mm.data",mm.data
    print "use time :",time.time()-t1
    data = dict(mm.data)
    print "mc get",mclient.get("tb_role_info:1:data")
    del data['id']
    mm_new = ma.new(data)
    print "mc get",mclient.get("tb_role_info:1:data")
    print "mm_new.data",mm_new.data
    del mm,mm_new


