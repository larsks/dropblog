#!/usr/bin/python

import os
import sys

from beaker.cache import CacheManager
from beaker.util import parse_cache_config_options

cache_opts = {
    'cache.type': 'file',
    'cache.data_dir': os.path.join(os.path.abspath('data'), 'cache'),
    'cache.lock_dir': os.path.join(os.path.abspath('data'), 'lock'),
}

cache = CacheManager(**parse_cache_config_options(cache_opts))
theme_cache = cache.get_cache('themes')

def get_theme_html(theme):
    pass

def get_theme_css(theme):
    pass

