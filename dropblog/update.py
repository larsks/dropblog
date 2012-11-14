#!/usr/bin/python

import os
import sys
import argparse
import mailbox
import re
import time

import models
from models import *
import dropbox

import utils

transtable = ''.join(chr(x) if (chr(x).isalpha()) else '-' for x in range(0,256))
deltable = ''.join(chr(x) for x in range(0,255) if not chr(x).isalpha() and
        not chr(x) in [' ', '-'])

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument('--dburi', '-d',
            default='sqlite:///data/dropblog.db')
    p.add_argument('--debug', action='store_true')
    return p.parse_args()

def slugify(title):
    return title.translate(transtable, deltable).lower()[:40]

def main():
    opts = parse_args()
    models.init(opts.dburi, echo=opts.debug)
    db = Session()

    dbx = dropbox.client.DropboxClient(utils.dropbox_session(db))

    for owner in db.query(Identity):
        blogs = {}
        cursor = owner.dropbox_cursor
        print 'Found cursor:', cursor
        dbx.session.set_token(owner.dropbox_key, owner.dropbox_secret)

        account_info = dbx.account_info()
        print 'Processing blogs for %s.' % account_info['display_name']

        for blog in owner.blogs:
            blogs[blog.name] = blog
        
        delta = dbx.delta(cursor)

        if delta['reset']:
            print 'RESET'
            for post in db.query(Post).join(Post.blog).filter(Blog.owner_id ==
                    owner.id):
                db.delete(post)
            db.commit()

        for entry in delta['entries']:
            if entry[1] and entry[1]['is_dir']:
                continue

            mo = re.match('/sites/(?P<blog>[^/]*)/posts/(?P<post>[^/]*\.md$)', entry[0])
            if not mo or mo.group('blog') not in blogs:
                continue

            print '->', entry[0]

            if entry[1] is None:
                db.query(Post).filter(Post.id == entry[0]).delete()
            else:
                doc = mailbox.Message(dbx.get_file(entry[0]))

                p = db.query(Post).get(entry[0])

                if not p:
                    p = Post(id=entry[0],
                        date=time.strftime('%Y-%m-%d',
                            time.localtime()))
                    db.add(p)

                blogs[mo.group('blog')].posts.append(p)

                p.title = doc.get('title',
                        os.path.splitext(os.path.basename(entry[0]))[0]).encode('utf-8')
                p.slug = slugify(p.title)
                p.published = doc.get('published', 'True') == 'True'
                p.date = doc.get('date', p.date)

                html = utils.filter_markdown(doc.get_payload())

                if not p.content:
                    p.content = Content()

                p.content.html = html

        owner.dropbox_cursor = delta['cursor']
        db.commit()

if __name__ == '__main__':
    main()

