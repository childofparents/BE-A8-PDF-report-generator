import os
import sqlite3
from datetime import datetime
from fastapi import FastAPI, HTTPException, Response, status
from fastapi.responses import FileResponse
from pydantic import BaseModel

from render_pdf import render_to_pdf

app = FastAPI()
DB_PATH = "report.db"


# Ensure reports table exists alongside books
def init_reports_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS reports
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       path
                       TEXT
                       NOT
                       NULL,
                       created_at
                       DATE
                       NOT
                       NULL
                   );
                   """)
    conn.commit()
    conn.close()


init_reports_db()


class ReportRequest(BaseModel):
    force: bool = False


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/reports")
def create_report(response: Response, req: ReportRequest = ReportRequest()):
    today = datetime.now().strftime("%Y-%m-%d")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Stage 5: Idempotency Check
    # If a report was already generated today and force=False, return the existing one.
    if not req.force:
        cursor.execute("SELECT id, path FROM reports WHERE created_at = ?", (today,))
        existing = cursor.fetchone()
        if existing:
            conn.close()
            response.status_code = status.HTTP_200_OK
            return {"id": existing["id"], "file": f"/reports/{existing['id']}/file"}

    # Stage 4: Generate the Report
    # Notice the request hangs here for a few seconds while Playwright runs.
    filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    filepath = os.path.join("reports", filename)

    render_to_pdf(filepath)

    cursor.execute("INSERT INTO reports (path, created_at) VALUES (?, ?)", (filepath, today))
    report_id = cursor.lastrowid
    conn.commit()
    conn.close()

    response.status_code = status.HTTP_201_CREATED
    return {"id": report_id, "file": f"/reports/{report_id}/file"}


@app.get("/reports/{report_id}")
def get_report_status(report_id: int):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT id, path, created_at FROM reports WHERE id = ?", (report_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Report not found")

    return {"id": row["id"], "created_at": row["created_at"], "file": f"/reports/{row['id']}/file"}


@app.get("/reports/{report_id}/file")
def download_report(report_id: int):
    """Store and link: Serves the PDF from disk."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT path FROM reports WHERE id = ?", (report_id,))
    row = cursor.fetchone()
    conn.close()

    if not row or not os.path.exists(row["path"]):
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(path=row["path"], filename=os.path.basename(row["path"]), media_type='application/pdf')