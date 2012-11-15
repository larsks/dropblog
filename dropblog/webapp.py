#!/usr/bin/python

import os
import sys
import logging

from pretty import pprint,pretty

import bottle
import beaker.middleware
import beaker.cache
import beaker.util

import settings
from utils import route, hook, routeapp

class Webapp (object):

    def __init__(self, config):
        self.config = config
        self.setup_logging()
        self.setup_cache()

    def run(self):
        pass

    @route('/')
    def hello(self):
        return 'Hello, world.'

    @hook('before_request')
    def before_request_hook(self):
        self.log.info('before_request hook')

    @hook('after_request')
    def after_request_hook(self):
        self.log.info('after_request hook')

    def setup_logging(self):
        levelname = self.config.get('loglevel', 'INFO')
        level = getattr(logging, levelname)

        logging.basicConfig(
                level=level,
                format='%(asctime)s %(levelname)s %(name)s: %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S')

        self.log = logging.getLogger('dropblog')
        self.log.info('logging at level %s' % levelname)

    def setup_cache(self):
        self.log.info('cache directory is %s',
                self.config['cache']['cache.data_dir'])
        cachemgr = beaker.cache.CacheManager(
                **beaker.util.parse_cache_config_options(
                    self.config['cache']))

######################################################################

settings.load_config()
app = beaker.middleware.SessionMiddleware(
        bottle.app(),
        settings.config['session'])
app = bottle.app()

DBAPP = Webapp(settings.config)
routeapp(DBAPP)

######################################################################

if __name__ == '__main__':
    bottle.run(reloader=True)

