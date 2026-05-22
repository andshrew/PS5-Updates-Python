#   MIT License

#   Copyright (c) 2025-2026 andshrew
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

from datetime import datetime
import json
import logging
from pathlib import Path
import struct
from urllib.parse import urlparse
import xml.etree.ElementTree as xml
from .pkg import *

import requests

@dataclass
class ContentPackage:
    """
    Creates an object to store data from the `<package>` tag of a titles update XML.

    Each ContentPackage represents a single update pkg file, with the `PKG` object accessible
    from the `pkg` property after calling `get_update()`.
    """
    version: str
    manifest_url: str
    digest: str
    mandatory: bool
    metadata_version: int # Number but string
    pfs_revision: int  # Number but string
    system_version: str
    delta_url: Optional[str] = None # App only?
    manifest_exists: Optional[bool] = False
    manifest_json: Optional[str] = None
    update_size: Optional[str] = None
    pkg_url: Optional[str] = None
    pkg: Optional[PKG] = None
    selective: Optional[bool] = False # Pre-download and pre-release updates
    distro_entitlements: Optional[list] = field(default_factory=list)
    distro_predownloads: Optional[list] = field(default_factory=list)
    distro_predownload_install_date: Optional[datetime] = None

    def __post_init__(self):
        self._format_system_version()
    
    @classmethod
    def from_xml(cls, xml_string: str) -> 'ContentPackage':
        """Create an instance from an XML string

        Attributes:
            xml_string: An XML string of a `<package>` tag within a titles update XML
        """
        package = xml.fromstring(xml_string)
        version = package.attrib.get('content_ver')
        manifest_url = package.attrib.get('manifest_url')
        digest = package.attrib.get('digest')
        mandatory = bool(package.attrib.get('mandatory'))
        metadata_ver = int(package.attrib.get('metadata_ver'))
        pfs_rev = int(package.attrib.get('pfs_revision'))
        system_ver = package.attrib.get('system_ver')
        selective = bool(package.attrib.get('selective', False))
        distro_entitlements = []
        distro_predownloads = []
        distro_predownload_install_date = None
        if selective:
            # Pre-release update based on an account entitlement
            distro_entitle = package.find('distro_entitlement')
            if distro_entitle is not None:
                logger.debug('This package is a pre-release download based on an account entitlement eligibility')
                entitlements = distro_entitle.findall('entitlement')
                for entitlement in entitlements:
                    e = entitlement.attrib.get('id')
                    if e is not None:
                        distro_entitlements.append(e)
            # Pre-download update
            distro_preload = package.find('distro_predownload')
            if distro_preload is not None:
                install_date = distro_preload.find('installable_date')
                if install_date is not None:
                    date = install_date.get('date')
                    if date[-1] != 'Z':
                        logger.error(f'Pre-download installable date is not the expected Z (UTC): {date}')
                    else:
                        distro_predownload_install_date = datetime.strptime(date, '%Y-%m-%dT%H:%M:%SZ')
                logger.debug(f'This package is a predownload of an upcoming update installable at: {distro_predownload_install_date}')
                install_groups = distro_preload.findall('distribution_date')
                for group in install_groups:
                    date = group.get('date')
                    if date[-1] != 'Z':
                        logger.error(f'Pre-download distribution date is not the expected Z (UTC): {date}')
                    else:
                        distro_date = datetime.strptime(date, '%Y-%m-%dT%H:%M:%SZ')
                    percentage = group.get('percentage')
                    distro_predownloads.append(
                        {'date': distro_date,
                         'percentage': percentage}
                    )

        return cls(version=version, manifest_url=manifest_url, digest=digest,
                   mandatory=mandatory, metadata_version=metadata_ver, pfs_revision=pfs_rev,
                   system_version=system_ver, selective=selective,
                   distro_entitlements=distro_entitlements, distro_predownloads=distro_predownloads,
                   distro_predownload_install_date=distro_predownload_install_date)

    def get_package(self):
        """
        Requests the manifest URL and partially downloads the '_sc.pkg' file to
        extract the updates `PKG` metadata.

        The `pkg` property should contain a valid `PKG` object once called.
        """
        self._parse_manifest_json()
        self._get_update_metadata()

    def _format_system_version(self):
        """
        The required system version is stored as an unsigned big-endian 32bit integer
        This is converted into a bytes object and converted to hex using '.' as the byte seperator
        to get the display version ie. 11.60.00.05
        """
        if type(self.system_version) is str and '.' not in self.system_version:
            try:
                sys_ver = int(self.system_version)
            except ValueError as ex:
                logger.error(f'Unable to convert system_version to int: {ex.args}')
                return False
            #sys_ver_bytes = sys_ver.to_bytes(length=struct.calcsize('>I'), byteorder='big')
            self.system_version = struct.pack('>I', sys_ver).hex('.', 1)

    def _parse_manifest_json(self):
        """
        Internal function for parsing a packages manifest JSON file.

        This will locate the `_sc.pkg` URL required for creating a `PKG` object.

        Additionally sets the download size for the update.
        """
        url = self.manifest_url
        logger.debug(f'Requesting package manifest URL: {url}')
        response = invoke_web_request(url, verify_https=False)
        if response == None:
            logger.error('Invalid response from package manifest URL')
            return
        try:
            manifest = json.loads(response.text)
        except json.JSONDecodeError as ex:
            logger.error(f'Unable to parse package manifest JSON: {ex.args}')
            return
        # Locate the _sc.pkg file so that addition data can be extracted
        package_piece = manifest['pieces'][0]
        package_piece = next((x for x in manifest['pieces'] if "_sc.pkg" in x['url'].lower()), None)
        # Update file size
        update_size = find_key(manifest, 'originalFileSize')
        if update_size is not None:
            self.update_size = bytes_to_formatted_filesize(update_size)
        self.manifest_exists = True
        self.pkg_url = package_piece['url']
        self.manifest_json = response.text

    def _get_update_metadata(self):
        """
        Internal function for creating a `PKG` object and retrieving
        the `PKG` metadata.
        """
        if self.pkg_url is not None:
            pkg = PKG.from_url(self.pkg_url)
            if pkg is not None:
                self.pkg = pkg
        else:
            logger.error(f'pkg_url is not valid: {self.pkg_url}')

