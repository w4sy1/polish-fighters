#!/usr/bin/env python3
"""Check produced APK contents; not a device/runtime test."""
import sys
from zipfile import ZipFile
required = {'assets/scripts/polish-fighters/package.manifest',
            'assets/scripts/polish-fighters/catalog.lua',
            'assets/scripts/polish-fighters/roster.lua',
            'assets/scripts/base/i18n/polish.lua',
            'lib/arm64-v8a/libmain.so'}
with ZipFile(sys.argv[1]) as apk:
    missing = required - set(apk.namelist())
    if missing: raise SystemExit('APK missing: ' + ', '.join(sorted(missing)))
    # Android binary XML stores string pools in UTF-8 or UTF-16.
    manifest = apk.read('AndroidManifest.xml')
    appid = 'pl.prestigetech.polishfighters'
    if appid.encode() not in manifest and appid.encode('utf-16-le') not in manifest:
        raise SystemExit('Wrong application ID in AndroidManifest.xml')
    if apk.testzip() is not None: raise SystemExit('Corrupt APK')
print('PASS: APK scripts, Polish locale, ARM64 library, application ID, ZIP CRC')
