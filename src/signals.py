from PyQt6.QtCore import QObject, pyqtSignal

class ServerSignals(QObject):
    state_changed = pyqtSignal(str) # "recording", "transcribing", "idle", "error"
    amplitude_changed = pyqtSignal(float) # 0.0 to 1.0
    text_ready = pyqtSignal(str) # The transcribed text (optional usage)
    cancel_requested = pyqtSignal()
