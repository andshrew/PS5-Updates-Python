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
import os
from pathlib import Path
import pytest

from ps5_updates.pkg import *
from ps5_updates.title import save_data_to_file

test_sc_file_path = Path().joinpath('tests', 'test_sc.pkg')
test_dp_file_path = Path().joinpath('tests', 'test_dp.pkg')

# PKG Tests
def test_PKG_create_from_file_sc():
    pkg = PKG.from_file(test_sc_file_path)
    assert pkg.__class__ is PKG
    assert pkg.file_count == 29
    assert len(pkg.files) == 29
    assert pkg.param.title_id == 'PPSA07811'
    assert pkg.param.content_version == '01.000.001'

def test_PKG_create_from_file_dp():
    pkg = PKG.from_file(test_dp_file_path)
    assert pkg.__class__ is PKG
    assert pkg.file_count == 8
    assert len(pkg.files) == 8
    assert pkg.param.title_id == 'PPSA07811'
    assert pkg.param.content_version == '01.000.001'
    
def test_PKG_create_from_url():
    url = 'https://sgst.prod.dl.playstation.net/sgst/prod/00/PPSA18654_00/app/info/95/f_23e129465f761a049d5477f4f4ec67db738a31927e981faa7ffb5b7eec9cb4c5/UP6312-PPSA18654_00-0220083948426038_sc.pkg'
    pkg = PKG.from_url(url)
    assert pkg.__class__ is PKG
    assert pkg.file_count == 32
    assert len(pkg.files) == 32
    assert pkg.param.title_id == 'PPSA18654'
    assert pkg.param.content_version == '01.029.000'

def test_PKG_create_from_invalid_url():
    url = 'file://invalid/_sc.pkg'
    with pytest.raises(ValueError):
        pkg = PKG.from_url(url)

# Save File Tests
def test_PKG_save_all_from_url():
    url = 'https://sgst.prod.dl.playstation.net/sgst/prod/00/PPSA07813_00/app/info/3/f_5b73779a54ecc5de73acc632ec293bb3ea92bf699d35d5ed5bed3045aac85397/UP0102-PPSA07813_00-SLUS007480000000_sc.pkg'
    pkg = PKG.from_url(url)
    base_path = Path().joinpath('data_dump', 'test_PKG_save_all_from_url')
    pkg.save_files(files=['all'], save_method=save_data_to_file, titleid=pkg.param.title_id, 
                   version=pkg.param.content_version, base_path=base_path,
                   write_bytes=True)
    files = [
        '1', '512', 'uds_npbind.dat', 'param.json',
        'pic2.png', 'icon0.png'
    ]
    for file in files:
        path = Path().joinpath(base_path, pkg.param.title_id,
                               pkg.param.content_version, file)
        assert os.path.exists(path)

def test_PKG_save_specific_from_url():
    url = 'https://sgst.prod.dl.playstation.net/sgst/prod/00/PPSA07813_00/app/info/3/f_5b73779a54ecc5de73acc632ec293bb3ea92bf699d35d5ed5bed3045aac85397/UP0102-PPSA07813_00-SLUS007480000000_sc.pkg'
    pkg = PKG.from_url(url)
    base_path = Path().joinpath('data_dump', 'test_PKG_save_specific_from_url')
    pkg.save_files(files=[1, 512, 8192], save_method=save_data_to_file, titleid=pkg.param.title_id, 
                   version=pkg.param.content_version, base_path=base_path,
                   write_bytes=True)
    files = [
        '1', '512', 'param.json'
    ]
    for file in files:
        path = Path().joinpath(base_path, pkg.param.title_id,
                               pkg.param.content_version, file)
        assert os.path.exists(path)

def test_PKG_save_all_from_file_sc():
    pkg = PKG.from_file(test_sc_file_path)
    base_path = Path().joinpath('data_dump', 'test_PKG_save_all_from_file_sc')
    pkg.save_files(files=['all'], save_method=save_data_to_file, titleid=pkg.param.title_id, 
                   version=pkg.param.content_version, base_path=base_path,
                   write_bytes=True)
    files = [
        '1', '512', 'uds_npbind.dat', 'param.json',
        'pic2.png', 'icon0.png'
    ]
    for file in files:
        path = Path().joinpath(base_path, pkg.param.title_id,
                               pkg.param.content_version, file)
        assert os.path.exists(path)

