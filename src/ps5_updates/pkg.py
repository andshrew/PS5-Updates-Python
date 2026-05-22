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

#   With thanks to PS4 Developer Wiki for the information on PKG files
#   PKG: https://www.psdevwiki.com/ps4/PKG_files

from datetime import datetime
import io
import json
import logging
import struct
from urllib.parse import urlparse, ParseResult
from dataclasses import dataclass, field
from typing import List, Optional, Callable, Union
from .data import HTTPSocket

def read_int8(b):
    return struct.unpack('<b', b.read(struct.calcsize('<b')))[0]

def read_int16(b):
    return struct.unpack('<h', b.read(struct.calcsize('<h')))[0]

def read_int32(b):
    return struct.unpack('<i', b.read(struct.calcsize('<i')))[0]

def read_uint32_be(b):
    return struct.unpack('>I', b.read(struct.calcsize('>I')))[0]

def read_uint64_be(b):
    return struct.unpack('>Q', b.read(struct.calcsize('>Q')))[0]

@dataclass
class PKG_Param:
    """Param metadata object

    The 'param' JSON file contains metadata releating to a title and is stored within the
    '_sc.pkg' and '_dp.pkg' files.

    Use the `get_property` function to retrieve properties which are not specifically mapped
    to attributes in this object.

    Read more about the param.json file:
        https://www.psdevwiki.com/ps5/Param.json

    Read more about attribute bit values:
        https://gist.github.com/andshrew/5ef86db5c10e65198a0f01c7795ea478

    Attributes:
        json: A valid JSON string
        data: A dict that has been created by parsing the JSON strong
    """
    json: str
    data: dict
    attribute: str = None
    attribute_binary: str = None
    attribute_set_bits: List = field(default_factory=list)
    attribute2: str = None
    attribute2_binary: str = None
    attribute2_set_bits: List = field(default_factory=list)
    attribute3: str = None
    attribute3_binary: str = None
    attribute3_set_bits: List = field(default_factory=list)
    attribute4: str = None
    attribute4_binary: str = None
    attribute4_set_bits: List = field(default_factory=list)
    download_data_size: str = None # Persistant user data storage (ie. mod support)
    title_id: str = None
    content_id: str = None
    content_version: str = None
    creation_date: datetime = None
    creation_date_string: str = None
    default_language: str = 'en-US'
    name: str = None
    pssr_version: str = None
    supports_ps5_pro: bool = False
    supports_8k: bool = False
    supports_hdr: bool = False # Supports High Dynamic Range
    supports_hfr: bool = False # Supports High Frame Rate (120hz)
    supports_power_saver: bool = False
    supports_vrr: bool = False # Supports Variable Refresh Rate
    supports_vrr_disabled: bool = False # VRR explicitly disabled
    supports_vrr_hfr: bool = False # A 120hz mode which requires VRR
    supports_psvr2_required: bool = False
    supports_psvr2_optional: bool = False
    required_system_version: str = None
    sdk_version: str = None
    version_url: str = None

    def __post_init__(self):
        default_language = self.get_property('defaultLanguage')
        if default_language is not None:
            logger.debug(f'defaultLanguage is {default_language}')
            self.default_language = default_language
        self.name = self.get_property('titleName', self.default_language)
        self.content_version = self.get_property('contentVersion')
        self.content_id = self.get_property('contentId')
        self.title_id = self.get_property('titleId')
        self.version_url = self.get_property('versionFileUri')
        if self.version_url is not None:
            self.version_url = self.version_url.strip()
        self.creation_date_string = self.get_property('creationDate')
        if self.creation_date_string is not None:
            try:
                self.creation_date = datetime.strptime(self.creation_date_string, '%Y-%m-%d %H:%M:%S')
            except Exception as ex:
                logger.error(f'Unable to parse creationDate into datetime: {self.creation_date_string}')
        self.required_system_version = self._format_hex_version(self.get_property('requiredSystemSoftwareVersion'))
        self.sdk_version = self._format_hex_version(self.get_property('sdkVersion'))
        # Parse the attribute properties
        for i in range(1,4):
            if i == 1:
                var_name = f'attribute'
            else:
                var_name = f'attribute{i}'
            setattr(self, var_name, self.get_property(var_name))
            if getattr(self, var_name) is not None:
                var_binary_name = f'{var_name}_binary'
                binary = format(getattr(self, var_name), '032b')
                setattr(self, var_binary_name, binary)
                var_set_bits = f'{var_name}_set_bits'
                set_bits = [32 - i for i, bit in enumerate(binary) if bit == '1']
                setattr(self, var_set_bits, set_bits)
        if self.attribute is not None:
            if 30 in self.attribute_set_bits:
                self.supports_hdr = True
        if self.attribute3 is not None:            
            if 23 in self.attribute3_set_bits:
                self.supports_ps5_pro = True
            if 7 in self.attribute3_set_bits:
                self.supports_hfr = True
            if 24 in self.attribute3_set_bits:
                self.supports_8k = True
            if 19 and 20 and 21 in self.attribute3_set_bits:
                self.supports_vrr_disabled = True
            elif 19 in self.attribute3_set_bits:
                self.supports_vrr = True
            elif 20 in self.attribute3_set_bits:
                self.supports_vrr_hfr = True
            if 11 and 12 in self.attribute3_set_bits:
                self.supports_psvr2_required = True
            elif 11 in self.attribute3_set_bits:
                self.supports_psvr2_optional = True
        if self.attribute4 is not None:
            if 1 in self.attribute4_set_bits:
                self.supports_power_saver = True
        self.pssr_version = self.get_property('mfsrVersion', 'psml')
        self.download_data_size = self._format_mebibyte_as_string(self.get_property('downloadDataSize'))

    @classmethod
    def from_bytes(cls, param_bytes: bytes):
        param_json_str = param_bytes.decode()
        param_parsed = json.loads(param_json_str)
        return cls(json=param_json_str, data=param_parsed)

    def get_property(self, name: Union[str, int], parent: Optional[str]=None):
        """Get a property by name

        Use this function to retrieve properties of the Param file which have
        not been specifically mapped to a variable in the parent object.

        Can return any valid JSON type (eg. String, Int, Dict, List).

        Returns None if property is not found.

        Attributes:
            name: Name of the property to find
            parent: Name of the parent this property must have (useful for returning
                properties which may share the same name)
        """
        def find_key(data, match, match_parent=None, parent=None, path=()):
            """Utility function for locating a key within a dict (or a list of dicts)

            Attributes:
                data: A dict, or list of dicts
                match: The value to match, or a function to do more complex matching
                match_parent: The value to match must have this parent
                parent: The current parent (internal use)
                path: The current value path (internal use)
            """
            def _find_key_static_match(data, match, match_parent, parent):
                if match_parent is not None:
                    if match_parent != parent[0]:
                        return False
                return data == match

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

        *_, v = next(find_key(data=self.data, match=name, match_parent=parent), (False, False, None))
        return v
    
    def _format_hex_version(self, version: str) -> Union[str, None]:
        if isinstance(version, str):
            if len(version) == 18:
                return '.'.join(version[2+i:2+i+2] for i in range(0, 8, 2))
        return None
    
    def _format_mebibyte_as_string(self, mebibyte: int) -> Union[str, None]:
        if isinstance(mebibyte, int):
            if mebibyte >= 1024:
                return f'{round(mebibyte / 1024, 2)} GiB'
            else:
                return f'{mebibyte} MiB'
        return None


