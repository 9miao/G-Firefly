#coding:utf8
'''
Created on 2014-12-31

@author: lan (www.9miao.com)
'''
from numbers import Number
import memclient
LOCK_TIMEOUT = 2
CACHE_TIMEOUT = 60*60


class MEMKeyError(Exception): 
    """
    memcached key error
    """
    
    def __str__(self):
        return "memcache key error"

class MemFields(object):
    """
    这个类表示memcache中的一个元素
    """
    
    def __init__(self, value=None, cache=True,timeout=CACHE_TIMEOUT):
        """
        @param name: str　字段的名称
        @param cache: bool 是否本地缓存获取到的值
        """
        self.name = ""
        self.value = value
        self.cache = cache
        self.timeout = timeout
        
    def getValue(self):
        """
        获取name对应的值
        当cache为True时，并且value值存在时，不再重新从memcache中获取值
        """
        if self.cache and self.value:
            return self.value
        else:
            self.refreshValue()
            return self.value
    
    def refreshValue(self):
        """
        重新从memcached中获取值
        """
        self.value = memclient.mclient.get(self.name)
        return self.value
    
    def setValue(self,value):
        """
        修改对应的值
        """
        self.value = value
        result = memclient.mclient.set(self.name,value,time=self.timeout)
        return result

class MemObj(object):
    
    def __init__(self, name, cache=True, cas=False, timeout=CACHE_TIMEOUT,**kw):
        """
        @param name: str 表示对象的名称
        
        """
        self._name = name
        self._locked = False
        self._cas = cas
        self._cache = cache
        self._timeout = timeout
        
    def initFields(self):
        """
        初始化字段
        """
        nowdict = dict(self.__dict__)
        for item_key,item_value in nowdict.items():
            if isinstance(item_value, MemFields):
                item_value.name = self.produceKey(item_key)
                item_value.timeout = self._timeout
                if item_key in ["state","cache"]:
                    item_value.cache = self._cache
                
    def produceKey(self,keyname):
        '''
        重新生成key
        '''
        if isinstance(keyname, basestring):
            return ''.join([self._name,':',keyname])
        else:
            raise MEMKeyError()
        
    def lock(self):
        '''
        检测对象是否被锁定
        '''
        key = self.produceKey('_lock')
        result = memclient.mclient.add(key,1,LOCK_TIMEOUT)
        if result:
            self._locked = result
        return result
    
    def release(self):
        '''释放锁
        '''
        key = self.produceKey('_lock')
        memclient.mclient.delete(key)
        self._locked = False
            
    def insert(self):
        '''
        插入对象记录
        '''
        nowdict = dict(self.__dict__)
        newmapping = dict([(self.produceKey(item_key), item_value.value) for item_key,item_value in\
                            nowdict.items() if isinstance(item_value, MemFields) and item_value.value])
        memclient.mclient.set_multi(newmapping,time=self._timeout)

    def mdelete(self):
        """
        删除缓存中的对象
        """
        nowdict = dict(self.__dict__)
        keys = [self.produceKey(item_key) for item_key,item_value in\
                            nowdict.items() if isinstance(item_value, MemFields)]
        return memclient.mclient.delete_multi(keys)
        
    def __getattribute__(self,attr):
        """
        封装了获取字段值的过程
        """
        value = object.__getattribute__(self,attr)
        if isinstance(value, MemFields):
            if self._cas:
                import time
                for _ in xrange(10):
                    if self.lock():
                        time.sleep(0.2)
                        continue
                    break
                else:
                    return None
            return value.getValue()
        return value
    
    def __setattr__(self, attr,value):
        """
        """
        if self.__dict__.has_key(attr):
            _value = object.__getattribute__(self,attr)
            if isinstance(_value, MemFields):
                result = _value.setValue(value)
                if self._cas:
                    self.release()
                return result
            else:
                return object.__setattr__(self, attr,value)
        else:
            return object.__setattr__(self, attr,value)
        
    def __del__(self):
        """
        在对象销毁时释放锁，避免在获取memcache数据时死锁
        """
        try:
            if not self._locked:
                self.release()
        except:
            pass
        
            
            

        
if __name__=="__main__":
    from memclient import memcached_connect
    memcached_connect(["127.0.0.1:11211"])
    class Mcharacter(MemObj):
        def __init__(self,name):
            MemObj.__init__(self, name)
            self.id = MemFields(1)
            self.level = MemFields(0)
            self.profession = MemFields(9)
            self.nickname = MemFields(u"")
            self.guanqia = MemFields(100)
            self.initFields()
    
    mcharacter = Mcharacter('character:1')
    mcharacter.nickname='lanjinmin'
    mcharacter.insert()
    print "mcharacter.nickname",mcharacter.nickname
    mc_other = Mcharacter('character:1')
    mc_other2 = Mcharacter('character:2')
    print "mc_other.nickname",mc_other.nickname
    print "mc_other2.nickname",mc_other2.nickname
    print "mcharacter.guanqia",mcharacter.guanqia
    print "mc_other.guanqia",mc_other.guanqia
    mcharacter.mdelete()
    print "mcharacter.guanqia",mcharacter.guanqia
    print type(mc_other.guanqia)
    isinstance(None, MemFields)
    del mcharacter,mc_other,mc_other2
    print "okkkkkkkkkkkk"
