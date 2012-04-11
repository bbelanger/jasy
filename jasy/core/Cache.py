#
# Jasy - Web Tooling Framework
# Copyright 2010-2012 Zynga Inc.
#

import shelve, time, logging, os, os.path, sys, pickle, dbm
from jasy import __version__ as version

class Cache:
    """ 
    A cache class based on shelve feature of Python. Supports transient in-memory 
    storage, too. Uses memory storage for caching requests to DB as well for 
    improved performance. Uses keys for identification of entries like a normal
    hash table / dictionary.
    """
    
    __shelve = None
    
    def __init__(self, path):
        self.__transient = {}
        self.__file = os.path.join(path, "jasycache")
        
        self.open()
        
        
    def open(self):
        """Opens a cache file in the given path"""
        
        try:
            if os.path.exists(self.__file):
                self.__shelve = shelve.open(self.__file, flag="w")
            
                if "jasy-version" in self.__shelve:
                    storedVersion = self.__shelve["jasy-version"]
                else:
                    storedVersion = None
                
                if storedVersion == version:
                    return
                    
                logging.debug("Jasy version has been changed. Recreating cache...")
                self.__shelve.close()
                    
            self.__shelve = shelve.open(self.__file, flag="n")
            self.__shelve["jasy-version"] = version
            
        except dbm.error as error:
            errno = None
            try:
                errno = error.errno
            except:
                pass
                
            if errno is 35:
                raise IOError("Cache file is locked by another process! Maybe there is still another open Session/Project?")
                
            elif "db type could not be determined" in str(error):
                logging.error("Could not detect cache file format!")
                logging.warn("Recreating cache database...")
                self.clear()
                
            else:
                raise error
    
    
    def clear(self):
        """
        Clears the cache file through re-creation of the file
        """
        
        if self.__shelve != None:
            logging.debug("Closing cache file %s..." % self.__file)
            
            self.__shelve.close()
            self.__shelve = None

        logging.debug("Clearing cache file %s..." % self.__file)
        self.__shelve = shelve.open(self.__file, flag="n")
        self.__shelve["jasy-version"] = version
        
        
    def read(self, key, timestamp=None):
        """ 
        Reads the given value from cache.
        Optionally support to check wether the value was stored after the given 
        time to be valid (useful for comparing with file modification times).
        """
        
        if key in self.__transient:
            return self.__transient[key]
        
        timeKey = key + "-timestamp"
        if key in self.__shelve and timeKey in self.__shelve:
            if not timestamp or timestamp <= self.__shelve[timeKey]:
                value = self.__shelve[key]
                
                # Useful to debug serialized size. Often a performance
                # issue when data gets to big.
                # rePacked = pickle.dumps(value)
                # print("LEN: %s = %s" % (key, len(rePacked)))
                
                # Copy over value to in-memory cache
                self.__transient[key] = value
                return value
                
        return None
        
    
    def store(self, key, value, timestamp=None, transient=False):
        """
        Stores the given value.
        Default timestamp goes to the current time. Can be modified
        to the time of an other files modification date etc.
        Transient enables in-memory cache for the given value
        """
        
        self.__transient[key] = value
        if transient:
            return
        
        if not timestamp:
            timestamp = time.time()
        
        try:
            self.__shelve[key+"-timestamp"] = timestamp
            self.__shelve[key] = value
        except pickle.PicklingError as err:
            logging.error("Failed to store enty: %s" % key)

        
    def sync(self):
        """ Syncs the internal storage database """
        
        if self.__shelve is not None:
            self.__shelve.sync() 
      
      
    def close(self):
        """ Closes the internal storage database """
        
        if self.__shelve is not None:
            self.__shelve.close()  
            self.__shelve = None

      