def test_PKG_save_specific_from_file_sc():
    pkg = PKG.from_file(test_sc_file_path)
    base_path = Path().joinpath('data_dump', 'test_PKG_save_specific_from_file_sc')
    pkg.save_files(files=[1, 512, 8192], save_method=save_data_to_file, titleid=pkg.param.title_id, 
                   version=pkg.param.content_version, base_path=base_path,
                   write_bytes=True)
    files = [
        '1', '512', 'param.json'
    ]
    for file in files:
        path = Path().joinpath(base_path, pkg.param.title_id,
                               pkg.param.content_version, file)
        assert os.path.exists(path)

def test_PKG_flexcontent_save_all_from_url():
    url = 'https://objectstore-publishers-cod.prod.demonware.net/cod-shared_fgc/activision/PPSA37414/01.001.000/01.013.000/subcontainer.dat'
    pkg = PKG.from_url(url)
    base_path = Path().joinpath('data_dump', 'test_PKG_flexcontent_save_all_from_url')
    pkg.save_files(files=['all'], save_method=save_data_to_file, titleid=pkg.param.title_id, 
                   version=pkg.param.content_version, base_path=base_path,
                   write_bytes=True)
    files = [
        '1', '512', 'param.json'
    ]
    for file in files:
        path = Path().joinpath(base_path, pkg.param.title_id,
                               pkg.param.content_version, file)
        assert os.path.exists(path)
    assert pkg.param.content_version == '01.013.000'
    assert pkg.param.content_id == 'EP0002-PPSA37414_00-PSRSVD0010000001'
    
