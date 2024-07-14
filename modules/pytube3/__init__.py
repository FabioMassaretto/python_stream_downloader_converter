# -*- coding: utf-8 -*-
# flake8: noqa: F401
# noreorder
"""
Pytube: a very serious Python library for downloading YouTube Videos.
"""
__title__ = "pytube3"
__author__ = "Nick Ficano, Harold Martin"
__license__ = "MIT License"
__copyright__ = "Copyright 2019 Nick Ficano"

from modules.pytube3.version import __version__
from modules.pytube3.streams import Stream
from modules.pytube3.captions import Caption
from modules.pytube3.query import CaptionQuery
from modules.pytube3.query import StreamQuery
from modules.pytube3.__main__ import YouTube
from modules.pytube3.contrib.playlist import Playlist
