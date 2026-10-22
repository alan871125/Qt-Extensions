"""Example usage of the TextEditLoggingHandler and HtmlFormatter"""
import logging
import sys
from PySide6.QtWidgets import QApplication, QVBoxLayout, QPushButton, QWidget
from qt_extensions.logging import TextEditLoggingHandler, HtmlFormatter
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
try:
    import colorlog
    handler = colorlog.StreamHandler()
    handler.setFormatter(
        colorlog.ColoredFormatter(
            "%(log_color)s[%(asctime)s][%(levelname).1s][%(name)s]%(reset)s %(message)s",
        )
    )
    logging.getLogger().addHandler(handler)
except ImportError:
    logger.warning("colorlog not installed, using default logging handler.")

app = QApplication(sys.argv)
window = QWidget()
layout = QVBoxLayout(window)

log_handler = TextEditLoggingHandler(window)
log_handler.setFormatter(
    HtmlFormatter(
        "%(log_color)s[%(asctime)s][%(levelname).1s][%(name)s]%(reset)s %(message)s",
        # theme = "darker"
    )
)
logging.getLogger().addHandler(log_handler)
logging.getLogger().setLevel(logging.DEBUG)

info = QPushButton("info")
info.clicked.connect(lambda: logger.info("Example info log message."))
debug = QPushButton("debug")
debug.clicked.connect(lambda: logger.debug("Example debug log message."))
error = QPushButton("error")
error.clicked.connect(lambda: logger.error("Example error log message."))
critical = QPushButton("critical")
critical.clicked.connect(lambda: logger.critical("Example critical log message."))

layout.addWidget(log_handler.widget)
layout.addWidget(info)
layout.addWidget(debug)
layout.addWidget(error)
layout.addWidget(critical)

window.show()
sys.exit(app.exec())