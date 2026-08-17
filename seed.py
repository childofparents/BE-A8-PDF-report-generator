import os
import json
import sqlite3

DB_PATH = "report.db"
BOOKS_JSON_PATH = "books.json"  # Adjust this path if your books.json is in a different directory


def seed_database():
    # 1. Connect to the database file (creates it if it doesn't exist)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 2. Create the books schema table
    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS books
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       title
                       TEXT
                       NOT
                       NULL,
                       price
                       REAL
                       NOT
                       NULL,
                       rating
                       TEXT
                       NOT
                       NULL,
                       url
                       TEXT
                       NOT
                       NULL
                       UNIQUE
                   );
                   """)

    # 3. Safe to run twice: Clean out any previous records
    cursor.execute("DELETE FROM books;")

    # 4. Read the raw dataset artifacts
    if not os.path.exists(BOOKS_JSON_PATH):
        print(f"Error: Could not find dataset file at {BOOKS_JSON_PATH}")
        conn.close()
        return

    with open(BOOKS_JSON_PATH, "r", encoding="utf-8") as f:
        books_data = json.load(f)

    # 5. Insert rows systematically mapping keys to columns
    inserted_count = 0
    for record in books_data:
        # Extract fields matching assignment instructions
        title = record.get("title")
        price = record.get("price_gbp")
        rating = record.get("rating_text")
        url = record.get("product_url")

        try:
            cursor.execute("""
                           INSERT INTO books (title, price, rating, url)
                           VALUES (?, ?, ?, ?);
                           """, (title, price, rating, url))
            inserted_count += 1
        except sqlite3.IntegrityError:
            # Skip if a canonical URL duplicate slips through
            continue

    # Commit changes and release database lock
    conn.commit()
    conn.close()
    print(f"Successfully seeded database. Total records loaded: {inserted_count}")


if __name__ == "__main__":
    seed_database()