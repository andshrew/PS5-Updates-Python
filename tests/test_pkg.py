import logging
import pytest

#from ps5_updates import title as ps5up
from ps5_updates.pkg import *

def test_pkg():

    with open("test_dp.pkg", "rb") as f:
        pkg = PKG(offset = 0)
        pkg.set_from_bytes(f)

        f.seek(pkg.table_offset)
        for i in range(pkg.file_count):
            file = PKG_File()
            file.unpack_from_bytes(f)
            if file.id == 512: # Filename Table
                pkg.filename_offset = file.offset
            if file.filename_offset != 0 and pkg.filename_offset > 0:
                # File has a name and the Filename Table has been discovered
                current_seek = f.tell()
                f.seek(pkg.filename_offset + file.filename_offset)
                while True:
                    data = f.read(1)
                    if data == b'\x00': # NULL terminated strings
                        break
                    else:
                        file.filename += data.decode()
                f.seek(current_seek)
            pkg.files.append(file)
        
        print("henlo")

def test_pkg2():

    with open("test_sc.pkg", "rb") as f:
        pkg = PKG(offset = 0)
        pkg.set_from_bytes(f)
        pkg.set_pkg_files(f)
        print('henlo')
    
    
        