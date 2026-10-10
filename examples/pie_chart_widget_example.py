import sys
import logging
from qt_extensions.widgets import PieChartWidget
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QSlider

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class DemoWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Composition Circle Demo")
        self.circle = PieChartWidget(num_segments=3, sum_proportion=None)
        
        self.circle.setStyleSheet("""
            qproperty-center_label_color: #DD2222;
            font-weight: bold;
            font-size: 50pt;
            font-family: Arial;
        """)
        
        layout = QVBoxLayout()
        layout.addWidget(self.circle)
        self.setLayout(layout)
        
        # Example proportions
        proportions = [30, 50, 20]
        self.circle.set_values([30, 50, 20])
        
        self.sliders = []
        for i, p in enumerate(proportions):
            slider = QSlider(Qt.Orientation.Horizontal)
            slider.setRange(0, 100)
            slider.setValue(p)
            slider.valueChanged.connect(
                lambda v,i=i: self.circle.set_value(i, v)
            )
            self.sliders.append(slider)
            layout.addWidget(slider)
        self.circle.value_changed.connect(self.update_proportions)
            
    def update_proportions(self, start, end):
        for i in range(start, end+1):
            logger.debug(f"Slider {i} value updated to {self.circle.values[i]}")
            self.sliders[i].setValue(round(self.circle.values[i]))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DemoWindow()
    window.resize(400, 400)
    window.show()
    sys.exit(app.exec())