# PKG_Param Tests
def test_PKG_Param_create_from_bytes():
    param_bytes = b'{\r\n  "addcont": {\r\n    "serviceIdForSharing": [\r\n      "                   ",\r\n      "                   ",\r\n      "                   ",\r\n      "                   ",\r\n      "                   ",\r\n      "                   ",\r\n      "                   "\r\n    ]\r\n  },\r\n  "ageLevel": {\r\n    "AE": 16,\r\n    "AR": 17,\r\n    "AT": 16,\r\n    "AU": 15,\r\n    "BE": 16,\r\n    "BG": 16,\r\n    "BH": 16,\r\n    "BO": 17,\r\n    "BR": 16,\r\n    "CA": 17,\r\n    "CH": 16,\r\n    "CL": 17,\r\n    "CO": 17,\r\n    "CR": 17,\r\n    "CY": 16,\r\n    "CZ": 16,\r\n    "DE": 18,\r\n    "DK": 16,\r\n    "EC": 17,\r\n    "ES": 16,\r\n    "FI": 16,\r\n    "FR": 16,\r\n    "GB": 16,\r\n    "GR": 16,\r\n    "GT": 17,\r\n    "HK": 17,\r\n    "HN": 17,\r\n    "HR": 16,\r\n    "HU": 16,\r\n    "ID": 17,\r\n    "IE": 16,\r\n    "IL": 16,\r\n    "IN": 16,\r\n    "IS": 16,\r\n    "IT": 16,\r\n    "JP": 17,\r\n    "KR": 19,\r\n    "KW": 16,\r\n    "LB": 16,\r\n    "LU": 16,\r\n    "MT": 16,\r\n    "MX": 17,\r\n    "MY": 17,\r\n    "NI": 17,\r\n    "NL": 16,\r\n    "NO": 16,\r\n    "NZ": 16,\r\n    "OM": 16,\r\n    "PA": 17,\r\n    "PE": 17,\r\n    "PL": 16,\r\n    "PT": 16,\r\n    "PY": 17,\r\n    "QA": 16,\r\n    "RO": 16,\r\n    "RU": 16,\r\n    "SA": 18,\r\n    "SE": 16,\r\n    "SG": 17,\r\n    "SI": 16,\r\n    "SK": 16,\r\n    "SV": 17,\r\n    "TH": 17,\r\n    "TR": 16,\r\n    "TW": 18,\r\n    "UA": 16,\r\n    "US": 17,\r\n    "UY": 17,\r\n    "ZA": 16,\r\n    "default": 19\r\n  },\r\n  "applicationCategoryType": 0,\r\n  "applicationDrmType": "standard",\r\n  "asa": {\r\n    "code": {\r\n      "asa14": "2"\r\n    },\r\n    "sign": [\r\n      "GDx1J1o5iA5j/C89Jf+/CsSmzyoP2tmbAPTgZTMdjQKfsIF/6VCEJ7qHUz/kTuZz",\r\n      "LKXKfAOxRDFjb0aGhD/NCQBZ6Pk9Sl+TevzJPRG3XMUdR50gArwqmAx21pZ7CjzM",\r\n      "JHTFvKe/VYz4PSnQpTmy4ceAT1OEu/HYx6MpQe64S1dQBIFC5xUE6P2u860+VJ/p",\r\n      "MjGK9725dYa07/M/0k+X7KUlCHz8xmuDtZbvetx8zSqCvgCB3EXaE4gTHZSoZn+c",\r\n      "V3P305MLfzXDI7tnIb62qhYvwUor8dgWE1PJscC+DdWgKTkz17XZoDMzViMAhz+l",\r\n      "Xf+dpke8q2CszhtjT3c0niQ59jhQNoiMvp4BICiiDU50J2IGgNwFb2TpTHC/b9em",\r\n      "x1VH0CAXt9wAjpjYAyJWKvqBFoGRX+Xh1MYet/hv80aw64UGF7P/OImwWcQ8HlYU",\r\n      "uzhYJQXFYrFnbPqPi+vPL12xxT2tORfU2V+ZMLxGpnsbTkPoCb65/wF/IfpstQGD"\r\n    ]\r\n  },\r\n  "attribute": 536870912,\r\n  "attribute2": 0,\r\n  "attribute3": 138674240,\r\n  "conceptId": "10009568",\r\n  "contentBadgeType": 1,\r\n  "contentId": "UP0006-PPSA19534_00-GLACIERGAME00000",\r\n  "contentVersion": "01.000.017",\r\n  "downloadDataSize": 256,\r\n  "gameIntent": {\r\n    "permittedIntents": [\r\n      {\r\n        "intentType": "joinSession"\r\n      },\r\n      {\r\n        "intentType": "launchActivity"\r\n      },\r\n      {\r\n        "intentType": "launchMultiplayerActivity"\r\n      }\r\n    ]\r\n  },\r\n  "kernel": {\r\n    "addcontMountLevel": 2\r\n  },\r\n  "localizedParameters": {\r\n    "defaultLanguage": "en-US",\r\n    "en-US": {\r\n      "titleName": "Battlefield\xe2\x84\xa2 6"\r\n    },\r\n    "zh-Hans": {\r\n      "titleName": "\xe3\x80\x8a\xe6\x88\x98\xe5\x9c\xb0\xe9\xa3\x8e\xe4\xba\x91\xe2\x84\xa2 6\xe3\x80\x8b"\r\n    },\r\n    "zh-Hant": {\r\n      "titleName": "\xe3\x80\x8a\xe6\x88\xb0\xe5\x9c\xb0\xe9\xa2\xa8\xe9\x9b\xb2\xe2\x84\xa2 6\xe3\x80\x8b"\r\n    }\r\n  },\r\n  "masterVersion": "01.00",\r\n  "originContentVersion": "01.000.000",\r\n  "pubtools": {\r\n    "creationDate": "2026-03-20 06:48:13",\r\n    "loudnessSnd0": "-23.99",\r\n    "submission": true,\r\n    "toolVersion": "3.13"\r\n  },\r\n  "requiredSystemSoftwareVersion": "0x1300000000000000",\r\n  "sdkVersion": "0x1000000000000000",\r\n  "targetContentVersion": "01.000.016",\r\n  "titleId": "PPSA19534",\r\n  "userDefinedParam1": 9534,\r\n  "userDefinedParam2": 0,\r\n  "userDefinedParam3": 0,\r\n  "userDefinedParam4": 0,\r\n  "versionFileUri": "https://sgst.prod.dl.playstation.net/sgst/prod/00/np/PPSA19534_00/2c0cca31-5f7b-45ea-8a3f-51a686579c21-version.xml                                                                                                                                             "\r\n}\r\n'
    param = PKG_Param.from_bytes(param_bytes=param_bytes)
    assert param.__class__ is PKG_Param
    assert param.version_url == 'https://sgst.prod.dl.playstation.net/sgst/prod/00/np/PPSA19534_00/2c0cca31-5f7b-45ea-8a3f-51a686579c21-version.xml'
    assert param.content_version == '01.000.017'
    assert param.supports_ps5_pro == True
    assert param.title_id == 'PPSA19534'

