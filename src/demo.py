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

import argparse
import json
import textwrap
import sys
import urllib3
from ps5_updates import title as ps5up

GITHUB_URL = 'https://github.com/andshrew/PS5-Updates-Python'

class TermANSIFormat:
    bold = '\x1b[1m'
    underline = '\x1b[4m'
    blink = '\x1b[5m'
    reverse = '\x1b[7m'
    reset = '\x1b[0m'

def get_update(url: str, from_pkg: bool=False, save_files=False, save_automatic=False):
    if from_pkg:
        update = ps5up.Ps5TitleUpdate.from_pkg_url(url)
    else:
        update = ps5up.Ps5TitleUpdate.from_url(url)
    
    if not update._is_parsed:
        print(f'Unable to parse update information from: {url}')
        return
    update.latest.get_package()

    fmt = TermANSIFormat()
    print(f'{fmt.bold}Title Id:{fmt.reset}    {update.title_id}')
    print(f'{fmt.bold}Content Id:{fmt.reset}  {update.content_id}')
    print(f'{fmt.bold}Name:{fmt.reset}        {update.latest.pkg.param.name}')
    print(f'{fmt.bold}URL:{fmt.reset}         {update.update_url}')
    print(f'{fmt.bold}Import Date:{fmt.reset} {update.import_date}')
    print(f'')
    print_update(update.latest)
    if save_files:
        if save_pkg_files(pkg=update.latest.pkg, automatic=save_automatic):
            save_metadata(update=update, content=update.latest, pkg=update.latest.pkg)

    for package in update.packages[1:]:
        package.get_package()
        print_update(package)
        if save_files:
            if save_pkg_files(package.pkg, automatic=save_automatic):
                save_metadata(update=update, content=package, pkg=package.pkg)
    
    if len(update.additional_content) > 0:
        response = input(f'This title has {len(update.additional_content)} additional content packs. '
                         'Download update information? Y/N : ')
        print('')
        if response.lower() == 'y':
            for ac in update.additional_content:
                ac.latest.get_package()
                print(f'{fmt.bold}Content Id:{fmt.reset}  {ac.content_id}')
                print(f'{fmt.bold}Name:{fmt.reset}        {ac.latest.pkg.param.name}')
                print(f'{fmt.bold}Import Date:{fmt.reset} {ac.import_date}')
                print(f'')
                for package in ac.packages:
                    package.get_package()
                    print_update(package, skip_features=True)
                    if save_files:
                        if save_pkg_files(package.pkg, automatic=save_automatic):
                            save_metadata(update=update, content=package, pkg=package.pkg)

def print_update(update: ps5up.ContentPackage, skip_features: bool = False):
    fmt = TermANSIFormat()
    print(f'  {fmt.bold}Version:{fmt.reset}        {update.version}')
    if update.selective and len(update.distro_entitlements) > 0:
        print(f'  {fmt.underline}{fmt.bold}This is a pre-release update only available for accounts with the following entitlements:{fmt.reset}')
        print(f'    {" ".join(update.distro_entitlements)}')
    if update.selective and update.distro_predownload_install_date is not None:
        print(f'  {fmt.underline}{fmt.bold}This is a pre-download update which will be installable: {str(update.distro_predownload_install_date)}{fmt.reset}')
    print(f'  {fmt.bold}Creation Date:{fmt.reset}  {update.pkg.param.creation_date}')
    print(f'  {fmt.bold}System Version:{fmt.reset} {update.system_version}')
    print(f'  {fmt.bold}Size:{fmt.reset}           {update.update_size}')
    if not skip_features:
        print(f'  {fmt.bold}Features supported:{fmt.reset}')
        print(f'    {fmt.bold}HDR:{fmt.reset}          {update.pkg.param.supports_hdr}')
        print(f'    {fmt.bold}120hz:{fmt.reset}        {update.pkg.param.supports_hfr}')
        if update.pkg.param.supports_vrr_disabled:
            print(f'    {fmt.bold}VRR:{fmt.reset}          Force Disabled')
        elif update.pkg.param.supports_vrr_hfr:
            print(f'    {fmt.bold}VRR:{fmt.reset}          True + 120hz VRR mode')
        else:
            print(f'    {fmt.bold}VRR:{fmt.reset}          {update.pkg.param.supports_vrr}')
        print(f'    {fmt.bold}Power Saver:{fmt.reset}  {update.pkg.param.supports_power_saver}')
        if update.pkg.param.supports_psvr2_required:
            print(f'    {fmt.bold}PSVR2:{fmt.reset}        Required')
        else:
            print(f'    {fmt.bold}PSVR2:{fmt.reset}        {update.pkg.param.supports_psvr2_optional}')
        print(f'    {fmt.bold}PS5 Pro:{fmt.reset}      {update.pkg.param.supports_ps5_pro}')
        if update.pkg.param.pssr_version is not None:
            print(f'    {fmt.bold}PSSR Version:{fmt.reset} {update.pkg.param.pssr_version}')
        print(f'  {fmt.bold}Attribute bits:{fmt.reset}')
        for i in range(1,5):
            if i == 1:
                var_name = 'attribute_set_bits'
            else:
                var_name = f'attribute{i}_set_bits'
            if len(getattr(update.pkg.param, var_name)) > 0:
                print(f'    {fmt.bold}{i}{fmt.reset}: {getattr(update.pkg.param, var_name)}')
    print(f'')

