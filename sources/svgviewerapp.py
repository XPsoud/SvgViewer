import sys
import wx
from sources import SVGViewerFrame

_ = wx.GetTranslation

class SVGViewerApp(wx.App):
    _locale = None
    _isDev = False

    def __init__(self):
        wx.App.__init__(self)
        self._isDev = getattr(sys, "frozen", False) is False
    
    def MyDarwinGetSystemLanguage():
        import locale
        loc, _ = locale.getlocale()
        language = wx.LANGUAGE_DEFAULT
        if loc is not None:
            info = wx.Locale.FindLanguageInfo(loc)
            language = info.Language
        return language if language is not None else wx.LANGUAGE_DEFAULT

    def OnInit(self):
        language = wx.LANGUAGE_DEFAULT
        if sys.platform == 'darwin':
            language = self.MyDarwinGetSystemLanguage()
        
        # Init locale if wanted (Shift key not pressed)
        if wx.GetKeyState(wx.WXK_SHIFT) is False:
            wx.Locale.AddCatalogLookupPathPrefix("./langs")
            self._locale = wx.Locale()
            if self._locale.Init(language):
                self._locale.AddCatalog("svgviewer")

        frame = SVGViewerFrame(None)
        self.SetTopWindow(frame)
        frame.Show()

        return True
    
    def OnExit(self):
        return wx.App.OnExit(self)
