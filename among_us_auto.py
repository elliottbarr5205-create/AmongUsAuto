#!/usr/bin/env python3
"""
Among Us Mobile Automation Suite — Desktop GUI
PyQt5 GUI + ADB backend. Runs on Windows/Mac/Linux, controls Android over USB or WiFi.
Requirements: pip install PyQt5 pillow opencv-python numpy
ADB must be installed: https://developer.android.com/studio/releases/platform-tools
"""

import sys
import subprocess
import time
import random
import threading
import io
import os
from typing import Optional, Tuple

import numpy as np
from PIL import Image
import cv2

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QComboBox, QSlider, QTextEdit, QGroupBox,
    QCheckBox, QSpinBox, QFrame, QSplitter, QStatusBar
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, pyqtSlot
from PyQt5.QtGui import QFont, QColor, QPalette, QTextCursor, QPixmap, QImage

# ─────────────────────────────────────────
# THEME
# ─────────────────────────────────────────

AMONG_RED    = "#C72B2B"
AMONG_DARK   = "#0D0D1A"
AMONG_PANEL  = "#14142A"
AMONG_CARD   = "#1C1C35"
AMONG_ACCENT = "#7B5CF0"
AMONG_GREEN  = "#2ECC71"
AMONG_TEXT   = "#E8E8F0"
AMONG_MUTED  = "#6B6B8A"
AMONG_WARN   = "#F39C12"

STYLESHEET = f"""
QMainWindow, QWidget {{
    background-color: {AMONG_DARK};
    color: {AMONG_TEXT};
    font-family: 'Segoe UI', 'Arial', sans-serif;
    font-size: 13px;
}}
QGroupBox {{
    background-color: {AMONG_CARD};
    border: 1px solid #2A2A4A;
    border-radius: 8px;
    margin-top: 14px;
    padding: 10px;
    font-weight: bold;
    font-size: 12px;
    color: {AMONG_MUTED};
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
    color: {AMONG_ACCENT};
    font-size: 11px;
    letter-spacing: 1px;
    text-transform: uppercase;
}}
QPushButton {{
    background-color: {AMONG_PANEL};
    color: {AMONG_TEXT};
    border: 1px solid #2A2A4A;
    border-radius: 6px;
    padding: 8px 18px;
    font-size: 13px;
    font-weight: 600;
}}
QPushButton:hover {{ background-color: #22224A; border-color: {AMONG_ACCENT}; }}
QPushButton:pressed {{ background-color: {AMONG_ACCENT}; }}
QPushButton#startBtn {{
    background-color: {AMONG_GREEN};
    color: #000;
    border: none;
    font-size: 14px;
    padding: 10px 28px;
    border-radius: 8px;
}}
QPushButton#startBtn:hover {{ background-color: #27AE60; }}
QPushButton#stopBtn {{
    background-color: {AMONG_RED};
    color: #fff;
    border: none;
    font-size: 14px;
    padding: 10px 28px;
    border-radius: 8px;
}}
QPushButton#stopBtn:hover {{ background-color: #A52020; }}
QPushButton#refreshBtn {{
    background-color: transparent;
    border: 1px solid {AMONG_ACCENT};
    color: {AMONG_ACCENT};
    padding: 5px 12px;
    font-size: 11px;
}}
QComboBox {{
    background-color: {AMONG_PANEL};
    border: 1px solid #2A2A4A;
    border-radius: 5px;
    padding: 5px 10px;
    color: {AMONG_TEXT};
    min-width: 160px;
}}
QComboBox::drop-down {{ border: none; }}
QComboBox QAbstractItemView {{
    background-color: {AMONG_CARD};
    border: 1px solid #2A2A4A;
    color: {AMONG_TEXT};
    selection-background-color: {AMONG_ACCENT};
}}
QSlider::groove:horizontal {{
    height: 4px;
    background: #2A2A4A;
    border-radius: 2px;
}}
QSlider::handle:horizontal {{
    background: {AMONG_ACCENT};
    width: 14px;
    height: 14px;
    margin: -5px 0;
    border-radius: 7px;
}}
QSlider::sub-page:horizontal {{ background: {AMONG_ACCENT}; border-radius: 2px; }}
QTextEdit {{
    background-color: #0A0A16;
    border: 1px solid #1A1A30;
    border-radius: 6px;
    color: #9FFFB0;
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 11px;
    padding: 6px;
}}
QCheckBox {{ spacing: 8px; color: {AMONG_TEXT}; }}
QCheckBox::indicator {{
    width: 16px; height: 16px;
    border: 1px solid #2A2A4A;
    border-radius: 3px;
    background: {AMONG_PANEL};
}}
QCheckBox::indicator:checked {{
    background: {AMONG_ACCENT};
    border-color: {AMONG_ACCENT};
}}
QSpinBox {{
    background-color: {AMONG_PANEL};
    border: 1px solid #2A2A4A;
    border-radius: 5px;
    padding: 4px 8px;
    color: {AMONG_TEXT};
    width: 70px;
}}
QLabel#sectionTitle {{
    font-size: 18px;
    font-weight: 800;
    color: {AMONG_TEXT};
    letter-spacing: 1px;
}}
QLabel#subtitle {{
    color: {AMONG_MUTED};
    font-size: 11px;
}}
QLabel#statusDot {{
    font-size: 22px;
}}
QStatusBar {{
    background-color: {AMONG_PANEL};
    color: {AMONG_MUTED};
    border-top: 1px solid #1A1A30;
    font-size: 11px;
}}
QFrame#divider {{
    color: #2A2A4A;
    max-height: 1px;
}}
"""

