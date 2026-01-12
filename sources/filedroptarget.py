import os
import wx

class FileDropTarget(wx.FileDropTarget):
    def __init__(self, window):
        super().__init__()
        self.window = window

    def OnDropFiles(self, x, y, filenames):
        if filenames:
            path = filenames[0]
            if os.path.isdir(path):
                self.window.load_directory(path)
                return True
        return False
