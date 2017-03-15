from singleton import SingletonMixin
from lock import ReadWriteLock
import threading

from datetime import date, timedelta


class Cache(SingletonMixin):

    __cache_lock = ReadWriteLock()

    map_id = None
    top_country_list = None
    update_time = None

    def get_vals(self):
        map_id_ret, country_list_ret = None, None

        # Safe read for the current value of map_id
        self.__cache_lock.acquire_read()
        is_expired = self.__expired()
        if not(is_expired):
            map_id_ret, country_list_ret =  self.map_id, self.top_country_list
        self.__cache_lock.release_read()


        if self.update_time is not None:
            print (date.today() - self.update_time).days

        # Invalidate cache
        if is_expired:
            print 'Cache is expired, invalidating it.'
            self.set_vals()

        return map_id_ret,country_list_ret


    def set_vals(self, map_id=None, country_list=None):

        # Safe write for the current value fo the map_id
        self.__cache_lock.acquire_write()
        self.map_id = map_id
        self.top_country_list = country_list
        self.update_time = date.today()
        self.__cache_lock.release_write()


    def __expired(self):
        return (self.update_time is not None) and ( (date.today() - self.update_time).days >= 1)