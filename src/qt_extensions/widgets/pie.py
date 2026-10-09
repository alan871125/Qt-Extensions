import logging
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QRectF, Signal
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QPaintEvent
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
    """A custom QWidget that displays a differnt arcs based on the given proportions. """
    DEFAULT_COLOR_BG = QColor("#e0e0e0")
    DEFAULT_FONT = QFont("Arial", 12, QFont.Weight.Bold)
    DEFAULT_FONT_COLOR = QColor("#333333")
    SEGMENT_COLORS = [
        "#FF8833", "#00BB33", "#3355FF", 
        "#FFAA00", "#8844AA", "#33AAAA",
        "#AA3333", "#FFEE00", "#DD33BB"
    ]  # Example colors for segments
    
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
    @property
    def center_label_font(self):
        return self._style.get('center_label_font', self.DEFAULT_FONT)
    @property
    def center_label_color(self):
        return self._style.get('center_label_color', self.DEFAULT_FONT_COLOR)

    @override
    def paintEvent(self, a0:Optional[QPaintEvent]=None):
        w,h = self.width(), self.height()
        size = min(w,h)
        
        if self._style.get('center_label', True):
            # Draw the center label
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setPen(self.center_label_color)
            painter.setFont(self.center_label_font)
            if self._sum is not None and self._sum > 0:
                text = f"{sum(self.values)/self._sum:.0%}"
            else:
                text = str(sum(self.values))
            
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, text)
            painter.end()
        
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

