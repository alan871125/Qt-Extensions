import types
import typing
from typing_extensions import TypeForm
import functools
from PySide6.QtCore import QMetaObject, Qt, QObject, Signal, SignalInstance

__all__ = ["TypedSignal", "TypedSignalWrapper"]

P = typing.ParamSpec("P")
T1 = typing.TypeVar("T1")
T2 = typing.TypeVar("T2")
T3 = typing.TypeVar("T3")
T4 = typing.TypeVar("T4")
# You probably don't need more than 4 type variables for signals,
# Use a dataclass or any custom class to wrap multiple parameters for more complex signals if needed.
# T5 = TypeVar("T5")
# T6 = TypeVar("T6")

def _resolve_qt_type(t: typing.Any) -> type:
    """Map a typing construct to a real class Signal can accept."""
    if t is typing.Any:
        return object

    origin = typing.get_origin(t)

    if origin is typing.Literal:
        arg_types = {type(a) for a in typing.get_args(t)}
        return arg_types.pop() if len(arg_types) == 1 else object
    
    if origin in (typing.Union, types.UnionType):
        return object
    
    if origin is not None:  # list[int], dict[str, int], etc.
        return origin

    if isinstance(t, type):
        return t

    return object  # last-resort fallback

class TypedSignal(typing.Generic[P]):
    @typing.overload
    def __new__(cls) -> "TypedSignal[[]]": ...
    @typing.overload
    def __new__(cls, t1: TypeForm[T1] | typing.Any, /) -> "TypedSignal[[T1]]": ...
    @typing.overload
    def __new__(cls, t1: TypeForm[T1] | typing.Any, t2: TypeForm[T2] | typing.Any, /) -> "TypedSignal[[T1, T2]]": ...
    @typing.overload
    def __new__(cls, t1: TypeForm[T1] | typing.Any, t2: TypeForm[T2] | typing.Any, t3: TypeForm[T3] | typing.Any, /) -> "TypedSignal[[T1, T2, T3]]": ...
    @typing.overload
    def __new__(cls, t1: TypeForm[T1] | typing.Any, t2: TypeForm[T2] | typing.Any, t3: TypeForm[T3] | typing.Any, t4: TypeForm[T4] | typing.Any, /) -> "TypedSignal[[T1, T2, T3, T4]]": ...
    def __new__(cls, *types: typing.Any) -> typing.Any:
        return typing.cast("TypedSignal[typing.Any]", super().__new__(cls))
    def __init__(self, *types: typing.Any) -> None:
        # self._orig_types = types
        qt_types = tuple(_resolve_qt_type(t) for t in types)
        self._signal = Signal(*qt_types)

    @typing.overload
    def __get__(self, instance: None, owner: type) -> "TypedSignal[P]": ...
    @typing.overload
    def __get__(self, instance: object, owner: type) -> "_BoundTypedSignal[P]": ...
    def __get__(self, instance: object | None, owner: type) -> typing.Any:
        if instance is None:
            return self
        return _BoundTypedSignal(getattr(instance, self._attr_name))

    def __set_name__(self, owner: type, name: str) -> None:
        self._attr_name = f"_{name}_raw"
        setattr(owner, self._attr_name, self._signal)

class _BoundTypedSignal(typing.Generic[P]):
    def __init__(self, bound_signal: typing.Any) -> None:
        self._bound_signal = bound_signal

    def connect(self, slot: typing.Callable[P, typing.Any], /, type: Qt.ConnectionType = Qt.ConnectionType.AutoConnection) -> QMetaObject.Connection:
        return self._bound_signal.connect(slot, type)
        
    def disconnect(self, slot: typing.Callable[P, typing.Any]) -> None:
        self._bound_signal.disconnect(slot)

    # This will cause a silence bug where the signal doesn't emit on a zero-arg signal, due to argument‑count mismatch.
    # def emit(self, *args: P.args, **kwargs: P.kwargs) -> None:
    #     self._bound_signal.emit(*args, **kwargs)
    @property
    def emit(self) -> typing.Callable[P, None]:
        # Return the *real* BoundSignal.emit, not a wrapping function.
        # This preserves Qt's native signal-to-signal connection semantics
        # (correct arity trimming) when this is used as a connect() target.
        return typing.cast(typing.Callable[P, None], self._bound_signal.emit)

class _SignalEmitter(typing.Protocol[P]):
    signal: _BoundTypedSignal[P]
    def deleteLater(self) -> None: ...

