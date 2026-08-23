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
import struct

from ps5_updates.title import *

def test_ContentPackage_create_object():
    package = ContentPackage(
        version='02.000.000', 
        manifest_url='https://',
        digest='abc123',
        mandatory=False,
        metadata_version=1,
        pfs_revision=1,
        system_version='291504133'
    )
    assert package.__class__ is ContentPackage

def test_ContentPackage_create_from_xml():
    xml_string = '<package content_ver="02.310.000" delta_url="http://gst.prod.dl.playstation.net/gst/prod/00/PPSA03974_00/app/pkg/47/f_bb1b3ea77bc527d9e5d0259c0c1e17f8e7069344f81f88ebcb2d9b1aeb908a4f/UP4497-PPSA03974_00-0000000000000CP1-DP.pkg" digest="261996e21f936c2f14af67eaa2c616afbe15e833bf337ed2a466627cb1a9773f" mandatory="false" manifest_url="https://sgst.prod.dl.playstation.net/sgst/prod/00/PPSA04029_00/app/info/85/f_b8b9ebfb1105001e92fdef937330b9ff6d169bdacfd83d97d93331fe1f45e2dc/EP4497-PPSA04029_00-0000000000000N22.json" metadata_ver="85" pfs_revision="47" system_ver="291504133"/>'
    package = ContentPackage.from_xml(xml_string)
    assert package.__class__ is ContentPackage

def test_ContentPackage_create_from_xml_parse_manifest():
    xml_string = '<package content_ver="02.310.000" delta_url="http://gst.prod.dl.playstation.net/gst/prod/00/PPSA03974_00/app/pkg/47/f_bb1b3ea77bc527d9e5d0259c0c1e17f8e7069344f81f88ebcb2d9b1aeb908a4f/UP4497-PPSA03974_00-0000000000000CP1-DP.pkg" digest="261996e21f936c2f14af67eaa2c616afbe15e833bf337ed2a466627cb1a9773f" mandatory="false" manifest_url="https://sgst.prod.dl.playstation.net/sgst/prod/00/PPSA04029_00/app/info/85/f_b8b9ebfb1105001e92fdef937330b9ff6d169bdacfd83d97d93331fe1f45e2dc/EP4497-PPSA04029_00-0000000000000N22.json" metadata_ver="85" pfs_revision="47" system_ver="291504133"/>'
    package = ContentPackage.from_xml(xml_string)
    package.get_package()
    assert package.__class__ is ContentPackage
    
def test_ContentPackage_create_from_xml_selective_entitlement():
    xml_string = '<package content_ver="02.310.100" delta_url="http://gst.prod.dl.playstation.net/gst/prod/00/PPSA03974_00/app/pkg/52/f_2a5d6baa88ef2b2bd2f354f299aa11c5798d1e2140f62e75b2bcc66b16404bbb/UP4497-PPSA03974_00-0000000000000CP1-DP.pkg" digest="5699098a882a5dcc12d2ed4e60851f3db7c346da89f0b02c811d30d828147a77" mandatory="false" manifest_url="https://sgst.prod.dl.playstation.net/sgst/prod/00/PPSA04029_00/app/info/97/f_e88f6cfef04eaec502319f38bc7a137e2f69f80c7b73fd391308f8236f87804f/EP4497-PPSA04029_00-0000000000000N22.json" metadata_ver="97" pfs_revision="52" selective="true" system_ver="318767168"><distro_entitlement><entitlement id="EP4497-PPSA04029_00-PROTRACKER000000"/></distro_entitlement></package>'
    package = ContentPackage.from_xml(xml_string)
    assert package.selective is True
    assert len(package.distro_entitlements) == 1
    assert package.distro_entitlements[0] == 'EP4497-PPSA04029_00-PROTRACKER000000'

def test_ContentPackage_create_from_xml_selective_predownload():
    xml_string = '<package content_ver="01.097.000" delta_url="http://gst.prod.dl.playstation.net/gst/prod/00/PPSA07950_00/app/pkg/101/f_7df59fe2bfbec653d8ed7c8dbcfdfce1f0520e2ae905346ab742c1f497fbb765/EP0002-PPSA07950_00-COREGAME00000001-DP.pkg" digest="b6f0a93707b377572b4a39f0844ea204de562c1b96a56066b8291aa3a05a57c4" mandatory="false" manifest_url="https://sgst.prod.dl.playstation.net/sgst/prod/00/PPSA07950_00/app/info/347/f_0c52a0a20ded315edb13758c793d9ecd435f1784461fd00afd824c3e3cafd642/EP0002-PPSA07950_00-COREGAME00000001.json" metadata_ver="347" pfs_revision="101" selective="true" system_ver="318767168"><distro_predownload><distribution_date date="2026-04-30T04:00:00Z" percentage="33"/><distribution_date date="2026-04-30T10:00:00Z" percentage="66"/><distribution_date date="2026-04-30T13:00:00Z" percentage="100"/><installable_date date="2026-04-30T16:00:00Z"/></distro_predownload></package>'
    package = ContentPackage.from_xml(xml_string)
    assert package.selective is True
    assert len(package.distro_predownloads) == 3
    assert package.distro_predownloads[0]['percentage'] == '33'
    assert package.distro_predownloads[1]['percentage'] == '66'
    assert package.distro_predownloads[2]['percentage'] == '100'
    assert str(package.distro_predownload_install_date) == '2026-04-30 16:00:00'

