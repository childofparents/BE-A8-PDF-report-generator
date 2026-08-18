import os
import sqlite3
from datetime import datetime
from playwright.sync_api import sync_playwright

# Import your working aggregation function
from report_queries import get_report_data

DB_PATH = "report.db"


def get_all_books():
    """Fetch all 60 books for the long table to test page breaks."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT title, price, rating FROM books;")
    books = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return books


def build_html(report_data, all_books):
    """Constructs the HTML document using the data and print-safe CSS."""
    today = datetime.now().strftime("%B %d, %Y")

    # Generate Top 5 rows
    top_5_rows = "".join(
        f"<tr><td>{b['title']}</td><td>£{b['price']:.2f}</td></tr>"
        for b in report_data["top_5_expensive"]
    )

    # Generate All Books rows
    all_books_rows = "".join(
        f"<tr><td>{b['title']}</td><td>£{b['price']:.2f}</td><td>{b['rating']}</td></tr>"
        for b in all_books
    )

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600&family=Merriweather:wght@700&display=swap" rel="stylesheet">
        <style>
            body {{
                font-family: 'Inter', sans-serif;
                color: #0F172A;
                background-color: #F1F5F9;
                margin: 40px;
            }}
            h1, h2, h3 {{
                font-family: 'Merriweather', serif;
                color: #0D9488;
            }}
            .summary-box {{
                border: 2px solid #475569;
                padding: 15px;
                margin-bottom: 30px;
                background-color: white;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 30px;
                background-color: white;
            }}
            th, td {{
                border: 1px solid #475569;
                padding: 10px;
                text-align: left;
            }}
            th {{
                background-color: #475569;
                color: #F1F5F9;
            }}

            /* THE FIX: Prevent rows from slicing in half across pages */
            tr {{
                break-inside: avoid;
            }}
            /* THE FIX: Repeat headers on new pages */
            thead {{
                display: table-header-group;
            }}
        </style>
    </head>
    <body>
        <h1>Bookstore Analytics Report</h1>
        <p><strong>Generated on:</strong> {today}</p>

        <div class="summary-box">
            <h2>Overview</h2>
            <p><strong>Total Books:</strong> {report_data['total_books']}</p>
            <p><strong>Average Price:</strong> £{report_data['average_price']:.2f}</p>
        </div>

        <h2>Top 5 Most Expensive Books</h2>
        <table>
            <thead>
                <tr><th>Title</th><th>Price</th></tr>
            </thead>
            <tbody>
                {top_5_rows}
            </tbody>
        </table>

        <h2>Full Inventory Log</h2>
        <table>
            <thead>
                <tr><th>Title</th><th>Price</th><th>Rating</th></tr>
            </thead>
            <tbody>
                {all_books_rows}
            </tbody>
        </table>
    </body>
    </html>
    """
    return html


def render_to_pdf():
    """Orchestrates data fetching, HTML building, and Playwright rendering."""
    # Ensure reports directory exists
    os.makedirs("reports", exist_ok=True)

    # 1. Query the data
    report_data = get_report_data()
    all_books = get_all_books()

    # 2. Build the HTML
    html_content = build_html(report_data, all_books)

    # 3. Render the PDF using Playwright
    print("Launching Chromium to render PDF...")
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.set_content(html_content)
        page.pdf(
            path="reports/test.pdf",
            format="A4",
            print_background=True,
            margin={"top": "20px", "bottom": "20px"}
        )
        browser.close()

    print("Success! PDF saved to reports/test.pdf")


if __name__ == "__main__":
    render_to_pdf()