def test_PKG_Param_get_property():
    param_bytes = b'{\r\n  "addcont": {\r\n    "serviceIdForSharing": [\r\n      "                   ",\r\n      "                   ",\r\n      "                   ",\r\n      "                   ",\r\n      "                   ",\r\n      "                   ",\r\n      "                   "\r\n    ]\r\n  },\r\n  "ageLevel": {\r\n    "AE": 16,\r\n    "AR": 17,\r\n    "AT": 16,\r\n    "AU": 15,\r\n    "BE": 16,\r\n    "BG": 16,\r\n    "BH": 16,\r\n    "BO": 17,\r\n    "BR": 16,\r\n    "CA": 17,\r\n    "CH": 16,\r\n    "CL": 17,\r\n    "CO": 17,\r\n    "CR": 17,\r\n    "CY": 16,\r\n    "CZ": 16,\r\n    "DE": 18,\r\n    "DK": 16,\r\n    "EC": 17,\r\n    "ES": 16,\r\n    "FI": 16,\r\n    "FR": 16,\r\n    "GB": 16,\r\n    "GR": 16,\r\n    "GT": 17,\r\n    "HK": 17,\r\n    "HN": 17,\r\n    "HR": 16,\r\n    "HU": 16,\r\n    "ID": 17,\r\n    "IE": 16,\r\n    "IL": 16,\r\n    "IN": 16,\r\n    "IS": 16,\r\n    "IT": 16,\r\n    "JP": 17,\r\n    "KR": 19,\r\n    "KW": 16,\r\n    "LB": 16,\r\n    "LU": 16,\r\n    "MT": 16,\r\n    "MX": 17,\r\n    "MY": 17,\r\n    "NI": 17,\r\n    "NL": 16,\r\n    "NO": 16,\r\n    "NZ": 16,\r\n    "OM": 16,\r\n    "PA": 17,\r\n    "PE": 17,\r\n    "PL": 16,\r\n    "PT": 16,\r\n    "PY": 17,\r\n    "QA": 16,\r\n    "RO": 16,\r\n    "RU": 16,\r\n    "SA": 18,\r\n    "SE": 16,\r\n    "SG": 17,\r\n    "SI": 16,\r\n    "SK": 16,\r\n    "SV": 17,\r\n    "TH": 17,\r\n    "TR": 16,\r\n    "TW": 18,\r\n    "UA": 16,\r\n    "US": 17,\r\n    "UY": 17,\r\n    "ZA": 16,\r\n    "default": 19\r\n  },\r\n  "applicationCategoryType": 0,\r\n  "applicationDrmType": "standard",\r\n  "asa": {\r\n    "code": {\r\n      "asa14": "2"\r\n    },\r\n    "sign": [\r\n      "GDx1J1o5iA5j/C89Jf+/CsSmzyoP2tmbAPTgZTMdjQKfsIF/6VCEJ7qHUz/kTuZz",\r\n      "LKXKfAOxRDFjb0aGhD/NCQBZ6Pk9Sl+TevzJPRG3XMUdR50gArwqmAx21pZ7CjzM",\r\n      "JHTFvKe/VYz4PSnQpTmy4ceAT1OEu/HYx6MpQe64S1dQBIFC5xUE6P2u860+VJ/p",\r\n      "MjGK9725dYa07/M/0k+X7KUlCHz8xmuDtZbvetx8zSqCvgCB3EXaE4gTHZSoZn+c",\r\n      "V3P305MLfzXDI7tnIb62qhYvwUor8dgWE1PJscC+DdWgKTkz17XZoDMzViMAhz+l",\r\n      "Xf+dpke8q2CszhtjT3c0niQ59jhQNoiMvp4BICiiDU50J2IGgNwFb2TpTHC/b9em",\r\n      "x1VH0CAXt9wAjpjYAyJWKvqBFoGRX+Xh1MYet/hv80aw64UGF7P/OImwWcQ8HlYU",\r\n      "uzhYJQXFYrFnbPqPi+vPL12xxT2tORfU2V+ZMLxGpnsbTkPoCb65/wF/IfpstQGD"\r\n    ]\r\n  },\r\n  "attribute": 536870912,\r\n  "attribute2": 0,\r\n  "attribute3": 138674240,\r\n  "conceptId": "10009568",\r\n  "contentBadgeType": 1,\r\n  "contentId": "UP0006-PPSA19534_00-GLACIERGAME00000",\r\n  "contentVersion": "01.000.017",\r\n  "downloadDataSize": 256,\r\n  "gameIntent": {\r\n    "permittedIntents": [\r\n      {\r\n        "intentType": "joinSession"\r\n      },\r\n      {\r\n        "intentType": "launchActivity"\r\n      },\r\n      {\r\n        "intentType": "launchMultiplayerActivity"\r\n      }\r\n    ]\r\n  },\r\n  "kernel": {\r\n    "addcontMountLevel": 2\r\n  },\r\n  "localizedParameters": {\r\n    "defaultLanguage": "en-US",\r\n    "en-US": {\r\n      "titleName": "Battlefield\xe2\x84\xa2 6"\r\n    },\r\n    "zh-Hans": {\r\n      "titleName": "\xe3\x80\x8a\xe6\x88\x98\xe5\x9c\xb0\xe9\xa3\x8e\xe4\xba\x91\xe2\x84\xa2 6\xe3\x80\x8b"\r\n    },\r\n    "zh-Hant": {\r\n      "titleName": "\xe3\x80\x8a\xe6\x88\xb0\xe5\x9c\xb0\xe9\xa2\xa8\xe9\x9b\xb2\xe2\x84\xa2 6\xe3\x80\x8b"\r\n    }\r\n  },\r\n  "masterVersion": "01.00",\r\n  "originContentVersion": "01.000.000",\r\n  "pubtools": {\r\n    "creationDate": "2026-03-20 06:48:13",\r\n    "loudnessSnd0": "-23.99",\r\n    "submission": true,\r\n    "toolVersion": "3.13"\r\n  },\r\n  "requiredSystemSoftwareVersion": "0x1300000000000000",\r\n  "sdkVersion": "0x1000000000000000",\r\n  "targetContentVersion": "01.000.016",\r\n  "titleId": "PPSA19534",\r\n  "userDefinedParam1": 9534,\r\n  "userDefinedParam2": 0,\r\n  "userDefinedParam3": 0,\r\n  "userDefinedParam4": 0,\r\n  "versionFileUri": "https://sgst.prod.dl.playstation.net/sgst/prod/00/np/PPSA19534_00/2c0cca31-5f7b-45ea-8a3f-51a686579c21-version.xml                                                                                                                                             "\r\n}\r\n'
    param = PKG_Param.from_bytes(param_bytes=param_bytes)
    assert param.__class__ is PKG_Param
    assert param.get_property('contentId') == 'UP0006-PPSA19534_00-GLACIERGAME00000'
    assert param.get_property('creationDate', 'pubtools') == '2026-03-20 06:48:13'
    assert param.get_property('non-existant') == None