def get_specifc_update(url: str, save_files=False, save_automatic=False):
    pkg = ps5up.PKG.from_url(url)

    fmt = TermANSIFormat()
    print(f'{fmt.bold}Title Id:{fmt.reset}    {pkg.param.title_id}')
    print(f'{fmt.bold}Content Id:{fmt.reset}  {pkg.param.content_id}')
    print(f'{fmt.bold}Name:{fmt.reset}        {pkg.param.name}')
    print(f'{fmt.bold}URL:{fmt.reset}         {pkg.param.version_url}')
    print(f'')

    print(f'  {fmt.bold}Version:{fmt.reset}        {pkg.param.content_version}')
    print(f'  {fmt.bold}Creation Date:{fmt.reset}  {pkg.param.creation_date}')
    print(f'  {fmt.bold}System Version:{fmt.reset} {pkg.param.required_system_version}')
    print(f'  {fmt.bold}Features supported:{fmt.reset}')
    print(f'    {fmt.bold}HDR:{fmt.reset}          {pkg.param.supports_hdr}')
    print(f'    {fmt.bold}120hz:{fmt.reset}        {pkg.param.supports_hfr}')
    if pkg.param.supports_vrr_disabled:
        print(f'    {fmt.bold}VRR:{fmt.reset}          Force Disabled')
    elif pkg.param.supports_vrr_hfr:
        print(f'    {fmt.bold}VRR:{fmt.reset}          True + 120hz VRR mode')
    else:
        print(f'    {fmt.bold}VRR:{fmt.reset}          {pkg.param.supports_vrr}')
    print(f'    {fmt.bold}Power Saver:{fmt.reset}  {pkg.param.supports_power_saver}')
    if pkg.param.supports_psvr2_required:
        print(f'    {fmt.bold}PSVR2:{fmt.reset}        Required')
    else:
        print(f'    {fmt.bold}PSVR2:{fmt.reset}        {pkg.param.supports_psvr2_optional}')
    print(f'    {fmt.bold}PS5 Pro:{fmt.reset}      {pkg.param.supports_ps5_pro}')
    if pkg.param.pssr_version is not None:
        print(f'    {fmt.bold}PSSR Version:{fmt.reset} {pkg.param.pssr_version}')
    print(f'  {fmt.bold}Attribute bits:{fmt.reset}')
    for i in range(1,5):
        if i == 1:
            var_name = 'attribute_set_bits'
        else:
            var_name = f'attribute{i}_set_bits'
        if len(getattr(pkg.param, var_name)) > 0:
            print(f'    {fmt.bold}{i}{fmt.reset}: {getattr(pkg.param, var_name)}')
    print(f'')
    if save_files:
        if save_pkg_files(pkg=pkg, automatic=save_automatic):
            save_metadata(pkg=pkg)

