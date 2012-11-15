#!/usr/bin/python

import os
import sys
import errno

import jinja2
import yaml

data_dir = os.path.abspath(
        os.environ.get('OPENSHIFT_DATA_DIR', 'data'))

config = None
defaults_file = os.path.join(
        os.path.dirname(__file__), 'defaults.yaml')
config_file = os.path.join(data_dir, 'config.yaml')

def read_one_config_file(path):
    data = {}

    try:
        with open(path) as fd:
            template = jinja2.Template(fd.read())
            data = yaml.load(template.render(
                data_dir=data_dir,
                environ=os.environ))
    except IOError, detail:
        if detail.errno == errno.ENOENT:
            pass
        else:
            raise

    return data

def load_config():
    global config

    # Load defaults from package.
    config = read_one_config_file(defaults_file)
    config.update(read_one_config_file(config_file))

