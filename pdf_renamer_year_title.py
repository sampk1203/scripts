import os
import re

import fitz  # PyMuPDF


def sanitize_filename(text):
    text = re.sub(r"\s+", " ", text).strip()
    text = text.lower()
    text = text.replace(" ", "_")
    text = re.sub(r"[^a-z0-9_-]", "", text)
    text = re.sub(r"_+", "_", text)
    text = text.strip("_")
    return text[:150] if text else "untitled"


def extract_year(text):
    years = re.findall(r"\b(19\d{2}|20\d{2})\b", text)
    return years[0] if years else None


def looks_like_id(title):
    if not title:
        return True
    title = title.strip()
    if len(title) < 15:
        return True
    if re.fullmatch(r"[a-z0-9]+", title):
        return True
    if title.count(" ") < 2:
        return True
    return False


def extract_title_from_text(text):
    lines = [l.strip() for l in text.split("\n") if len(l.strip()) > 25]
    if not lines:
        return "UnknownTitle"
    title_lines = []
    for line in lines:
        if re.search(r"(abstract|introduction|keywords)", line, re.I):
            break
        title_lines.append(line)
        if len(" ".join(title_lines)) > 60:
            break
    return " ".join(title_lines)


def get_title_and_year(pdf_path):
    doc = fitz.open(pdf_path)
    metadata = doc.metadata
    meta_title = metadata.get("title", "")
    year = None

    if metadata.get("creationDate"):
        match = re.search(r"(19\d{2}|20\d{2})", metadata["creationDate"])
        if match:
            year = match.group(1)

    first_page_text = doc[0].get_text()
    doc.close()

    if looks_like_id(meta_title):
        title = extract_title_from_text(first_page_text)
    else:
        title = meta_title

    if not year:
        year = extract_year(first_page_text)

    return sanitize_filename(title), year or "unknownyear"


def get_unique_filename(base_name):
    name, ext = os.path.splitext(base_name)
    counter = 1
    new_name = base_name
    while os.path.exists(new_name):
        new_name = f"{name}_{counter}{ext}"
        counter += 1
    return new_name


def rename_preserving_mtime(old_name, new_name):
    stat_info = os.stat(old_name)
    atime = stat_info.st_atime
    mtime = stat_info.st_mtime
    os.rename(old_name, new_name)
    os.utime(new_name, (atime, mtime))


def main():
    for filename in os.listdir("."):
        if not filename.lower().endswith(".pdf"):
            continue
        try:
            title, year = get_title_and_year(filename)
            new_name = f"{year}_{title}.pdf"
            new_name = sanitize_filename(new_name.replace(".pdf", "")) + ".pdf"
            new_name = get_unique_filename(new_name)
            if filename != new_name:
                rename_preserving_mtime(filename, new_name)
                print(f"Renamed: {filename} -> {new_name}")
        except Exception as e:
            print(f"Failed on {filename}: {e}")


if __name__ == "__main__":
    main()
