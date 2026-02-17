import sys
import random
from PyQt6.QtWidgets import QWidget, QLabel, QHBoxLayout, QVBoxLayout, QApplication
from PyQt6.QtCore import Qt, QTimer, pyqtSlot, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen, QFont

class OverlayWindow(QWidget):
    cancelled = pyqtSignal()

    def __init__(self):
        super().__init__()
        
        # State for flags
        self._on_top = True
        self._focusable = True
        
        # Initial Flags calculation
        self._update_flags()

        # State
        self.bars = [0.1] * 20  # 20 bars for visualization
        self.target_amplitude = 0.0
        self.state_text = "Ready"
        self.details_text = None
        self.is_transcribing = False

        # Timer for smooth animation
        self.anim_timer = QTimer()
        self.anim_timer.timeout.connect(self.update_animation)
        self.anim_timer.start(30)
        
        # Ensure we have screen geometry
        self.screen_geo = QApplication.primaryScreen().geometry()
        self.setGeometry(self.screen_geo)

    def _update_flags(self):
        flags = Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool
        
        if self._on_top:
            flags |= Qt.WindowType.WindowStaysOnTopHint
            
        if not self._focusable:
            flags |= Qt.WindowType.WindowDoesNotAcceptFocus
            
        self.setWindowFlags(flags)
        
        # Re-apply attributes that might reset on flag change
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        
        # We need to re-apply this specific attribute too because setWindowFlags clears attributes
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, not self.check_interactive())
        
        if self.isVisible():
            self.show()
            
    def check_interactive(self):
        # Helper to read current attribute state, though we might not rely on it
        return not self.testAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

    def set_focusable(self, focusable: bool):
        if self._focusable == focusable:
            return
        self._focusable = focusable
        self._update_flags()
        
    def set_on_top(self, on_top: bool):
        if self._on_top == on_top:
            return
        self._on_top = on_top
        self._update_flags()

    def set_interactive(self, interactive: bool):
        # Invert logic: If interactive=True, Transparent=False
        current = not self.testAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        if current == interactive:
            return
            
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, not interactive)
        
        # Force update if visible
        if self.isVisible():
            # Sometimes hide/show is needed for attribute change to take effect on some WMs
            self.hide()
            self.show()
 
        
    def showEvent(self, event):
        super().showEvent(event)
        # Ensure fullscreen
        self.setGeometry(QApplication.primaryScreen().geometry())
        # Request focus to catch ESC key
        self.activateWindow()
        self.raise_()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.cancelled.emit()
            event.accept()
        else:
            super().keyPressEvent(event)

    def update_amplitude(self, level):
        # Boost low levels for visibility
        if level > 0.001:
            self.target_amplitude = level * 15.0 # HUGE Boost for visibility
            if self.target_amplitude > 1.0: self.target_amplitude = 1.0
        else:
            self.target_amplitude = 0.0

    def update_amplitude(self, level):
        # Boost low levels for visibility
        if level > 0.001:
            self.target_amplitude = level * 15.0 # HUGE Boost for visibility
            if self.target_amplitude > 1.0: self.target_amplitude = 1.0
        else:
            self.target_amplitude = 0.0

    def set_state(self, state, text="", details=None):
        self.state_text = text if text else state.title()
        self.details_text = details
        self.is_transcribing = (state == "transcribing")
        self.update()
        
        if state == "idle":
            # Fade out or hide after a delay?
            # For now, parent controller handles show/hide
            pass

    def update_animation(self):
        if not self.isVisible():
            return
            
        # Update bars logic
        for i in range(len(self.bars)):
            # Random variations based on target amplitude to simulate "wave"
            # Middle bars higher than edges
            dist_from_center = abs(i - len(self.bars)/2) / (len(self.bars)/2)
            scale = 1.0 - (dist_from_center * 0.5)
            
            target = self.target_amplitude * scale * random.uniform(0.8, 1.2)
            if self.is_transcribing:
                # Spinning wave effect
                import math
                t = time.time() * 10
                target = (math.sin(t + i*0.5) + 1) / 4 + 0.2

            # Smooth approach
            self.bars[i] += (target - self.bars[i]) * 0.2
            
            # Decay (silence)
            self.target_amplitude *= 0.95

        self.update() # Trigger repaint

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()
        
        # Define layout constants based on state
        overlay_w = 380
        overlay_h = 100
        
        overlay_x = (w - overlay_w) // 2
        overlay_y = h - overlay_h - 100 
        
        # 1. Draw Background Pill
        bg_color = QColor(20, 20, 20, 230)
        painter.setBrush(QBrush(bg_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(overlay_x, overlay_y, overlay_w, overlay_h, 16, 16)

        # 2. Draw Visualization Bars
        bar_w = 6
        gap = 4
        num_bars = len(self.bars)
        total_bar_width = num_bars * (bar_w + gap) - gap
        start_x = overlay_x + (overlay_w - total_bar_width) // 2
        
        # Branch Layout Logic
        if self.details_text:
            # Transcribing / Loading Mode (Compact Bars + 2 Line Text)
            bars_center_y = overlay_y + 30
            max_bar_h = 40
            
            # Text Y positions
            y_main = overlay_y + 70
            y_sub = overlay_y + 88
            
        else:
            # Recording Mode (Large Bars + 1 Line Text)
            bars_center_y = overlay_y + 40 # Lower center for balance
            max_bar_h = 60
            
            # Text Y positions
            y_main = overlay_y + 85 # Bottom center
            
        
        # Bar Colors
        color_start = QColor("#007acc")
        color_loud = QColor("#00ff88") # Greenish for loud
        if self.is_transcribing:
             color_start = QColor("#a64dff") 
             color_loud = QColor("#ff4da6")

        for i, height_factor in enumerate(self.bars):
            # Height calculation
            # factor 0.0-1.0
            if self.details_text:
                 bar_h = 4 + (height_factor * 30)
            else:
                 bar_h = 10 + (height_factor * 50)
                 
            if bar_h > max_bar_h: bar_h = max_bar_h
            
            x = start_x + i * (bar_w + gap)
            y = bars_center_y - (bar_h / 2)
            
            # Dynamic Color
            c = QColor(color_start)
            if height_factor > 0.6:
                c = color_loud
            
            painter.setBrush(QBrush(c))
            painter.drawRoundedRect(int(x), int(y), int(bar_w), int(bar_h), 2, 2)

        # 3. Draw Text Status
        text_center_x = overlay_x + overlay_w // 2
        
        if self.details_text:
            # Main Text
            painter.setPen(QColor(255, 255, 255))
            painter.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
            rect_main = painter.boundingRect(0, 0, overlay_w, 30, Qt.AlignmentFlag.AlignCenter, self.state_text)
            painter.drawText(text_center_x - rect_main.width() // 2, int(y_main), self.state_text)
            
            # Details Text
            painter.setPen(QColor(180, 180, 180)) 
            painter.setFont(QFont("Segoe UI", 10, QFont.Weight.Normal))
            rect_sub = painter.boundingRect(0, 0, overlay_w, 20, Qt.AlignmentFlag.AlignCenter, self.details_text)
            painter.drawText(text_center_x - rect_sub.width() // 2, int(y_sub), self.details_text)
            
        else:
            # Single line centered (Recording)
            painter.setPen(QColor(255, 255, 255))
            painter.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold)) # Slightly larger for emphasis
            rect_main = painter.boundingRect(0, 0, overlay_w, 30, Qt.AlignmentFlag.AlignCenter, self.state_text)
            painter.drawText(text_center_x - rect_main.width() // 2, int(y_main), self.state_text)

import time