@dataclass
class AdditionalContent:
    """
    An object for storing Additional Content update information for a PS5 title.

    Attributes:
        content_id: The unique content id for the additional content
    """
    content_id: str
    revision: str = None
    name: str = None
    import_date: datetime = None
    packages: List[ContentPackage] = field(default_factory=list)
    latest: Optional[ContentPackage] = None

    def __post_init__(self):
        if len(self.packages) > 0:
            # Set the first package in the list as the latest
            self.latest = self.packages[0]

    @classmethod
    def from_xml_element(cls, xml_data: xml.Element) -> 'AdditionalContent':
        """Create an instance from a parsed xml `Element` object

        Attributes:
            xml_data: An `<ac_tag>` xml tag which has been parsed into an `Element` object
        """
        content_id = xml_data.attrib.get('content_id')
        revision = xml_data.attrib.get('revision')
        name = xml_data.attrib.get('name')
        if name is not None:
            try:
                import_date = datetime.strptime(name[7:], '%Y%m%d%H%M%S')
            except Exception as ex:
                logger.error(f'Unable to parse name (Import Date) into datetime: {name}')
            parsed_packages = []
            packages = xml_data.findall('package')
            for package in packages:
                content = ContentPackage.from_xml(xml.tostring(package))
                parsed_packages.append(content)
        return cls(content_id=content_id, revision=revision, name=name,
                   import_date=import_date,packages=parsed_packages)

