#!/usr/bin/env python3

import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QStackedWidget, QGraphicsDropShadowEffect,
    QSpacerItem, QSizePolicy
)
from PyQt5.QtGui import QPixmap, QImage, QColor
from PyQt5.QtCore import Qt, QTimer, pyqtSlot, QPropertyAnimation, QPoint

# Pastikan Anda sudah menginstal: pip install PyQt5 opencv-python pyzbar
# Dan di sistem (Ubuntu/Debian): sudo apt-get install libzbar0
import cv2
from pyzbar.pyzbar import decode

class PolicyKitCard(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_base_window()
        self.setup_views_and_animations()
        self.finalize_layout()

    def setup_base_window(self):
        """Mengatur properti dasar window dan widget utama."""
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(30)
        shadow.setXOffset(0)
        shadow.setYOffset(0)
        shadow.setColor(QColor(0, 0, 0, 120))

        self.main_widget = QWidget()
        self.main_widget.setObjectName("main_widget")
        self.main_widget.setGraphicsEffect(shadow)
        self.setStyleSheet(self.get_stylesheet())

    def setup_views_and_animations(self):
        """Mempersiapkan semua view dan animasi yang dibutuhkan."""
        self.stacked_widget = QStackedWidget()
        self.password_view = QWidget()
        self.qr_view = QWidget()

        # Penting: Buat widget input password terlebih dahulu
        self.password_input = QLineEdit()
        
        # Sekarang buat view yang menggunakan widget tersebut
        self.setup_password_view()
        self.setup_qr_view()

        self.stacked_widget.addWidget(self.password_view)
        self.stacked_widget.addWidget(self.qr_view)
        
        # Inisialisasi animasi goyang (shake)
        self.animation_shake = QPropertyAnimation(self.password_input, b"pos")
        self.animation_shake.setDuration(400)
        pos = self.password_input.pos()
        self.animation_shake.setKeyValueAt(0.0, pos)
        self.animation_shake.setKeyValueAt(0.1, QPoint(pos.x() - 10, pos.y()))
        self.animation_shake.setKeyValueAt(0.3, QPoint(pos.x() + 10, pos.y()))
        self.animation_shake.setKeyValueAt(0.5, QPoint(pos.x() - 5, pos.y()))
        self.animation_shake.setKeyValueAt(0.7, QPoint(pos.x() + 5, pos.y()))
        self.animation_shake.setEndValue(pos)


    def finalize_layout(self):
        """Menyusun layout utama dan menampilkan view awal."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.main_widget)
        
        container_layout = QVBoxLayout(self.main_widget)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.addWidget(self.stacked_widget)
        
        self.switch_to_password_view()

    def get_stylesheet(self):
        # Stylesheet tidak berubah, tetap sama seperti sebelumnya
        return """
            #main_widget { background-color: #2C2F33; border-radius: 12px; }
            QLabel { font-family: sans-serif; color: #FFFFFF; }
            #title_label { font-size: 18px; font-weight: bold; }
            #username_label { font-size: 14px; color: #B9BBBE; }
            QLineEdit { background-color: #23272A; border: 1px solid #1A1C1E; border-radius: 8px; padding: 10px; font-size: 14px; color: #FFFFFF; }
            QLineEdit:focus { border-color: #5865F2; }
            QPushButton#primary_button { background-color: #5865F2; color: white; font-size: 14px; font-weight: bold; border: none; border-radius: 8px; padding: 10px; min-width: 120px; }
            QPushButton#primary_button:hover { background-color: #4752C4; }
            QPushButton#secondary_button { background-color: #40444B; color: #FFFFFF; border: none; border-radius: 8px; padding: 10px; }
            QPushButton#secondary_button:hover { background-color: #4F545C; }
            QPushButton#close_button { background-color: transparent; color: #B9BBBE; border: none; font-size: 18px; font-weight: bold; max-width: 30px; }
            QPushButton#close_button:hover { color: #FFFFFF; }
        """

    def create_close_button_layout(self):
        close_button_layout = QHBoxLayout()
        spacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        close_button = QPushButton("✕")
        close_button.setObjectName("close_button")
        close_button.setCursor(Qt.PointingHandCursor)
        close_button.clicked.connect(self.close)
        
        close_button_layout.addSpacerItem(spacer)
        close_button_layout.addWidget(close_button)
        return close_button_layout

    def setup_password_view(self):
        layout = QVBoxLayout(self.password_view)
        layout.setContentsMargins(25, 15, 25, 25)
        layout.setSpacing(15)

        layout.addLayout(self.create_close_button_layout())

        title_label = QLabel("Otentikasi Dibutuhkan")
        title_label.setObjectName("title_label")
        title_label.setAlignment(Qt.AlignCenter)

        username = os.getenv("USER") or "pengguna"
        username_label = QLabel(f"Masuk sebagai: <b>{username}</b>")
        username_label.setObjectName("username_label")
        username_label.setAlignment(Qt.AlignCenter)

        self.password_input.setPlaceholderText("Kata Sandi")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.returnPressed.connect(self.authenticate)

        scan_qr_button = QPushButton("Pindai Kode QR")
        scan_qr_button.setObjectName("secondary_button")
        scan_qr_button.clicked.connect(self.switch_to_qr_view)
        
        auth_button = QPushButton("Otentikasi")
        auth_button.setObjectName("primary_button")
        auth_button.clicked.connect(self.authenticate)
        
        button_layout = QHBoxLayout()
        button_layout.addWidget(scan_qr_button)
        button_layout.addStretch()
        button_layout.addWidget(auth_button)
        
        layout.addWidget(title_label)
        layout.addWidget(username_label)
        layout.addSpacing(10)
        layout.addWidget(self.password_input)
        layout.addLayout(button_layout)
        
    def setup_qr_view(self):
        layout = QVBoxLayout(self.qr_view)
        layout.setContentsMargins(25, 15, 25, 25)
        
        layout.addLayout(self.create_close_button_layout())

        title_label = QLabel("Arahkan ke Kode QR")
        title_label.setObjectName("title_label")
        title_label.setAlignment(Qt.AlignCenter)

        self.camera_label = QLabel("Menyalakan Kamera...")
        self.camera_label.setAlignment(Qt.AlignCenter)
        self.camera_label.setStyleSheet("background-color: #1A1C1E; border-radius: 8px;")
        self.camera_label.setMinimumHeight(200)

        back_button = QPushButton("Kembali ke Kata Sandi")
        back_button.setObjectName("secondary_button")
        back_button.clicked.connect(self.switch_to_password_view)
        
        layout.addWidget(title_label)
        layout.addWidget(self.camera_label, 1)
        layout.addSpacing(10)
        layout.addWidget(back_button, alignment=Qt.AlignCenter)

        self.capture = None
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
    
    @pyqtSlot()
    def switch_to_password_view(self):
        """Beralih ke tampilan password."""
        self.resize_window(420, 280)
        self.stacked_widget.setCurrentWidget(self.password_view)
        if hasattr(self, 'capture') and self.capture and self.capture.isOpened():
            self.timer.stop()
            self.capture.release()
            self.capture = None
        self.password_input.setFocus()

    @pyqtSlot()
    def switch_to_qr_view(self):
        """Beralih ke tampilan QR dan mencari kamera."""
        self.resize_window(420, 420)
        self.stacked_widget.setCurrentWidget(self.qr_view)
        
        if not (hasattr(self, 'capture') and self.capture and self.capture.isOpened()):
            # Mencoba beberapa indeks kamera
            for i in range(4):
                self.capture = cv2.VideoCapture(i)
                if self.capture.isOpened():
                    break
            else: # Jika loop selesai tanpa break
                self.camera_label.setText("Error: Kamera tidak ditemukan.")
                self.capture = None
                return

        self.timer.start(20)

    def update_frame(self):
        if not self.capture or not self.capture.isOpened(): return
        
        ret, frame = self.capture.read()
        if ret:
            frame = cv2.flip(frame, 1)
            decoded_objects = decode(frame)
            
            if decoded_objects:
                password = decoded_objects[0].data.decode('utf-8')
                self.password_input.setText(password)
                self.switch_to_password_view()
                self.authenticate()
            else:
                rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb_image.shape
                qt_image = QImage(rgb_image.data, w, h, ch * w, QImage.Format_RGB888)
                self.camera_label.setPixmap(QPixmap.fromImage(qt_image).scaled(
                    self.camera_label.width(), self.camera_label.height(), Qt.KeepAspectRatio))

    @pyqtSlot()
    def authenticate(self):
        password = self.password_input.text()
        if password:
            print(f"Otentikasi dengan password: {password}")
            # Di sini Anda akan mengintegrasikan logika PolicyKit
            self.close() 
        else:
            self.animation_shake.start()

    def resize_window(self, width, height):
        self.setFixedSize(width, height)
        self.main_widget.setFixedSize(width, height)

    def closeEvent(self, event):
        if hasattr(self, 'capture') and self.capture and self.capture.isOpened():
            self.capture.release()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PolicyKitCard()
    window.show()
    sys.exit(app.exec_())