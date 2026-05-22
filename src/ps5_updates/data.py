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
import socket
import ssl
from urllib.parse import urlparse, ParseResult
from dataclasses import dataclass
from typing import Optional, Union

@dataclass
class HTTPSocket:
    """A socket based HTTP downloader

    Intended for partially downloading a file from a web server using a
    manually created HTTP/1.1 request.

    Warning: HTTPS server validation is disabled to enable downloading
    from servers using certificates issued from non-public CAs.

    Attributes:
        port: Remote server port
        url: URL as a ParseResult of the file to download
        timeout: Socket timeout in seconds
    """
    port: int
    url: ParseResult
    timeout: Optional[int] = 60
    connection: Optional[socket.socket] = None
    no_more_data: Optional[bool] = False
    _is_connected: Optional[bool] = False

    def __post_init__(self):
        self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connection.settimeout(self.timeout)

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False      

    @classmethod
    def from_url(cls, url: Union[str, ParseResult], port: int=0, timeout: int=30) -> 'HTTPSocket':
        """Creates an instance from a URL

        Attributes:
            url: URL as a String or ParseResult of the file to download
            port: Specific remote server port
            timeout: Socket timeout in seconds
        """
        if isinstance(url, str):
            url = urlparse(url)
        if not isinstance(url, ParseResult):
            raise TypeError('Url should be of type ParseResult')
        if url.scheme != 'http' and url.scheme != 'https':
            raise ValueError('Url should be HTTP or HTTPS')
        if url.port is not None:
            port = url.port
        if url.port is None and port == 0:
            if url.scheme == 'http':
                port = 80
            if url.scheme == 'https':
                port = 443

        return cls(url=url, port=port, timeout=timeout)

    def connect(self):
        """Initiates connection to the remote server
        """
        if self._is_connected:
            logger.debug(f'This socket is already connected. Close the socket and create a new one ' +
                          f' before calling connect again')
            return
        self._is_connected = False

        try:
            self.connection.connect((self.url.hostname, self.port))
        except socket.timeout as ex:
            logger.error(f'Socket timeout connecting to: {self.url.hostname} port {self.port}')
            return
        
        if self.url.scheme == "https":
            # ssl.CERT_NONE will disable validating server cert (ie. no requirement for issuing CA to be in our trusted CAs)
            # When HTTPS is used by the update servers they are typically using certificates issued by an internal CA, so
            # this validation would fail.
            # Ref: https://docs.python.org/3/library/ssl.html
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            try:
                self.connection = context.wrap_socket(self.connection, server_hostname=self.url.hostname)
            except Exception as ex:
                logger.error(f'Socket error {self.url.hostname} port {self.port}: {ex.args}')
                self._is_connected = False
                return
        self._is_connected = True

    def close(self):
        """Closes the socket
        
        If a new socket is to subsequently be opened using this object then first create a
        new socket by calling _recreate_socket
        """
        if self._is_connected:
            try:
                self.connection.close()
            except Exception as ex:
                logger.error(f'Error when closing socket: {self.url.hostname} port {self.port}: {ex.args}')
            self._is_connected = False

    def initial_receive(self, magic: bytes, byte_limit: int=16384, redirect_count: int=0,
            redirect_limit: int=5) -> 'bytes':
        """Starts downloading a file

        Creates the initial HTTP request and handles CDN-type redirects
        If magic bytes are found in the response the response bytes are returned aligned to the
        location of the magic (ie. the initial response is discarded)

        Attributes:
        magic: Bytes of the files 'magic' signature
        byte_limit: Maximum number of bytes that will be downloaded for finding the files signature
        redirect_limit: If the connection is redirected to another server this is the maximum number of times it will be followed
        """
        url = self.url
        request = f'GET {url.path} HTTP/1.1\r\nHost:{url.hostname}\r\nConnection: close\r\n\r\n'
        self.connection.send(request.encode())

        received_data = b''
        while len(received_data) < byte_limit:
            response = self.receive(4096)
            if magic in response:
                break
            if magic not in response:
                # Sometimes downloads are redirected to a specific CDN URL
                if any(s in response[0:100].decode() for s in ('302 Moved Temporarily', '302 Found') ):
                    logger.debug(f'302 redirect response received, current redirect count: {redirect_count}')
                    if redirect_count > redirect_limit:
                        self.close()
                        logger.error(f'Too many 302 redirect responses have been received, aborting')
                        break
                    # Parse the responses HTTP headers to find the redirect location
                    response_headers = response.decode().splitlines()
                    for i, header in enumerate(response_headers):
                        if "Location: " in header:
                            redirect_url = urlparse(header.replace("Location: ", ""))
                            logger.debug(f'Trying again with URL: {redirect_url.geturl()}')
                            # Close and recreate the socket, and then call
                            # this method agian using the redirected URL
                            self.close()
                            redirect_count = redirect_count + 1
                            self.url = redirect_url
                            # Validate if the port has changed
                            if redirect_url.port is None:
                                if url.scheme == 'http':
                                    self.port = 80
                                if url.scheme == 'https':
                                    self.port = 443
                            else:
                                # New URL is using a non-standard port
                                self.port = url.port
                            self._recreate_socket()
                            self.connect()
                            return self.initial_receive(magic=magic, byte_limit=byte_limit,
                                        redirect_count=redirect_count, redirect_limit=redirect_limit)
            if self.no_more_data:
                break

        if magic not in response:
            # File signaure not found within receive byte limit
            logger.error(f'File magic NOT found and the byte limit {byte_limit} has been reached - actual bytes downloaded {len(response)}')
            response = b''
            self.connection.close()

        if magic in response:
            # File signaure has been found
            # Discard bytes prior to the location of the magic
            magic_offset = response.find(magic)
            response = response[magic_offset:]

        return response

    def receive(self, buffer: int=4096, length: int=0) -> 'bytes':
        """Requests bytes from the remote server

        Attributes:
        buffer: The number of bytes to receive in each request
        length: The maximum number of bytes to receive
        """
        received_data = b''
        if length == 0:
            length = buffer
        if length < buffer:
            buffer = length
        if self.no_more_data is False:
            while len(received_data) <= length:
                response = self.connection.recv(buffer)
                if len(response) == 0:
                    # No more data received in the request
                    self.no_more_data = True
                    break
                received_data = received_data + response
        return received_data

    def _recreate_socket(self):
        """
        Internal function for recreating the underlying socket
        """
        self.close()
        self.no_more_data = False
        self._is_connected = False
        self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connection.settimeout(self.timeout)

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    print('https://github.com/andshrew/PS5-Updates-Python')