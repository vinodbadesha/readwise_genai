import os, shutil
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from ingest import load_pdf
from retrieve import build_index
from answer import answer, summarize_document, ask_llm
from csv_insights import summarize_csv, charts, get_insights

app = FastAPI()
os.makedirs("uploads", exist_ok=True)
os.makedirs("charts", exist_ok=True)
state = {"kind": None, "chunks": None, "vectors": None, "df": None, "summary": None}

@app.post("/upload")
def upload(file: UploadFile = File(...)):
    path = f"uploads/{file.filename}"
    with open(path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    name = file.filename.lower()
    if name.endswith(".pdf"):
        state["kind"] = "pdf"
        state["chunks"] = load_pdf(path)
        state["vectors"] = build_index(state["chunks"])
        return {"type": "pdf", "chunks": len(state["chunks"]),
                "summary": summarize_document(state["chunks"])}
    if name.endswith(".csv"):
        df, stats = summarize_csv(path)
        state["kind"] = "csv"
        state["df"], state["summary"] = df, stats
        paths = charts(df)
        return {"type": "csv", "rows": len(df),
                "insights": get_insights(stats),
                "charts": ["/" + p for p in paths]}
    return {"error": "Only PDF and CSV files are supported"}

@app.post("/ask")
def ask(question: str = Form(...)):
    if state["kind"] == "pdf":
        text, cites = answer(question, state["chunks"], state["vectors"])
        return {"answer": text, "sources": cites}
    if state["kind"] == "csv":
        prompt = (
            "Answer the question using ONLY these dataset statistics. If they are not "
            "enough to answer exactly (for example a specific filter or calculation), "
            "say what is missing instead of guessing.\n\n"
            f"Statistics: {state['summary']}\n\nQuestion: {question}"
        )
        return {"answer": ask_llm(prompt), "sources": []}
    return {
            "answer": "Hello! I'm ready to help, but I don't have a document yet. "
                      "Please upload a PDF or CSV using the panel on the left, "
                      "and then ask me anything about it.",
            "sources": [],
        }

@app.post("/reset")
def reset():
    for k in state:
        state[k] = None
    return {"ok": True}

app.mount("/charts", StaticFiles(directory="charts"), name="charts")