# ─────────────────────────────────────────
# ADB CORE
# ─────────────────────────────────────────

class ADB:
    device_id: Optional[str] = None

    @classmethod
    def run(cls, *args, timeout=10) -> str:
        cmd = ["adb"]
        if cls.device_id:
            cmd += ["-s", cls.device_id]
        cmd += list(args)
        try:
            r = subprocess.run(cmd, capture_output=True, timeout=timeout)
            return r.stdout.decode("utf-8", errors="ignore")
        except FileNotFoundError:
            return "ERROR: adb not found"
        except subprocess.TimeoutExpired:
            return "ERROR: adb timeout"

    @classmethod
    def list_devices(cls) -> list:
        out = subprocess.run(["adb", "devices"], capture_output=True).stdout.decode()
        devices = []
        for line in out.splitlines()[1:]:
            if "\tdevice" in line:
                devices.append(line.split("\t")[0].strip())
        return devices

    @classmethod
    def tap(cls, x: int, y: int, jitter: int = 8):
        x += random.randint(-jitter, jitter)
        y += random.randint(-jitter, jitter)
        cls.run("shell", "input", "tap", str(x), str(y))
        time.sleep(random.uniform(0.08, 0.18))

    @classmethod
    def swipe(cls, x1, y1, x2, y2, ms=200):
        cls.run("shell", "input", "swipe", str(x1), str(y1), str(x2), str(y2), str(ms))

    @classmethod
    def screenshot(cls) -> Optional[np.ndarray]:
        try:
            r = subprocess.run(
                ["adb"] + (["-s", cls.device_id] if cls.device_id else []) + ["exec-out", "screencap", "-p"],
                capture_output=True, timeout=6
            )
            img = Image.open(io.BytesIO(r.stdout))
            return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        except Exception:
            return None

    @classmethod
    def screen_size(cls) -> Tuple[int, int]:
        out = cls.run("shell", "wm", "size")
        try:
            part = out.strip().split(":")[-1].strip()
            w, h = part.split("x")
            return int(w), int(h)
        except Exception:
            return 1080, 2400


# ─────────────────────────────────────────
# VISION
# ─────────────────────────────────────────

def find_color(frame, hsv_lo, hsv_hi, min_area=800) -> Optional[Tuple[int,int]]:
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, np.array(hsv_lo), np.array(hsv_hi))
    cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not cnts:
        return None
    big = max(cnts, key=cv2.contourArea)
    if cv2.contourArea(big) < min_area:
        return None
    M = cv2.moments(big)
    if M["m00"] == 0:
        return None
    return int(M["m10"]/M["m00"]), int(M["m01"]/M["m00"])

def is_meeting(frame, h) -> bool:
    roi = frame[:h//3, :]
    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, np.array((15,100,100)), np.array((35,255,255)))
    return cv2.countNonZero(mask) > 5000


# ─────────────────────────────────────────
# BOT WORKER THREAD
# ─────────────────────────────────────────

