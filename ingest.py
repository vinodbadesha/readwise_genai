import pymupdf as fitz

def load_pdf(path):
    doc = fitz.open(path)
    chunks = []

    for page_number, page in enumerate(doc, start=1):
        text = page.get_text()
        if not text.strip():
            continue
        start = 0
        while start < len(text):
            piece = text[start:start + 1000]
            chunks.append({"text": piece, "page": page_number, "source": path})
            start += 900
    return chunks

if __name__ == "__main__":
    result = load_pdf("sample.pdf")
    print("Total Chunks: ", len(result))
    for c in result[:3]:
        print(c["page"], c["text"][:1000])
        print("-----")
