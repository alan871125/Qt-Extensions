import logging
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QRectF, Signal
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QPaintEvent
from PySide6.QtCore import Property
from typing import Optional, override, TypedDict, Unpack, Sequence

logger = logging.getLogger(__name__)

QtArc = int  # PyQt uses integers for angles in 1/16th of a degree
class PieChartStyleDict(TypedDict, total=False):
    bar_width: int
    color_background: QColor
    start_arc: QtArc
    center_label: bool
    center_label_font: QFont
    center_label_color: QColor

class PieChartWidget(QWidget):
    """A custom QWidget that displays a differnt arcs based on the given proportions. 
    
    The z-order of the pie chart and the center label can be controlled by setting the constants PIE_CHART_Z_ORDER and CENTER_LABEL_Z_ORDER, lower numbers are drawn first.
    """
    DEFAULT_COLOR_BG = QColor("#e0e0e0")
    DEFAULT_FONT_COLOR = QColor("#333333")
    SEGMENT_COLORS = [
        "#FF8833", "#00BB33", "#3355FF", 
        "#FFAA00", "#8844AA", "#33AAAA",
        "#AA3333", "#FFEE00", "#DD33BB"
    ]  # Example colors for segments
    PIE_CHART_Z_ORDER = 0  # Z-order for the pie chart
    CENTER_LABEL_Z_ORDER = 1  # Z-order for the center label
    value_changed = Signal(int, int)  # Signal to emit when the value changes, start->end
    
    def __init__(
        self, num_segments:int, sum_proportion:Optional[float]=None, parent:Optional[QWidget]=None, style:Optional[PieChartStyleDict]=None,
    ):
        super().__init__(parent)
        assert num_segments > 0, "Number of segments must be greater than zero."
        self.values:list[float] = [0]*num_segments
        self._sum = sum_proportion
        self._style:PieChartStyleDict = {}
        self.set_style(**style or {})
        
    def set_style(self,**kwargs:Unpack[PieChartStyleDict]):
        """Set the style of the pie chart. Accepts any of the keys in PieChartStyleDict."""
        self._style.update(kwargs)
        self.update()  # Trigger a repaint
    
    def set_sum_proportion(self, sum_proportion:Optional[float]):
        """Set the total sum for the proportions. If None, the sum is dynamic based on the values."""
        self._sum = sum_proportion
        self.update()  # Trigger a repaint

    @property
    def bar_width(self):
        return self._style.get('bar_width', 36)
    @property
    def color_background(self):
        return self._style.get('color_background', self.DEFAULT_COLOR_BG)
    @property
    def start_arc(self):
        return self._style.get('start_arc', 0)
    @property
    def center_label(self):
        return self._style.get('center_label', True)
    
    @Property(QColor)
    def center_label_color(self): # seems like pylance doesn't recognize this as a property
        return self._style.get('center_label_color', self.DEFAULT_FONT_COLOR)
    @center_label_color.setter
    def center_label_color(self, color:QColor):
        self._style['center_label_color'] = color
        self.update()  # Trigger a repaint
    
    def _paint_center_label(self):
        """Draw the center label of the pie chart."""
        if not self.center_label:
            return
        painter = QPainter(self)
        painter.setPen(self.center_label_color)
        painter.setFont(self.font())
        if self._sum is not None and self._sum > 0:
            text = f"{sum(self.values)/self._sum:.0%}"
        else:
            text = str(sum(self.values))
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, text)
        painter.end()
        
    def _paint_pie_chart(self):
        """Draw the main pie chart based on the current proportions."""
        w,h = self.width(), self.height()
        size = min(w,h)
        
        margin = self.bar_width / 2
        rect = QRectF(
            (w-size)/2 + margin,
            (h-size)/2 + margin,
            size - self.bar_width,
            size - self.bar_width
        )
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        pen_background = QPen(self.color_background, self.bar_width)
        pen_background.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen_background)
        painter.drawEllipse(rect)
        
        rect = QRectF(
                    (w-size)/2 + margin,
                    (h-size)/2 + margin,
                    size - self.bar_width,
                    size - self.bar_width
                )
        
        # Draw the arcs based on the proportions
        arc = self.start_arc*16
        for i, proportion in enumerate(self.proportions):
            pen_segment = QPen(QColor(self.SEGMENT_COLORS[i]), self.bar_width)
            pen_segment.setCapStyle(Qt.PenCapStyle.FlatCap)
            painter.setPen(pen_segment)
            # PyQt uses 1/16th of a degree
            if (span := proportion * 360 * 16) <= 0:  
                continue # skip segments with no proportion
            painter.drawArc(rect, int(arc), int(span))
            arc += span
        painter.end()
        
    @override
    def paintEvent(self, a0:Optional[QPaintEvent]=None):
        """Override the paint event to draw the pie chart and center label."""
        painter_funcs = {
            self.PIE_CHART_Z_ORDER: self._paint_pie_chart,
            self.CENTER_LABEL_Z_ORDER: self._paint_center_label
        }
        for z_order in sorted(painter_funcs.keys()):
            painter_funcs[z_order]()
    
    @property
    def proportions(self):
        _sum = self._sum if self._sum is not None else (sum(self.values))
        if _sum == 0:
            return [0] * len(self.values)  # Avoid division by zero; return equal proportions
        return [c / _sum for c in self.values]

    def set_values(self, values: Sequence[float|int]):
        if len(values) != len(self.values):
            raise ValueError("Number of values must match the number of segments.")
        if self._sum is not None and sum(values) > self._sum:
            raise ValueError(f"Sum of values {sum(values)} exceeds the total sum {self._sum}.")
        for i, v in enumerate(values):
            if v < 0:
                raise ValueError(f"Value at index {i} is negative: {v}. All values must be non-negative.")
            self.values[i] = v
        self.value_changed.emit(0, len(self.values)-1)  # Emit signal for each value change
        self.update()  # Trigger a repaint

    def set_value(self, index: int, value: float):
        if not 0 <= index < len(self.values):
            raise IndexError("Segment index out of range.")
        elif self.values[index] == value:
            return  # No change needed, prevent recursive updates
        if self._sum is None:
            self.values[index] = value
            self.value_changed.emit(index, index)
            self.update()
            return

        if value > self._sum:
            raise ValueError(f"Value {value} exceeds the total sum {self._sum}.")

        current_sum = sum(self.values)

        if current_sum - self.values[index] + value <= self._sum:
            self.values[index] = value
            self.value_changed.emit(index, index)
            self.value_changed.emit(index, index)
        else:
            remain = self._sum - value
            other_sum = sum(self.values)-self.values[index]
            if other_sum > 0:
                scale = remain / other_sum
                self.values[:] = [x * scale for x in self.values]
            else:
                self.values[:] = [0.0] * len(self.values)

            self.values[index] = value
            self.value_changed.emit(0, len(self.values)-1)  # Emit signal for all values changed
        self.update()

