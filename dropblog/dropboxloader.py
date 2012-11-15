#!/usr/bin/python

import os
import sys
import logging

from beaker.cache import CacheManager
from beaker.util import parse_cache_config_options

import sqlalchemy
import dropbox

from utils import dropbox_session
from models import *

default_cache_opts = {
    'cache.type': 'file',
    'cache.data_dir': '/tmp/cache/data',
    'cache.lock_dir': '/tmp/cache/lock',
}

class DropboxLoader (object):
    def __init__ (self, uid, cache_opts=None):
        if cache_opts is None:
            cache_opts = default_cache_opts

        self.log = logging.getLogger('dropblog.dropboxloader.%s' % uid)
        self.uid = uid
        self.cache = CacheManager(
                **parse_cache_config_options(cache_opts)).get_cache(
                        'dropbox-%s' % uid)

    def get(self, path):
        self.log.debug('get %s:%s' % (self.uid, path))

        def load():
            self.log.debug('load %s:%s' % (self.uid, path))

            try:
                s = Session()
                u = s.query(Identity).get(self.uid)
                dbx = dropbox_session(s, u.dropbox_key, u.dropbox_secret)
                client = dropbox.client.DropboxClient(dbx)
                fd = client.get_file(path)
                data = fd.read()
                fd.close()
                return data
            except dropbox.rest.ErrorResponse, detail:
                self.log.warn('error %s from dropbox: %s' % (detail.status,
                    detail.reason))
                raise KeyError(path)
            except sqlalchemy.orm.exc.NoResultFound:
                self.log.warn('uid %s not found in database' % self.uid)
                raise KeyError(path)

        res = self.cache.get(path, createfunc=load)
        return res

if __name__ == '__main__':
    import yaml
    config = yaml.load(open(sys.argv[1]))
    dbx = dropbox.session.DropboxSession(
            config['app_key'],
            config['app_secret'],
            config['access_type'],
            )
    dbx.set_token(
            config[sys.argv[2]]['key'],
            config[sys.argv[2]]['secret'],
            )
    dbx = dropbox.client.DropboxClient(dbx)
    loader = DropboxLoader(dbx)