def save_pkg_files(pkg: ps5up.PKG, automatic: bool = False) -> bool:
    save = True
    file_count = pkg.file_count
    file_size = 0
    for file in pkg.files:
        file_size = file_size + file.size
    file_size = ps5up.bytes_to_formatted_filesize(file_size)
    if not automatic:    
        response = input(f'Save {file_count} files from within this update PKG? ({file_size}) Y/N : ')
        if response.lower() != 'y':
            save = False
    else:
        print(f'Saving {file_count} files from within the update PKG ({file_size})...')
    print('')
    if save:
        pkg.save_files(files=['all'], save_method=ps5up.save_data_to_file, titleid=pkg.param.title_id,
                    content_id=pkg.param.content_id, version=pkg.param.content_version, write_bytes=True,
                    base_path='saved_update_files')
        return True
    return False

def save_metadata(pkg: ps5up.PKG, update: ps5up.Ps5TitleUpdate = None, content: ps5up.ContentPackage = None):
    title_id = pkg.param.title_id
    content_id = pkg.param.content_id
    version = pkg.param.content_version
    name = pkg.param.name
    metadata = {
        'titleId': title_id,
        'contentId': content_id,
        'name': name,
        'version': version
    }
    if update.__class__ == ps5up.Ps5TitleUpdate:
        metadata['update_url'] = update.update_url
        ps5up.save_data_to_file(update.update_xml, titleid=title_id, content_id=content_id, version=version,
                                url=update.update_url, base_path='saved_update_files')
    if metadata.get('update_url') is None:
        metadata['update_url'] = pkg.param.version_url

    if content.__class__ == ps5up.ContentPackage:
        metadata['manifest_url'] = content.manifest_url
        ps5up.save_data_to_file(content.manifest_json, titleid=title_id, content_id=content_id, version=version,
                                url=content.manifest_url, base_path='saved_update_files')
    if metadata.get('manifest_url') is None:
        if pkg.url.geturl()[-7:].lower() == '_sc.pkg':
            metadata['manifest_url'] = pkg.url.geturl().replace('_sc.pkg', '.json')
        
    metadata['pkg_sc_url'] = pkg.url.geturl()
    ps5up.save_data_to_file(json.dumps(metadata, indent=2), titleid=title_id, content_id=content_id, version=version,
                            filename='update_metadata.json', base_path='saved_update_files')


if __name__ == "__main__":
    release_version = None
    args_parser = argparse.ArgumentParser(description='Simple PS5 Title Update Checker', usage='demo.py -u URL',
                                          epilog=GITHUB_URL)
    args_parser.formatter_class = argparse.RawDescriptionHelpFormatter
    args_parser.description = textwrap.dedent(f"""\
            A simple PS5 title update checker using
            the ps5-updates Python module {release_version or ''}
            -------------------------------------------------------
        """)
    interactive_group = args_parser.add_argument_group('Interactive Commands')
    interactive_group.description = "Display the latest update details for a PS5 title"
    interactive_group.add_argument("-u", "--url", action='store', type=str, help='an update XML URL or "_sc.pkg" URL', required=False)
    interactive_group.add_argument("-s", "--specific", action='store_true', help='display specific update information when an "_sc.pkg" URL is used', required=False)
    interactive_group.add_argument("--save", action='store_true', help='prompt to save files within the update PKG to ./saved_update_files/', required=False)
    interactive_group.add_argument("-a", "--auto", action='store_true', help='save files without prompting. Requires --save', required=False)
    args_parser.add_argument_group(interactive_group)
    args = args_parser.parse_args()

    if args.url:
        # PS5 title update XML files are hosted on a server using certificates
        # issued from an internal Sony CA. This disables warnings that we
        # aren't validating the server certificates when making HTTPS requests.
        urllib3.disable_warnings()

        if args.url[-4:].lower() == '.pkg':
            if args.specific:
                get_specifc_update(url=args.url, save_files=args.save, save_automatic=args.auto)
            else:
                get_update(url=args.url, from_pkg=True, save_files=args.save, save_automatic=args.auto)
        else:
            if args.specific:
                args_parser.error('--specific requires an "_sc.pkg" URL')
            get_update(args.url, save_files=args.save, save_automatic=args.auto)
        sys.exit()

    args_parser.print_help()
    sys.exit()
