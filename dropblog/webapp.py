#!/usr/bin/python

import os
import sys
import logging
import urlparse

from pretty import pprint,pretty

import bottle
from bottle import request, response, redirect, abort
import beaker.middleware
import beaker.cache
import beaker.util
import dropbox
from oauth import oauth
import sqlalchemy

import settings
from utils import route_instance
from decorators import *
from models import *

class Webapp (object):

    def __init__(self, config):
        self.config = config
        self.setup_logging()
        self.setup_cache()
        self.setup_routes()
        self.setup_models()

    def run(self):
        pass

    @route('/')
    def hello(self):
        return 'Hello, world.'

    @route('/dump')
    @content_type('text/plain')
    @authenticated
    def dump(self):
        return pretty(self.config)

    @route('/login')
    def login(self):
        token = request.box.obtain_request_token()
        request.session['request_token'] = (
                token.key,
                token.secret,
                )

        callback = urlparse.urljoin(request.url,
                '/dropbox/callback')

        if 'url' in request.params:
            callback = '%s?%s' % (
                    callback,
                    urllib.urlencode(dict(url=request.params['url'])))

        url = request.box.build_authorize_url(
                token,
                oauth_callback=callback)

        print 'URL:', url
        redirect(url)

    @route('/dropbox/callback')
    @content_type('text/plain')
    def dropbox_oauth_callback(self, uid=None, oauth_token=None):
        if not 'request_token' in request.session:
            abort()

        access_token, account_info = self.validate_user()
        user = self.update_or_add_user(access_token, account_info)
        request.session['authenticated'] = True
        request.session['uid'] = user.id

        redirect(request.params.get('url', '/'))

    def validate_user(self):
        try:
            request_token = oauth.OAuthToken(
                    *request.session['request_token'])
            access_token = request.box.obtain_access_token(request_token)
            box = dropbox.client.DropboxClient(request.box)
            account_info = box.account_info()
        except dropbox.rest.ErrorResponse, detail:
            self.log.warn('unable to communicate with dropbox: %s: %s',
                detail.reason,detail.error_msg)
            abort(text='Unable to communicate with Dropbox.')

        self.log.info('successfully connected dropbox user %s',
                account_info['uid'])

        return access_token, account_info

    def update_or_add_user(self, access_token, account_info):
        try:
            user = request.db.query(User).filter(
                    User.dropbox_uid == account_info['uid']).one()
            user.dropbox_key = access_token.key
            user.dropbox_secret = access_token.secret
        except sqlalchemy.orm.exc.NoResultFound:
            user = User(
                    display_name=account_info['display_name'],
                    email=account_info['email'],
                    dropbox_uid=account_info['uid'],
                    dropbox_key = access_token.key,
                    dropbox_secret = access_token.secret,
                    )
            request.db.add(user)

        # We have to commit here to provision user.id.
        request.db.commit()
        return user

    @hook('before_request')
    def before_request_hook(self):
        request.db = Session()
        request.session = request.environ['beaker.session']
        request.box = dropbox.session.DropboxSession(
                self.config['app_key'],
                self.config['app_secret'],
                self.config['access_type'],
                )

    @hook('after_request')
    def after_request_hook(self):
        request.db.commit()

    def setup_models(self):
        initmodels(self.config['dburi'])

    def setup_routes(self):
        route_instance(self)

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

DBAPP = Webapp(settings.config)

######################################################################

if __name__ == '__main__':
    bottle.run(app=app, reloader=True)

