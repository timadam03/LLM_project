import sys
from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch


def md_to_plaintext(md_text: str) -> str:
    """
    Very lightweight Markdown-to-plain-text cleaning:
    - Strips leading '#' from headings
    - Removes '**' used for bold
    """
    lines = []
    for line in md_text.splitlines():
        stripped = line.lstrip()
        # Remove leading markdown heading markers
        while stripped.startswith("#"):
            stripped = stripped[1:].lstrip()
        # Remove bold markers
        stripped = stripped.replace("**", "")
        lines.append(stripped)
    return "\n".join(lines)


def write_pdf_from_text(text: str, pdf_path: Path) -> None:
    pdf_path.parent.mkdir(parents=True, exist_ok=True)

    c = canvas.Canvas(str(pdf_path), pagesize=letter)
    width, height = letter

    x_margin = 1 * inch
    y_margin = 1 * inch
    line_height = 12

    y = height - y_margin

    for line in text.splitlines():
        # Basic line wrapping: split long lines into chunks
        while len(line) > 90:
            chunk = line[:90]
            line = line[90:]
            c.drawString(x_margin, y, chunk)
            y -= line_height
            if y < y_margin:
                c.showPage()
                y = height - y_margin

        c.drawString(x_margin, y, line)
        y -= line_height
        if y < y_margin:
            c.showPage()
            y = height - y_margin

    c.save()


def main():
    if len(sys.argv) < 3:
        print("Usage: python md_to_pdf.py <input_md> <output_pdf>")
        sys.exit(1)

    md_path = Path(sys.argv[1])
    pdf_path = Path(sys.argv[2])

    if not md_path.exists():
        print(f"Markdown file not found: {md_path}")
        sys.exit(1)

    md_text = md_path.read_text(encoding="utf-8")
    plain_text = md_to_plaintext(md_text)
    write_pdf_from_text(plain_text, pdf_path)
    print(f"Wrote PDF to {pdf_path}")


if __name__ == "__main__":
    main()

