#coding:utf8
'''
Created on 2015-1-8

@author: root
'''
from gfirefly.dbentrust.dbpool import dbpool,RouterBase
from gfirefly.dbentrust.memclient import memcached_connect
memcached_connect(["127.0.0.1:11211"])
from gfirefly.dbentrust.memmodel import MemAdmin
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

class router(RouterBase): 
    def db_for_read(self, **kw):
        return "default"
    def db_for_write(self, **kw):
        return "master"

dbpool.bind_router(router)

ma = MemAdmin('tb_role_info','id',incrkey='id')
mm = ma.getObj(1)
mm.data['vip_exp'] = 123
print "mm.data",mm.data
data = dict(mm.data)
del data['id']
mm_new = ma.new(data)
print mm_new.data['id']
