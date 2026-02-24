"""
Odtwarzanie treści na wyświetlaczu.
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
    print("PyQt6 nie jest dostępny - tryb testowy")

import config


class ContentPlayer:
    """Odtwarzacz treści wyświetlacza."""

    def __init__(self):
        self.app: Optional[QApplication] = None
        self.window: Optional[QWidget] = None
        self.label: Optional[QLabel] = None
        self.status_dot: Optional[QLabel] = None
        self.current_content_path: Optional[Path] = None
        self.vlc_player = None

    def init_display(self) -> None:
        if not PYQT6_AVAILABLE:
            print("PyQt6 nie jest dostępny - tryb testowy")
            return

        self.app = QApplication.instance() or QApplication(sys.argv)
        self.window = QWidget()
        self.window.setWindowTitle("Digital Signage")
        self.window.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowFullscreenButtonHint
        )
        self.window.setCursor(Qt.CursorShape.BlankCursor)
        self.app.setOverrideCursor(Qt.CursorShape.BlankCursor)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        self.label = QLabel()
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet("background-color: black; color: white; font-size: 28px;")
        self.label.setText("Połączono z serwerem\nOczekiwanie na treść...")
        layout.addWidget(self.label)

        self.window.setLayout(layout)

        self.status_dot = QLabel(self.window)
        self.status_dot.setFixedSize(14, 14)
        self.status_dot.setStyleSheet("background-color: #2e7d32; border-radius: 7px;")
        self.status_dot.raise_()

        self.window.showFullScreen()
        self._position_status_dot()
        self.pump_events()

    def _position_status_dot(self) -> None:
        if not self.window or not self.status_dot:
            return
        margin = 12
        x = max(0, self.window.width() - self.status_dot.width() - margin)
        y = max(0, self.window.height() - self.status_dot.height() - margin)
        self.status_dot.move(x, y)

    def set_connection_state(self, state: str) -> None:
        if not self.status_dot:
            return
        color = {
            "connected": "#2e7d32",
            "connecting": "#f9a825",
            "error": "#c62828",
        }.get(state, "#757575")
        self.status_dot.setStyleSheet(f"background-color: {color}; border-radius: 7px;")

    def pump_events(self) -> None:
        if PYQT6_AVAILABLE and self.app:
            self._position_status_dot()
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

    def display_image(self, image_path: Path) -> bool:
        if not PYQT6_AVAILABLE:
            print(f"Wyświetlanie obrazu: {image_path}")
            return True
        if not self.label:
            return False

        pixmap = QPixmap(str(image_path))
        if pixmap.isNull():
            self.display_message("Nie można wczytać pliku obrazu")
            return False

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
        return True

    def display_pdf(self, pdf_path: Path) -> bool:
        try:
            from pdf2image import convert_from_path

            images = convert_from_path(str(pdf_path), first_page=1, last_page=1)
            if images:
                temp_image = pdf_path.parent / f"{pdf_path.stem}_temp.jpg"
                images[0].save(temp_image, "JPEG")
                return self.display_image(temp_image)
            self.display_message("Brak stron PDF do wyświetlenia")
            return False
        except Exception as e:
            print(f"Błąd wyświetlania PDF: {e}")
            self.display_message("Błąd renderowania PDF")
            return False

    def display_excel(self, excel_path: Path) -> bool:
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
            return self.display_image(temp_image)
        except Exception as e:
            print(f"Błąd wyświetlania Excel: {e}")
            self.display_message("Błąd renderowania pliku Excel")
            return False

    def display_video(self, video_path: Path) -> bool:
        if not PYQT6_AVAILABLE:
            print(f"Odtwarzanie wideo: {video_path}")
            return True

        try:
            import vlc
        except Exception as e:
            print(f"Błąd importu VLC: {e}")
            self.display_message("Brak biblioteki VLC do odtwarzania wideo")
            return False

        try:
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
            rc = player.play()
            if rc == -1:
                self.display_message("Nie udało się uruchomić odtwarzania wideo")
                return False

            self.current_content_path = video_path
            self.pump_events()
            return True
        except Exception as e:
            print(f"Błąd odtwarzania wideo: {e}")
            self.display_message("Błąd odtwarzania wideo")
            return False

    def run(self) -> None:
        if PYQT6_AVAILABLE and self.app:
            sys.exit(self.app.exec())
        print("Aplikacja w trybie testowym - brak PyQt6")
