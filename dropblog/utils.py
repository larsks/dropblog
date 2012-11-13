#!/usr/bin/python

import os
import sys

import dropbox

import models

def dropbox_session(db, token=None):
    app_key = db.query(models.Setting).get('app_key').value
    app_secret = db.query(models.Setting).get('app_secret').value
    access_type = db.query(models.Setting).get('access_type').value

    sess = dropbox.session.DropboxSession(
            app_key,
            app_secret,
            access_type,
            )

    if token is not None:
        sess.set_token(token.key, token.secret)

    return sess

