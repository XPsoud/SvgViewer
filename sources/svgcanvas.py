# svgcanvas.py
import wx

try:
    from wx.svg import SVGimage
except ImportError:
    SVGimage = None


class SVGCanvas(wx.Panel):
    """
    Canvas for displaying a single SVG.
    The SVG is rendered to a bitmap that fits the available space,
    with a visible background and border.
    """

    def __init__(self, parent, background_color=wx.Colour(200, 200, 200)):
        super().__init__(parent)

        self.background_color = background_color
        self.current_path = None
        self.current_bitmap = None

        self.SetBackgroundColour(self.background_color)

        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.Bind(wx.EVT_SIZE, self.on_resize)

        # Create a "checkerboard" brush for transparency indication
        cell_size = 15
        bmp = wx.Bitmap(2 * cell_size, 2 * cell_size)
        dc = wx.MemoryDC(bmp)
        light = wx.Colour(240, 240, 240)
        dark = wx.Colour(200, 200, 200)
        
        dc.SetBrush(wx.Brush(light))
        dc.SetPen(wx.TRANSPARENT_PEN)
        dc.DrawRectangle(0, 0, 2 * cell_size, 2 * cell_size)
        dc.SetBrush(wx.Brush(dark))
        dc.DrawRectangle(0, 0, cell_size, cell_size)
        dc.DrawRectangle(cell_size, cell_size, cell_size, cell_size)
        dc.SelectObject(wx.NullBitmap)
        self.checkerboard_brush = wx.Brush(bmp)

    def load_svg(self, path):
        """Load and render an SVG file into a bitmap suitable for display."""
        self.current_path = path
        self._render_svg_to_bitmap()
        self.Refresh()

    def _render_svg_to_bitmap(self):
        if SVGimage is None or not self.current_path:
            self.current_bitmap = None
            return

        try:
            svg = SVGimage.CreateFromFile(self.current_path)
        except Exception:
            self.current_bitmap = None
            return
        
        # Get the original SVG size
        svg_w = svg.width
        svg_h = svg.height
        
        if svg_w <= 0 or svg_h <= 0:
            self.current_bitmap = None
            return

        # Available drawing area inside the canvas
        client_w, client_h = self.GetClientSize()
        margin = 10
        avail_w = max(10, client_w - 2 * margin)
        avail_h = max(10, client_h - 2 * margin)

        # Compute scale factor to fit SVG inside available area
        scale_w = avail_w / svg_w if svg_w > 0 else 1
        scale_h = avail_h / svg_h if svg_h > 0 else 1
        scale = min(scale_w, scale_h)

        # Compute final bitmap size (keeping aspect ratio)
        bmp_w = int(svg_w * scale)
        bmp_h = int(svg_h * scale)

        self.current_bitmap = svg.ConvertToScaledBitmap((bmp_w, bmp_h), self)


    def on_paint(self, event):
        dc = wx.PaintDC(self)
        dc.SetBackground(wx.Brush(wx.Colour(240, 240, 240)))
        dc.Clear()

        width, height = self.GetClientSize()

        margin = 10
        rect = wx.Rect(margin, margin, width - 2 * margin, height - 2 * margin)
        

        if self.current_bitmap:
            bmp_w = self.current_bitmap.GetWidth()
            bmp_h = self.current_bitmap.GetHeight()
            # Center the bitmap inside the inner rectangle
            x = rect.x + (rect.width - bmp_w) // 2
            y = rect.y + (rect.height - bmp_h) // 2

            # Draw a thin border around the SVG area
            dc.SetPen(wx.Pen(wx.BLACK, 1))
            #dc.SetBrush(wx.Brush(wx.Colour(240, 240, 240)))
            dc.SetBrush(self.checkerboard_brush)
            dc.DrawRectangle(x-2, y-2, bmp_w+4, bmp_h+4)

            # Draw the SVG bitmap
            dc.DrawBitmap(self.current_bitmap, x, y, True)

    def on_resize(self, event):
        # Re-render the SVG to match new size
        if self.current_path:
            self._render_svg_to_bitmap()
        event.Skip()
        self.Refresh()
