# main.py
import sys
import wx
from sources import SVGViewerApp, AppVersion

def main():
    app = SVGViewerApp()
    app.MainLoop()

def show_version():
    app_version = AppVersion()
    print(f"{app_version.getAppName()} (v{app_version.getVersion(full=True)}) : {app_version.getCopyright()}")
    print(f"{app_version.getAppDescription()}")

def do_build():
    from tools import create_windows_package
    create_windows_package()

def usage():
    print("Usage: python main.py [options]")
    print("Options:")
    print("  -h, --help     Show this help message and exit")
    print("  -v, --version  Show application version and exit")
    print("      --svg2py   Embed SVG files into Python code")
    print("      --build    Create a Ms Windows executable package")
    print("If no options are provided, the application will start normally.")

if __name__ == "__main__":
    args = sys.argv[1:]
    isDev = getattr(sys, "frozen", False) is False

    if args and isDev:
        if args[0] in ("--help", "-h", "/?"):
            usage()
        elif args[0] in ("--version", "-v", "/v"):
            show_version()
        elif args[0] == "--svg2py":
            from tools import embed_svg_files
            embed_svg_files()
        elif args[0] == "--build":
            sys.argv[1] = "build"
            do_build()
        else:
            usage()
    else:
        main()
