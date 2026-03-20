#   MIT License

#   Copyright (c) 2025, 2026 andshrew
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
import io
import json
import logging
from pathlib import Path
import socket
import ssl
from urllib.parse import urlparse
import xml.etree.ElementTree as xml
from .pkg import *

import requests

class Ps5TitleUpdate:
    """A simple PS5 title update object.

    Create a simple PS5 title update object by supplying a PS5 title id and an update
    URL. Optionally can extract metadata from the updates PKG file.

    Attributes:
        title_id: A PS5 Title Id like PPSA01001_00
        update_url: The URL for the titles update XML
        download_pkg: Download and extract param.sfo and changeinfo from update pkg file
                    Default is 'True'
        byte_limit: Download up to this many bytes of the update pkg file
    """

    def __init__(self, title_id=None, update_url=None, download_pkg=True, byte_limit=50000000,
                 ac=False, content_id=None):
        
        # Parse params
        self.title_id = title_id.replace("_00", "")
        self.title_id = self.title_id.upper()
        if len(self.title_id) != 9:
            raise ValueError('Title Id must be like PPSA01001 or PPSA01001_00')
        if update_url == None:
            raise ValueError('Title Update Url must be supplied')
        if self.title_id not in update_url.upper():
            raise ValueError('Title Id not in Update Url')
        self.byte_download_limit = byte_limit
        if isinstance(self.byte_download_limit, int) is not True:
            logger.debug(f'Byte download limit is not an integer: {self.byte_download_limit}')
            raise ValueError('Byte Limit must be an integer')
        # Additional Content
        self.is_ac = False
        self.ac_content_id = None
        if ac is True:
            if content_id is None:
                raise ValueError('Additional Content updates require the Content Id')
            self.is_ac = True
            self.ac_content_id = content_id
        # Setup object
        self.content_id = None
        self.creation_date = None
        self.import_date = None
        self.import_date_string = None
        self.tool_version = None
        self.name = None
        self.update_url = update_url
        self.version = None
        self.update_exists = False
        self.update_size = None
        self.update_xml = None
        self.update_pkg_manifest_exists = False
        self.update_pkg_manifest_url = None
        self.update_pkg_manifest_json = None
        self.update_pkg_param_exists = False
        self.update_pkg_param = None
        self.update_pkg_param_json = None

    def _parse_update_xml(self):
        url = self.update_url
        response = invoke_web_request(url, verify_https=False)
        if response == None:
            return
        if response.status_code == 404:
            # No update exists
            return
        
        try:
            update_xml = xml.fromstring(response.text)
        except xml.ParseError as ex:
            logger.error(f'Unable to parse XML: {ex.args}')
            return
        
        tag_name = 'app_tag'
        tag_index = 0
        if self.is_ac:
            tag_name = 'ac_tag'
        
        app_update = update_xml.findall(tag_name)

        if self.is_ac:
            ac_index = -1
            for i in range(len(app_update)):
                if app_update[i].attrib['content_id'] == self.ac_content_id:
                    tag_index = i
                    break
                if ac_index == -1:
                    logger.warning(f'No entry in update XML for Additional Content Id: {self.ac_content_id}')
                    return

        if len(app_update) == 0:
            logger.error(f'Tag "{tag_name}" not found in update XML: {url}')
        else:
            if len(app_update) > 1 and self.is_ac == False:
                logger.warning(f'App has multiple "app_tag" entries in the update XML. Only the first entry will be processed')
            if 'content_id' in app_update[tag_index].keys():
                    self.content_id = app_update[tag_index].attrib['content_id']
            if 'name' in app_update[tag_index].keys():
                    self.import_date_string = app_update[tag_index].attrib['name']
                    try:
                        self.import_date = datetime.strptime(self.import_date_string[7:], '%Y%m%d%H%M%S')
                    except Exception as ex:
                        logger.error(f'Unable to parse import_date into datetime: {self.import_date_string}')
            app_package = app_update[tag_index].find('package')
            if app_package is not None:
                self.update_exists = True
                if 'content_ver' in app_package.keys():
                    self.version = app_package.attrib['content_ver']
                if 'manifest_url' in app_package.keys():
                    self.update_pkg_manifest_url = app_package.attrib['manifest_url']
            self.update_xml = response.text

    def _parse_update_pkg_json(self):
        """Internal method for parsing the updates pkg manifest JSON file

        The URL for downloading an update pkg file is stored in the manifest JSON file.
        Determines if the manifest file is available, and extracts the URL to the pkg file.
        """

        url = self.update_pkg_manifest_url
        response = invoke_web_request(url, verify_https=False)
        if response == None:
            return
        try:
            package_data = json.loads(response.text)
        except json.JSONDecodeError as ex:
            logger.error(f'Unable to parse JSON: {ex.args}')
            return
        # Locate the _sc.pkg file so that addition data can be extracted
        package_piece = package_data['pieces'][0]
        package_piece = next((x for x in package_data['pieces'] if "_sc.pkg" in x['url'].lower()), None)
        # Update file size
        *_, v = next(find_key(package_data, 'originalFileSize'), None)
        if v is not None:
            self.update_size = bytes_to_formatted_filesize(v)
        self.update_pkg_manifest_exists = True
        self.update_pkg_url = package_piece['url']
        self.update_pkg_manifest_json = response.text

    def save_update_info(self, base_path="data_dump"):
        """Save title update information as files

        When a title has an update available, this method can save some files associated with the update to disk.
        It will attempt to save the files in 'base_path/title_id/version'

        Files saved:
        param.json (pkg metadata, included in update pkg file)
        {guid}-version.xml (the main update XML)
        {content_id}.json (URLs to the update pkg file)
        {creation_date} (creation date, included in update pkg file)

        Note this does not save the update pkg file.

        Attributes:
            base_path: Path where the files should be created
        """

        content_id = None
        if self.is_ac:
            content_id = self.ac_content_id

        if self.update_exists is True:
            save_data_to_file(data=self.update_xml, titleid=self.title_id, version=self.version,
                            url=self.update_url, base_path=base_path, content_id=content_id)
        if self.update_pkg_manifest_exists is True:
            save_data_to_file(data=self.update_pkg_manifest_json, titleid=self.title_id, version=self.version,
                            url=self.update_pkg_manifest_url, base_path=base_path, content_id=content_id)
        if self.update_pkg_param_exists is True:
            if self.update_pkg_param_exists is True:
                save_data_to_file(data=self.update_pkg_param_json, titleid=self.title_id, version=self.version,
                                filename='param.json', base_path=base_path, content_id=content_id)
                if self.creation_date is not None:
                    save_data_to_file(data=self.creation_date, titleid=self.title_id, version=self.version,
                                filename=f'{self.creation_date[0:10]}', base_path=base_path, content_id=content_id)
    
    def _get_partial_pkg_file(self, url=None, port=80, additional_files=None):
        """Internal method for partially downloading an update pkg file

        The PKG file for an update contains additional information relating to update.
        This method parses the PKG header and file table, and then will download data
        up to the location of the files of interest.
        Currently looks for 'param.json'

        Attributes:
            url: URL to a pkg file
            additional_files: Download all files within the pkg
        """

        self.update_pkg_bytes_exceeded = False
        if url is None:
            url = self.update_pkg_url
        url_parsed = urlparse(url)
        if url_parsed.port != None:
            port=url_parsed.port
        elif url_parsed.scheme == "https":
            port=443
        byte_limit = self.byte_download_limit
        
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(10)
        try:
            s.connect((url_parsed.hostname, port))
        except socket.timeout as ex:
            logger.error(f'Socket timeout connecting to: {url_parsed.hostname} port {port}')
            return

        if url_parsed.scheme == "https":
            # ssl.CERT_NONE will disable validating server cert (ie. no requirement for issuing CA to be in our trusted CAs)
            # When HTTPS is used by the update servers they are typically using certificates issued by an internal CA, so
            # this validation would fail.
            # Ref: https://docs.python.org/3/library/ssl.html
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            #context = ssl._create_unverified_context(cert_reqs=ssl.CERT_NONE)
            try:
                s = context.wrap_socket(s, server_hostname=url_parsed.hostname)
            except Exception as ex:
                logger.error(f'Socket error {url_parsed.hostname} port {port}: {ex.args}')
                return
        s.settimeout(60)
        request = f'GET {url_parsed.path} HTTP/1.1\r\nHost:{url_parsed.hostname}\r\nConnection: close\r\n\r\n'
        s.send(request.encode())

        # Build up the pkg file in the response variable
        response = b''
        bytes_rcvd = 0

        pkg = None
        pkg_magic = b'\x7fCNT'

        # Locate the PKG file in the downloaded data
        while True:
            response, success = socket_recv_data(s, 4096)
            bytes_rcvd += len(response)
            if pkg_magic in response:
                break
            if pkg_magic not in response:
                # Sometimes downloads are redirected to specific CDN URL
                if "302 Moved Temporarily" in response[0:100].decode():
                    logger.debug(f'302 Moved Temporarily')
                    response_headers = response.decode().splitlines()
                    for i, c in enumerate(response_headers):
                        if "Location: " in c:
                            redirect_url = urlparse(response_headers[i].replace("Location: ", ""))
                            logger.debug(f'Trying again with URL: {redirect_url.geturl()}')
                            # Call this method again to try and download using the CDN URL
                            s.close()
                            return self._get_partial_pkg_file(url=redirect_url.geturl())
            if bytes_rcvd >= byte_limit:
                logger.error(f'PKG file header NOT found - byte limit {byte_limit} reached - actual bytes downloaded {bytes_rcvd}')
                response = None
                break
        # The PKG file has been found in the response
        if pkg_magic in response:            
            # Discard the initial part of the response, so that response now starts with the PKG file
            offset = response.find(pkg_magic)
            response = response[offset:]
            pkg = PKG(offset = 0)

            # Parse the PKG header
            with io.BytesIO(response) as b:
                pkg.set_from_bytes(b)

            # Continue downloading data up to the end of the PKG files table
            pkg_table_end = pkg.table_offset + (pkg.file_count * 32)
            s_data, end = socket_recv_data(s, 4096, pkg_table_end)
            response = response + s_data
            bytes_rcvd += len(response)
            
            # If end of socket data?
            
            # Parse the PKG files table
            with io.BytesIO(response) as b:
                pkg.set_pkg_files(b)

            # Download up to the PKG filenames file
            if len(response) < pkg.filename_offset + pkg.filename_size:
                s_data, end = socket_recv_data(s, 4096, pkg.filename_offset + pkg.filename_size)
                with io.BytesIO(response) as b:
                    pkg._set_filename_offset(b)

            # Download up to param.json
            param_json = next((x for x in pkg.files if x.id == 8192), None)
            if param_json is not None:
                if len(response) < param_json.offset + param_json.size:
                    s_data, end = socket_recv_data(s, 4096, param_json.offset + param_json.size)
                    response = response + s_data
                    bytes_rcvd += len(response)
                self.update_pkg_param = json.loads(response[param_json.offset:param_json.offset + param_json.size])
                self.update_pkg_param_json = response[param_json.offset:param_json.offset + param_json.size].decode()
                self.update_pkg_param_exists = True

                # Set what language to read param.json metadata, but for now this is overridden by
                # the param.json's defaultLanguage if it exists
                language = "en-US"
                *_, v = next(find_key(self.update_pkg_param, 'defaultLanguage'), None)
                if v is not None:
                    language = v
                    logger.debug(f'Param.json defaultLanguage is {v}')
                
                *_, v = next(find_key(self.update_pkg_param, 'titleName', language))
                if v is not None:
                    self.name = v
                else:
                    logger.warning(f'No titleName found for {language} in the param.json')

                #*_, v = next(find_key(self.update_pkg_param, 'titleName'), None)
                #if v is not None:
                #    self.name = v

                *_, v = next(find_key(self.update_pkg_param, 'creationDate'), None)
                if v is not None:
                    self.creation_date = v
                
                *_, v = next(find_key(self.update_pkg_param, 'toolVersion'), None)
                if v is not None:
                    self.tool_version = v
            
            # Download additional files within the pkg
            if additional_files is not None:
                #file = next((x for x in pkg.files if x.id == 12288), None)
                for file in pkg.files:
                    if file is not None:
                        logger.debug(f'Current bytes: {bytes_to_formatted_filesize(bytes_rcvd)} Target bytes: {bytes_to_formatted_filesize(file.offset + file.size)}')
                        if len(response) < file.offset + file.size:
                            s_data, end = socket_recv_data(s, 131072, file.offset + file.size)
                            response = response + s_data
                            bytes_rcvd += len(response)
                        content_id = None
                        if self.is_ac:
                            content_id = self.ac_content_id
                        filename = file.filename
                        if filename == '':
                            filename = f'{file.id}'
                        #save_data_to_file(data=response[file.offset:file.offset + file.size].decode(), titleid=self.title_id, version=self.version,
                                    #content_id=content_id, filename=filename)
                        save_data_to_file(data=response[file.offset:file.offset + file.size], titleid=self.title_id, version=self.version,
                                    content_id=content_id, filename=filename, write_bytes=True)



        s.close()

        logger.debug(f'In total {bytes_to_formatted_filesize(bytes_rcvd)} of the PKG file was downloaded')

        return
    
    def get_update(self, download_pkg=True):
        """Get title update information

        This method retrieves information relating to the titles updates.

        By default, if an update exists, it will download the pkg file to retrieve information
        such as changeinfo.xml and cdate.

        Attributes:
            download_pkg: Disables downloading update pkg file when set to False
                            Default is True
        """

        self._get_update_run = True
        self._parse_update_xml()
        if self.update_exists is True:
            self._parse_update_pkg_json()
        if self.update_pkg_manifest_exists == download_pkg == True:
            self._get_partial_pkg_file()

