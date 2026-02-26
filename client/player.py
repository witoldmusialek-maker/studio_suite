"""
Odtwarzanie treĹ›ci na wyĹ›wietlaczu
"""
from pathlib import Path
from typing import Optional
from PIL import Image
import sys

try:
    from PyQt6.QtWidgets import QApplication, QLabel, QWidget
    from PyQt6.QtCore import Qt, QTimer
    from PyQt6.QtGui import QPixmap, QTransform
    PYQT6_AVAILABLE = True
except ImportError:
    PYQT6_AVAILABLE = False
    print("PyQt6 nie jest dostÄ™pny - tryb testowy")

import config


class ContentPlayer:
    """Odtwarzacz treĹ›ci"""

    def __init__(self):
        self.app: Optional[QApplication] = None
        self.window: Optional[QWidget] = None
        self.label: Optional[QLabel] = None
        self.current_content_path: Optional[Path] = None

    def init_display(self):
        """Inicjalizacja wyĹ›wietlacza"""
        if not PYQT6_AVAILABLE:
            print("PyQt6 nie dostÄ™pny - tryb testowy")
            return

        self.app = QApplication(sys.argv)
        self.window = QWidget()
        self.window.setWindowTitle("Studio Suite")
        self.window.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowFullscreenButtonHint
        )
        self.window.showFullScreen()

        from PyQt6.QtWidgets import QVBoxLayout
        layout = QVBoxLayout()
        self.label = QLabel()
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setScaledContents(True)
        layout.addWidget(self.label)
        self.window.setLayout(layout)

    def display_image(self, image_path: Path):
        """WyĹ›wietlenie obrazu"""
        if not PYQT6_AVAILABLE:
            print(f"WyĹ›wietlanie obrazu: {image_path}")
            return

        if not self.label:
            return

        pixmap = QPixmap(str(image_path))
        
        # Rotacja jeĹ›li potrzeba
        if config.ORIENTATION != 0:
            transform = QTransform().rotate(config.ORIENTATION)
            pixmap = pixmap.transformed(transform)

        # Skalowanie do rozdzielczoĹ›ci ekranu
        scaled_pixmap = pixmap.scaled(
            config.RESOLUTION_WIDTH,
            config.RESOLUTION_HEIGHT,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )

        self.label.setPixmap(scaled_pixmap)
        self.current_content_path = image_path

    def display_pdf(self, pdf_path: Path):
        """WyĹ›wietlenie PDF (pierwsza strona jako obraz)"""
        try:
            from pdf2image import convert_from_path
            images = convert_from_path(str(pdf_path), first_page=1, last_page=1)
            if images:
                # Zapisanie jako tymczasowy obraz
                temp_image = pdf_path.parent / f"{pdf_path.stem}_temp.jpg"
                images[0].save(temp_image, "JPEG")
                self.display_image(temp_image)
        except Exception as e:
            print(f"BĹ‚Ä…d wyĹ›wietlania PDF: {e}")

    def display_excel(self, excel_path: Path):
        """WyĹ›wietlenie Excel (renderowanie do obrazu)"""
        try:
            import openpyxl
            from PIL import Image, ImageDraw, ImageFont

            workbook = openpyxl.load_workbook(excel_path)
            sheet = workbook.active

            # Renderowanie do obrazu (uproszczone)
            img = Image.new("RGB", (config.RESOLUTION_WIDTH, config.RESOLUTION_HEIGHT), "white")
            draw = ImageDraw.Draw(img)

            # Renderowanie danych (uproszczone - tylko pierwsze wiersze)
            y = 50
            for row in sheet.iter_rows(max_row=20, values_only=True):
                text = " | ".join(str(cell) if cell else "" for cell in row)
                draw.text((50, y), text, fill="black")
                y += 30
                if y > config.RESOLUTION_HEIGHT - 50:
                    break

            # Zapisanie jako tymczasowy obraz
            temp_image = excel_path.parent / f"{excel_path.stem}_temp.jpg"
            img.save(temp_image, "JPEG")
            self.display_image(temp_image)
        except Exception as e:
            print(f"BĹ‚Ä…d wyĹ›wietlania Excel: {e}")

    def display_video(self, video_path: Path):
        """WyĹ›wietlenie video"""
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
                    # PyQt6 - uĹĽyj winId() dla Windows lub windowId() dla Linux
                    if sys.platform == "win32":
                        player.set_hwnd(int(self.window.winId()))
                    else:
                        # Linux - uĹĽyj X11 window ID
                        player.set_xwindow(int(self.window.winId()))
                except:
                    # Fallback - odtwarzanie bez okna
                    pass
            
            player.play()
            self.current_content_path = video_path
        except Exception as e:
            print(f"BĹ‚Ä…d odtwarzania video: {e}")

    def run(self):
        """Uruchomienie aplikacji"""
        if PYQT6_AVAILABLE and self.app:
            sys.exit(self.app.exec())
        else:
            print("Aplikacja w trybie testowym - brak PyQt6")


