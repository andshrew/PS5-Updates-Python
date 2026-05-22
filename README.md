# PS5 Title Update Information

This Python package retrieves information about updates available for a PS5 title. The information is stored in a `Ps5TitleUpdate` object which you can integrate into your application.  

A similar package for PS4 title updates is available here: https://github.com/andshrew/PS4-Updates-Python

## Installation
```
pip install ps5-updates
```

## Typical Usage
An example implementation is included in [`src/demo.py`](src/demo.py).  

Create a `Ps5TitleUpdate` object using the titles update XML URL or a the URL to a specific updates `_sc.pkg` file.  

Invoke `get_update()` on the object to download information about all currently available update packages. This will partially download the update `.pkg` file to extract
the `param.json` where metadata about the update is stored.  

The latest update is available as a `ContentPackage` object in the `latest` attribute. If the title has multiple updates currently available (ie. there is a pre-download for an upcoming update, or a pre-release update) then each individual update is available as a `ContentPackage` object in the `packages` attribute.  

Within the `ContentPackage` object, information about the update `.pkg` file is available as a `PKG` object on the `pkg` attribute.  

Within the `PKG` object the `param.json` data is available as a `PKG_Param` object. Any information from this file which is not specifically mapped to attributes on the object can be accessed by invoking `get_property('name')`.  

Titles can also include Additional Content (ie. DLC). If any Additional Content is available then it is available as an `AdditionalContent` object in the `additional_content` attribute of the `Ps5TitleUpdate` object. Accessing the update information then mirrors the above except it is accessed via the `AdditionalContent` objects `latest` or `packages` attributes.

## Limitations
This package is not intended for downloading entire PS5 title update files, although it can be used to download and save files from within an updates `_sc.pkg` file.  

Only information about the currently available update version can be retrieved. However if you have the URL for an specific updates `_sc.pkg` file then you can create a `PKG` object directly from that and parse some information about the update.  

Keep in mind when considering the attributes of a `PKG` (the features that it is flagged as supporting) that it does not necessarily mean that the game has a mode available which actually implements the feature. This is true at least for features like 120hz and PSSR; whereas other features like VRR, HDR, and Power Saver do always seem to be available whenever the `PKG` is flagged as supporting them.  

Unlike PS4 and earlier titles the update XML URLs are not predetermined. They can only be obtained from the `app_sc.pkg` file on a PS5 game disc, from the `entitlement.db` file on an exploitable console, or from the `_sc.pkg` of an already known update.

## Usage Examples

An example implementation is included in [`src/demo.py`](src/demo.py).

### Create `Ps5TitleUpdate` object and retrieve latest update information
```python
from ps5_updates import title as ps5up

url = 'https://sgst.prod.dl.playstation.net/sgst/prod/00/np/PPSA07632_00/53d40bc7-7b1a-403c-8260-4b293b1711fd-version.xml'
title = ps5up.Ps5TitleUpdate.from_url(url)
title.get_update()
print(f'Title Id:       {title.title_id}')
print(f'Content Id:     {title.content_id}')
print(f'Name:           {title.latest.pkg.param.name}')
print(f'Version:        {title.latest.version}')
print(f'Creation Date:  {title.latest.pkg.param.creation_date}')
print(f'System Version: {title.latest.system_version}')
print(f'Size:           {title.latest.update_size}')
```

#### Console Output
```
Title Id:       PPSA07632_00
Content Id:     UP9000-PPSA07632_00-SAROS00000000000
Name:           SAROS
Version:        01.004.003
Creation Date:  2026-05-14 00:37:26
System Version: 13.20.00.06
Size:           78.27 GiB
```

### Create a `PKG` object and retrieve information about a specific update
```python
from ps5_updates import pkg as ps5pkg

url = 'https://sgst.prod.dl.playstation.net/sgst/prod/00/PPSA18654_00/app/info/95/f_23e129465f761a049d5477f4f4ec67db738a31927e981faa7ffb5b7eec9cb4c5/UP6312-PPSA18654_00-0220083948426038_sc.pkg'
pkg = ps5pkg.PKG.from_url(url)
print(f'Title Id:       {pkg.param.title_id}')
print(f'Content Id:     {pkg.param.content_id}')
print(f'Name:           {pkg.param.name}')
print(f'Version:        {pkg.param.content_version}')
print(f'Creation Date:  {pkg.param.creation_date}')
print(f'System Version: {pkg.param.required_system_version}')
print(f'Update URL:     {pkg.param.version_url}')
```

#### Console Output
```
Title Id:       PPSA18654
Content Id:     UP6312-PPSA18654_00-0220083948426038
Name:           Age of Empires II: Definitive Edition
Version:        01.029.000
Creation Date:  2026-04-24 19:24:29
System Version: 13.00.00.00
Update URL:     https://sgst.prod.dl.playstation.net/sgst/prod/00/np/PPSA18654_00/935e23b3-169e-439b-99d8-ae2b8b534b37-version.xml
```

## Development

_All commands after step 1 should be run from the root of the git repo_  

**1. Clone the repo**
```
git clone git@github.com:andshrew/PS5-Updates-Python.git
```
**2. Create and load a virtual python environment**
```
python -m venv .venv
source .venv/bin/activate
```
**3. Install the package in editable mode**
```
pip install -e ".[test]"
```
**4. Build the package**
```
pip install build
python -m build
```

## Additional Thanks
[psdevwiki](https://www.psdevwiki.com/ps4) - documentation on [PKG file format](https://www.psdevwiki.com/ps4/PKG_files) and [param.json files](https://www.psdevwiki.com/ps5/Param.json)