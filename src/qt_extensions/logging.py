import logging, html
from typing import Literal
from PySide6.QtWidgets import QPlainTextEdit, QWidget
from qt_extensions.core import TypedSignalWrapper

__all__ = ["THEME_DARKER", "THEME_DEFAULT", "TextLoggingHandler", "HtmlFormatter"]

THEME_DARKER = {
    "black":         "#3f4451",
    "blue":          "#4aa5f0",
    "brightBlack":   "#4f5666",
    "brightBlue":    "#4dc4ff",
    "brightCyan":    "#4cd1e0",
    "brightGreen":   "#a5e075",
    "brightMagenta": "#de73ff",
    "brightRed":     "#ff616e",
    "brightWhite":   "#e6e6e6",
    "brightYellow":  "#f0a45d",
    "cyan":          "#42b3c2",
    "green":         "#8cc265",
    "magenta":       "#c162de",
    "red":           "#e05561",
    "white":         "#d7dae0",
    "yellow":        "#d18f52",
}
THEME_DEFAULT = {
    "black":         "#000000",
    "blue":          "#0000ff",
    "brightBlack":   "#808080",
    "brightBlue":    "#8080ff",
    "brightCyan":    "#80ffff",
    "brightGreen":   "#80ff80",
    "brightMagenta": "#ff80ff",
    "brightRed":     "#ff8080",
    "brightWhite":   "#ffffff",
    "brightYellow":  "#ffff80",
    "cyan":          "#00ffff",
    "green":         "#00ff00",
    "magenta":       "#ff00ff",
    "red":           "#ff0000",
    "white":         "#f0f0f0",
    "yellow":        "#ffff00",
}

class TextLoggingHandler(logging.Handler):
    log_signal = TypedSignalWrapper(str)
    DEFAULT_FONT_FAMILY = "Consolas"
    DEFAULT_FONT_SIZE = 10
    def __init__(self, parent:QWidget|None = None):
        super().__init__()
        self.widget = QPlainTextEdit(parent)
        self.widget.setReadOnly(True)
        # use console-like font
        font = self.widget.font()
        # Consolas, 'Courier New', monospace
        font.setFamily(self.DEFAULT_FONT_FAMILY)
        font.setPointSize(self.DEFAULT_FONT_SIZE)
        font.setStyleHint(font.StyleHint.Monospace)
        font.setFixedPitch(True)
        self.widget.setFont(font)
        self.log_signal.connect(self.widget.appendHtml)
        
    def emit(self, record):
        msg = self.format(record)
        self.log_signal.emit(msg)

class HtmlFormatter(logging.Formatter):
    """Formats log records into HTML with colors based on log level.
    
    The default colors matches the defaults of colorlog
    """
    DEFAULT_COLORS = {
        logging.DEBUG:    "white",
        logging.INFO:     "green",
        logging.WARNING:  "yellow",
        logging.ERROR:    "red",
        logging.CRITICAL: "red",
    }
    DEFAULT_WEIGHTS = {
        logging.CRITICAL: "bold",
    }
    def __init__(
        self, fmt: str | None = None, datefmt: str | None = None, 
        colors:  dict[int, str] | None = None, 
        weights: dict[int, str] | None = None,
        theme:Literal["default", "darker"]|dict[str, str] = "default"
    ):
        super().__init__(fmt, datefmt)
        self.colors = colors or self.DEFAULT_COLORS
        self.weights = weights or self.DEFAULT_WEIGHTS
        match theme:
            case "default":
                _theme = THEME_DEFAULT
            case "darker":
                _theme = THEME_DARKER
            case dict():
                _theme = theme
            case _:
                _theme = {}
        if _theme:
            self.colors = {k: _theme.get(v, v) for k, v in self.colors.items()}

    def formatMessage(self, record: logging.LogRecord) -> str:
        org = record.message
        record.message = html.escape(record.message)
        try:
            return super().formatMessage(record)
        finally:
            record.message = org

    def formatException(self, ei) -> str:
        return html.escape(super().formatException(ei))

    def format(self, record: logging.LogRecord) -> str:
        color = self.colors.get(record.levelno, "#000000")
        weight = self.weights.get(record.levelno, "normal")
        record.log_color = f'<div style="color: {color}; font-weight: {weight};">'
        record.reset = '</div>'
        return super().format(record)

