# Qt-Extensions

A lightweight collection of utility extensions, type-safe signals, and custom widgets for **PySide6**.

---

## Features
`core.signal`:
- `TypedSignalWrapper`: A type-safe wrapper for Qt signals that allows attaching signals to non-QObject classes.
- `TypedSignal`: A type-hinted wrapper around `pyqtSignal` that provides full IDE autocompletion and static type checking (e.g. via Pylance / Mypy) for `.connect()` slots and `.emit()` arguments.

`widgets`:
- `PieChartWidget`: A customizable circular donut / pie chart widget supporting multiple segments, configurable styling, and real-time value updates. [(example)](examples/pie_chart_widget_example.py)

- `TextEditLoggingHandler`: A logging handler that outputs log messages to a `QPlainTextEdit` widget, with optional HTML formatting for colored log levels by using with `HtmlFormatter`. [(example)](examples/logging_example.py)
---

## Requirements

- Python 3.10+
- `PySide6`
- `typing_extensions`

---

## Quick Start

### 1. Type-Safe Signals

Use `TypedSignal` to get type checking on signal emissions and slot connections:

```python
from PySide6.QtWidgets import QWidget
from qt_extentions.core import TypedSignal

class WorkerWidget(QWidget):
    # Specify the argument types accepted by the signal
    progress_updated = TypedSignal(int, str)

    def do_work(self):
        # IDE / static type checkers will enforce (int, str)
        self.progress_updated.emit(50, "Processing...")

def on_progress(percent: int, status: str):
    print(f"{percent}%: {status}")

widget = WorkerWidget()
widget.progress_updated.connect(on_progress)
widget.do_work()
```

### 2. Multi-Segment Pie Chart Widget

`PieChartWidget` provides a clean donut chart for displaying proportional data:

```python
import sys
from PySide6.QtWidgets import QApplication, QVBoxLayout, QWidget
from qt_extentions.widgets import PieChartWidget

app = QApplication(sys.argv)
window = QWidget()
layout = QVBoxLayout(window)

# Create a 3-segment pie chart
chart = PieChartWidget(num_segments=3, sum_proportion=100)
chart.set_style(bar_width=28, center_label=True)
chart.set_values([30, 50, 20])

layout.addWidget(chart)
window.resize(300, 300)
window.show()

sys.exit(app.exec_())
```

---

## Examples

To run the interactive pie chart demo:

```bash
python examples/pie_chart_widget_example.py
```
Interactive logging demo with colored log levels:
```bash
python examples/logging_example.py
```