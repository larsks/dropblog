#!/usr/bin/python

import os
import sys
import logging

import sqlalchemy
import dropbox

from utils import dropbox_session
from models import *

class DropboxLoader (object):
    def __init__ (self, uid, cachemgr):
        self.log = logging.getLogger('dropblog.dropboxloader.%s' % uid)
        self.uid = uid
        self.cache = cachemgr(
                **parse_cache_config_options(cache_opts)).get_cache(
                        'dropbox/%s' % uid)

    def get(self, path):
        self.log.debug('get %s:%s' % (self.uid, path))

        def load():
            self.log.debug('load %s:%s' % (self.uid, path))

            try:
                dbx = dropbox_client_for(self.uid)
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

