import wx
from graphx import mainSvgFiles

_ = wx.GetTranslation

class AppVersion():
    def __init__(self):
        self.Major = 1
        self.Minor = 0
        self.Revision = 0
        self.Build = 60112

    def getVersion(self, full=False):
        sVers = str(self.Major) + "." + str(self.Minor) + '.' + str(self.Revision)
        if full is True:
            sVers += "." + str(self.Build)

        return sVers

    def getCopyright(self):
        sYear = " 202" + str(self.Build)[:1]
        return _("Copyright (c) X.P.") + sYear

    def getAppName(self):
        return "SVGViewer"

    def getAppDescription(self):
        return _("Simple SVG images viewer")

    def getMainWindowTitle(self):
        return self.getAppName() + " (v" + self.getVersion(False) + ") by X@v'"
