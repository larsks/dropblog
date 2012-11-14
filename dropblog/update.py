#!/usr/bin/python

import os
import sys
import argparse

import models
import dropbox

import utils

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument('--dburi', '-d',
            default='sqlite:///data/dropblog.db')
    p.add_argument('--debug', action='store_true')
    return p.parse_args()

def main():
    opts = parse_args()
    models.init(opts.dburi, echo=opts.debug)
    db = models.Session()

    dbx = dropbox.client.DropboxClient(utils.dropbox_session(db))

    for owner in db.query(models.Identity):
        blogs = {}
        cursor = owner.dropbox_cursor
        print 'Found cursor:', cursor
        dbx.session.set_token(owner.dropbox_key, owner.dropbox_secret)

        account_info = dbx.account_info()
        print 'Processing blogs for %s.' % account_info['display_name']

        for blog in owner.blogs:
            blogs[blog.name] = blog
        
        delta = dbx.delta(cursor)

        for entry in delta['entries']:
            print entry[0]

        owner.dropbox_cursor = delta['cursor']
        db.commit()

if __name__ == '__main__':
    main()