@dataclass
class Ps5TitleUpdate:
    """A PS5 title update object

    Creates an object for storing information relating to the current update
    for a PS5 title.

    Attributes:
        update_url: The URL for the titles update XML
    """
    update_url: str
    additional_content: List[AdditionalContent] = field(default_factory=list)
    packages: List[ContentPackage] = field(default_factory=list)
    latest: Optional[ContentPackage] = None
    content_id: Optional[str] = None
    update_xml: Optional[str] = None
    title_id: Optional[str] = None
    import_date: Optional[datetime] = None
    _is_parsed: Optional[bool] = False

    def __post_init__(self):
        self._parse_update_xml()

    @classmethod
    def from_url(cls, url: str) -> 'Ps5TitleUpdate':
        """Create an instance from a URL

        Attributes:
            url: A URL of titles update XML, eg: `https://sgst.prod.dl.playstation.net/sgst/prod/00/np/PPSA07632_00/53d40bc7-7b1a-403c-8260-4b293b1711fd-version.xml`
        """
        return cls(update_url=url)
    
    @classmethod
    def from_pkg_url(cls, url) -> 'Ps5TitleUpdate':
        """Create an instance from an `_sc.pkg` URL
        
        Attributes:
            url: A URL of a specific `_sc.pkg` update file, eg: `https://sgst.prod.dl.playstation.net/sgst/prod/00/PPSA07632_00/app/info/26/f_7d7a8867ec1eae1e09d81732b29010e14420e152254af6d04eda18ab3c364240/UP9000-PPSA07632_00-SAROS00000000000_sc.pkg`
        """
        pkg = PKG.from_url(url)
        return cls(update_url=pkg.param.version_url)
    
    @classmethod
    def from_pkg_file(cls, path) -> 'Ps5TitleUpdate':
        """Create an instance from an `_sc.pkg` file path

        Attributes:
            path: A path to an `_sc.pkg` file
        """
        pkg = PKG.from_file(path)
        return cls(update_url=pkg.param.version_url)

    def _parse_update_xml(self):
        """
        An internal function for parsing the update XML file.
        """
        url = self.update_url
        logger.debug(f'Requesting package update URL: {url}')
        response = invoke_web_request(url, verify_https=False)
        if response == None:
            logger.error('Invalid response from package update URL')
            return
        if response.status_code == 404:
            # No update exists
            return
        try:
            update_xml = xml.fromstring(response.text)
            self._is_parsed = True
        except xml.ParseError as ex:
            logger.error(f'Unable to parse parse update XML: {ex.args}')
            return
        
        # Parse attributes of interest
        self.title_id = update_xml.attrib.get('nptitleid')

        # Parse app updates into objects
        for tag in ['app_tag', 'ac_tag']:
            updates = update_xml.findall(tag)
            if tag == 'app_tag':
                # Main app content
                # Assumption that there is only 1 `app_tag` entry per title
                self.content_id = updates[0].attrib.get('content_id')
                try:
                    name = updates[0].attrib.get('name')
                    self.import_date = datetime.strptime(name[7:], '%Y%m%d%H%M%S')
                except Exception as ex:
                    logger.error(f'Unable to parse name (Import Date) into datetime: {name}')
                if len(updates) > 1:
                    logger.warning('This title has more than one item listed within the "app_tag"')
                packages = updates[0].findall('package')
                for package in packages:
                    content = ContentPackage.from_xml(xml.tostring(package))
                    self.packages.append(content)
            if tag == 'ac_tag':
                # Additional content
                for update in updates:
                    ac = AdditionalContent.from_xml_element(update)
                    self.additional_content.append(ac)
        
        # Set the first package in the list as the latest
        if len(self.packages) > 0:
            self.latest = self.packages[0]

        # Save the XML string
        self.update_xml = response.text

    def get_update(self):
        """
        Downloads `PKG` data for all packages listed in the update XML.

        Alternatively call `get_package()` on each `ContentPackage` to
        download specific `PKG` file data.
        """
        if self._is_parsed:
            for package in self.packages:
                package.get_package()
            for ac in self.additional_content:
                for package in ac.packages:
                    package.get_package()