def test_ContentPackage_create_from_xml_flexcontent():
    xml_string = '<package content_ver="01.001.000" delta_url="http://gst.prod.dl.playstation.net/gst/prod/00/PPSA37414_00/app/pkg/2/f_1e4d2bcc9b27cbe6243fdf6c2d687a38a4af15baaf8aa9e7d88c0e96a0b17471/EP0002-PPSA37414_00-CODMW4BETA000001-DP.pkg" digest="075cca26ebb3ab61abd03541eb7f0273c9f6e22566e2399022c08f9b2426dc59" mandatory="false" manifest_url="https://sgst.prod.dl.playstation.net/sgst/prod/00/PPSA37414_00/app/info/2/f_a557190bf439d572b971eaf34afb7e41b715851d3f20e5b3f860eaefc7241fc4/EP0002-PPSA37414_00-CODMW4BETA000001.json" metadata_ver="2" pfs_revision="2" system_ver="325058567"/>'
    package = ContentPackage.from_xml(xml_string)
    package.get_package()
    assert package.__class__ is ContentPackage
    assert len(package.flex_content) == 1
    assert package.flex_content[0].__class__ is FlexContent

def test_ContentPackage_parse_system_version():
    def get_system_versions(version_str):
        version_hex_str = version_str.replace('.', '')
        version_int_str = str(struct.unpack('>I', bytes.fromhex(version_hex_str))[0])
        return (version_str, version_int_str)

    xml_string = '<package content_ver="02.310.000" delta_url="http://gst.prod.dl.playstation.net/gst/prod/00/PPSA03974_00/app/pkg/47/f_bb1b3ea77bc527d9e5d0259c0c1e17f8e7069344f81f88ebcb2d9b1aeb908a4f/UP4497-PPSA03974_00-0000000000000CP1-DP.pkg" digest="261996e21f936c2f14af67eaa2c616afbe15e833bf337ed2a466627cb1a9773f" mandatory="false" manifest_url="https://sgst.prod.dl.playstation.net/sgst/prod/00/PPSA04029_00/app/info/85/f_b8b9ebfb1105001e92fdef937330b9ff6d169bdacfd83d97d93331fe1f45e2dc/EP4497-PPSA04029_00-0000000000000N22.json" metadata_ver="85" pfs_revision="47" system_ver="291504133"/>'
    package = ContentPackage.from_xml(xml_string)
    expected_system_version = '11.60.00.05'
    package._format_system_version()
    assert package.system_version == expected_system_version

    expected_versions = get_system_versions('01.50.00.00')
    expected_system_version = expected_versions[0]
    package.system_version = expected_versions[1]
    package._format_system_version()
    assert package.system_version == expected_system_version

    expected_versions = get_system_versions('99.99.99.99')
    expected_system_version = expected_versions[0]
    package.system_version = expected_versions[1]
    package._format_system_version()
    assert package.system_version == expected_system_version

def test_ContentPackage_parse_system_version_bad_version():
    xml_string = '<package content_ver="02.310.000" delta_url="http://gst.prod.dl.playstation.net/gst/prod/00/PPSA03974_00/app/pkg/47/f_bb1b3ea77bc527d9e5d0259c0c1e17f8e7069344f81f88ebcb2d9b1aeb908a4f/UP4497-PPSA03974_00-0000000000000CP1-DP.pkg" digest="261996e21f936c2f14af67eaa2c616afbe15e833bf337ed2a466627cb1a9773f" mandatory="false" manifest_url="https://sgst.prod.dl.playstation.net/sgst/prod/00/PPSA04029_00/app/info/85/f_b8b9ebfb1105001e92fdef937330b9ff6d169bdacfd83d97d93331fe1f45e2dc/EP4497-PPSA04029_00-0000000000000N22.json" metadata_ver="85" pfs_revision="47" system_ver="291504133"/>'
    package = ContentPackage.from_xml(xml_string)
    package.system_version = '123bad'
    assert package._format_system_version() is False

logger = logging.getLogger(__name__)