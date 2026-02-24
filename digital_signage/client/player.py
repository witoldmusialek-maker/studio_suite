"""
Content playback for display client.
"""
from pathlib import Path
from typing import Optional
import sys

try:
    from PyQt6.QtCore import Qt
    from PyQt6.QtGui import QPixmap, QTransform
    from PyQt6.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget
    PYQT6_AVAILABLE = True
except ImportError:
    PYQT6_AVAILABLE = False
    print("PyQt6 nie jest dostepny - tryb testowy")

import config


class ContentPlayer:
    """Display content player."""

    def __init__(self):
        self.app: Optional[QApplication] = None
        self.window: Optional[QWidget] = None
        self.label: Optional[QLabel] = None
        self.current_content_path: Optional[Path] = None
        self.vlc_player = None

    def init_display(self) -> None:
        if not PYQT6_AVAILABLE:
            print("PyQt6 nie dostepny - tryb testowy")
            return

        self.app = QApplication.instance() or QApplication(sys.argv)
        self.window = QWidget()
        self.window.setWindowTitle("Digital Signage")
        self.window.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowFullscreenButtonHint
        )

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.label = QLabel()
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet("background-color: black; color: white; font-size: 28px;")
        self.label.setText("Polaczono z serwerem\nOczekiwanie na tresc...")
        layout.addWidget(self.label)

        self.window.setLayout(layout)
        self.window.showFullScreen()
        self.pump_events()

    def pump_events(self) -> None:
        if PYQT6_AVAILABLE and self.app:
            self.app.processEvents()

    def display_message(self, message: str) -> None:
        if not PYQT6_AVAILABLE:
            print(message)
            return
        if not self.label:
            return
        self.label.setPixmap(QPixmap())
        self.label.setText(message)
        self.pump_events()

    def display_image(self, image_path: Path) -> None:
        if not PYQT6_AVAILABLE:
            print(f"Wyswietlanie obrazu: {image_path}")
            return
        if not self.label:
            return

        pixmap = QPixmap(str(image_path))
        if pixmap.isNull():
            self.display_message("Nie mozna wczytac pliku obrazu")
            return

        if config.ORIENTATION != 0:
            transform = QTransform().rotate(config.ORIENTATION)
            pixmap = pixmap.transformed(transform)

        scaled_pixmap = pixmap.scaled(
            config.RESOLUTION_WIDTH,
            config.RESOLUTION_HEIGHT,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )

        self.label.setText("")
        self.label.setPixmap(scaled_pixmap)
        self.current_content_path = image_path
        self.pump_events()

    def display_pdf(self, pdf_path: Path) -> None:
        try:
            from pdf2image import convert_from_path

            images = convert_from_path(str(pdf_path), first_page=1, last_page=1)
            if images:
                temp_image = pdf_path.parent / f"{pdf_path.stem}_temp.jpg"
                images[0].save(temp_image, "JPEG")
                self.display_image(temp_image)
        except Exception as e:
            print(f"Blad wyswietlania PDF: {e}")

    def display_excel(self, excel_path: Path) -> None:
        try:
            import openpyxl
            from PIL import Image, ImageDraw

            workbook = openpyxl.load_workbook(excel_path)
            sheet = workbook.active

            img = Image.new("RGB", (config.RESOLUTION_WIDTH, config.RESOLUTION_HEIGHT), "white")
            draw = ImageDraw.Draw(img)

            y = 50
            for row in sheet.iter_rows(max_row=20, values_only=True):
                text = " | ".join(str(cell) if cell else "" for cell in row)
                draw.text((50, y), text, fill="black")
                y += 30
                if y > config.RESOLUTION_HEIGHT - 50:
                    break

            temp_image = excel_path.parent / f"{excel_path.stem}_temp.jpg"
            img.save(temp_image, "JPEG")
            self.display_image(temp_image)
        except Exception as e:
            print(f"Blad wyswietlania Excel: {e}")

    def display_video(self, video_path: Path) -> None:
        if not PYQT6_AVAILABLE:
            print(f"Odtwarzanie video: {video_path}")
            return

        try:
            import vlc

            instance = vlc.Instance()
            player = instance.media_player_new()
            media = instance.media_new(str(video_path))
            player.set_media(media)

            if self.window:
                try:
                    if sys.platform == "win32":
                        player.set_hwnd(int(self.window.winId()))
                    else:
                        player.set_xwindow(int(self.window.winId()))
                except Exception:
                    pass

            self.vlc_player = player
            player.play()
            self.current_content_path = video_path
            self.pump_events()
        except Exception as e:
            print(f"Blad odtwarzania video: {e}")

    def run(self) -> None:
        if PYQT6_AVAILABLE and self.app:
            sys.exit(self.app.exec())
        print("Aplikacja w trybie testowym - brak PyQt6")
