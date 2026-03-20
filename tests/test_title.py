import logging
import pytest

from ps5_updates import title as ps5up

def test_create_update_object():
    update = ps5up.Ps5TitleUpdate(
        title_id='PPSA07811_00',
        update_url='https://sgst.prod.dl.playstation.net/sgst/prod/00/np/PPSA07811_00/1e18836b-ede1-42c2-8b4e-38866c0ff030-version.xml'
    )
    assert update.__class__ is ps5up.Ps5TitleUpdate

def test_create_update_object_failure():
    with pytest.raises(ValueError):
        update = ps5up.Ps5TitleUpdate(
            title_id='PPSA07810_00',
            update_url='https://sgst.prod.dl.playstation.net/sgst/prod/00/np/PPSA07811_00/1e18836b-ede1-42c2-8b4e-38866c0ff030-version.xml'
        )

def test_save_data():
    update = ps5up.Ps5TitleUpdate(
        title_id='PPSA07811_00',
        update_url='https://sgst.prod.dl.playstation.net/sgst/prod/00/np/PPSA07811_00/1e18836b-ede1-42c2-8b4e-38866c0ff030-version.xml'
    )
    update.save_update_info()

def test_update_object():
    update = ps5up.Ps5TitleUpdate(
        title_id='PPSA07811_00',
        update_url='https://sgst.prod.dl.playstation.net/sgst/prod/00/np/PPSA07811_00/1e18836b-ede1-42c2-8b4e-38866c0ff030-version.xml'
    )
    update.get_update()
    update.save_update_info()
    print('hello')

def test_update_object_non_english():
    update = ps5up.Ps5TitleUpdate(
        title_id='PPSA19534_00',
        update_url='https://sgst.prod.dl.playstation.net/sgst/prod/00/np/PPSA19534_00/2c0cca31-5f7b-45ea-8a3f-51a686579c21-version.xml',
        ac=True,
        content_id='UP0006-PPSA19534_00-CONTENTPACK00001'
    )
    update.get_update()
    update.save_update_info()
    print('hello')

def test_update_with_ac():
    update = ps5up.Ps5TitleUpdate(
        title_id='PPSA08260_00',
        update_url='https://sgst.prod.dl.playstation.net/sgst/prod/00/np/PPSA08260_00/faa39e63-4d80-4062-85ac-5966114ac1e6-version.xml'
    )
    update.get_update()
    ac = ps5up.Ps5AdditionalContentUpdate()
    print('hello')

def test_update_additional_content():
    update = ps5up.Ps5TitleUpdate(
        title_id='PPSA08260_00',
        update_url='https://sgst.prod.dl.playstation.net/sgst/prod/00/np/PPSA08260_00/faa39e63-4d80-4062-85ac-5966114ac1e6-version.xml',
        ac=True,
        content_id='EP0001-PPSA08260_00-OUTLAWDLC1000000'
    )
    update.get_update()
    update.save_update_info()
    print('hello')

def test_update_additional_content_bad_content_id():
    update = ps5up.Ps5TitleUpdate(
        title_id='PPSA08260_00',
        update_url='https://sgst.prod.dl.playstation.net/sgst/prod/00/np/PPSA08260_00/faa39e63-4d80-4062-85ac-5966114ac1e6-version.xml',
        ac=True,
        content_id='EP0001-PPSA08260_00-BADLAWDLC1000000'
    )
    assert update.__class__ is ps5up.Ps5TitleUpdate
    assert update.is_ac == True
    assert update.update_exists == False
    update.get_update()

def test_update_cod():
    update = ps5up.Ps5TitleUpdate(
        title_id='PPSA07950_00',
        update_url='https://sgst.prod.dl.playstation.net/sgst/prod/00/np/PPSA07950_00/4c4d5312-e602-424b-baef-3e3a4bbfc48f-version.xml'
    )
    update.get_update(download_pkg=False)
    update._get_partial_pkg_file(additional_files=True, url="http://gst.prod.dl.playstation.net/gst/prod/00/PPSA07950_00/app/pkg/90/f_a972f1722489a67845d046ea5178f77b72dc7d6cf9c26e96c9d187c30a1ff1cc/EP0002-PPSA07950_00-COREGAME00000001-DP.pkg")
    print('hello')
    
logger = logging.getLogger(__name__)