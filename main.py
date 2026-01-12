# main.py
import wx
from sources import SVGViewerFrame


def main():
    app = wx.App(False)
    frame = SVGViewerFrame(None, title="SVG Viewer")
    frame.Show()
    app.MainLoop()


if __name__ == "__main__":
    main()
