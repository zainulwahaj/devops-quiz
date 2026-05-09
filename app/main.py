from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse

from app.scraper import fetch_first_article
from app.summarizer import summarize

REGISTRATION = "FA23-BAI-058"
NEWS_SOURCE = "The Atlantic"

app = FastAPI(
    title="DevOps Quiz News Summarizer",
    description="Selenium-powered news search and summarization API for Quiz 3.",
    version="1.0.0",
)


@app.get("/", response_class=HTMLResponse)
def home() -> str:
    return """
    <!doctype html>
    <html lang="en">
      <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>FA23-BAI-058 News API</title>
        <style>
          body {
            margin: 0;
            font-family: Arial, sans-serif;
            background: #f5f7fb;
            color: #172033;
          }
          main {
            max-width: 760px;
            margin: 0 auto;
            padding: 56px 20px;
          }
          section {
            background: white;
            border: 1px solid #d8deea;
            border-radius: 8px;
            padding: 28px;
            box-shadow: 0 8px 24px rgba(24, 32, 51, 0.08);
          }
          h1 {
            margin: 0 0 12px;
            font-size: 32px;
          }
          p {
            line-height: 1.55;
          }
          code {
            display: block;
            margin-top: 16px;
            padding: 14px;
            border-radius: 6px;
            background: #eef2f8;
            overflow-wrap: anywhere;
          }
        </style>
      </head>
      <body>
        <main>
          <section>
            <h1>FA23-BAI-058</h1>
            <p><strong>News Source:</strong> The Atlantic</p>
            <p>This container exposes the required Selenium news summary API on port 7000.</p>
            <code>GET /get?keyword=technology</code>
          </section>
        </main>
      </body>
    </html>
    """


@app.get("/get")
def get_summary(keyword: str = Query(..., min_length=1)) -> dict[str, str]:
    clean_keyword = keyword.strip()
    if not clean_keyword:
        raise HTTPException(status_code=400, detail="keyword query parameter is required")

    article = fetch_first_article(clean_keyword)
    summary = summarize(article.text, clean_keyword)

    if not article.url:
        summary = f"No article result was found on {NEWS_SOURCE} for keyword '{clean_keyword}'."

    return {
        "registration": REGISTRATION,
        "newssource": NEWS_SOURCE,
        "keyword": clean_keyword,
        "url": article.url,
        "summary": summary,
    }
