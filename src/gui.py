import sys
import time
import threading
import sounddevice as sd
from PyQt6.QtWidgets import (QApplication, QSystemTrayIcon, QMenu, QWidget, QVBoxLayout, 
                            QLabel, QComboBox, QPushButton, QRadioButton, QGroupBox, QHBoxLayout, QFrame,
                            QDialog, QProgressBar, QMessageBox, QCheckBox, QFileDialog, QLineEdit)
from PyQt6.QtGui import QIcon, QAction, QFont, QColor, QPalette
from PyQt6.QtCore import Qt, pyqtSignal, QObject, QTimer
from config_manager import settings
from input_simulator import simulate_ctrl_v


# --- Modern Dark StyleSheet ---
STYLESHEET = """
    QWidget {
        background-color: #2b2b2b;
        color: #ffffff;
        font-family: 'Segoe UI', 'Ubuntu', sans-serif;
        font-size: 14px;
    }
    QGroupBox {
        border: 1px solid #3d3d3d;
        border-radius: 6px;
        margin-top: 12px;
        font-weight: bold;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        left: 10px;
        padding: 0 5px;
        color: #aaaaaa;
    }
    QPushButton {
        background-color: #007acc;
        color: white;
        border-radius: 4px;
        padding: 8px 16px;
        font-weight: bold;
    }
    QPushButton:hover {
        background-color: #0098ff;
    }
    QPushButton:pressed {
        background-color: #005c99;
    }
    QComboBox {
        background-color: #3d3d3d;
        border: 1px solid #555555;
        border-radius: 4px;
        padding: 5px;
    }
    QComboBox::drop-down {
        subcontrol-origin: padding;
        subcontrol-position: top right;
        width: 15px;
        border-left-width: 0px;
        border-top-right-radius: 3px;
        border-bottom-right-radius: 3px;
    }
    QRadioButton {
        spacing: 8px;
    }
    QRadioButton::indicator {
        width: 16px;
        height: 16px;
        border-radius: 8px;
        border: 2px solid #555555;
    }
    QRadioButton::indicator:checked {
        background-color: #007acc;
        border-color: #007acc;
    }
    QLabel#Title {
        font-size: 18px;
        font-weight: bold;
        color: #dddddd;
        margin-bottom: 10px;
    }
"""

# --- Model Definitions ---
# Label -> (backend, variant, size)
MODEL_OPTIONS = {
    "Parakeet (Fast English)": ("parakeet_tdt", "v2_en", None),
    "Parakeet (Multilingual)": ("parakeet_tdt", "v3_multi", None),
    "Whisper (Tiny)": ("faster_whisper", None, "tiny"),
    "Whisper (Base)": ("faster_whisper", None, "base"),
    "Whisper (Small)": ("faster_whisper", None, "small"),
    "Whisper (Medium)": ("faster_whisper", None, "medium"),
    "Whisper (Large)": ("faster_whisper", None, "large-v3"),
}

def get_input_devices():
    """List input devices: returns list of names. Filters out raw ALSA hw devices."""
    devices = []
    try:
        devs = sd.query_devices()
        # Filter for input devices (max_input_channels > 0)
        
        # Priority 1: Pulse/Pipewire/Default
        priority_devs = []
        # Priority 2: Other useful ones (USB, etc)
        other_devs = []
        
        seen_names = set()
        
        for d in devs:
            if d['max_input_channels'] > 0:
                name = d['name']
                
                # Filter out raw ALSA hardware devices which usually cause sample rate issues
                # e.g. "sof-hda-dsp: - (hw:0,0)"
                if "(hw:" in name or "dmix" in name or "surround" in name:
                    continue
                    
                if name in seen_names:
                    continue
                seen_names.add(name)
                
                lower_name = name.lower()
                if "default" in lower_name or "pipewire" in lower_name or "pulse" in lower_name:
                    priority_devs.append(name)
                else:
                    other_devs.append(name)
        
        devices.extend(sorted(priority_devs))
        devices.extend(sorted(other_devs))
        
        # Always ensure Default is present if nothing else found or as fallback
        if "Default" not in devices and "default" not in devices:
             devices.insert(0, "Default")
             
    except Exception as e:
        print(f"Error querying devices: {e}")
        devices.append("Default")
    return devices

