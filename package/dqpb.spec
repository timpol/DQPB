"""
PyInstaller script for building the standalone DQPB application on macOS and
Windows.

Based on script by Marius Retegan of the European Synchrotron Radiation
Facility. See: https://github.com/mretegan/crispy/package

Mac: requires create-dmg to be installed and accessible from the terminal:
See: https://github.com/create-dmg/create-dmg

Win: requires inno setup to be installed and added to users PATH.

"""

import os
import logging
import sys
import subprocess

# from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# from DQPB import version
version = "0.1.1a"

logger = logging.getLogger("pyinstaller")

block_cipher = None
package_path = "../DQPB"

icon = None
# ----- Just use default icon for now... -------
# if sys.platform == "darwin":
#     icon = "DQPB.icns"
# elif sys.platform == "win32":
#     icon = "DQPB.ico"
# icon = os.path.join(os.getcwd(), icon)
# logger.info(icon)
# ----------------------------------------------

datas = [
    (os.path.join(package_path, "uis"), "uis"),
    # (os.path.join(package_path, "icons"), "icons"),
]

hiddenimports = []

# Needed to ensure savefigure command works properly on Windows.
hooksconfig = {
                  "matplotlib": {
                      "backends": ["Agg", "pdf", "pgf", "svg", "ps"],
                  },
              }

a = Analysis(
    [os.path.join(package_path, "__main__.py")],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig=hooksconfig,
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="DQPB",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    icon=icon,
)

# Remove the MKL libraries.
for binary in sorted(a.binaries):
    name, _, _ = binary
    for key in ("mkl",):
        if key in name:
            a.binaries.remove(binary)
            logger.info(f"Removed {name}.")

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="DQPB",
)

app = BUNDLE(
    coll,
    name="DQPB.app",
    icon=icon,
    bundle_identifier=None,
    info_plist={
        "CFBundleIdentifier": "com.github.timpol.DQPB",
        "CFBundleShortVersionString": version,
        "CFBundleVersion": "DQPB " + version,
        "LSTypeIsPackage": True,
        "LSMinimumSystemVersion": "10.13.0",
        "NSHumanReadableCopyright": "MIT",
        "NSHighResolutionCapable": True,
        "NSPrincipalClass": "NSApplication",
        "NSAppleScriptEnabled": False,
    },
)

# Post build actions.
if sys.platform == "darwin":
    # Remove the signature from the Python interpreter.
    # see https://github.com/pyinstaller/pyinstaller/issues/5062.
    subprocess.call(
        [
            "codesign",
            "--remove-signature",
            os.path.join("dist", "DQPB.app", "Contents", "MacOS", "Python"),
        ]
    )

    # Remove the extended attributes from the MacOS application as this causes
    # the application to fail to launch ("is damaged and can’t be opened. You
    # should move it to the Trash").
    subprocess.call(["xattr", "-cr", os.path.join("dist", "DQPB.app")])

    # Pack the application using create-dmg.
    # see: https://github.com/create-dmg/create-dmg
    subprocess.call(["bash", "create-dmg.sh"])

    # Rename the created .dmg image.
    os.rename(
        os.path.join("artifacts", "DQPB.dmg"),
        os.path.join("artifacts", f"DQPB-{version}-macOS.dmg"),
    )

elif sys.platform == "win32":

    # Create the Inno Setup script.
    root = os.path.join(os.getcwd(), "assets")
    name = "create-installer.iss"
    template = open(name + ".template").read()
    template = template.replace("#Version", version)
    with open(os.path.join(name), "w") as f:
        f.write(template)

    # Run the Inno Setup compiler.
    subprocess.call(["iscc", name])

    # Remove the .iss file
    os.remove(name)

