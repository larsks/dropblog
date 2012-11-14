#!/usr/bin/python

import os
import sys

from sqlalchemy import Column, Integer, String, Text, Boolean
from sqlalchemy import ForeignKey
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, relationship, backref
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.interfaces import PoolListener

Base = declarative_base()
Session = sessionmaker()

class Setting (Base):
    __tablename__ = 'settings'

    name = Column(String, primary_key=True)
    value = Column(Text)

class Identity (Base):
    __tablename__ = 'identities'

    id = Column(Integer, primary_key=True)
    display_name = Column(String)
    email = Column(String)

    dropbox_key = Column(String)
    dropbox_secret = Column(String)
    dropbox_cursor = Column(String)

    blogs = relationship('Blog', backref='owner')

class Blog (Base):
    __tablename__ = 'blogs'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    title = Column(String)

    posts = relationship('Post', backref='blog')

    owner_id = Column(Integer, ForeignKey('identities.id'))

class Post (Base):
    __tablename__ = 'posts'

    # This is the path to the source file.
    id = Column(String, primary_key=True)

    slug = Column(String)
    title = Column(String)
    date = Column(String)
    published = Column(Boolean)

    blog_id = Column(Integer, ForeignKey('blogs.id'))

    content = relationship('Content', uselist=False, backref='post')

class Content (Base):
    __tablename__ = 'content'

    id = Column(Integer, primary_key=True)
    post_id = Column(Integer, ForeignKey('posts.id'))
    html = Column(Text)

class ForeignKeysListener(PoolListener):
    def connect(self, dbapi_con, con_record):
        db_cursor = dbapi_con.execute('pragma foreign_keys=ON')

def init(dburi, echo=False):
    listeners = []

    # Enable foreign key enforcement under sqlite.
    if dburi.startswith('sqlite:'):
        listeners.append(ForeignKeysListener())

    engine = create_engine(dburi, echo=echo, listeners=listeners)
    Base.metadata.create_all(engine)
    Session.configure(bind=engine)

