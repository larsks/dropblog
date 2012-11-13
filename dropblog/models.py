#!/usr/bin/python

import os
import sys

from sqlalchemy import Column, Integer, String, Text, create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
Session = sessionmaker()

class Setting (Base):
    __tablename__ = 'settings'

    name = Column(String, primary_key=True)
    value = Column(Text)

class Identity (Base):
    __tablename__ = 'identities'

    uid = Column(Integer, primary_key=True)
    display_name = Column(String)
    email = Column(String)
    dropbox_key = Column(String)
    dropbox_secret = Column(String)

def init(dburi, echo=False):
    engine = create_engine(dburi, echo=echo)
    Base.metadata.create_all(engine)
    Session.configure(bind=engine)

