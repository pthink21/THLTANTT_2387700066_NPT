"""Check README encoding, normalization, and relative image links."""
from pathlib import Path
import re
import unicodedata

readme = Path(__file__).parents[1] / "README.md"
text = readme.read_text(encoding="utf-8")
assert "Buổi 5" in text and "Nguyễn Phúc Thịnh" in text
assert "�" not in text
assert not any(marker in text for marker in ("Ã", "â€”", "á»", "Æ°"))
assert unicodedata.normalize("NFC", text) == text
images = re.findall(r"!\[[^\]]*\]\(([^)]+\.png)\)", text)
missing = [name for name in images if not (readme.parent / name).is_file()]
assert not missing, f"missing images: {missing}"
print(f"UTF-8/NFC OK; {len(images)} README image links exist; no mojibake markers")