@dataclass
class PKG_File:
    """PKG File object.

    Create a PKG File object to store information about a specific file within a PKG file.

    This object should be appended to the files attribute of a PKG object.

    For more information on the data structure see:

    https://www.psdevwiki.com/ps4/PKG_files#Files
    """
    id: Optional[int] = None
    filename_offset: Optional[int] = None
    filename: Optional[str] = ''
    flags1: Optional[int] = None
    flags2: Optional[int] = None
    offset: Optional[int] = None
    size: Optional[int] = None
    padding: Optional[int] = None

    def set_from_bytes(self, b):
        """Set object attributes from a ReadableBuffer of bytes.

        The PKG file table is of a fixed size. This will read the supplied ReadableBuffer
        and assign the values to the appropriate attributes. This data is stored in the
        PKG file as big-endian.

        Attributes:
            b: A ReadableBuffer of bytes pre-positioned at the location of
               a PKG file table entry
        """

        self.id = read_uint32_be(b)
        self.filename_offset = read_uint32_be(b)
        self.flags1 = read_uint32_be(b)
        self.flags2 = read_uint32_be(b)
        self.offset = read_uint32_be(b)
        self.size = read_uint32_be(b)
        self.padding = read_uint64_be(b)
    
    def unpack_from_bytes(self, b):
        """Set object attributes from a ReadableBuffer of bytes.

        The PKG file table is of a fixed size. This will read the supplied ReadableBuffer
        and assign the values to the appropriate attributes.

        This is the same as set_from_bytes except this uses struct.unpack to read and assign
        the attributes.

        Attributes:
            b: A ReadableBuffer of bytes pre-positioned at the location of
               a PKG file table entry
        """

        format = '>IIIIIIQ'
        self.id, self.filename_offset, self.flags1, \
            self.flags2, self.offset, self.size, \
            self.padding = struct.unpack(format, b.read(struct.calcsize(format)))

