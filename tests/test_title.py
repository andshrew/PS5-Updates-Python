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
from pathlib import Path
import pytest

from ps5_updates import title as ps5up

test_sc_file_path = Path().joinpath('tests', 'test_sc.pkg')

def test_Ps5TitleUpdate_create_from_url():
    url = 'https://gist.githubusercontent.com/andshrew/441c2183abe1f46f9d3c9dd01d5fe111/raw/db25bab7536720f4958e84f40a26478bcf192ec1/PPSA04029_00-ec290d4a-77a8-4060-888f-44335151e45b-version.xml'
    update = ps5up.Ps5TitleUpdate.from_url(url)
    update.get_update()
    assert update.__class__ is ps5up.Ps5TitleUpdate
    assert update._is_parsed == True
    assert update.content_id == 'EP4497-PPSA04029_00-0000000000000N22'
    assert update.title_id == 'PPSA04029_00'
    assert len(update.additional_content) == 1
    assert len(update.packages) == 2

def test_Ps5TitleUpdate_create_from_invalid_url():
    url = 'https://gist.githubusercontent.com/andshrew/441c2183abe1f46f9d3c9dd01d5fe111/raw/db25bab7536720f4958e84f40a26478bcf192ec1/invalid.xml'
    update = ps5up.Ps5TitleUpdate.from_url(url)
    update.get_update()
    assert update.__class__ is ps5up.Ps5TitleUpdate
    assert update.update_xml is None
    assert update._is_parsed == False

def test_Ps5TitleUpdate_create_from_pkg_url():
    url = 'https://sgst.prod.dl.playstation.net/sgst/prod/00/PPSA24662_00/app/info/36/f_275645ba43d8acf1aa0f0a0912aad91f36aa65b6261edbb2fb612131467b678d/UP0006-PPSA24662_00-F12025PS5GAME000_sc.pkg'
    update = ps5up.Ps5TitleUpdate.from_pkg_url(url)
    update.get_update()
    assert update.__class__ is ps5up.Ps5TitleUpdate
    assert update._is_parsed == True
    assert update.update_url == 'https://sgst.prod.dl.playstation.net/sgst/prod/00/np/PPSA24662_00/a547a902-f447-469f-ada0-0e58dc81e5e3-version.xml'
    assert update.title_id == 'PPSA24662_00'
    assert update.content_id == 'UP0006-PPSA24662_00-F12025PS5GAME000'

def test_Ps5TitleUpdate_create_from_pkg_file():
    update = ps5up.Ps5TitleUpdate.from_pkg_file(test_sc_file_path)
    assert update.__class__ is ps5up.Ps5TitleUpdate
    assert update._is_parsed == True
    assert update.title_id == 'PPSA07811_00'
    assert update.content_id == 'UP0102-PPSA07811_00-SLUS005510000000'
    assert len(update.additional_content) == 0

def test_Ps5TitleUpdate_create_from_url_with_additional_content():
    url = 'https://sgst.prod.dl.playstation.net/sgst/prod/00/np/PPSA08260_00/faa39e63-4d80-4062-85ac-5966114ac1e6-version.xml'
    update = ps5up.Ps5TitleUpdate.from_url(url)
    assert update.__class__ is ps5up.Ps5TitleUpdate
    assert update.title_id == 'PPSA08260_00'
    assert update.content_id == 'EP0001-PPSA08260_00-GAME000000000000'
    assert len(update.additional_content) > 0
    assert update._is_parsed == True

logger = logging.getLogger(__name__)