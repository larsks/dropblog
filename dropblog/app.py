#!/usr/bin/python

import os
import sys
import urlparse

import bottle
from bottle import request, route, hook, redirect
from bottle import jinja2_view as view
from bottle import jinja2_template as template
import beaker.middleware
import markdown
from oauth import oauth
import dropbox

import models

######################################################################

def filter_markdown(s):
    '''Allows us to embed Markdown markup inside
    {% filter markdown %} blocks.'''
    return markdown.markdown(s)

bottle.TEMPLATE_PATH.insert(0, os.path.join(
    os.path.dirname(__file__), 'views'))

# Global install a Markdown filter.
bottle.BaseTemplate.settings['filters'] = { 'markdown': filter_markdown }

session_opts = {
    'session.type': 'file',
    'session.cookie_expires': 300,
    'session.data_dir': os.path.join(os.path.abspath('data'), 'sessions'),
    'session.auto': True,
    'session.invalidate_corrupt': False,
}

print session_opts

app = beaker.middleware.SessionMiddleware(bottle.app(), session_opts)

######################################################################

def dropbox_session(token=None):
    app_key = request.db.query(models.Setting).get('app_key').value
    app_secret = request.db.query(models.Setting).get('app_secret').value
    access_type = request.db.query(models.Setting).get('access_type').value

    sess = dropbox.session.DropboxSession(
            app_key,
            app_secret,
            access_type,
            )

    if token is not None:
        sess.set_token(token.key, token.secret)

    return sess

def authenticated(func):
    def _(*args, **kwargs):
        if not request.session.get('authenticated'):
            redirect('/login')

        if not 'uid' in request.session:
            redirect('/login')

        uid = request.session['uid']
        u = request.db.query(models.Identity).get(uid)

        if u is None:
            redirect('/login')

        dbx = dropbox.client.DropboxClient(
                dropbox_session(
                    oauth.OAuthToken(
                        u.dropbox_key,
                        u.dropbox_secret
                        )))

        request.user = u
        request.dbx = dbx

        return func(*args, **kwargs)

    return _

######################################################################

@hook('before_request')
def setup_request():
    db = models.Session()
    session = request.environ['beaker.session']

    request.db      = db
    request.session = session

@hook('after_request')
def finish_request():
    request.db.commit()
    request.session.save()

@route('/')
@view('index.html')
def index():
    return {'title': 'Main', 'request': request}

@route('/login', method=['GET', 'POST'])
@view('redirect.html')
def login():
    dbx = dropbox_session()
    request_token = dbx.obtain_request_token()
    request.session['request_token'] = (
            request_token.key,
            request_token.secret,
            )

    url = dbx.build_authorize_url(request_token,
            oauth_callback=urlparse.urljoin(request.url,
                '/dropbox/callback'))

    return { 'target': url }

@route('/dropbox/callback')
@view('redirect.html')
def callback():
    if not 'request_token' in request.session:
        redirect('/error')

    dbx = dropbox_session()

    request_token = oauth.OAuthToken(
            *request.session['request_token'])
    access_token = dbx.obtain_access_token(request_token)

    try:
        dbx = dropbox.client.DropboxClient(dbx)
        account_info = dbx.account_info()
    except dropbox.ErrorResponse:
        redirect('/error')

    u = request.db.query(models.Identity).get(account_info['uid'])

    if u:
        u.dropbox_key = access_token.key
        u.dropbox_secret = access_token.secret
    else:
        u = models.Identity(
                uid=account_info['uid'],
                display_name=account_info['display_name'],
                email=account_info['email'],
                dropbox_key = access_token.key,
                dropbox_secret = access_token.secret,
                )
        request.db.add(u)

    request.session['authenticated'] = True
    request.session['uid'] = u.uid

    return { 'target': '/' }

@route('/error')
def error():
    return 'An error occurred.'

@route('/info')
@authenticated
def info():
    try:
        account_info = request.dbx.account_info()
    except dropbox.ErrorResponse:
        redirect('/error')

    return str(account_info)

if __name__ == '__main__':
    models.init('sqlite:///data/dropblog.db', echo=True)
    bottle.run(app=app, reloader=True)

