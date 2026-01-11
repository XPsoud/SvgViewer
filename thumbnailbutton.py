# thumbnailbutton.py
import wx

class ThumbnailButton(wx.Panel):
    """
    Custom control that displays a thumbnail bitmap with a selectable border.
    """

    def __init__(self, parent, path, bitmap, on_click, thumb_size=(50, 50)):
        super().__init__(parent, style=wx.BORDER_NONE)

        self.path = path
        self.bitmap = bitmap
        self.on_click = on_click
        self.is_selected = False
        self.thumb_size = thumb_size

        self.SetBackgroundColour(wx.Colour(220, 220, 220))

        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.Bind(wx.EVT_LEFT_DOWN, self.on_mouse_down)

        # Set size based on thumb_size
        self.SetMinSize((thumb_size[0] + 6, thumb_size[1] + 6))

    def set_selected(self, selected):
        self.is_selected = selected
        self.Refresh()

    def set_bitmap(self, bitmap):
        """Set or update the bitmap for this button."""
        self.bitmap = bitmap
        if bitmap is not None:
            self.SetMinSize((bitmap.GetWidth() + 6, bitmap.GetHeight() + 6))
        self.Refresh()

    def on_paint(self, event):
        dc = wx.PaintDC(self)
        dc.SetBackground(wx.Brush(self.GetBackgroundColour()))
        dc.Clear()

        w, h = self.GetClientSize()
        
        if self.bitmap is not None:
            bmp_w = self.bitmap.GetWidth()
            bmp_h = self.bitmap.GetHeight()

            x = (w - bmp_w) // 2
            y = (h - bmp_h) // 2

            dc.DrawBitmap(self.bitmap, x, y, True)
        else:
            # Draw placeholder when bitmap is not loaded yet
            dc.SetPen(wx.Pen(wx.Colour(150, 150, 150), 1))
            dc.SetBrush(wx.Brush(wx.Colour(200, 200, 200)))
            dc.DrawRectangle(3, 3, w - 6, h - 6)
            
            # Draw a simple placeholder icon or text
            dc.SetFont(wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
            dc.SetTextForeground(wx.Colour(100, 100, 100))
            dc.DrawText("SVG", (w - 20) // 2, (h - 12) // 2)

        # Draw selection frame
        if self.is_selected:
            dc.SetPen(wx.Pen(wx.Colour(0, 120, 215), 3))
        else:
            dc.SetPen(wx.Pen(wx.Colour(100, 100, 100), 1))

        dc.SetBrush(wx.TRANSPARENT_BRUSH)
        dc.DrawRectangle(1, 1, w - 2, h - 2)

    def on_mouse_down(self, event):
        if self.on_click:
            self.on_click(self.path)
