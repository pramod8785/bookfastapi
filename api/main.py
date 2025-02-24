from typing import Any
from fastapi import FastAPI, Depends, Request, Query
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session
from sqlalchemy import text

from database import engine, SessionLocal
from models import BooksAuthor, Book

Base = declarative_base()

app = FastAPI()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# @app.get("/")
# async def read_root():
#     return {"message": "Hello World"}

# @app.get("/authors/")
# async def read_authors(db: Session = Depends(get_db)):
#     Author = db.query(BooksAuthor).all()
#     return Author

@app.get("/booklist/")
async def get_booklist(db: Session = Depends(get_db),
    title: str = Query(None, description="The book title"),
    author: str = Query(None, description="The book author"),
    subject: str = Query(None, description="The book subject"),
    language: str = Query(None, description="The book language"),
    category: str = Query(None, description="The book category"),
    filetype: str = Query(None, description="The book file type"),
    offset: int = Query(1, description="The book list start offset"),
    limit: int = Query(10, description="Number of books to return"),):

    dynamic_columns = [
        "b.title",
        "b.media_type",
        "a.name",
        "a.birth_year",
        "a.death_year",
        "array_agg(DISTINCT l.code) AS languages",
        "array_agg(DISTINCT s.name) AS subjects",
        "array_agg(DISTINCT bsh.name) AS bookshelves",
        "json_agg(json_build_object('mime_type', f.mime_type, 'url', f.url)) AS download_links"
    ]

    fromtable_str = '''
        books_book b
        JOIN books_book_authors ba ON b.id = ba.book_id
        JOIN books_author a ON ba.author_id = a.id
        JOIN books_book_bookshelves bbs ON bbs.book_id = b.id
        JOIN books_bookshelf bsh ON bbs.bookshelf_id = bsh.id
        JOIN books_book_languages bl ON b.id = bl.book_id
        JOIN books_language l ON bl.language_id = l.id
        JOIN books_book_subjects bsu ON b.id = bsu.book_id
        JOIN books_subject s ON bsu.subject_id = s.id
        JOIN books_format f ON b.id = f.book_id'''

    column_filter_map = {
        "title" : "b.title",
        "author" : "a.name",
        "subject": "s.name",
        "language" : "l.code",
        "category" : "bsh.name",
        "filetype" : "b.media_type"
    }
    # Construct the filter criteria
    filter_criteria = {
        "title": title,
        "author": author,
        "subject": subject,
        "language": language,
        "category": category,
        "filetype": filetype
    }
    columns_str = ','.join(dynamic_columns)
    group_str = "b.title, b.media_type, a.name, a.birth_year, a.death_year"
    limit_str = "LIMIT :limit OFFSET :offset"


    print(filter_criteria)

    # Construct the WHERE clause
    where_str = " AND ".join(f"{column_filter_map[k]} = '{v}'" for k, v in filter_criteria.items() if k in column_filter_map and v is not None)

    print(where_str)
    where_str = f"WHERE {where_str}" if where_str else ""
    print(where_str)

    # Define the query
    stmt_result = f'''
        SELECT
            {columns_str}             
        FROM {fromtable_str}
        {where_str}
        GROUP BY
            {group_str}
        {limit_str}
    '''

    # Define the query
    stmt_totalcnt = f'''
        SELECT
            count(1)             
        FROM (
            SELECT
                {columns_str}             
            FROM {fromtable_str}
            {where_str}
            GROUP BY
                {group_str}
        ) AS subquery
    '''

    # Define the parameters
    params = {'limit': limit, 'offset': offset}
    print(stmt_result)
    print(stmt_totalcnt)
    # Execute the query and map results to Book objects
    results = db.execute(stmt_result, params).fetchall()
    totalcnt = db.execute(stmt_totalcnt).scalar()
    books = [Book(*row) for row in results]
    return {"result" : books, "totalcnt" : totalcnt} 
