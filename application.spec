# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['src/main.py'],
    pathex=['src'],
    binaries=[],
    datas=[
        ('resources', 'resources'),
        ('src/plugins/filters/Gauss.py', 'plugins/filters/'),
        ('src/plugins/speed_models/NaismithHiking1892.py', 'plugins/speed_models/'),
        ('src/plugins/speed_models/BasicRoadCycling.py', 'plugins/speed_models/'),
        ('src/plugins/exporters/GPX.py', 'plugins/exporters/'),
        ('src/plugins/exporters/YAML.py', 'plugins/exporters/'),
    ],
    hiddenimports=[
        'garmin_fit_sdk',
    ],
    hookspath=[],
    hooksconfig={
        'matplotlib': {
            'backends': ['QtAgg'],
        }
    },
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='GPX Track Planner',
    debug=False,
    strip=False,
    upx=False,
    console=False,
    icon='resources/icon.png',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name='GPX Track Planner',
)

app = BUNDLE(
    coll,
    name='GPX Track Planner.app',
    icon='resources/icon.png',
    bundle_identifier='com.moelter.gpx-track-planner',
)
