#coding:utf8
'''
Created on 2013-5-8

@author: lan (www.9miao.com)
'''
from DBUtils.PooledDB import PooledDB

DBCS = {'MySQLdb':"MySQLdb",}

# class DBPool(PooledDB):
#     """
#     """
#     def __init__(self, creator, *args, **kwargs):
#         PooledDB.__init__(self, creator, *args, **kwargs)
#         self.config = kwargs
        
class MultiDBPool(object):
    """
    """
    def __init__(self):
        """
        """
        self.router = None
    
    def initPool(self,config):
        """
        """
        self.dbpool = {}
        for dbkey,dbconfig in config.items():
            _creator = DBCS.get(dbconfig.get('engine','MySQLdb'))
            creator = __import__(_creator)
            self.dbpool[dbkey] = PooledDB(creator,**dbconfig)
            
    def bind_router(self,router):
        """
        """
        self.router = router()
        
    def getPool(self,write=True,**kw):
        """
        """
        if not self.router:
            return self.dbpool.values()[0]
        if write:
            dbkey = self.router.db_for_write(**kw)
            return self.dbpool[dbkey]
        else:
            dbkey = self.router.db_for_read(**kw)
            return self.dbpool[dbkey]
        
    def connection(self,write=True,**kw):
        """
        """
        if not self.router:
            return self.dbpool.values()[0].connection(shareable=kw.get("shareable",True))
        if write:
            dbkey = self.router.db_for_write(**kw)
            return self.dbpool[dbkey].connection(shareable=kw.get("shareable",True))
        else:
            dbkey = self.router.db_for_read(**kw)
            return self.dbpool[dbkey].connection(shareable=kw.get("shareable",True))


dbpool = MultiDBPool()

