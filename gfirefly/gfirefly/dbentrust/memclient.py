#coding:utf-8
'''
Created on 2014-12-30
memcached client
@author: lan (www.9miao.com)
'''
import memcache
MEMCS = {'python-memcached':"memcache",
        "python-ultramemcache":"ultramemcache",
        "default":"memcache"}
_DEAD_RETRY = 5
mclient = object()

class MemConnError(Exception): 
    """
    memcached connect error
    """
    
    def __str__(self):
        return "memcache connect error"
    
    
def memcached_connect(servers,mem_lib="default",dead_retry=_DEAD_RETRY,**kw):
    """
    memcached connect
    @param servers: (list) memcached的地址，例如["127.0.0.1:11211","127.0.0.1:11222",]
    @param mem_lib: 选择性的使用memcached库,默认的使用python-memcached
    {'python-memcached':"memcache","python-ultramemcache":"ultramemcache","default":"memcache"}
    """
    global mclient
    memcache = __import__(MEMCS.get(mem_lib))
    mclient = memcache.Client(servers,dead_retry=dead_retry,**kw)
    server,key = mclient._get_server("ping")
    if not server or not key:
        raise MemConnError()
    


if __name__=="__main__":
    """
    test
    """
    import time
    memcached_connect(["127.0.0.1:11211"])
    print mclient.add("key",1,time=1)
    print mclient.delete("key")
    print mclient.add("key",1,time=1)
    while True:
        time.sleep(1)
        print mclient.get("key")
        print mclient.add("key",1,time=1)
    
    
    
