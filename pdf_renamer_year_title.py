import fitz  # PyMuPDF
import os
import re

def sanitize_filename(text):
    text = re.sub(r'[\\/*?:"<>|]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text[:180]

def extract_year(text):
    years = re.findall(r'\b(19\d{2}|20\d{2})\b', text)
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
    lines = [
        l.strip()
        for l in text.split("\n")
        if len(l.strip()) > 25
    ]

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
        match = re.search(r'(19\d{2}|20\d{2})', metadata["creationDate"])
        if match:
            year = match.group(1)

    first_page_text = doc[0].get_text()
    doc.close()

    # Determine title source
    if looks_like_id(meta_title):
        title = extract_title_from_text(first_page_text)
    else:
        title = meta_title

    if not year:
        year = extract_year(first_page_text)

    return sanitize_filename(title), year or "UnknownYear"

def main():
    for filename in os.listdir("."):
        if not filename.lower().endswith(".pdf"):
            continue

        try:
            title, year = get_title_and_year(filename)
            new_name = f"{year}_{title}.pdf"

            if filename != new_name:
                os.rename(filename, new_name)
                print(f"Renamed: {filename} -> {new_name}")

        except Exception as e:
            print(f"Failed on {filename}: {e}")

if __name__ == "__main__":
    main()
