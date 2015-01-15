#coding:utf8
'''
Created on 2015-1-8

@author: root
'''
from gfirefly.dbentrust.memclient import memcached_connect
memcached_connect(["127.0.0.1:11211"])
from gfirefly.dbentrust.memfields import MemObj,MemFields
class Mcharacter(MemObj):
    def __init__(self,name):
        MemObj.__init__(self, name)
        self.id = MemFields()
        self.level = MemFields()
        self.profession = MemFields()
        self.nickname = MemFields()
        self.guanqia = MemFields()
        self.initFields()

mcharacter = Mcharacter('character:1')
mcharacter.nickname='lanjinmin'
mc_other = Mcharacter('character:1')
mc_other2 = Mcharacter('character:2')
print "mcharacter.nickname",mcharacter.nickname
print "mc_other.nickname",mc_other.nickname
print "mc_other2.nickname",mc_other2.nickname
mcharacter.mdelete()

