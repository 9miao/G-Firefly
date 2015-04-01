#coding:utf8
'''
Created on 2011-10-17

@author: lan (www.9miao.com)
'''
import gc
import objgraph
### 强制进行垃圾回收

from gfirefly.utils import  services
from gfirefly.distributed.root import PBRoot,BilateralFactory
from gtwisted.core import reactor
from gtwisted.utils import log
import sys
reactor = reactor
log.startLogging(sys.stdout)
    
root = PBRoot()
ser = services.Service('test')
root.addServiceChannel(ser)


def serviceHandle(target):
    '''服务处理
    @param target: func Object
    '''
    ser.mapTarget(target)

@serviceHandle
def printData1(data,data1):
    print data,data1
    print "############################"
#     d = root.callChild("test_node",1,u'Root测试')
    return data

@serviceHandle
def printData2(data,data1):
    print data,data1
    print "############################"
    d = root.callChild("test_node",1,u'Root测试')
    return data

def printMem():
    ### 强制进行垃圾回收
    print gc.collect()
    print "###################MEM#####################"
    print gc.garbage  
    print "###########################################"
    reactor.callLater(2, printMem)

if __name__=='__main__':
    reactor.listenTCP(9090, BilateralFactory(root))
    reactor.callLater(2, printMem)
    reactor.run()
