import sqlite3

DB_PATH = "report.db"


def get_report_data():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Enables access to results by column names
    cursor = conn.cursor()

    # Full report object containing the four required numbers
    report_dict = {}

    # Query A: Total number of books
    cursor.execute("SELECT COUNT(*) as total_books FROM books;")
    report_dict["total_books"] = cursor.fetchone()["total_books"]

    # Query B: Average book price
    cursor.execute("SELECT AVG(price) as avg_price FROM books;")
    report_dict["average_price"] = round(cursor.fetchone()["avg_price"], 2)

    # Query C: Top 5 most expensive books
    cursor.execute("""
                   SELECT title, price
                   FROM books
                   ORDER BY price DESC LIMIT 5;
                   """)
    report_dict["top_5_expensive"] = [dict(row) for row in cursor.fetchall()]

    # Query D: Number of books per star rating
    cursor.execute("""
                   SELECT rating, COUNT(*) as book_count
                   FROM books
                   GROUP BY rating
                   ORDER BY book_count DESC;
                   """)
    report_dict["rating_distribution"] = [dict(row) for row in cursor.fetchall()]

    conn.close()
    return report_dict


if __name__ == "__main__":
    import json

    # Execution validation block
    data = get_report_data()
    print(json.dumps(data, indent=2))