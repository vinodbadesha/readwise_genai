import { useState, useRef, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import "./styles.css";

async function post(url, fd) {
  try {
    const r = await fetch(url, { method: "POST", body: fd });
    if (!r.ok) return { error: "Server error. Check the uvicorn terminal." };
    return await r.json();
  } catch {
    return { error: "Cannot reach the server. Is uvicorn running?" };
  }
}

export default function App() {
  const [file, setFile] = useState(null);
  const [status, setStatus] = useState(null);
  const [kind, setKind] = useState(null);
  const [summary, setSummary] = useState("");
  const [charts, setCharts] = useState([]);
  const [messages, setMessages] = useState([]);
  const [question, setQuestion] = useState("");
  const [asking, setAsking] = useState(false);
  const endRef = useRef(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, asking]);

  useEffect(() => {
  fetch("/reset", { method: "POST" });
}, []);

  const upload = async () => {
    if (!file) return;
    const fd = new FormData();
    fd.append("file", file);
    setStatus({ kind: "busy", text: "Processing " + file.name + "... this can take a few seconds" });
    setSummary(""); setCharts([]);
    const d = await post("/upload", fd);
    if (d.error) return setStatus({ kind: "err", text: d.error });
    setKind(d.type);
    setMessages((m) => [...m, { role: "ai", text: `${file.name} is ready. Ask me anything about it.`, sources: [] }]);
    if (d.type === "pdf") {
      setSummary(d.summary);
      setStatus({ kind: "ok", text: `${file.name} ready (${d.chunks} chunks)` });
    } else {
      setSummary(d.insights);
      setCharts((d.charts || []).map((c) => c + "?t=" + Date.now()));
      setStatus({ kind: "ok", text: `${file.name} ready (${d.rows} rows)` });
    }
  };

  const ask = async () => {
  const q = question.trim();
  if (!q || asking) return;
  setMessages((m) => [...m, { role: "user", text: q }]);
  setQuestion("");
  if (!kind) {
    setMessages((m) => [
      ...m,
      {
        role: "ai",
        text: "Hello! I'm ready to help, but I don't have a document yet. Please upload a PDF or CSV using the panel on the left, and then ask me anything about it.",
        sources: [],
      },
    ]);
    return;
  }
  setAsking(true);
  const fd = new FormData();
  fd.append("question", q);
  const d = await post("/ask", fd);
  setMessages((m) => [...m, { role: "ai", text: d.error || d.answer, sources: d.sources || [] }]);
  setAsking(false);
};

  return (
    <div className="app">
      <header>
        <h1>ReadWise</h1>
        <p>Upload PDF or CSV • Get Cited Answers • Key Insights</p>
      </header>

      <div className="layout">
        <div className="card col">
          <h3>1. Upload</h3>
          <label className="file">
            <input type="file" accept=".pdf,.csv" onChange={(e) => setFile(e.target.files[0])} />
            <span>{file ? file.name : "Choose a PDF or CSV"}</span>
          </label>
          <button className="primary" onClick={upload} disabled={!file}>Upload</button>
          {status && <div className={"status " + status.kind}>{status.text}</div>}
        </div>

        <div className="card col">
          <h3>{kind === "csv" ? "2. Key insights & data quality" : "2. Document summary"}</h3>
          {!summary && <div className="empty">The summary or insights appear here after upload.</div>}
          {summary && <div className="insights"><ReactMarkdown>{summary}</ReactMarkdown></div>}
          {charts.length > 0 && (
            <div className="charts">
              {charts.map((c) => <img key={c} src={c} alt="chart" />)}
            </div>
          )}
        </div>

        <div className="card col">
          <h3>3. Ask questions</h3>
          <div className="chat">
            {messages.length === 0 && <div className="empty">Ask a full-sentence question.</div>}
            {messages.map((m, i) => (
              <div key={i} className={"msg " + m.role}>
                <div className="bubble">{m.text}</div>
                {m.sources && m.sources.length > 0 && (
                  <div className="sources">
                    {m.sources.map((s, j) => (
                      <span key={j} className="badge">
                        Page {s.page}{s.heading ? " · " + s.heading : ""}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))}
            {asking && <div className="msg ai"><div className="bubble typing">Thinking...</div></div>}
            <div ref={endRef} />
          </div>
          <div className="inputRow">
            <input
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && ask()}
              placeholder="Ask about your file..."
            />
            <button className="primary" onClick={ask} disabled={asking}>Ask</button>
          </div>
        </div>
      </div>
    </div>
  );
}