@functools.lru_cache(maxsize=None)
def _emitter_class(types: tuple[type, ...]) -> typing.Callable[[], _SignalEmitter[...]]:
    name = "_Emitter" + "".join(t.__name__.capitalize() for t in types)
    cls = type(name, (QObject,), {"signal": TypedSignal(*types)})
    return typing.cast("typing.Callable[[], _SignalEmitter[...]]", cls)

class TypedSignalWrapper(typing.Generic[P]):
    """
    A Signal Wrapper that allows attatching a signal to Non-Qbject classes.
    
    **Warning:**
    A connection to a non-QObject slot may run in the emitting thread.
    If such a slot touches the GUI, it can crash due to thread-affinity issues.
    Prefer QObject slots for GUI updates.
    """
    
    @typing.overload
    def __new__(cls) -> "TypedSignalWrapper[[]]": ...
    @typing.overload
    def __new__(cls, t1: TypeForm[T1] | typing.Any, /) -> "TypedSignalWrapper[[T1]]": ...
    @typing.overload
    def __new__(cls, t1: TypeForm[T1] | typing.Any, t2: TypeForm[T2] | typing.Any, /) -> "TypedSignalWrapper[[T1, T2]]": ...
    @typing.overload
    def __new__(cls, t1: TypeForm[T1] | typing.Any, t2: TypeForm[T2] | typing.Any, t3: TypeForm[T3] | typing.Any, /) -> "TypedSignalWrapper[[T1, T2, T3]]": ...
    @typing.overload
    def __new__(cls, t1: TypeForm[T1] | typing.Any, t2: TypeForm[T2] | typing.Any, t3: TypeForm[T3] | typing.Any, t4: TypeForm[T4] | typing.Any, /) -> "TypedSignalWrapper[[T1, T2, T3, T4]]": ...
    def __new__(cls, *types: typing.Any) -> typing.Any:
        return super().__new__(cls)

    def __init__(self, *types: typing.Any) -> None:
        qt_types = tuple(_resolve_qt_type(t) for t in types)
        self._emitter: _SignalEmitter[P] = _emitter_class(qt_types)()

    def connect(self, slot: typing.Callable[P, typing.Any], type:Qt.ConnectionType=Qt.ConnectionType.AutoConnection,/,warn: bool = True) -> QMetaObject.Connection:
        """
        Connects the signal to a slot.

        Arguments:
            slot (typing.Callable[P, typing.Any]): The slot to connect to.
            type (Qt.ConnectionType): The type of connection.
            warn (bool): Whether to warn if the slot is not a QObject method. Turn False if you know what you're doing and want to avoid the warning.

        Returns:
            A connection object.
        """
        
        owner = getattr(slot, "__self__", None)
        if warn and not isinstance(owner, (QObject, SignalInstance)):
            import warnings
            warnings.warn(
                "Connecting a plain callable: it may run in the emitting thread. "
                "Prefer a QObject method for anything that touches the GUI.",
                stacklevel=2,
            )
        return self._emitter.signal.connect(slot, type)

    def disconnect(self, slot: typing.Callable[P, typing.Any]) -> None:
        self._emitter.signal.disconnect(slot) 
        
    @property
    def emit(self) -> typing.Callable[P, None]:
        # Still return the real bound emit at runtime (not a wrapper function).
        return self._emitter.signal.emit

if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton
    import sys
    class OtherWidget(QWidget):
        SignalType = TypedSignal[[int, str]]
        signal = TypedSignal(int, str)
    other_widget = OtherWidget()
    class MyWidget(QWidget):
        my_signal = TypedSignal(int, str)

        def __init__(self):
            super().__init__()
            self.my_signal.connect(self.handle_signal)
            # this should show warning in pylance if uncommented:
            # self.my_signal.connect(self.handle_signal_wrong)
            layout = QVBoxLayout()
            button = QPushButton("Emit Signal")
            button.clicked.connect(self.emit_signal)
            layout.addWidget(button)
            self.setLayout(layout)

        def emit_signal(self):
            self.my_signal.emit(42, "Hello")
        def handle_signal(self, number: int, text: str):
            print(f"Received signal with number: {number} and text: {text}")

        
        def handle_signal_wrong(self, number: str, text: int):
            ...
    app = QApplication(sys.argv)
    widget = MyWidget()
    widget.show()
    sys.exit(app.exec())
    
    