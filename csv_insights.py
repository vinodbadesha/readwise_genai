import os, time
import pandas as pd
import matplotlib 
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from google import genai

client = genai.Client()
model = "gemini-3.5-flash-lite"

def summarize_csv(path):
    df = pd.read_csv(path)
    summary = {
        "rows": len(df),
        "columns": list(df.columns),
        "missing_values": df.isna().sum().to_dict(),
        "stats": df.describe().round(2).to_dict(),
        "Total Revenue": df[df["Booking Status"] == "Completed"]["Booking Value"].sum()
    }
    category_cols = [c for c in df.select_dtypes(include="object").columns if df[c].nunique() <= 15][:3]
    summary["top_categories"] = {c: df[c].value_counts().head(5).to_dict() for c in category_cols}
    return df, summary

def charts(df, out_dir="charts"):
    os.makedirs(out_dir, exist_ok=True)
    paths = []
    for i, col in enumerate(df.select_dtypes(include="number").columns[:2]):
        plt.figure()
        df[col].hist()
        plt.title(col)
        p = f"{out_dir}/num_{i}.png"
        plt.savefig(p);
        plt.close()
        paths.append(p)

    for i, col in enumerate([c for c in df.select_dtypes(include="object").columns if df[c].nunique() <= 15][:2]):
        plt.figure()
        df[col].value_counts().head(5).plot(kind="bar")
        plt.title(col);
        plt.tight_layout()
        q = f"{out_dir}/cat_{i}.png"
        plt.savefig(q);
        plt.close()
        paths.append(q)
    return paths

def get_insights(summary, focus=""):
    prompt = (
        "You are a data analyst. Using ONLY the statistics below, write 5 short, "
        "specific insights and 2 data quality concerns. Do not invent numbers.\n\n"
        "Blank values in cancellation columns mean the event did not happen; do not treat the corresponding rows with blank values, " 
        "as data quality issues.\n\n"
        + (f"The user expecially wnats insights about: {focus}\n\n" if focus else "")
        + f"{summary}"
    )
    for attempt in range(3):
        try:
            return client.models.generate_content(model=model, contents=prompt).text
        except Exception as e:
            if "503" in str(e) and attempt < 2:
                time.sleep(3 * (attempt + 1))
            else:
                raise

if __name__ == "__main__":
    path = input("Enter path to CSV file: ").strip()
    focus = input("What insight do you want to focus on ? (press Enter for general insights) ").strip()
    df, summary = summarize_csv(path)
    print("Charts saved: ", charts(df))
    print(get_insights(summary, focus))