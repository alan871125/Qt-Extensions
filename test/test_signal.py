import pytest
import warnings
from typeguard import check_type
from qt_extensions.core.signal import TypedSignal, TypedSignalWrapper
from PySide6.QtCore import QObject

class TestTypedSignal:
    def test_signal_typing(self):
        class TestObject(QObject):
            signal = TypedSignal(int, str)
            signal2 = TypedSignal(int, dict, int|str)
            def __init__(self):
                super().__init__()
                self.signal.connect(self.handle_signal)
            def handle_signal(self, value: int, text: str):
                assert isinstance(value, int)
                assert isinstance(text, str)
        check_type(TestObject.signal, TypedSignal[int, str])
        check_type(TestObject.signal2, TypedSignal[int, dict, int|str])
        
    def test_optional_signal(self):
        class TestObject(QObject):
            signal = TypedSignal(int|None)
            def __init__(self):
                super().__init__()
                self.value = None
                self.signal.connect(self.handle_signal)
            def handle_signal(self, value: int|None):
                self.value = value
                assert isinstance(value, int) or value is None
                
        obj = TestObject()
        obj.signal.emit(42)
        assert obj.value == 42
        obj.signal.emit(None)
        assert obj.value is None
        
class TestTypedSignalWrapper:
    def test_wrapper_warning(self):
        class NormalObject:
            value = None
            signal = TypedSignalWrapper(int|None)
            signal2 = TypedSignalWrapper(int|None)
            def __init__(self):
                with pytest.warns():
                    self.signal.connect(self.handle_signal)
                with warnings.catch_warnings():
                    warnings.simplefilter("error")
                    self.signal2.connect(self.handle_signal, warn=False) # should not warn
            def handle_signal(self, value: int|None):
                ...
        obj = NormalObject()
        
    def test_wrapper_typing(self):
        class NormalObject:
            value = None
            signal = TypedSignalWrapper(int|None)
            def __init__(self):
                self.signal.connect(self.handle_signal, warn=False)
            def handle_signal(self, value: int|None):
                self.value = value
                assert isinstance(value, int) or value is None
                
        obj = NormalObject()
        obj.signal.emit(42)
        assert obj.value == 42
        obj.signal.emit(None)
        assert obj.value is None
        check_type(NormalObject.signal, TypedSignalWrapper[int|None])
        
    def test_wrapper_signal_to_QObject(self):
        class TestObject(QObject):
            def foo(self, value: str):
                assert isinstance(value, str)
        class NormalObject:
            signal = TypedSignalWrapper(str)
        qobj = TestObject()
        obj = NormalObject()
        obj.signal.connect(qobj.foo)
        obj.signal.emit("Hello")