class Ps5AdditionalContentUpdate(Ps5TitleUpdate):
    def __init__(self):
        pass

def invoke_web_request(url, verify_https=True):
    """Invoke a web request
    
    Utility function to create a request to a URL and return the response.

    Attributes:
        url: URL to request
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

def save_data_to_file(data, titleid, version, content_id=None, filename=None, url=None, base_path="data_dump", write_bytes=False):
    """Save a string of data to a file

    Utility function to save a string of data to a file. The file is created at:
    {base_path}/{titleid}/{version}/{filename OR url}
    or {base_path}/{titleid}/{additional_content_id}/{version}/{filename OR url}

    Attributes:
        data: String of data which will be the contents of the file
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

    Converts file size in bytes to a formatted string in either MB or GB.

    Attributes:
        size_in_bytes: Size as bytes for conversion
    """

    if size_in_bytes > 1073741824:
        return f'{round(size_in_bytes / 1048576 / 1024, 2)} GB'
    return f'{round(size_in_bytes / 1048576, 2)} MB'

def socket_recv_data(s: socket.socket, chunk_size: int, size_to_recv: int = None):
    """Utility function to receive data from an open socket

    Receives data in chunks of chunk_size up to a maximum or size_to_recv

    Attributes:
        s: An open socket ready to recv data
        chunk_size: Each recv requrest will request up to this number of bytes
        size_to_recv: Total amount of bytes to recv before returning
    """
    bytes_recv = b''
    no_more_data = False
    if size_to_recv is None:
        size_to_recv = chunk_size
    while len(bytes_recv) < size_to_recv:
        chunk = s.recv(chunk_size)
        if len(chunk) == 0:
            # No more data received in the request
            no_more_data = True
            break
        bytes_recv = bytes_recv + chunk
    return bytes_recv, no_more_data

def find_key(data, match, match_parent=None, parent=None, path=()):
    """Utility function for locating a key within a dict (or a list of dicts)

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
            yield from find_key(value, match, match_parent, (key, type(key)), path + (key,))
    if isinstance(data, list):
        for index, value in enumerate(data):
            yield from find_key(value, match, match_parent, parent, path + (index,))

def _find_key_static_match(data, match, match_parent, parent):
    if match_parent is not None:
        if match_parent != parent[0]:
            return False
    return data == match

logger = logging.getLogger(__name__)