class DownloadDialog(QDialog):
    def __init__(self, parent=None, target_dir=None, expected_size_mb=670):
        super().__init__(parent)
        self.setWindowTitle("Downloading Model")
        self.setFixedSize(300, 100)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.CustomizeWindowHint | Qt.WindowType.WindowTitleHint)
        self.target_dir = target_dir
        self.expected_size_mb = expected_size_mb
        
        layout = QVBoxLayout()
        self.label = QLabel(f"Downloading model...\nTarget: ~{expected_size_mb} MB")
        self.label.setWordWrap(True)
        layout.addWidget(self.label)
        
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        layout.addWidget(self.progress)
        
        self.setLayout(layout)
        
        # Start Polling
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.poll_progress)
        self.timer.start(500) # Check every 500ms

    def poll_progress(self):
        if not self.target_dir:
            return
            
        try:
             import os
             total_size = 0
             if os.path.exists(self.target_dir):
                 for dirpath, dirnames, filenames in os.walk(self.target_dir):
                     for f in filenames:
                         fp = os.path.join(dirpath, f)
                         # skip incomplete extensions if any, usually huggingface uses temp names but eventually renames
                         # just counting all bytes in folder is a good approximation
                         total_size += os.path.getsize(fp)
             
             size_mb = total_size / (1024 * 1024)
             percent = int((size_mb / self.expected_size_mb) * 100)
             if percent > 100: percent = 99 # clamping until actual success

             self.progress.setValue(percent)
             self.label.setText(f"Downloaded: {size_mb:.1f} MB / ~{self.expected_size_mb} MB")
        except Exception:
             pass

