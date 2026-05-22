#   MIT License

#   Copyright (c) 2026 andshrew
#   https://github.com/andshrew/PS5-Updates-Python

#   Permission is hereby granted, free of charge, to any person obtaining a copy
#   of this software and associated documentation files (the "Software"), to deal
#   in the Software without restriction, including without limitation the rights
#   to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#   copies of the Software, and to permit persons to whom the Software is
#   furnished to do so, subject to the following conditions:

#   The above copyright notice and this permission notice shall be included in all
#   copies or substantial portions of the Software.

#   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#   IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#   FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#   AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#   LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#   OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#   SOFTWARE.

import logging
import pytest

from ps5_updates.data import *

def test_HTTPSocket_create_from_url_https():
    url = 'https://sgst.prod.dl.playstation.net/sgst/prod/00/PPSA19534_00/app/info/749/f_795964dd897a4e0e6844365f08fe16dac09123a6ee2a40fe71c83279ee0da3ab/UP0006-PPSA19534_00-GLACIERGAME00000_sc.pkg'
    s = HTTPSocket.from_url(url)
    assert s.port == 443

def test_HTTPSocket_create_from_url_https_non_standard_port():
    url = 'https://sgst.prod.dl.playstation.net:8443/sgst/prod/00/PPSA19534_00/app/info/749/f_795964dd897a4e0e6844365f08fe16dac09123a6ee2a40fe71c83279ee0da3ab/UP0006-PPSA19534_00-GLACIERGAME00000_sc.pkg'
    s = HTTPSocket.from_url(url)
    assert s.port == 8443

def test_HTTPSocket_create_from_url_and_receive():
    url = 'https://sgst.prod.dl.playstation.net/sgst/prod/00/PPSA19534_00/app/info/749/f_795964dd897a4e0e6844365f08fe16dac09123a6ee2a40fe71c83279ee0da3ab/UP0006-PPSA19534_00-GLACIERGAME00000_sc.pkg'
    s = HTTPSocket.from_url(url)
    magic = b'\x7fCNT'
    s.connect()
    result = s.initial_receive(magic=magic)
    s.close()
    assert magic in result

def test_HTTPSocket_create_from_url_with():
    url = 'https://sgst.prod.dl.playstation.net/sgst/prod/00/PPSA19534_00/app/info/749/f_795964dd897a4e0e6844365f08fe16dac09123a6ee2a40fe71c83279ee0da3ab/UP0006-PPSA19534_00-GLACIERGAME00000_sc.pkg'
    with HTTPSocket.from_url(url=url) as s:
        magic = b'\x7fCNT'
        result = s.initial_receive(magic=magic)
    assert magic in result

# Error tests
def test_HTTPSocket_create_from_url_invalid_scheme():
    url = 'file://localhost/file.pkg'
    with pytest.raises(ValueError):
        s = HTTPSocket.from_url(url)

"""
def test_HTTPSocket_create_from_url_403():
    url = 'https://.dev/302'
    with HTTPSocket.from_url(url=url) as s:
        magic = b'\x7fCNT'
        result = s.initial_receive(magic=magic)
    assert magic in result

def test_HTTPSocket_create_from_url_403_multiple():
    url = 'https://.dev/multiple/302'
    with HTTPSocket.from_url(url=url) as s:
        magic = b'\x7fCNT'
        result = s.initial_receive(magic=magic, redirect_limit=3)
    assert magic not in result
"""

logger = logging.getLogger(__name__)