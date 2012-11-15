#!/usr/bin/python

import os
import sys
import urlparse
import logging

import bottle
from bottle import request, route, post, hook, redirect, abort
from bottle import jinja2_view as view
from bottle import jinja2_template as template
import beaker.middleware
from oauth import oauth
import dropbox

import sqlalchemy
from sqlalchemy import and_

import models
from dropboxloader import DropboxLoader
from utils import dropbox_session, filter_markdown

######################################################################

logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s %(levelname)s %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S')

bottle.TEMPLATE_PATH.insert(0, os.path.join(
    os.path.dirname(__file__), 'views'))

# Global install a Markdown filter.
bottle.BaseTemplate.settings['filters'] = { 'markdown': filter_markdown }

session_opts = {
    'session.type': 'file',
    'session.cookie_expires': 1800,
    'session.data_dir': os.path.join(os.path.abspath('data'), 'sessions'),
    'session.auto': True,
    'session.invalidate_corrupt': False,
}

cache_opts = {
    'cache.type': 'file',
    'cache.data_dir': os.path.join(os.path.abspath('data'), 'cache', 'data'),
    'cache.lock_dir': os.path.join(os.path.abspath('data'), 'cache', 'lock'),
}

app = beaker.middleware.SessionMiddleware(bottle.app(), session_opts)

######################################################################

def authenticated(func):
    def _(*args, **kwargs):
        if not request.session.get('authenticated'):
            print '*** session is not authenticated'
            redirect('/login')

        if not 'uid' in request.session:
            print '*** session has no uid'
            redirect('/login')

        uid = request.session['uid']
        u = request.db.query(models.Identity).get(uid)

        if u is None:
            print '*** user with uid = %s not found in database' % uid
            redirect('/login')

        dbx = dropbox.client.DropboxClient(
                dropbox_session(request.db, u.dropbox_key,
                    u.dropbox_secret))

        request.user = u
        request.dbx = dbx

        return func(*args, **kwargs)

    return _

######################################################################

@hook('app_reset')
def appreset():
    print '*** RESET ***'

def configured():
    v = request.db.query(models.Setting).get('app_key')
    return (v is not None)

@hook('before_request')
def setup_request():
    db = models.Session()
    session = request.environ['beaker.session']

    request.db      = db
    request.session = session

    if not configured() and not request.urlparts.path == '/config':
        redirect('/config')

@hook('after_request')
def finish_request():
    request.db.commit()
    request.session.save()

@route('/config')
@view('config.html')
def config(message=None):
    return {'title': 'Application configuration',
            'message': message}

@post('/config')
def handle_config():
    for name in 'app_key', 'app_secret', 'access_type':
        if not request.params.get(name):
            return config(message="Missing value for %s." % name)

    for name in 'app_key', 'app_secret', 'access_type':
        s = models.Setting(
                name=name,
                value=request.params.get(name),
                )
        request.db.add(s)
    request.db.commit()

    redirect('/')

@route('/')
@view('index.html')
def index():
    return {'title': 'Main', 'request': request}

@route('/login', method=['GET', 'POST'])
@view('redirect.html')
def login():
    dbx = dropbox_session(request.db)
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

    dbx = dropbox_session(request.db)

    request_token = oauth.OAuthToken(
            *request.session['request_token'])
    access_token = dbx.obtain_access_token(request_token)

    try:
        dbx = dropbox.client.DropboxClient(dbx)
        account_info = dbx.account_info()
    except dropbox.ErrorResponse:
        redirect('/error')

    try:
        u = request.db.query(models.Identity).filter(
                models.Identity.dropbox_uid == account_info['uid']).one()
        u.dropbox_key = access_token.key
        u.dropbox_secret = access_token.secret
    except sqlalchemy.orm.exc.NoResultFound:
        u = models.Identity(
                display_name=account_info['display_name'],
                email=account_info['email'],
                dropbox_uid=account_info['uid'],
                dropbox_key = access_token.key,
                dropbox_secret = access_token.secret,
                )
        request.db.add(u)

        # We need to commit here so that u.id is available.
        request.db.commit()

    request.session['uid'] = u.id
    request.session['authenticated'] = True

    return { 'target': '/' }

@route('/error')
def error():
    return 'An error occurred.'

@route('/info')
@authenticated
@view('info.html')
def info():
    try:
        account_info = request.dbx.account_info()
    except dropbox.ErrorResponse:
        redirect('/error')

    return {'title': 'User information',
            'request': request}

@route('/logout')
@view('redirect.html')
def logout():
    request.session.delete()
    return { 'target': '/' }

@route('/:blog/post/:slug')
@view('post.html')
def render_blog_post(blog, slug):
    try:
        p = request.db.query(models.Post).join(models.Post.blog).filter(
                and_(models.Post.slug == slug,
                    models.Blog.name == blog)).one()
        return {'title': p.title, 'post': p}
    except sqlalchemy.orm.exc.NoResultFound:
        abort(404, 'Page not found.')

@route('/:blog')
@view('blogmain.html')
def render_blog_main(blog):
    try:
        blog = request.db.query(models.Blog).filter(models.Blog.name == blog).one()
        return {'title': blog.title, 'blog': blog}
    except (sqlalchemy.orm.exc.NoResultFound, KeyError):
        abort(404, 'Page not found.')

@route('/theme/u/:theme/theme.html')
def get_user_theme_html(theme):
    pass

@route('/theme/u/:uid/:theme/:filename')
def get_user_theme_resource(uid, theme, filename):
    try:
        loader = DropboxLoader(uid, cache_opts=cache_opts)
        return loader.get('/sites/themes/%s/%s' % (theme, filename))
    except KeyError:
        abort(404, 'Page not found.')

if __name__ == '__main__':
    models.init('sqlite:///data/dropblog.db')
    bottle.run(app=app, reloader=True)

