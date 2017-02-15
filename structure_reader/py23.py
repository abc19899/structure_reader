# encoding=utf8
"""一些兼容python2/python3的接口

"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

__author__ = '1661'
import sys


if sys.version_info[0] >= 3:
    number_type_list = (int, )
    str_type_list = (str, )
else:
    # py2
    number_type_list = (int, long, )
    str_type_list = (str, unicode, )
