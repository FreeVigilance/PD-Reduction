"""
Обработчик PDF-документов.
"""

from .base import Document
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4


class PdfProcessor(Document):
    """
    Класс для извлечения текста из PDF-документов и создания редактированной копии.
    """

    def get_text(self) -> str:
        """
        Извлекает текст из PDF-файла.

        Returns:
            str: Извлечённый текст.
        """
        from PyPDF2 import PdfReader

        reader_now = PdfReader(self.file_path)
        text_now = ""

        for page_now in reader_now.pages:
            text_now += page_now.extract_text() or ""

        self.text_content = text_now
        return self.text_content

    def create_redacted_copy(self, reduced_text: str) -> None:
        """
        Создаёт редактированную копию PDF-документа с заменённым текстом.

        Args:
            reduced_text (str): Текст после анонимизации.
        """
        redacted_path_now = Path(self.file_path).with_name(
            Path(self.file_path).stem + "_redacted.pdf"
        )

        canvas_now = canvas.Canvas(str(redacted_path_now), pagesize=A4)
        page_width, page_height = A4
        y_pos_now = page_height - 40

        lines_now = reduced_text.split("\n")

        for line_now in lines_now:
            canvas_now.drawString(40, y_pos_now, line_now.strip())
            y_pos_now -= 15

            if y_pos_now < 40:
                canvas_now.showPage()
                y_pos_now = page_height - 40

        canvas_now.save()
        self.metadata['redacted_path'] = str(redacted_path_now)
