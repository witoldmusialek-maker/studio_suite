"""
Odtwarzanie treści na wyświetlaczu.
"""
from pathlib import Path
from typing import Optional
import sys

try:
    from PyQt6.QtCore import Qt, QUrl
    from PyQt6.QtGui import QPixmap, QTransform
    from PyQt6.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget
    PYQT6_AVAILABLE = True
except ImportError:
    PYQT6_AVAILABLE = False
    print("PyQt6 nie jest dostępny - tryb testowy")

if PYQT6_AVAILABLE:
    try:
        from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer
        from PyQt6.QtMultimediaWidgets import QVideoWidget
        QTMULTIMEDIA_AVAILABLE = True
    except ImportError:
        QTMULTIMEDIA_AVAILABLE = False
else:
    QTMULTIMEDIA_AVAILABLE = False

import config


class ContentPlayer:
    """Odtwarzacz treści wyświetlacza."""

    def __init__(self):
        self.app: Optional[QApplication] = None
        self.window: Optional[QWidget] = None
        self.label: Optional[QLabel] = None
        self.video_widget: Optional[QVideoWidget] = None
        self.media_player: Optional[QMediaPlayer] = None
        self.audio_output: Optional[QAudioOutput] = None
        self.status_dot: Optional[QLabel] = None
        self.current_content_path: Optional[Path] = None

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

        if QTMULTIMEDIA_AVAILABLE:
            self.video_widget = QVideoWidget()
            self.video_widget.setStyleSheet("background-color: black;")
            self.video_widget.hide()
            self.video_widget.setCursor(Qt.CursorShape.BlankCursor)
            layout.addWidget(self.video_widget)

            self.audio_output = QAudioOutput()
            self.media_player = QMediaPlayer()
            self.media_player.setAudioOutput(self.audio_output)
            self.media_player.setVideoOutput(self.video_widget)
            self.media_player.mediaStatusChanged.connect(self._on_media_status_changed)

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

    def _show_label(self) -> None:
        if self.label:
            self.label.show()
        if self.video_widget:
            self.video_widget.hide()

    def _show_video(self) -> None:
        if self.label:
            self.label.hide()
        if self.video_widget:
            self.video_widget.show()

    def _stop_video(self) -> None:
        if self.media_player:
            try:
                self.media_player.stop()
            except Exception:
                pass

    def _on_media_status_changed(self, status) -> None:
        if not self.media_player:
            return
        # Zapętlenie wideo bez użycia VLC.
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.media_player.setPosition(0)
            self.media_player.play()

    def display_message(self, message: str) -> None:
        if not PYQT6_AVAILABLE:
            print(message)
            return
        if not self.label:
            return
        self._stop_video()
        self._show_label()
        self.label.setPixmap(QPixmap())
        self.label.setText(message)
        self.pump_events()

    def display_image(self, image_path: Path) -> bool:
        if not PYQT6_AVAILABLE:
            print(f"Wyświetlanie obrazu: {image_path}")
            return True
        if not self.label:
            return False

        self._stop_video()
        self._show_label()
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

        if not QTMULTIMEDIA_AVAILABLE or not self.media_player or not self.video_widget:
            self.display_message("Brak modułu multimediów PyQt6 (QMediaPlayer)")
            return False

        try:
            self._show_video()
            self.media_player.stop()
            self.media_player.setSource(QUrl.fromLocalFile(str(video_path.resolve())))
            self.media_player.play()
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