@dataclass
class PKG:
    """PKG object.

    Create a `PKG` object to store a selection of the header entries from a `PKG`
    file. The `files` attribute stores a list of the files found within the `PKG` file.

    The `param` attribute stores metadata relating the the `PKG` contents, this is parsed
    from the `param.json` file which is usually included within an `_sc.pkg` or `_dp.pkg`
    file.

    For more information on the data structure see:

    https://www.psdevwiki.com/ps4/PKG_files#File_Header
    """

    offset: int
    url: Optional[ParseResult] = None
    magic: Optional[bytes] = b'\x7fCNT'
    file_count: Optional[int] = None
    entry_count: Optional[int] = None
    table_offset: Optional[int] = None
    body_offset: Optional[int] = None
    content_offset: Optional[int] = None
    filename_offset: Optional[int] = None
    filename_size: Optional[int] = None
    files: List[PKG_File] = field(default_factory=list)
    param: Optional[PKG_Param] = None
    _is_from_file: bool = False
    _file_path: str = None
   
    @classmethod
    def from_url(cls, url) -> 'PKG':
        """Creates an instance from a URL

        Partially downloads a pkg file from the URL to extract the metadata
        required to create PKG object.

        Attributes:
            url: URL to an '_sc' or '_dp' pkg file
        """
        url = urlparse(url)
        if url.scheme not in ('http', 'https'):
            raise ValueError('Url must be a http or https address')
        pkg = cls(offset=0)
        pkg.url = url
        with HTTPSocket.from_url(url=pkg.url) as s:
            pkg_data = s.initial_receive(magic=pkg.magic)
            if pkg.magic not in pkg_data[:len(pkg.magic)]:
                raise ValueError('Unable to download PKG')
            # Parse the PKG header
            with io.BytesIO(pkg_data) as b:
                pkg.set_from_bytes(b)

            # Download up to the end of the PKG files table
            pkg_table_end = pkg.table_offset + (pkg.file_count * 32)
            response = s.receive(buffer=4096, length=pkg_table_end - len(pkg_data))
            pkg_data = pkg_data + response

            # Parse the PKG files table
            with io.BytesIO(pkg_data) as b:
                pkg.set_pkg_files(b)

            # Download up to the end of the PKG filenames file
            pkg_filename_end = pkg.filename_offset + pkg.filename_size
            if len(pkg_data) < pkg_filename_end:
                response = s.receive(buffer=4096, length=pkg_filename_end - len(pkg_data))
                pkg_data = pkg_data + response
            with io.BytesIO(pkg_data) as b:
                pkg.set_pkg_file_names(b)

            # Download param.json
            param_file = next((x for x in pkg.files if x.id == 8192), None)
            if param_file is None:
                logger.warning(f'This PKG does not have a param.json file')
            if param_file is not None:
                param_end = param_file.offset + param_file.size
                if len(pkg_data) < param_end:
                    response = s.receive(buffer=16384, length=param_end - len(pkg_data))
                    pkg_data = pkg_data + response
                param_json_bytes = pkg_data[param_file.offset:param_file.offset + param_file.size]
                pkg.param = PKG_Param.from_bytes(param_bytes=param_json_bytes)

            logger.debug(f'{pkg._bytes_to_formatted_filesize(len(pkg_data))} was downloaded to create the PKG object')
        return pkg

    @classmethod
    def from_file(cls, path) -> 'PKG':
        """Creates an instance from a file path

        Attributes:
            path: Path to an '_sc' or '_dp' pkg file
        """
        with open(path, 'rb') as f:
            pkg = cls(offset=0)
            pkg._is_from_file = True
            pkg._file_path = path
            pkg.set_from_bytes(f)
            pkg.set_pkg_files(f)
            pkg.set_pkg_file_names(f)
            # Extract param.json file
            param_file = next((x for x in pkg.files if x.id == 8192), None)
            if param_file is None:
                logger.warning(f'This PKG does not have a param.json file')
            if param_file is not None:
                f.seek(pkg.offset + param_file.offset)
                pkg.param = PKG_Param.from_bytes(f.read(param_file.size))
        return pkg

    def print_files(self):
        for f in self.files:
            print(f'{f.id}: {f.filename}')
    
    def save_files(self, files: list=[], save_method: Callable[..., None]=lambda x: logger.error('Save method not implemented')
                   , **kwargs):
        """Extract one or more PKG_File and save it to the file system

        Select a PKG_File based on its id and save it to the file system.

        If the PKG file was created from a URL then the file will be partially downloaded
        up to the location of the files specified for saving.

        You must provide your own function to implement `save_method`. The bytes for
        the file to be saved will be supplied as a parameter to your function along
        with a `filename` parameter. Any other parameters supplied after `save_method`
        will also also be passed to your own function.

        Attributes:
            files: A list of PKG_File ids or 'all' to save all files in self.files
            save_method: A user-supplied function which implements the saving
        """
        # Sort the file list based on their offset so that they can be accessed in
        # the sequence order based on their location in the pkg file
        # In-place sort
        # self.files.sort(key=lambda obj: obj.offset)
        pkg_files: List[PKG_File] = sorted(self.files, key=lambda obj: obj.offset)

        try:
            if self._is_from_file:
                file = open(self._file_path, 'rb')
            else:
                sock = HTTPSocket.from_url(url=self.url)
                sock.connect()
                data = sock.initial_receive(magic=self.magic)
                
            for f in pkg_files:
                if f.id in files or files[0] == 'all':
                    logger.debug(f'Saving file {f.id} ({self._bytes_to_formatted_filesize(f.size)}) located {self._bytes_to_formatted_filesize(f.offset)} into the file')
                    if f.filename != '':
                        kwargs['filename'] = f.filename.replace('/','_')
                    else:
                        kwargs['filename'] = str(f.id)
                    if self._is_from_file:
                        file.seek(self.offset + f.offset)
                        save_method(file.read(f.size), **kwargs)
                    else:
                        if len(data) < f.offset + f.size:
                            # More data must be downloaded
                            response = sock.receive(buffer=4194304, length=(f.offset + f.size) - len(data))
                            data = data + response
                        save_method(data[f.offset:f.offset + f.size], **kwargs)
        finally:
            if self._is_from_file:
                file.close()
            else:
                sock.close()

    def set_from_bytes(self, b: io.BufferedReader):
        """Set object attributes from a ReadableBuffer of bytes.

        The PKG file header entries are at fixed locations offset from the start of the file.
        This will read the supplied ReadableBuffer and assign the values of interest to
        the appropriate attributes. This data is stored in the PKG file as big-endian.

        Attributes:
            b: A ReadableBuffer of bytes pre-positioned at the location of
               a PKG file
        """

        self.magic = b.read(4)
        if self.magic != b'\x7fCNT':
            logging.error(f'The supplied ReadableBuffer is not a PKG file')
            self.magic = None
            return
        b.seek(0x10)
        self.file_count = read_uint32_be(b)
        b.seek(0x18)
        self.table_offset = read_uint32_be(b)
        b.seek(0x20)
        self.body_offset = read_uint64_be(b)
        b.seek(0x30)
        self.content_offset = read_uint64_be(b)

    def set_pkg_files(self, b: io.BufferedReader, offset = 0):
        """
        Parses the files within the `PKG` into individual `PKG_File` objects.

        Appends them to the `files` attribute.
        """
        b.seek(self.table_offset + offset)
        for i in range(self.file_count):
            file = PKG_File()
            file.unpack_from_bytes(b)
            if file.id == 512:
                logger.debug(f'PKG filename table exists at: {file.offset}')
                self.filename_offset = file.offset
                self.filename_size = file.size
            self.files.append(file)

    def set_pkg_file_names(self, b: io.BufferedReader, offset = 0):
        """
        Reads the filename table and adds the file name to each `PKG_File` object.
        """
        if self.filename_offset is not None:
            for f in self.files:
                b.seek(self.filename_offset + f.filename_offset + offset)
                while True:
                    data = b.read(1)
                    if data == b'\x00': # NULL terminated strings
                        break
                    else:
                        f.filename += data.decode()

    def _bytes_to_formatted_filesize(self, size_in_bytes):
        """Format bytes to file size string (MB/GB)

        Converts file size in bytes to a formatted string in either MiB or GiB.

        Attributes:
            size_in_bytes: Size as bytes for conversion
        """
        # 1 GiB == 1073741824 bytes
        if size_in_bytes > 1073741824:
            return f'{round(size_in_bytes / 1048576 / 1024, 2)} GiB'
        return f'{round(size_in_bytes / 1048576, 2)} MiB'
        
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    print('https://github.com/andshrew/PS5-Updates-Python')