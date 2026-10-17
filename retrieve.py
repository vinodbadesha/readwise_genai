import numpy as np
from sentence_transformers import SentenceTransformer
from ingest import load_pdf

model = SentenceTransformer("all-MiniLM-L6-v2")

def build_index(chunks):
    texts = [c["text"] for c in chunks]
    return model.encode(texts, normalize_embeddings=True)

def search(question, chunks, vectors, k=4):
    q_vector = model.encode([question], normalize_embeddings=True)[0]
    scores = vectors @ q_vector
    sorted_indices = np.argsort(scores)
    best_indices = sorted_indices[::-1][:k]

    results = []

    for i in best_indices:
        results.append(chunks[i])
    return results

if __name__ == "__main__":
    chunks = load_pdf("sample.pdf")
    vectors = build_index(chunks)
    question = input("Ask something about PDF: ")
    for c in search(question, chunks, vectors):
        print("page", c["page"], ":", c["text"][:300])
        print("-----")