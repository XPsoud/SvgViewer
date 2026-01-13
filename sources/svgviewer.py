# svgviewer.py
import os
import threading
import wx
import wx.adv
from wx.svg import SVGimage

from sources import SVGCanvas, ThumbnailPanel, AppVersion
from graphx import mainSvgFiles

_ = wx.GetTranslation

class FileDropHandler(wx.FileDropTarget):
    """
    File and folder drag-and-drop handler.
    Calls a callback on the frame with the dropped paths.
    """

    def __init__(self, on_drop_callback):
        super().__init__()
        self.on_drop_callback = on_drop_callback

    def OnDropFiles(self, x, y, filenames):
        self.on_drop_callback(filenames)
        return True


class SVGViewerFrame(wx.Frame):
    """
    Main application window.
    - Contains the SVG viewing canvas (center).
    - Contains the thumbnail strip (bottom).
    - Provides menus, status bar, and drag & drop support.
    """

    def __init__(self, parent):
        self.version = AppVersion()
        super().__init__(parent, title=self.version.getMainWindowTitle(), size=(1000, 700))

        img = SVGimage.CreateFromBytes(mainSvgFiles["svgviewer.svg"])
        self.SetIcon(wx.Icon(img.ConvertToScaledBitmap((32, 32))))

        # List of SVG file paths
        self.svg_files = []
        self.current_index = -1

        # Thread-related attributes
        self.thumb_loader_thread = None
        self._stop_loading = False

        self._create_ui()
        self._bind_events()

    # ------------------------------------------------------------------
    # UI creation
    # ------------------------------------------------------------------
    def _create_ui(self):
        self._create_menu_bar()
        self._create_status_bar()
        self._create_main_layout()
        self._setup_drag_and_drop()

    def _create_menu_bar(self):
        menubar = wx.MenuBar()

        file_menu = wx.Menu()
        open_item = file_menu.Append(wx.ID_OPEN)
        open_folder_item = file_menu.Append(wx.ID_ANY, _("Open &Folder...\tCtrl+Shift+O"), _("Open all SVG files in a folder"))
        file_menu.AppendSeparator()
        exit_item = file_menu.Append(wx.ID_EXIT)

        menubar.Append(file_menu, wx.GetStockLabel(wx.ID_FILE))

        help_menu = wx.Menu()
        about_item = help_menu.Append(wx.ID_ABOUT)
        
        menubar.Append(help_menu, wx.GetStockLabel(wx.ID_HELP))

        self.SetMenuBar(menubar)

        self.Bind(wx.EVT_MENU, self.on_open_files, open_item)
        self.Bind(wx.EVT_MENU, self.on_open_folder, open_folder_item)
        self.Bind(wx.EVT_MENU, self.on_exit, exit_item)
        self.Bind(wx.EVT_MENU, self.on_about, about_item)

    def _create_status_bar(self):
        # Use 2 fields: [0] generic info, [1] loading/progress
        self.status_bar = self.CreateStatusBar(2)
        self.status_bar.SetStatusWidths([-2, -1])
        self.status_bar.SetStatusText(_("Ready"), 0)
        self.status_bar.SetStatusText("", 1)

    def _create_main_layout(self):
        panel = wx.Panel(self)

        vbox = wx.BoxSizer(wx.VERTICAL)

        # Main SVG viewing canvas
        self.canvas = SVGCanvas(panel)
        vbox.Add(self.canvas, 1, wx.EXPAND | wx.ALL, 5)

        # Thumbnail panel at the bottom
        self.thumb_panel = ThumbnailPanel(panel, on_thumbnail_selected=self.on_thumbnail_selected)
        vbox.Add(self.thumb_panel, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)

        panel.SetSizer(vbox)

    def _setup_drag_and_drop(self):
        drop_target = FileDropHandler(self.on_files_dropped)
        self.SetDropTarget(drop_target)

    def _bind_events(self):
        self.Bind(wx.EVT_CLOSE, self.on_close)
        # Keyboard navigation at frame level
        self.Bind(wx.EVT_KEY_DOWN, self.on_key_down)
        # Ensure the frame can receive keyboard focus
        self.SetFocus()

    # ------------------------------------------------------------------
    # File management
    # ------------------------------------------------------------------
    def on_open_files(self, event):
        with wx.FileDialog(
            self,
            _("Open SVG files"),
            wildcard=_("SVG files (*.svg)|*.svg|All files (*.*)|*.*"),
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST | wx.FD_MULTIPLE,
        ) as dlg:
            if dlg.ShowModal() == wx.ID_CANCEL:
                return
            paths = dlg.GetPaths()
        self.add_svg_files(paths)

    def on_open_folder(self, event):
        with wx.DirDialog(self, _("Open folder with SVG files")) as dlg:
            if dlg.ShowModal() == wx.ID_CANCEL:
                return
            folder = dlg.GetPath()

        svg_files = []
        for name in os.listdir(folder):
            path = os.path.join(folder, name)
            if os.path.isfile(path) and name.lower().endswith(".svg"):
                svg_files.append(path)

        self.add_svg_files(svg_files)

    def on_files_dropped(self, paths):
        svg_files = []
        for path in paths:
            if os.path.isdir(path):
                for name in os.listdir(path):
                    full = os.path.join(path, name)
                    if os.path.isfile(full) and name.lower().endswith(".svg"):
                        svg_files.append(full)
            elif os.path.isfile(path) and path.lower().endswith(".svg"):
                svg_files.append(path)

        self.add_svg_files(svg_files)

    def add_svg_files(self, paths):
        # Filter new files only
        new_paths = [p for p in paths if p not in self.svg_files]

        if not new_paths:
            return

        self.svg_files.extend(new_paths)
        # Start thumbnail loading in a background thread
        self.start_thumbnail_loading(new_paths)

        # Update thumbnail panel with the full file list
        self.thumb_panel.set_file_list(self.svg_files)

        # If nothing was selected before, select first added
        if self.current_index < 0 and self.svg_files:
            self.set_current_index(0)

    # ------------------------------------------------------------------
    # Thumbnail loading in a background thread
    # ------------------------------------------------------------------
    def start_thumbnail_loading(self, new_paths):
        if self.thumb_loader_thread and self.thumb_loader_thread.is_alive():
            # Optionally, we could queue the new paths; for now just continue
            pass

        self._stop_loading = False

        def worker(paths):
            total = len(paths)
            
            # Phase 1: Create all thumbnail buttons (without bitmaps)
            for path in paths:
                if self._stop_loading:
                    break
                wx.CallAfter(self.thumb_panel.add_or_update_thumbnail, path, False)
            
            # Force layout update
            wx.CallAfter(self.thumb_panel.scroll.Layout)
            wx.CallAfter(self.thumb_panel.scroll.FitInside)
            
            # Phase 2: Load thumbnails around current selection first
            current_index = getattr(self, 'current_index', 0)
            priority_paths = []
            
            # Load thumbnails around current selection (5 before, 5 after)
            start_idx = max(0, current_index - 5)
            end_idx = min(len(paths), current_index + 6)
            priority_paths = paths[start_idx:end_idx]
            
            for i, path in enumerate(priority_paths, start=1):
                if self._stop_loading:
                    break
                wx.CallAfter(
                    self.status_bar.SetStatusText,
                    _("Loading priority thumbnails:") + f" {i}/{len(priority_paths)}",
                    1,
                )
                wx.CallAfter(self.thumb_panel.load_thumbnail_bitmap, path)
            
            # Phase 3: Load remaining thumbnails
            remaining_paths = [p for p in paths if p not in priority_paths]
            
            for i, path in enumerate(remaining_paths, start=1):
                if self._stop_loading:
                    break
                wx.CallAfter(
                    self.status_bar.SetStatusText,
                    _("Loading remaining thumbnails:") + f" {i}/{len(remaining_paths)}",
                    1,
                )
                wx.CallAfter(self.thumb_panel.load_thumbnail_bitmap, path)
            
            wx.CallAfter(self.status_bar.SetStatusText, "", 1)

        self.thumb_loader_thread = threading.Thread(target=worker, args=(new_paths,))
        self.thumb_loader_thread.daemon = True
        self.thumb_loader_thread.start()

    # ------------------------------------------------------------------
    # Selection, navigation, display
    # ------------------------------------------------------------------
    def set_current_index(self, index):
        if not self.svg_files:
            # No files: show app title and default image
            self.current_index = -1
            self.SetTitle(self.version.getMainWindowTitle())
            self.status_bar.SetStatusText("", 0)
            self.canvas.clear()
            return

        index = max(0, min(index, len(self.svg_files) - 1))
        if index == self.current_index:
            return

        self.current_index = index
        current_path = self.svg_files[self.current_index]

        # Update window title and status bar
        self.SetTitle(self.version.getMainWindowTitle() + f" - {os.path.basename(current_path)}")
        self.status_bar.SetStatusText(current_path, 0)

        # Update canvas
        self.canvas.load_svg(current_path)

        # Update thumbnail selection highlight
        self.thumb_panel.set_selected_file(current_path)

    def on_thumbnail_selected(self, filename):
        if filename in self.svg_files:
            index = self.svg_files.index(filename)
            self.set_current_index(index)

    # ------------------------------------------------------------------
    # Keyboard navigation
    # ------------------------------------------------------------------
    def on_key_down(self, event):
        key = event.GetKeyCode()
        if not self.svg_files:
            event.Skip()
            return

        if key == wx.WXK_LEFT:
            self.set_current_index(self.current_index - 1)
        elif key == wx.WXK_RIGHT:
            self.set_current_index(self.current_index + 1)
        elif key == wx.WXK_HOME:
            self.set_current_index(0)
        elif key == wx.WXK_END:
            self.set_current_index(len(self.svg_files) - 1)
        else:
            event.Skip()

    # ------------------------------------------------------------------
    # App lifecycle
    # ------------------------------------------------------------------
    def on_exit(self, event):
        self.Close()

    def on_close(self, event):
        # Stop thumbnail loading thread if running
        self._stop_loading = True
        event.Skip()

    def on_about(self, event):
        info = wx.adv.AboutDialogInfo()
        v = AppVersion()
        info.SetName(v.getAppName())
        info.SetVersion(v.getVersion(True))
        info.SetDescription(v.getAppDescription())
        info.SetCopyright(v.getCopyright())
        img = SVGimage.CreateFromBytes(mainSvgFiles["svgviewer.svg"])
        info.SetIcon(wx.Icon(img.ConvertToScaledBitmap((128, 128))))

        wx.adv.AboutBox(info)