class BotWorker(QThread):
    log_signal   = pyqtSignal(str)
    status_signal = pyqtSignal(str, str)  # label, color

    MODE_CREWMATE = "crewmate"
    MODE_IMPOSTOR = "impostor"
    MODE_ANTIAFK  = "antiafk"

    def __init__(self, mode, config):
        super().__init__()
        self.mode   = mode
        self.config = config
        self._stop  = threading.Event()

    def stop(self):
        self._stop.set()

    def log(self, msg: str):
        ts = time.strftime("%H:%M:%S")
        self.log_signal.emit(f"[{ts}] {msg}")

    def run(self):
        sw, sh = ADB.screen_size()
        self.log(f"Screen: {sw}×{sh}")
        self.status_signal.emit("RUNNING", AMONG_GREEN)

        if self.mode == self.MODE_CREWMATE:
            self._run_crewmate(sw, sh)
        elif self.mode == self.MODE_IMPOSTOR:
            self._run_impostor(sw, sh)
        elif self.mode == self.MODE_ANTIAFK:
            self._run_antiafk(sw, sh)

        self.status_signal.emit("IDLE", AMONG_MUTED)
        self.log("Bot stopped.")

    def _run_crewmate(self, sw, sh):
        COLOR_USE = ((35, 80, 80), (85, 255, 255))
        dirs = ["up","right","down","left","ur","ul","dr","dl"]
        idx = 0
        while not self._stop.is_set():
            frame = ADB.screenshot()
            if frame is None:
                self.log("Screenshot failed — retrying")
                time.sleep(1); continue

            if is_meeting(frame, sh):
                self.log("Meeting detected — skipping vote")
                time.sleep(5)
                ADB.tap(sw//2, int(sh*0.88))
                continue

            pos = find_color(frame, *COLOR_USE)
            if pos:
                self.log(f"USE button @ {pos} — completing task")
                ADB.tap(*pos)
                time.sleep(random.uniform(1.5, 3.0))
                ADB.tap(int(sw*0.88), int(sh*0.12))
            else:
                d = dirs[idx % len(dirs)]
                self._joystick(sw, sh, d, random.uniform(0.6, 1.4))
                idx += 1

            time.sleep(self.config.get("poll", 0.25))

    def _run_impostor(self, sw, sh):
        COLOR_KILL = ((0, 200, 200),  (15, 255, 200))
        COLOR_VENT = ((100, 60, 60),  (130, 255, 255))
        COLOR_SAB  = ((0, 150, 150),  (10, 255, 255))
        cooldown   = self.config.get("kill_cooldown", 30)
        last_kill  = 0.0
        in_vent    = False

        while not self._stop.is_set():
            frame = ADB.screenshot()
            if frame is None:
                time.sleep(1); continue

            if is_meeting(frame, sh):
                in_vent = False
                self.log("Meeting — waiting")
                time.sleep(6)
                slot = random.choice([int(sh*p) for p in [0.38,0.48,0.58,0.68]])
                ADB.tap(sw//2, slot)
                continue

            if in_vent:
                linger = random.uniform(2, 6)
                self.log(f"In vent — lingering {linger:.1f}s")
                time.sleep(linger)
                f2 = ADB.screenshot()
                if f2 is not None:
                    vp = find_color(f2, *COLOR_VENT)
                    if vp: ADB.tap(*vp)
                in_vent = False
                continue

            if time.time() - last_kill >= cooldown:
                kp = find_color(frame, *COLOR_KILL, min_area=500)
                if kp:
                    self.log(f"KILL @ {kp}")
                    ADB.tap(*kp)
                    last_kill = time.time()
                    if self.config.get("vent", True):
                        time.sleep(0.3)
                        f2 = ADB.screenshot()
                        if f2 is not None:
                            vp = find_color(f2, *COLOR_VENT)
                            if vp:
                                self.log(f"Venting @ {vp}")
                                ADB.tap(*vp)
                                in_vent = True
                    continue

            if self.config.get("sabotage", True) and random.random() < 0.04:
                self.log("Triggering sabotage")
                ADB.tap(int(sw*0.82), int(sh*0.78))
                time.sleep(0.4)
                f2 = ADB.screenshot()
                if f2 is not None:
                    sp = find_color(f2, *COLOR_SAB, min_area=400)
                    if sp: ADB.tap(*sp)

            d = random.choice(["up","down","left","right","ul","ur"])
            self._joystick(sw, sh, d, random.uniform(0.5, 1.8))
            time.sleep(self.config.get("poll", 0.25))

    def _run_antiafk(self, sw, sh):
        while not self._stop.is_set():
            interval = random.uniform(20, 38)
            self.log(f"Anti-AFK: next wiggle in {interval:.0f}s")
            self._stop.wait(interval)
            if self._stop.is_set(): break
            self._joystick(sw, sh, "left", 0.15)
            time.sleep(0.1)
            self._joystick(sw, sh, "right", 0.15)
            self.log("Anti-AFK wiggle sent")

    def _joystick(self, sw, sh, direction, duration):
        cx, cy = int(sw*0.18), int(sh*0.82)
        r = int(sw*0.07)
        off = {"up":(0,-r),"down":(0,r),"left":(-r,0),"right":(r,0),
               "ul":(-r//2,-r//2),"ur":(r//2,-r//2),
               "dl":(-r//2,r//2),"dr":(r//2,r//2)}
        dx, dy = off.get(direction, (0,0))
        ADB.swipe(cx, cy, cx+dx, cy+dy, 50)
        time.sleep(duration)
        ADB.swipe(cx+dx, cy+dy, cx, cy, 50)
        time.sleep(0.05)


# ─────────────────────────────────────────
# MAIN WINDOW
# ─────────────────────────────────────────

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Among Us Mobile Auto Suite")
        self.setMinimumSize(820, 620)
        self.worker: Optional[BotWorker] = None
        self._build_ui()
        self.setStyleSheet(STYLESHEET)
        self._refresh_devices()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(14)

        # ── LEFT PANEL ──────────────────────
        left = QVBoxLayout()
        left.setSpacing(12)

        # Header
        hdr = QVBoxLayout()
        title = QLabel("AMONG US")
        title.setObjectName("sectionTitle")
        sub = QLabel("MOBILE AUTOMATION SUITE  •  ADB BACKEND")
        sub.setObjectName("subtitle")
        hdr.addWidget(title)
        hdr.addWidget(sub)
        left.addLayout(hdr)

        # Status indicator
        status_row = QHBoxLayout()
        self.status_dot = QLabel("●")
        self.status_dot.setObjectName("statusDot")
        self.status_dot.setStyleSheet(f"color: {AMONG_MUTED};")
        self.status_label = QLabel("IDLE")
        self.status_label.setStyleSheet(f"color: {AMONG_MUTED}; font-weight: bold; font-size: 13px;")
        status_row.addWidget(self.status_dot)
        status_row.addWidget(self.status_label)
        status_row.addStretch()
        left.addLayout(status_row)

        # Device group
        dev_grp = QGroupBox("DEVICE")
        dev_layout = QHBoxLayout(dev_grp)
        self.device_combo = QComboBox()
        self.device_combo.currentTextChanged.connect(self._on_device_change)
        refresh_btn = QPushButton("↺ Refresh")
        refresh_btn.setObjectName("refreshBtn")
        refresh_btn.clicked.connect(self._refresh_devices)
        dev_layout.addWidget(self.device_combo)
        dev_layout.addWidget(refresh_btn)
        left.addWidget(dev_grp)

        # Mode group
        mode_grp = QGroupBox("MODE")
        mode_layout = QVBoxLayout(mode_grp)
        self.mode_combo = QComboBox()
        self.mode_combo.addItems([
            "🟢  Crewmate — Task Bot",
            "🔴  Impostor — Kill + Vent + Sabotage",
            "⏱   Anti-AFK Only"
        ])
        self.mode_combo.currentIndexChanged.connect(self._on_mode_change)
        mode_layout.addWidget(self.mode_combo)
        left.addWidget(mode_grp)

        # Impostor options
        self.imp_grp = QGroupBox("IMPOSTOR OPTIONS")
        imp_layout = QVBoxLayout(self.imp_grp)
        self.chk_vent = QCheckBox("Auto-Vent after kill")
        self.chk_vent.setChecked(True)
        self.chk_sab  = QCheckBox("Random Sabotage")
        self.chk_sab.setChecked(True)
        cd_row = QHBoxLayout()
        cd_row.addWidget(QLabel("Kill cooldown (s):"))
        self.spin_cd = QSpinBox()
        self.spin_cd.setRange(10, 60)
        self.spin_cd.setValue(30)
        cd_row.addWidget(self.spin_cd)
        cd_row.addStretch()
        imp_layout.addWidget(self.chk_vent)
        imp_layout.addWidget(self.chk_sab)
        imp_layout.addLayout(cd_row)
        left.addWidget(self.imp_grp)

        # Poll speed
        speed_grp = QGroupBox("SCAN SPEED")
        speed_layout = QVBoxLayout(speed_grp)
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setRange(1, 10)
        self.speed_slider.setValue(4)
        speed_row = QHBoxLayout()
        speed_row.addWidget(QLabel("Slow"))
        speed_row.addWidget(self.speed_slider)
        speed_row.addWidget(QLabel("Fast"))
        self.speed_val = QLabel("0.25s")
        self.speed_val.setStyleSheet(f"color:{AMONG_ACCENT}; font-weight:bold;")
        self.speed_slider.valueChanged.connect(self._on_speed_change)
        speed_layout.addLayout(speed_row)
        speed_layout.addWidget(self.speed_val)
        left.addWidget(speed_grp)

        left.addStretch()

        # Start / Stop
        btn_row = QHBoxLayout()
        self.start_btn = QPushButton("▶  START")
        self.start_btn.setObjectName("startBtn")
        self.start_btn.clicked.connect(self._start)
        self.stop_btn = QPushButton("■  STOP")
        self.stop_btn.setObjectName("stopBtn")
        self.stop_btn.clicked.connect(self._stop)
        self.stop_btn.setEnabled(False)
        btn_row.addWidget(self.start_btn)
        btn_row.addWidget(self.stop_btn)
        left.addLayout(btn_row)

        # ── RIGHT PANEL — Log ──────────────
        right = QVBoxLayout()
        log_grp = QGroupBox("ACTIVITY LOG")
        log_layout = QVBoxLayout(log_grp)
        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setMinimumWidth(340)
        clear_btn = QPushButton("Clear")
        clear_btn.setFixedWidth(70)
        clear_btn.clicked.connect(self.log_box.clear)
        log_layout.addWidget(self.log_box)
        log_layout.addWidget(clear_btn, alignment=Qt.AlignRight)
        right.addWidget(log_grp)

        root.addLayout(left, 40)
        root.addLayout(right, 60)

        # Status bar
        self.sb = QStatusBar()
        self.setStatusBar(self.sb)
        self.sb.showMessage("Ready — connect an Android device with USB debugging enabled")

        self._on_mode_change(0)

    # ── SLOTS ────────────────────────────

    def _refresh_devices(self):
        devices = ADB.list_devices()
        self.device_combo.clear()
        if devices:
            self.device_combo.addItems(devices)
            self.sb.showMessage(f"{len(devices)} device(s) found")
        else:
            self.device_combo.addItem("No devices — run: adb devices")
            self.sb.showMessage("No ADB devices detected")

    def _on_device_change(self, text):
        if text and "No devices" not in text:
            ADB.device_id = text
            self.sb.showMessage(f"Active device: {text}")

    def _on_mode_change(self, idx):
        self.imp_grp.setVisible(idx == 1)

    def _on_speed_change(self, val):
        poll = round(1.1 - val * 0.1, 2)
        self.speed_val.setText(f"{poll}s")

    @pyqtSlot(str)
    def _append_log(self, msg):
        self.log_box.append(msg)
        self.log_box.moveCursor(QTextCursor.End)

    @pyqtSlot(str, str)
    def _update_status(self, label, color):
        self.status_label.setText(label)
        self.status_label.setStyleSheet(f"color:{color}; font-weight:bold; font-size:13px;")
        self.status_dot.setStyleSheet(f"color:{color};")

    def _start(self):
        mode_map = {0: BotWorker.MODE_CREWMATE, 1: BotWorker.MODE_IMPOSTOR, 2: BotWorker.MODE_ANTIAFK}
        mode = mode_map[self.mode_combo.currentIndex()]
        poll = round(1.1 - self.speed_slider.value() * 0.1, 2)
        config = {
            "poll":          poll,
            "vent":          self.chk_vent.isChecked(),
            "sabotage":      self.chk_sab.isChecked(),
            "kill_cooldown": self.spin_cd.value(),
        }
        self.worker = BotWorker(mode, config)
        self.worker.log_signal.connect(self._append_log)
        self.worker.status_signal.connect(self._update_status)
        self.worker.finished.connect(self._on_worker_done)
        self.worker.start()
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self._append_log(f"▶ Started [{mode.upper()}] mode")

    def _stop(self):
        if self.worker:
            self.worker.stop()
        self.stop_btn.setEnabled(False)

    def _on_worker_done(self):
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)

    def closeEvent(self, event):
        if self.worker:
            self.worker.stop()
            self.worker.wait(2000)
        event.accept()


# ─────────────────────────────────────────
# ENTRY
# ─────────────────────────────────────────

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("Among Us Auto Suite")
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())