class SettingsWindow(QWidget):
    saved = pyqtSignal()

    def __init__(self, server=None):
        super().__init__()
        self.server = server
        self.setWindowTitle("uWhisper Settings")
        self.setMinimumSize(450, 550) # Increased height
        self.setup_ui()
        self.load_settings()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Title
        title = QLabel("Application Settings")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Form Layout
        form_frame = QFrame()
        form_frame.setObjectName("panel")
        form_layout = QVBoxLayout(form_frame)
        
        # Model Selection
        lbl_model = QLabel("Model:")
        model_row = QHBoxLayout()
        self.combo_model = QComboBox()
        self.combo_model.addItems(MODEL_OPTIONS.keys())
        self.combo_model.currentTextChanged.connect(self.on_model_changed)
        model_row.addWidget(self.combo_model)
        
        self.btn_delete = QPushButton("🗑️")
        self.btn_delete.setToolTip("Delete this model from cache")
        self.btn_delete.setFixedSize(30, 30)
        self.btn_delete.clicked.connect(self.delete_current_model)
        model_row.addWidget(self.btn_delete)
        
        form_layout.addWidget(lbl_model)
        form_layout.addLayout(model_row)
        
        self.lbl_model_status = QLabel("")
        self.lbl_model_status.setStyleSheet("color: #888; font-size: 10px;")
        form_layout.addWidget(self.lbl_model_status)

        # Language
        self.lbl_lang = QLabel("Language:")
        self.combo_lang = QComboBox()
        self.combo_lang.addItems(["auto", "en", "pl", "de", "fr", "es", "it", "ja", "zh", "ru"])
        form_layout.addWidget(self.lbl_lang)
        form_layout.addWidget(self.combo_lang)
        
        # Microphone Note (Replaces Selection)
        lbl_mic_title = QLabel("Microphone:")
        lbl_mic_note = QLabel("Select microphone in your OS settings")
        lbl_mic_note.setStyleSheet("color: #888; font-style: italic;")
        
        form_layout.addWidget(lbl_mic_title)
        form_layout.addWidget(lbl_mic_note)
        
        # Mic Test Area
        test_layout = QHBoxLayout()
        test_layout.setContentsMargins(0, 0, 0, 0)
        
        self.btn_test_mic = QPushButton("Test Microphone")
        self.btn_test_mic.setCheckable(True)
        self.btn_test_mic.clicked.connect(self.on_test_mic_clicked)
        self.btn_test_mic.setStyleSheet("background-color: #555; color: white;") # Neutral default
        
        test_layout.addWidget(self.btn_test_mic)
        
        # Embedded Amplitude Visualizer
        self.progress_mic_level = QProgressBar()
        self.progress_mic_level.setRange(0, 100)
        self.progress_mic_level.setTextVisible(False)
        self.progress_mic_level.setFixedHeight(10)
        self.progress_mic_level.setStyleSheet("""
            QProgressBar {
                border: 1px solid #444;
                border-radius: 2px;
                background-color: #222;
            }
            QProgressBar::chunk {
                background-color: #00ff88;
                width: 1px;
            }
        """)
        test_layout.addWidget(self.progress_mic_level)
        
        lbl_test_hint = QLabel("Records and plays back audio to verify input.")
        lbl_test_hint.setStyleSheet("color: #888; font-size: 11px; font-style: italic;")
        
        form_layout.addLayout(test_layout)
        form_layout.addWidget(lbl_test_hint)

        # Output Mode
        lbl_mode = QLabel("Output Mode:")
        form_layout.addWidget(lbl_mode)
        
        self.radio_clipboard = QRadioButton("Clipboard Only")
        self.radio_paste = QRadioButton("Clipboard + Auto-Paste")
        self.radio_paste.setToolTip("Requires setup_permissions.sh to work natively")
        
        form_layout.addWidget(self.radio_clipboard)
        form_layout.addWidget(self.radio_paste)

        # Logging
        log_group = QGroupBox("Logging")
        log_layout = QVBoxLayout()
        
        self.chk_logging = QCheckBox("Enable Logging")
        log_layout.addWidget(self.chk_logging)
        
        log_path_layout = QHBoxLayout()
        self.txt_log_dir = QLineEdit()
        self.txt_log_dir.setPlaceholderText("/tmp/uwhisper_logs")
        self.btn_browse_log = QPushButton("...")
        self.btn_browse_log.setFixedWidth(40)
        self.btn_browse_log.clicked.connect(self.browse_log_dir)
        
        log_path_layout.addWidget(self.txt_log_dir)
        log_path_layout.addWidget(self.btn_browse_log)
        
        log_layout.addLayout(log_path_layout)
        log_group.setLayout(log_layout)
        
        form_layout.addWidget(log_group)
        
        layout.addWidget(form_frame)

        # Save Button
        self.btn_save = QPushButton("Save Settings")
        self.btn_save.setObjectName("primaryButton")
        self.btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_save.clicked.connect(self.save_settings)
        layout.addWidget(self.btn_save)
        
        # Connect server signal if available to update button state
        if self.server:
            self.server.signals.state_changed.connect(self.on_server_state_changed)

        self.setLayout(layout)

    def update_amplitude(self, level):
        # Convert 0.0-1.0 to 0-100 with some boosting for visibility
        if level < 0.001: val = 0
        else:
             # loose log/boost curve
             val = int(level * 400) # Simple boost
             if val > 100: val = 100
        self.progress_mic_level.setValue(val)        


    def on_server_state_changed(self, state):
        # Update Test Button if relevant
        if state == "recording":
             # We might be in test mode or normal mode.
             if self.btn_test_mic.isChecked():
                 self.btn_test_mic.setText("Stop recording and play")
                 self.btn_test_mic.setStyleSheet("background-color: #d94444; color: white;")
        elif state == "recording_test" or (state == "recording" and self.btn_test_mic.isChecked()):
             self.btn_test_mic.setText("Stop recording and play")
             self.btn_test_mic.setStyleSheet("background-color: #d94444; color: white;")
        elif state == "idle" or state == "playing":
             self.btn_test_mic.setChecked(False)
             self.btn_test_mic.setText("Test Microphone")
             self.btn_test_mic.setStyleSheet("background-color: #555; color: white;")

    def on_test_mic_clicked(self):
        if not self.server:
            return
            
        if self.btn_test_mic.isChecked():
            # Start Test
            self.server.start_mic_test()
        else:
            # Stop Test
            self.server.stop_recording()

    def load_settings(self):
        try:
            backend = settings.get("model_backend", "faster_whisper")
            variant = settings.get("parakeet_variant", "v2_en")
            size = settings.get("model_size", "base")
            if size == "large-v3": size = "large-v3"
            elif size and "base" in size: size = "base"
            
            # Find matching label
            target_label = "Whisper (Base)" # Default
            for label, (b, v, s) in MODEL_OPTIONS.items():
                if backend == "parakeet_tdt":
                     if b == backend and v == variant:
                         target_label = label
                         break
                else:
                     if b == backend and s == size:
                         target_label = label
                         break
            
            # Safely set Model
            try:
                self.combo_model.blockSignals(True)
                self.combo_model.setCurrentText(target_label)
                self.combo_model.blockSignals(False)
            except RuntimeError:
                pass # C++ object deleted
                
            # Safely set Language
            try:
                self.combo_lang.blockSignals(True)
                self.combo_lang.setCurrentText(settings.get("language"))
                self.combo_lang.blockSignals(False)
            except RuntimeError:
                pass
            
            # Microphone settings ignored (using OS default)
            
            mode = settings.get("output_mode")
            if mode == "paste":
                self.radio_paste.setChecked(True)
            else:
                self.radio_clipboard.setChecked(True)
                
            self.chk_logging.setChecked(settings.get("enable_logging", True))
            self.txt_log_dir.setText(settings.get("log_dir", ""))
                
            # Manually trigger update once
            self.on_model_changed(target_label)
            
        except Exception as e:
            print(f"Error loading settings: {e}")

    def on_model_changed(self, text):
        data = MODEL_OPTIONS.get(text)
        if not data: return
        
        backend, variant, size = data
        
        if backend == "parakeet_tdt":
            self.lbl_lang.hide()
            self.combo_lang.hide()
        else:
            self.lbl_lang.show()
            self.combo_lang.show()
            
        self.check_model_status()

    def browse_log_dir(self):
        path = QFileDialog.getExistingDirectory(self, "Select Log Directory")
        if path:
            self.txt_log_dir.setText(path)

    def check_model_status(self, text=None):
        if not self.server:
            return
            
        model_label = self.combo_model.currentText()
        data = MODEL_OPTIONS.get(model_label)
        if not data: return
        
        backend, variant, size = data
        
        is_installed = False

        if backend == "faster_whisper":
            # Check if size is in downloaded models
            check_model = size # e.g. "base"
            installed_list = self.server.get_downloaded_models()
            is_installed = check_model in installed_list
        elif backend == "parakeet_tdt":
             import os
             # variant is v2_en or v3_multi
             if variant == "v3_multi":
                 cache_dir = os.path.expanduser("~/.cache/uwhisper/parakeet_model_v3")
             else:
                 cache_dir = os.path.expanduser("~/.cache/uwhisper/parakeet_model")
                 
             required_files = ["encoder.int8.onnx", "decoder.int8.onnx", "joiner.int8.onnx", "tokens.txt"]
             is_installed = all(os.path.exists(os.path.join(cache_dir, f)) for f in required_files)

        if is_installed:
            self.lbl_model_status.setText("✓ Installed")
            self.lbl_model_status.setStyleSheet("color: #00ff88; font-size: 10px;")
            self.btn_delete.setEnabled(True)
            self.btn_delete.setStyleSheet("") # Default
            self.btn_save.setText("Save Settings")
        else:
            self.lbl_model_status.setText("⚠ Not Installed (Will download on save)")
            self.lbl_model_status.setStyleSheet("color: #ffaa00; font-size: 10px;")
            self.btn_delete.setEnabled(False)
            self.btn_delete.setStyleSheet("opacity: 0.5;")
            self.btn_save.setText("Download & Save")

    def delete_current_model(self):
        if not self.server: return
        model_label = self.combo_model.currentText()
        data = MODEL_OPTIONS.get(model_label)
        if not data: return
        
        backend, variant, size = data
        
        if backend == "faster_whisper":
             model_id = size
        else:
             model_id = backend 

        reply = QMessageBox.question(self, "Confirm Delete", 
                                   f"Are you sure you want to delete model '{model_label}'?",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            success = self.server.delete_model(model_id) # Ensure server handles this ID
            if success:
                self.check_model_status()
            else:
                QMessageBox.warning(self, "Error", "Failed to delete model.")

    def save_settings(self):
        # Update settings first so download uses correct values
        model_label = self.combo_model.currentText()
        data = MODEL_OPTIONS.get(model_label)
        if not data: return
        
        backend, variant, size = data
        
        settings.set("model_backend", backend)
        if variant:
            settings.set("parakeet_variant", variant)
        if size:
            settings.set("model_size", size)
            
        settings.set("language", self.combo_lang.currentText())
        settings.set("enable_logging", self.chk_logging.isChecked())
        settings.set("log_dir", self.txt_log_dir.text())
        # Mic setting is ignored/cleared
        settings.set("input_device_name", "Default")
        
        mode = "paste" if self.radio_paste.isChecked() else "clipboard"
        settings.set("output_mode", mode)

        if self.btn_save.text().startswith("Download"):
            import os
            
            if backend == "parakeet_tdt":
                target_dir = os.path.expanduser("~/.cache/uwhisper/parakeet_model") # Default v2
                expected_size = 641 
                
                if variant == "v3_multi":
                     target_dir = os.path.expanduser("~/.cache/uwhisper/parakeet_model_v3")
                     expected_size = 641
            else:
                # Faster Whisper
                size_map = {
                    "tiny": 75,
                    "base": 145,
                    "small": 490,
                    "medium": 1500,
                    "large-v3": 3000
                }
                expected_size = size_map.get(size, 500)
                target_dir = os.path.expanduser(f"~/.cache/huggingface/hub/models--Systran--faster-whisper-{size}")

            # Trigger Download
            dlg = DownloadDialog(self, target_dir=target_dir, expected_size_mb=expected_size)
            dlg.show()
            QApplication.processEvents()
            
            import threading
            self.download_success = False
            
            def run_download():
                download_arg = size if size else "parakeet-tdt-0.6b"
                self.download_success = self.server.download_model(download_arg)
                
            t = threading.Thread(target=run_download)
            t.start()
            
            while t.is_alive():
                QApplication.processEvents()
                time.sleep(0.05)
                
            dlg.close()
            
            if not self.download_success:
                QMessageBox.critical(self, "Download Failed", "Could not download model. Check internet connection.")
                return

        self.saved.emit()
        self.close()

import signal
from PyQt6.QtGui import QActionGroup
from overlay import OverlayWindow

class SystemTrayApp:
    def __init__(self, start_server_callback, stop_server_callback, server_instance=None):
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)
        
        # Server reference for signals
        self.server = server_instance
        
        # Windows
        self.callbacks = {
            "start": start_server_callback,
            "stop": stop_server_callback
        }

        # Handle Signals (Ctrl+C, etc.)
        signal.signal(signal.SIGINT, self.handle_exit_signal)
        signal.signal(signal.SIGTERM, self.handle_exit_signal)

        # Python/Qt signal workaround
        self.keep_alive_timer = QTimer()
        self.keep_alive_timer.timeout.connect(lambda: None)
        self.keep_alive_timer.start(500)
        
        # Create Dummy Icon
        self.tray_icon = QSystemTrayIcon()
        
        # Try multiple common icon names or fallback to a color
        icon = QIcon.fromTheme("audio-input-microphone")
        if icon.isNull():
            icon = QIcon.fromTheme("microphone")
        if icon.isNull():
            # Fallback
            from PyQt6.QtGui import QPixmap, QPainter
            pixmap = QPixmap(16, 16)
            pixmap.fill(Qt.GlobalColor.transparent)
            painter = QPainter(pixmap)
            painter.setBrush(QColor("red"))
            painter.drawEllipse(0, 0, 16, 16)
            painter.end()
            icon = QIcon(pixmap)
            
        self.tray_icon.setIcon(icon)
        self.tray_icon.setVisible(True)
        self.tray_icon.setToolTip("uWhisper")
        
        # Setup Extended Menu
        self.create_tray_menu()

        # Show Settings Window immediately on startup
        self.settings_window = SettingsWindow(server=self.server)
        self.settings_window.saved.connect(self.on_settings_saved)

        # Create Overlay Window
        self.overlay = OverlayWindow()
        self.overlay.cancelled.connect(self.on_cancel_requested)
        
        # Connect Signals if server exists
        if self.server:
            self.server.signals.state_changed.connect(self.on_state_changed)
            self.server.signals.amplitude_changed.connect(self.on_amplitude_changed)
            self.server.signals.text_ready.connect(self.on_text_ready)
            self.server.signals.notification.connect(self.on_notification)

    def create_tray_menu(self):
        self.menu = QMenu()
        
        # 1. Start/Stop Action
        self.act_toggle = QAction("Start Recording", self.menu)
        self.act_toggle.triggered.connect(self.toggle_recording_action)
        self.menu.addAction(self.act_toggle)
        
        self.menu.addSeparator()
        
        # 2. Model Submenu
        self.menu_model = QMenu("Model", self.menu)
        self.group_model = QActionGroup(self.menu)
        
        # Reverse map for syncing
        self.model_config_map = {} # Keyed by config tuple to Label
        
        for label, data in MODEL_OPTIONS.items():
            act = QAction(label, self.menu_model, checkable=True)
            act.setData(data)
            self.group_model.addAction(act)
            self.menu_model.addAction(act)
            
            # Store map: (backend, variant, size) -> Action
            self.model_config_map[data] = act
        
        self.group_model.triggered.connect(self.on_menu_model_changed)
        self.menu.addAction(self.menu_model.menuAction())
        
        # 3. Language Submenu
        self.menu_lang = QMenu("Language", self.menu)
        self.group_lang = QActionGroup(self.menu)
        self.lang_actions = {}
        
        langs = ["auto", "en", "pl", "de", "fr", "es", "it", "ja", "zh", "ru"]
        for lang in langs:
            act = QAction(lang, self.menu_lang, checkable=True)
            act.setData(lang)
            self.group_lang.addAction(act)
            self.menu_lang.addAction(act)
            self.lang_actions[lang] = act
            
        self.group_lang.triggered.connect(self.on_menu_lang_changed)
        self.menu.addAction(self.menu_lang.menuAction())
        
        self.menu.addSeparator()

        # REMOVED Microphone Submenu as requested
        
        # 5. Standard Items
        self.act_settings = QAction("Settings", self.menu)
        self.act_settings.triggered.connect(self.show_settings)
        self.menu.addAction(self.act_settings)
        
        self.act_quit = QAction("Quit", self.menu)
        self.act_quit.triggered.connect(self.quit)
        self.menu.addAction(self.act_quit)
        
        self.tray_icon.setContextMenu(self.menu)
        
        # Initialize Selection
        self.sync_menu_from_settings()

    def sync_menu_from_settings(self):
        # 1. Sync Model
        backend = settings.get("model_backend", "faster_whisper")
        variant = settings.get("parakeet_variant", "v2_en")
        size = settings.get("model_size", "base")
        if size == "large-v3": size = "large-v3"
        elif "base" in size or size == "base": size = "base" 
        else: size = "base" # default fallback
        
        # Match against our known presets
        target_action = None
        
        if backend == "parakeet_tdt":
            # Match by variant
            for label, data in MODEL_OPTIONS.items():
                if data[0] == "parakeet_tdt" and data[1] == variant:
                    target_action = self.model_config_map.get(data)
                    break
        else:
            # Match by size
            for label, data in MODEL_OPTIONS.items():
                if data[0] == "faster_whisper" and data[2] == size:
                    target_action = self.model_config_map.get(data)
                    break
        
        if target_action:
            target_action.setChecked(True)
            
        # 2. Sync Language
        lang = settings.get("language", "auto")
        if lang in self.lang_actions:
            self.lang_actions[lang].setChecked(True)
            
        # 3. Mic sync removed

        # 4. Apply Constraints (Parakeet lock)
        self.apply_constraints()

    def apply_constraints(self):
        # Logic: If Parakeet is checked, disable Language menu (force auto)
        backend = settings.get("model_backend")
        if backend == "parakeet_tdt":
            self.menu_lang.setEnabled(False)
            self.menu_lang.setTitle("Language (Auto)")
            # Force visual check on 'auto'
            if "auto" in self.lang_actions:
                self.lang_actions["auto"].setChecked(True)
        else:
            self.menu_lang.setEnabled(True)
            self.menu_lang.setTitle("Language")

    def on_menu_model_changed(self, action):
        data = action.data()
        backend, variant, size = data
        
        print(f"Menu Model Changed: {backend}, var={variant}, size={size}")
        
        settings.set("model_backend", backend)
        if variant:
            settings.set("parakeet_variant", variant)
        if size:
            settings.set("model_size", size)
            
        self.apply_constraints()
        
        # Update Settings Window if open
        if self.settings_window and self.settings_window.isVisible():
            self.settings_window.load_settings()

    def on_menu_lang_changed(self, action):
        lang = action.data()
        print(f"Menu Lang Changed: {lang}")
        settings.set("language", lang)
        
        if self.settings_window and self.settings_window.isVisible():
            self.settings_window.load_settings()

    # on_menu_mic_changed removed

        
        if self.settings_window and self.settings_window.isVisible():
            self.settings_window.load_settings()

    def toggle_recording_action(self):
        if self.server:
            # Check current state from server logic?
            # We don't direct access 'server.recording' property easily unless we assume implementation.
            # But we can just use the toggle via client sim or method
            # If act_toggle says "Stop", we stop.
            
            if "Stop" in self.act_toggle.text():
                 self.server.stop_recording()
            else:
                 self.server.start_recording()

    def on_cancel_requested(self):
        if self.server:
            self.server.cancel_recording()
        self.overlay.hide()
        
    def on_notification(self, title, message):
        self.overlay.show()
        self.overlay.set_state(title, message)
        QTimer.singleShot(3000, self.overlay.hide)

    def on_state_changed(self, state):
        is_rec = (state == "recording") or (state == "recording_test")
        
        # Update Tray Menu Text
        if is_rec:
            self.act_toggle.setText("Stop Recording")
            try:
                self.act_toggle.setIcon(QIcon.fromTheme("media-playback-stop"))
            except: pass
        else:
            self.act_toggle.setText("Start Recording")
            try:
                self.act_toggle.setIcon(QIcon.fromTheme("media-record"))
            except: pass
            
        # Handle Overlay State
    def on_state_changed(self, state):
        is_rec = (state == "recording") or (state == "recording_test")
        
        # Update Tray Menu Text
        if is_rec:
            self.act_toggle.setText("Stop Recording")
            try:
                self.act_toggle.setIcon(QIcon.fromTheme("media-playback-stop"))
            except: pass
        else:
            self.act_toggle.setText("Start Recording")
            try:
                self.act_toggle.setIcon(QIcon.fromTheme("media-record"))
            except: pass
            
        # Handle Overlay State
        if state == "recording":
            # Normal Dictation: Overlay on top, focused to catch ESC
            self.overlay.set_on_top(True)
            self.overlay.set_focusable(True) 
            self.overlay.set_interactive(True) 
            self.overlay.set_state("Recording", "Listening...")
            self.overlay.show()
            self.overlay.activateWindow()

        elif state == "recording_test":
            # Mic Test: Use Embedded Visualizer in Settings Window
            # Do NOT show overlay, as it causes focus/click issues on some WMs
            self.overlay.hide()
            
            # Ensure Settings is visible
            if self.settings_window:
                self.settings_window.show()
                self.settings_window.raise_()
                self.settings_window.activateWindow()

        elif state == "transcribing":
            self.overlay.set_on_top(True)
            self.overlay.set_state("Transcribing", "Processing...")
            self.overlay.show()
            
        elif state == "playing":
             # Playback state (Mic Test finished)
             self.overlay.set_state("Playback", "Playing...")
             self.overlay.set_on_top(False)
             self.overlay.show()
             
        elif state == "idle":
            # Hide overlay immediately when going to idle
            self.overlay.hide()

    # Removed incorrect on_server_state_changed from SystemTrayApp that references btn_test_mic


    def on_amplitude_changed(self, level):
        # Dispatch to correct visualizer
        if self.server and self.server.mic_testing:
             if self.settings_window and self.settings_window.isVisible():
                 self.settings_window.update_amplitude(level)
        else:
             self.overlay.update_amplitude(level)

    def on_text_ready(self, text):
        self.overlay.set_state("Done", f"Success")
        self.overlay.set_focusable(False) 
        QApplication.processEvents()
        
        start = time.time()
        while self.overlay.isActiveWindow() and (time.time() - start < 1.0):
             QApplication.processEvents()
             time.sleep(0.01)

        mode = settings.get("output_mode")
        if mode == "paste":
            simulate_ctrl_v()

        QTimer.singleShot(800, self.overlay.hide)

    
    def show_settings(self):
        if not self.settings_window:
            self.settings_window = SettingsWindow(server=self.server)
            self.settings_window.saved.connect(self.on_settings_saved)
        self.settings_window.show()
        self.settings_window.raise_()
        self.settings_window.activateWindow()

    def on_settings_saved(self):
        print("Settings saved.")
        self.sync_menu_from_settings()

    def handle_exit_signal(self, signum, frame):
        print(f"Received signal {signum}. Quitting...")
        self.quit()

    def run(self):
        sys.exit(self.app.exec())

    def quit(self):
        if self.callbacks["stop"]:
            self.callbacks["stop"]()
        self.tray_icon.hide()
        self.app.quit()
        
if __name__ == "__main__":
    # Test run
    app = SystemTrayApp(None, None)
    app.run()
