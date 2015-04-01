#coding:utf8
'''
Created on 2012-7-10
memcached 关系对象\n
通过key键的名称前缀来建立\n
各个key-value 直接的关系\n
@author: lan (www.9miao.com)
'''
import memclient
import gevent
import time
LOCK_TIMEOUT = 2
CACHE_TIMEOUT = 60*60

class MEMKeyError(Exception): 
    """
    memcached key error
    """
    
    def __str__(self):
        return "memcache key error"

class MemObject:
    '''memcached 关系对象,可以将一个对象的属性值记录到memcached中。
    
    >>> class Mcharacter(MemObject):
    >>>    def __init__(self,pid,name,mc):
    >>>        MemObject.__init__(self, name, mc)
    >>>        self.id = pid
    >>>        self.level = 0
    >>>        self.profession = 0
    >>>        self.nickname = u''
    >>>        self.guanqia = 1000
    >>> mcharacter = Mcharacter(1,'character:1',mclient)
    >>> mcharacter.name='lan'
    >>> mcharacter.insert()
    >>> mcharacter.get('nickname')
    lan
    '''
    
    def __init__(self,name,**kw):
        '''
        @param name: str 对象的名称\n
        @param _lock: int 对象锁  为1时表示对象被锁定无法进行修改\n
        '''
        self._name = name
        self._locked = False
        self._timestamp = 0
        self._cas = kw.get("cas",False)
        self._cache = kw.get("cache",True)
        self._timeout = kw.get("timeout",CACHE_TIMEOUT)
        if self._cas:
            self.lock()
        
    def produceKey(self,keyname):
        '''
        重新生成key
        '''
        if isinstance(keyname, basestring):
            return str(''.join([self._name,':',keyname]))
        else:
            raise MEMKeyError()
        
    def isLocked(self):
        """
        """
        tdelta = time.time()-self._timestamp
        if tdelta>=LOCK_TIMEOUT:
            self._locked=False
        return self._locked
    
    def lock(self):
        '''锁定对象
        '''
        print "locked"
        if not self.isLocked():
            key = self.produceKey('_lock')
            result = memclient.mclient.add(key,1,LOCK_TIMEOUT)
            if result:
                self._timestamp=time.time()
                self._locked = result
        return self._locked
        
    def release(self):
        '''释放锁
        '''
        if self.isLocked():
            print "release..."
            key = self.produceKey('_lock')
            memclient.mclient.delete(key)
            self._locked = False
        
    def get(self,key):
        '''获取对象值
        '''
        if self._cas and not self.isLocked():
            for _ in xrange(10):
                if not self.lock():
                    gevent.sleep(0.2)
                    continue
                break
            else:
                return None
        key = self.produceKey(key)
        return memclient.mclient.get(key)
    
    def get_multi(self,keys):
        '''一次获取多个key的值
        @param keys: list(str) key的列表
        '''
        if self._cas and not self.isLocked():
            for _ in xrange(10):
                if not self.lock():
                    gevent.sleep(0.2)
                    continue
                break
            else:
                return None
        keynamelist = [self.produceKey(keyname) for keyname in keys]
        olddict = memclient.mclient.get_multi(keynamelist)
        newdict = dict(zip([keyname.split(':')[-1] for keyname in olddict.keys()],
                              olddict.values()))
        return newdict

    def update(self,key,values):
        '''修改对象的值
        '''
        if self._cas and not self.isLocked():
            for _ in xrange(10):
                if not self.lock():
                    gevent.sleep(0.2)
                    continue
                break
            else:
                return None
        key = self.produceKey(key)
        return memclient.mclient.set(key,values,time=self._timeout)
            
    def update_multi(self,mapping):
        '''同时修改多个key值
        '''
        if self._cas and not self.isLocked():
            for _ in xrange(10):
                if not self.lock():
                    gevent.sleep(0.2)
                    continue
                break
            else:
                return None
        newmapping = dict(zip([self.produceKey(keyname) for keyname in mapping.keys()],
                              mapping.values()))
        return memclient.mclient.set_multi(newmapping,time=self._timeout)
        
    def mdelete(self):
        '''删除memcache中的数据
        '''
        nowdict = dict(self.__dict__)
        keys = [keyname for keyname in nowdict.keys() if not keyname.startswith('_')]
        keys = [self.produceKey(key) for key in keys]
        memclient.mclient.delete_multi(keys)
        
    def insert(self):
        '''插入对象记录
        '''
        nowdict = dict(self.__dict__)
        newmapping = dict([(self.produceKey(keyname),nowdict[keyname]) for keyname in nowdict.keys() if not keyname.startswith('_')])
        memclient.mclient.set_multi(newmapping,time=self._timeout)
        
    def __del__(self):
        """
        在对象销毁时释放锁，避免在获取memcache数据时死锁
        """
        try:
            if self.isLocked():
                self.release()
        except Exception as e:
            print e
        
        
if __name__=="__main__":
    
    from memclient import memcached_connect
    memcached_connect(["127.0.0.1:11211"])
    from memclient import mclient
    class Mcharacter(MemObject):
        def __init__(self,pid,name,**kw):
            MemObject.__init__(self, name,**kw)
            self.id = pid
            self.level = 0
            self.profession = 0
            self.nickname = u''
            self.guanqia = 1000000000000000
    mcharacter = Mcharacter(1,'character:1',cas=True)
    mcharacter.nickname='lan'
    mcharacter.insert()
    
    _mcharacter = Mcharacter(1,'character:1',cas=True)
    mcharacter.release()
    _mcharacter.release()
    print mcharacter.get('nickname')
    mcharacter.release()
    print _mcharacter.get('nickname')
    _mcharacter.release()
    print mcharacter.get('guanqia'),type(mcharacter.get('guanqia'))
    mcharacter.release()
    print _mcharacter.get('guanqia'),type(_mcharacter.get('guanqia'))
    
