# thumbnailpanel.py
import os
import wx
from wx.svg import SVGimage
from thumbnailbutton import ThumbnailButton

class ThumbnailPanel(wx.Panel):
    """
    Bottom thumbnail strip with left/right buttons and a scrollable area.
    Thumbnails are loaded lazily when requested by add_or_update_thumbnail().
    """

    def __init__(self, parent, on_thumbnail_selected, thumb_size=(50, 50)):
        super().__init__(parent, size=(-1, thumb_size[1] + 10))

        self.on_thumbnail_selected = on_thumbnail_selected
        self.thumb_size = thumb_size
        self.thumbs = {}           # path -> wx.Bitmap
        self.buttons = {}          # path -> ThumbnailButton
        self.selected_path = None
        self.file_list = []        # List of file paths in order

        self._create_ui()

    def _create_ui(self):
        hbox = wx.BoxSizer(wx.HORIZONTAL)

        self.btn_left = wx.Button(self, label="  <  ", style=wx.BU_EXACTFIT)
        self.btn_right = wx.Button(self, label="  >  ", style=wx.BU_EXACTFIT)

        # Scrollable area for thumbnails
        self.scroll = wx.ScrolledWindow(self, style=wx.HSCROLL | wx.BORDER_SIMPLE | wx.ALWAYS_SHOW_SB)
        self.scroll.SetMinClientSize((-1, self.thumb_size[1] + 8))
        self.scroll.SetScrollRate(10, 0)
        self.thumb_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.scroll.SetSizer(self.thumb_sizer)

        hbox.Add(self.btn_left, 0, wx.EXPAND | wx.RIGHT, 5)
        hbox.Add(self.scroll, 1)
        hbox.Add(self.btn_right, 0, wx.EXPAND | wx.LEFT, 5)

        self.SetSizer(hbox)
        hbox.SetSizeHints(self)

        # Bind navigation buttons
        self.btn_left.Bind(wx.EVT_BUTTON, self.on_left_click)
        self.btn_right.Bind(wx.EVT_BUTTON, self.on_right_click)
        
        # Bind keyboard events for navigation - only on the scroll window
        self.scroll.Bind(wx.EVT_KEY_DOWN, self.on_key_down)

    # ------------------------------------------------------------------
    # Thumbnail management
    # ------------------------------------------------------------------
    def add_or_update_thumbnail(self, path, load_bitmap=True):
        """
        Ensure a thumbnail exists for the given SVG path.
        If load_bitmap is True, load the bitmap immediately.
        If load_bitmap is False, create an empty button that can be filled later.
        """
        if path in self.buttons:
            return
        
        bmp = None
        if load_bitmap:
            bmp = self._create_thumbnail_bitmap(path)
        
        btn = ThumbnailButton(
            self.scroll,
            path=path,
            bitmap=bmp,
            on_click=self._handle_thumb_click,
            thumb_size=self.thumb_size,
        )

        self.thumb_sizer.Add(btn, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 2)
        self.buttons[path] = btn
        self.scroll.Layout()
        self.scroll.FitInside()

        # If there is already a selected path, update border state
        if path == self.selected_path:
            btn.set_selected(True)

    def load_thumbnail_bitmap(self, path):
        """Load the bitmap for an existing thumbnail button."""
        if path not in self.buttons:
            return
        
        bmp = self._create_thumbnail_bitmap(path)
        if bmp is not None:
            self.buttons[path].set_bitmap(bmp)

    def _create_thumbnail_bitmap(self, path):
        """Render a small thumbnail bitmap from an SVG file."""
        if SVGimage is None:
            return None

        try:
            svg = SVGimage.CreateFromFile(path)
        except Exception:
            return None

        try:
            bmp = svg.ConvertToScaledBitmap(self.thumb_size, self)
        except Exception:
            return None
        return bmp

    def set_selected_file(self, path):
        """Update which thumbnail is highlighted as selected."""
        if self.selected_path == path:
            return

        # Clear previous selection
        if self.selected_path in self.buttons:
            self.buttons[self.selected_path].set_selected(False)

        self.selected_path = path

        # Highlight new selection
        if path in self.buttons:
            btn = self.buttons[path]
            btn.set_selected(True)
            self._scroll_to_button(btn)

    def _scroll_to_button(self, btn):
        """Ensure the given button is centered in the scroll area when possible."""
        if self.selected_path not in self.file_list:
            return
            
        # Calculate the logical position of the selected button
        selected_index = self.file_list.index(self.selected_path)
        target_x = 0
        
        # Sum up the widths of all buttons before the selected one
        for i, path in enumerate(self.file_list[:selected_index]):
            if path in self.buttons:
                button = self.buttons[path]
                # Each button has size + margins (2 on each side = 4 total)
                target_x += button.GetSize().width + 4
        
        # Add half the width of the selected button to center it
        if self.selected_path in self.buttons:
            selected_button = self.buttons[self.selected_path]
            target_x += selected_button.GetSize().width // 2
        
        # Get the visible area width
        scroll_size = self.scroll.GetClientSize()
        scroll_width = scroll_size.width
        
        # Calculate the scroll position to center the button
        target_x = target_x - (scroll_width // 2)
        
        # Ensure we don't scroll beyond the left edge
        target_x = max(0, target_x)
        
        # Check if we're at the right edge - don't center if it would show empty space
        virtual_size = self.scroll.GetVirtualSize()
        total_width = virtual_size.width
        
        # If the target position would show empty space on the right, adjust
        if target_x + scroll_width > total_width:
            target_x = max(0, total_width - scroll_width)
        
        # Convert to scroll units (scroll rate is 10 pixels per unit)
        scroll_unit = target_x // 10
        self.scroll.Scroll(scroll_unit, 0)

    def _handle_thumb_click(self, path):
        if self.on_thumbnail_selected:
            self.on_thumbnail_selected(path)
        # Ensure the scroll window has focus for keyboard navigation
        self.scroll.SetFocus()

    def set_file_list(self, file_list):
        """Set the list of files for keyboard navigation."""
        self.file_list = file_list

    # ------------------------------------------------------------------
    # Navigation buttons
    # ------------------------------------------------------------------
    def on_left_click(self, event):
        if not self.file_list or self.selected_path not in self.file_list:
            # Fallback to just scrolling
            x, y = self.scroll.GetViewStart()
            self.scroll.Scroll(max(0, x - 10), y)
            return
            
        current_index = self.file_list.index(self.selected_path)
        if current_index > 0:
            next_path = self.file_list[current_index - 1]
            if self.on_thumbnail_selected:
                self.on_thumbnail_selected(next_path)

    def on_right_click(self, event):
        if not self.file_list or self.selected_path not in self.file_list:
            # Fallback to just scrolling
            x, y = self.scroll.GetViewStart()
            self.scroll.Scroll(x + 10, y)
            return
            
        current_index = self.file_list.index(self.selected_path)
        if current_index < len(self.file_list) - 1:
            next_path = self.file_list[current_index + 1]
            if self.on_thumbnail_selected:
                self.on_thumbnail_selected(next_path)

    def get_visible_thumbnail_indices(self):
        """Return the indices of thumbnails that are currently visible in the scroll area."""
        if not self.file_list:
            return []
        
        # Get scroll position in pixels
        scroll_x, _ = self.scroll.GetViewStart()
        scroll_pixel_x = scroll_x * 10  # Convert scroll units to pixels
        
        # Get visible width
        client_size = self.scroll.GetClientSize()
        visible_width = client_size.width
        
        visible_indices = []
        current_x = 0
        
        for i, path in enumerate(self.file_list):
            if path in self.buttons:
                button = self.buttons[path]
                button_width = button.GetSize().width + 4  # +4 for margins
                
                # Check if this button is at least partially visible
                if current_x + button_width > scroll_pixel_x and current_x < scroll_pixel_x + visible_width:
                    visible_indices.append(i)
                
                current_x += button_width
        
        return visible_indices

    def on_key_down(self, event):
        """Handle keyboard navigation."""
        key = event.GetKeyCode()
        
        if not self.file_list or self.selected_path not in self.file_list:
            event.Skip()
            return
            
        current_index = self.file_list.index(self.selected_path)
        
        if key == wx.WXK_LEFT:
            if current_index > 0:
                next_path = self.file_list[current_index - 1]
                if self.on_thumbnail_selected:
                    self.on_thumbnail_selected(next_path)
            # Do not call event.Skip() to prevent scrollbar from handling the event
        elif key == wx.WXK_RIGHT:
            if current_index < len(self.file_list) - 1:
                next_path = self.file_list[current_index + 1]
                if self.on_thumbnail_selected:
                    self.on_thumbnail_selected(next_path)
            # Do not call event.Skip() to prevent scrollbar from handling the event
        else:
            event.Skip()

