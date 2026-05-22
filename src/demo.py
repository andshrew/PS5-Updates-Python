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
import textwrap
import sys
import urllib3
from ps5_updates import title as ps5up

GITHUB_URL = 'https://github.com/andshrew/PS5-Updates-Python'

def get_update(url: str, from_pkg: bool=False):
    # PS5 title update XML files are hosted on a server using certificates
    # issued from an internal Sony CA. This disables warnings that we
    # aren't validating the server certificates when making HTTPS requests.
    urllib3.disable_warnings()

    if from_pkg:
        update = ps5up.Ps5TitleUpdate.from_pkg_url(url)
    else:
        update = ps5up.Ps5TitleUpdate.from_url(url)
    
    if not update._is_parsed:
        print(f'Unable to parse update information from: {url}')
        return
    update.latest.get_package()

    print(f'Title Id:    {update.title_id}')
    print(f'Content Id:  {update.content_id}')
    print(f'Name:        {update.latest.pkg.param.name}')
    print(f'URL:         {update.update_url}')
    print(f'Import Date: {update.import_date}')
    print(f'')
    print_update(update.latest)

    for package in update.packages[1:]:
        package.get_package()
        print_update(package)
    
    if len(update.additional_content) > 0:
        response = input(f'This title has {len(update.additional_content)} additional content packs. '
                         'Download update information? Y/N : ')
        print('')
        if response.lower() == 'y':
            for ac in update.additional_content:
                ac.latest.get_package()
                print(f'Content Id:  {ac.content_id}')
                print(f'Name:        {ac.latest.pkg.param.name}')
                print(f'Import Date: {ac.import_date}')
                print(f'')
                print_update(ac.latest, skip_features=True)
            for package in update.packages[1:]:
                package.get_package()
                print_update(package, skip_features=True)

def print_update(update: ps5up.ContentPackage, skip_features: bool = False):
    print(f'Version:        {update.version}')
    print(f'Creation Date:  {update.pkg.param.creation_date}')
    print(f'System Version: {update.system_version}')
    print(f'Size:           {update.update_size}')
    if update.selective and len(update.distro_entitlements) > 0:
        print('This is a pre-release update only available for accounts with the following entitlements:')
        print(f'  {" ".join(update.distro_entitlements)}')
    if update.selective and update.distro_predownload_install_date is not None:
        print(f'This is a pre-download update which will be installable: {str(update.distro_predownload_install_date)}')
    if not skip_features:
        print(f'Features supported:')
        print(f'  HDR:          {update.pkg.param.supports_hdr}')
        print(f'  120hz:        {update.pkg.param.supports_hfr}')
        if update.pkg.param.supports_vrr_disabled:
            print(f'  VRR:          Force Disabled')
        elif update.pkg.param.supports_vrr_hfr:
            print(f'  VRR:          True + 120hz VRR mode')
        else:
            print(f'  VRR:          {update.pkg.param.supports_vrr}')
        print(f'  Power Saver:  {update.pkg.param.supports_hfr}')
        if update.pkg.param.supports_psvr2_required:
            print(f'  PSVR2:        Required')
        else:
            print(f'  PSVR2:        {update.pkg.param.supports_psvr2_optional}')
        print(f'  PS5 Pro:      {update.pkg.param.supports_ps5_pro}')
        if update.pkg.param.pssr_version is not None:
            print(f'  PSSR Version: {update.pkg.param.pssr_version}')
        print(f'Attribute bits:')
        for i in range(1,4):
            if i == 1:
                var_name = 'attribute_set_bits'
            else:
                var_name = f'attribute{i}_set_bits'
            if len(getattr(update.pkg.param, var_name)) > 0:
                print(f'  {i}: {getattr(update.pkg.param, var_name)}')
    print(f'')

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
    args_parser.add_argument_group(interactive_group)
    args = args_parser.parse_args()

    if args.url:
        if args.url[-4:].lower() == '.pkg':
            get_update(url=args.url, from_pkg=True)
        else:
            get_update(args.url)
        sys.exit()

    args_parser.print_help()
    sys.exit()
