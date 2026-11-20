import os
import sqlite3
from contextlib import closing
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

DB_PATH = os.getenv("DB_PATH", "/tmp/todos.db")
STATIC_DIR = Path(os.getenv("STATIC_DIR", "static"))

app = FastAPI(title="Todo API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:5173").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)


def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


with closing(db()) as conn:
    conn.execute(
        "CREATE TABLE IF NOT EXISTS todos ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, "
        "title TEXT NOT NULL, "
        "done INTEGER NOT NULL DEFAULT 0)"
    )
    conn.commit()


class TodoIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)


class TodoUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    done: bool | None = None


def row_to_dict(row):
    return {"id": row["id"], "title": row["title"], "done": bool(row["done"])}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/todos")
def list_todos():
    with closing(db()) as conn:
        rows = conn.execute("SELECT * FROM todos ORDER BY id DESC").fetchall()
    return [row_to_dict(r) for r in rows]


@app.post("/api/todos", status_code=201)
def create_todo(body: TodoIn):
    with closing(db()) as conn:
        cur = conn.execute("INSERT INTO todos (title) VALUES (?)", (body.title.strip(),))
        conn.commit()
        row = conn.execute("SELECT * FROM todos WHERE id = ?", (cur.lastrowid,)).fetchone()
    return row_to_dict(row)


@app.patch("/api/todos/{todo_id}")
def update_todo(todo_id: int, body: TodoUpdate):
    with closing(db()) as conn:
        row = conn.execute("SELECT * FROM todos WHERE id = ?", (todo_id,)).fetchone()
        if not row:
            raise HTTPException(404, "Todo not found")
        title = body.title.strip() if body.title is not None else row["title"]
        done = int(body.done) if body.done is not None else row["done"]
        conn.execute("UPDATE todos SET title = ?, done = ? WHERE id = ?", (title, done, todo_id))
        conn.commit()
        row = conn.execute("SELECT * FROM todos WHERE id = ?", (todo_id,)).fetchone()
    return row_to_dict(row)


@app.delete("/api/todos/{todo_id}", status_code=204)
def delete_todo(todo_id: int):
    with closing(db()) as conn:
        cur = conn.execute("DELETE FROM todos WHERE id = ?", (todo_id,))
        conn.commit()
    if cur.rowcount == 0:
        raise HTTPException(404, "Todo not found")


# Serve built React app (present in the Docker image)
if STATIC_DIR.exists():
    app.mount("/assets", StaticFiles(directory=STATIC_DIR / "assets"), name="assets")

    @app.get("/{full_path:path}")
    def spa(full_path: str):
        file = STATIC_DIR / full_path
        if full_path and file.is_file():
            return FileResponse(file)
        return FileResponse(STATIC_DIR / "index.html")
