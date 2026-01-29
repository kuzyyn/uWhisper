import sys
import random
from PyQt6.QtWidgets import QWidget, QLabel, QHBoxLayout, QVBoxLayout, QApplication
from PyQt6.QtCore import Qt, QTimer, pyqtSlot, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen, QFont

class OverlayWindow(QWidget):
    cancelled = pyqtSignal()

    def __init__(self):
        super().__init__()
        # Window Flags: Frameless, On Top, Tool
        # We remove WindowDoesNotAcceptFocus to allow catching ESC key
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | 
                            Qt.WindowType.WindowStaysOnTopHint | 
                            Qt.WindowType.Tool)
        
        # Transparent Background & Click-through
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        # Note: If we want to catch keys, we might need to disable TransparentForMouseEvents 
        # OR just rely on focus. Let's try keeping it for now.
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        
        # Fullscreen to bypass Wayland positioning restrictions
        self.screen_geo = QApplication.primaryScreen().geometry()
        self.setGeometry(self.screen_geo)

        # State
        self.bars = [0.1] * 20  # 20 bars for visualization
        self.target_amplitude = 0.0
        self.state_text = "Ready"
        self.is_transcribing = False

        # Timer for smooth animation
        self.anim_timer = QTimer()
        self.anim_timer.timeout.connect(self.update_animation)
        self.anim_timer.start(30) 
        
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

    def set_state(self, state, text=""):
        self.state_text = text if text else state.title()
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
        
        # Define the "Virtual" overlay area (bottom center)
        overlay_w = 400
        overlay_h = 100
        overlay_x = (w - overlay_w) // 2
        overlay_y = h - overlay_h - 100 # 100px padding from bottom
        
        # 1. Draw Background Pill (in virtual area)
        bg_color = QColor(20, 20, 20, 220) # Dark semi-transparent
        painter.setBrush(QBrush(bg_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(overlay_x, overlay_y, overlay_w, overlay_h, 20, 20)

        # 2. Draw Text Status
        painter.setPen(QColor(255, 255, 255))
        painter.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        text_rect = painter.boundingRect(0, 0, overlay_w, 30, Qt.AlignmentFlag.AlignCenter, self.state_text)
        painter.drawText(overlay_x + (overlay_w - text_rect.width()) // 2, overlay_y + overlay_h - 20, self.state_text)

        # 3. Draw Visualization Bars
        bar_w = 8
        gap = 4
        total_bar_width = len(self.bars) * (bar_w + gap)
        start_x = overlay_x + (overlay_w - total_bar_width) // 2
        
        center_y = overlay_y + (overlay_h - 30) // 2 + 10 # Vertically centered above text

        color_start = QColor("#007acc")
        color_loud = QColor("#00ff88") # Greenish for loud

        for i, height_factor in enumerate(self.bars):
            # Height calculation (max 50px)
            bar_h = 10 + (height_factor * 50)
            if bar_h > 60: bar_h = 60
            
            x = start_x + i * (bar_w + gap)
            y = center_y - (bar_h / 2)
            
            # Dynamic Color
            c = QColor(color_start)
            if height_factor > 0.6:
                c = color_loud
            
            painter.setBrush(QBrush(c))
            painter.drawRoundedRect(int(x), int(y), int(bar_w), int(bar_h), 4, 4)

import time