def invoke_web_request(url: str, verify_https: bool=True):
    """Invoke a web request

    Utility function to create a request to a URL and return the response.

    Attributes:
        url: URL to request
        verify_https: False to disable server certificate validation
    """

    try:
        urlparse(url)
    except Exception as ex:
        # TODO does not throw exception on invalid URL
        logger.debug(f'Invalid URL?: {ex.args}')
        return
    try:
        req = requests.get(url, verify=verify_https)
    except requests.exceptions.RequestException as ex:
        logger.error(f'Requests protocol exception for: {url}: {ex.args}')
        return
    except Exception as ex:
        logger.error(f'Unable to request: {url}: {ex.args}')
        return
    return req 

def save_data_to_file(data: Union[str, bytes], titleid, version, content_id=None, filename=None, url=None, base_path="data_dump", write_bytes=False):
    """Save data to a file

    Utility function to save a string or bytes of data to a file. The file is created at:
    {base_path}/{titleid}/{version}/{filename OR url}
    or {base_path}/{titleid}/{content_id}/{version}/{filename OR url}

    Attributes:
        data: String or bytes of data which will be the contents of the file
        titleid: Part of folder path
        version: Part of folder path
        filename: Name for the file - Note not used if url is supplied
        url: Last part of path will be used as the filename
        base_path: Base folder path
    """

    destination_path = Path(base_path)
    if content_id is not None:
        destination_path = destination_path.joinpath(titleid, content_id, version)
    else:
        destination_path = destination_path.joinpath(titleid, version)
    if destination_path.exists() is False:
        try:
            destination_path.mkdir(parents=True)
            logging.debug(f'Created path: {destination_path}')
        except Exception as ex:
            logging.error(f'Unable to create path: {ex.args}')
            return

    if url is not None:
        filename = url.split('/')[-1]

    full_path = destination_path.joinpath(filename)

    if full_path.exists() is False:
        try:
            if write_bytes:
                full_path.write_bytes(data)
            else:
                full_path.write_text(data)
            logging.debug(f'Created {full_path}')
        except Exception as ex:
            logging.error(f'Unable to write file: {ex.args}')
            return

def bytes_to_formatted_filesize(size_in_bytes):
    """Format bytes to file size string (MB/GB)

    Converts file size in bytes to a formatted string in either MiB or GiB.

    Attributes:
        size_in_bytes: Size as bytes for conversion
    """
    # 1 GiB == 1073741824 bytes
    if size_in_bytes > 1073741824:
        return f'{round(size_in_bytes / 1048576 / 1024, 2)} GiB'
    return f'{round(size_in_bytes / 1048576, 2)} MiB'

def find_key(data: Union[dict, List], match, match_parent=None):
    """Find and return the value of a key within a dict (or a list of dicts)

    Utility function for locating a key within a dict (or a list of dicts) and
    returning the value.

    If the key is not found returns `None`.

    Attributes:
        data: A dict, or list of dicts
        match: The value to match
        match_parent: The value to match must have this parent
    """
    *_, v = next(_find_key(data=data, match=match, match_parent=match_parent), (False, False, None))
    return v

def _find_key(data, match, match_parent=None, parent=None, path=()):
    """
    Internal function for `find_key`.

    Attributes:
        data: A dict, or list of dicts
        match: The value to match, or a function to do more complex matching
        match_parent: The value to match must have this parent
        parent: The current parent (internal use)
        path: The current value path (internal use)
    """
    if parent == None:
        parent = ('.', type(data))
    if isinstance(data, dict):
        for key, value in data.items():
            if callable(match):
                if match(key, match_parent, parent):
                    yield path, key, value 
            else:
                if _find_key_static_match(key, match, match_parent, parent):
                    yield path, key, value
            yield from _find_key(value, match, match_parent, (key, type(key)), path + (key,))
    if isinstance(data, list):
        for index, value in enumerate(data):
            yield from _find_key(value, match, match_parent, parent, path + (index,))

def _find_key_static_match(data, match, match_parent, parent):
    """
    Interal function for `find_key`
    """
    if match_parent is not None:
        if match_parent != parent[0]:
            return False
    return data == match

logger = logging.getLogger(__name__)