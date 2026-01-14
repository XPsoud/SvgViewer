import sys
import os
import shutil
import subprocess
import zipfile
from pathlib import Path
from cx_Freeze import setup, Executable
from sources import AppVersion


def create_package(withArchive = True):
    # Initialize variables
    appVers = AppVersion()
    sName = appVers.getAppName() + "-" + appVers.getVersion(False)
    archi = '64' if (sys.maxsize > 2**32) else '32'
    v = sys.version_info
    pyVersion = f"{v[0]}.{v[1]}.{v[2]}"
    pyVersFloat = float(f"{v[0]}.{v[1]}")
    print(f"Building package for {sName}-Win{archi}-Py{pyVersion}")

    myExcludes = [
        'asyncio', 'backports', 'cabarchive', 'filelock',
        'concurrent', 'ctypes', 'distutils', 'freeze_core',
        'html', 'http', 'jaraco', 'json', 'lief', 'logging',
        'packaging', 'pydoc_data',
        'setuptools', 'unittest', 'urllib', 'xml'
        ]
    myIncludes = [('./langs/fr/svgviewer.mo','langs/fr/svgviewer.mo')]

    build_exe_options = {
        "build_exe": "build/SvgViewer",
        'excludes': myExcludes,
        'include_files': myIncludes,
        "optimize": 2
    }

    exeName = appVers.getAppName()
    if sys.platform == "win32":
        exeName = exeName + ".exe"

    base = "gui"
    if sys.platform == "win32":
        if pyVersFloat <= 3.12:
            base = "Win32GUI"

    setup(  name = appVers.getAppName(),
            version = appVers.getVersion(False),
            description = appVers.getAppDescription(),
            options = {
                "build_exe": build_exe_options
            },
            executables = [Executable(
                script = "main.py",
                base = base,
                icon = 'graphx/svgviewer.ico',
                copyright = appVers.getCopyright(),
                target_name = exeName
                )])
    
    if withArchive is False:
        return

    # Try to find 7zip command line executable
    sevenZip = None
    systName = None
    if sys.platform == "linux":
        systName = f"Linux{archi}"
        # For Linux we search for "7za"
        sevenZip = shutil.which('7za')
    elif sys.platform == "win32":
        systName = f"Win{archi}"
        # First, search thru the PATH
        sevenZip = shutil.which('7z.exe')
        if sevenZip is None:
            # Try the standard installation folder
            sevenZip = Path(os.environ.get("ProgramFiles")) / '7-Zip' / '7z.exe'
            if not sevenZip.exists():
                sevenZip = None
    else:
        systName = f"UnknownOS{archi}"
        sevenZip = None

    archName = sName +"_Python-" + pyVersion + '_' + systName + ('.7z' if sevenZip is not None else '.zip')

    source_dir = Path(__file__).parent.parent / 'build' / 'SvgViewer'
    archive = source_dir.parent / archName
    if archive.is_file():
        archive.unlink()

    print(f"Creating archive {archName} from {source_dir}")
    if sevenZip:
        subprocess.run(
                [sevenZip, "a" ,"-t7z", '-mx9', '../' + archName, "."],
                cwd=source_dir,
                check=True
            )
    else:
        with zipfile.ZipFile('build/' + archName, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_path in source_dir.rglob('*'):
                    if file_path.is_file():
                        # arcname permet de garder la structure relative sans le dossier parent
                        zipf.write(file_path, arcname=file_path.relative_to(source_dir))
    