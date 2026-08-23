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

from ps5_updates.title import *

def test_FlexContent_create_object():
    content = FlexContent(
        version='02.000.000', 
        version_url='https://',
        base_url='https://',
        contents_json='{}',
        content_id='EP0002-PPSA37414_00-PSRSVD0010000001'
    )
    assert content.__class__ is FlexContent

def test_FlexContent_create_from_json():
    json_string = '{"contentId":"EP0002-PPSA37414_00-PSRSVD0010000001","maxFlexContentSizeInGib":32,"maxInstallableSizeInGib":32,"versionJsonUri":"https://objectstore-publishers-cod.prod.demonware.net/cod-shared_fgc/activision/PPSA37414/01.001.000/version.json"}'
    json_parsed = json.loads(json_string)
    content = FlexContent.from_json(json_parsed)
    assert content.content_id == 'EP0002-PPSA37414_00-PSRSVD0010000001'
    assert content.version_url == 'https://objectstore-publishers-cod.prod.demonware.net/cod-shared_fgc/activision/PPSA37414/01.001.000/version.json'
    assert content.base_url == 'https://objectstore-publishers-cod.prod.demonware.net/cod-shared_fgc/activision/PPSA37414/01.001.000'
    assert content.update_max_size == '32 GiB'

def test_FlexContent_parse_version():
    json_string = '{"contentId":"EP0002-PPSA37414_00-PSRSVD0010000001","maxFlexContentSizeInGib":32,"maxInstallableSizeInGib":32,"versionJsonUri":"https://objectstore-publishers-cod.prod.demonware.net/cod-shared_fgc/activision/PPSA37414/01.001.000/version.json"}'
    json_parsed = json.loads(json_string)
    content = FlexContent.from_json(json_parsed)
    content._parse_version_json()
    assert content.content_id == 'EP0002-PPSA37414_00-PSRSVD0010000001'
    assert content.version_url == 'https://objectstore-publishers-cod.prod.demonware.net/cod-shared_fgc/activision/PPSA37414/01.001.000/version.json'
    assert content.base_url == 'https://objectstore-publishers-cod.prod.demonware.net/cod-shared_fgc/activision/PPSA37414/01.001.000'

def test_FlexContent_get_update():
    json_string = '{"contentId":"EP0002-PPSA37414_00-PSRSVD0010000001","maxFlexContentSizeInGib":32,"maxInstallableSizeInGib":32,"versionJsonUri":"https://objectstore-publishers-cod.prod.demonware.net/cod-shared_fgc/activision/PPSA37414/01.001.000/version.json"}'
    json_parsed = json.loads(json_string)
    content = FlexContent.from_json(json_parsed)
    content.get_update()
    assert content.content_id == 'EP0002-PPSA37414_00-PSRSVD0010000001'
    assert content.version_url == 'https://objectstore-publishers-cod.prod.demonware.net/cod-shared_fgc/activision/PPSA37414/01.001.000/version.json'
    assert content.base_url == 'https://objectstore-publishers-cod.prod.demonware.net/cod-shared_fgc/activision/PPSA37414/01.001.000'
    assert content.update_max_size == '32 GiB'
    assert content.pkg.__class__ is PKG

logger = logging.getLogger(__name__)