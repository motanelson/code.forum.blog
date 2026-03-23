from flask import Flask, request, redirect, send_from_directory
import sqlite3
import hashlib
import secrets
import os

app = Flask(__name__)

DB = "blog.db"
UPLOAD_FOLDER = "files"
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

lista1 = [
    "c",
    "cpp",
    "python",
    "visual_basic",
    "csharp",
    "pascal",
    "basic"
]

# ---------- DB ----------
def get_db():
    return sqlite3.connect(DB, timeout=10, check_same_thread=False)


def init_db():
    with get_db() as db:
        c = db.cursor()

        c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE,
            password TEXT,
            approved INTEGER DEFAULT 0,
            activation_key TEXT
        )
        """)

        c.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT,
            url TEXT,
            message TEXT,
            file_id INTEGER
        )
        """)


# ---------- UTIL ----------
def sanitize(text):
    return text.replace("<", "").replace(">", "")


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def generate_key():
    return secrets.token_hex(16)


# ---------- USERS ----------
def create_user(url, password):
    key = generate_key()

    with get_db() as db:
        c = db.cursor()
        c.execute(
            "INSERT INTO users (url, password, approved, activation_key) VALUES (?, ?, 0, ?)",
            (url, hash_password(password), key)
        )
        user_id = c.lastrowid

    link = f"http://127.0.0.1:5000/activate/{user_id}/{key}"

    with open("approve.txt", "a") as f:
        f.write(f"{url}|||{link}\n")


def check_user(url, password):
    with get_db() as db:
        c = db.cursor()
        c.execute("SELECT password, approved FROM users WHERE url=?", (url,))
        row = c.fetchone()

    if row:
        if row[0] != hash_password(password):
            return "wrong_pass"
        if row[1] == 0:
            return "not_approved"
        return "ok"

    return "not_exist"


# ---------- POSTS ----------
def save_post(category, url, message, file_id):
    with get_db() as db:
        c = db.cursor()
        c.execute(
            "INSERT INTO posts (category, url, message, file_id) VALUES (?, ?, ?, ?)",
            (category, url, message, file_id)
        )


def load_posts(category, page, per_page=5):
    offset = (page - 1) * per_page

    with get_db() as db:
        c = db.cursor()
        c.execute(
            "SELECT url, message, file_id FROM posts WHERE category=? ORDER BY id DESC LIMIT ? OFFSET ?",
            (category, per_page, offset)
        )
        return c.fetchall()


def count_posts(category):
    with get_db() as db:
        c = db.cursor()
        c.execute("SELECT COUNT(*) FROM posts WHERE category=?", (category,))
        return c.fetchone()[0]


# ---------- FILE ----------
def save_file(file):
    if file and file.filename.endswith(".zip"):
        data = file.read()

        if len(data) > MAX_FILE_SIZE:
            return None

        with get_db() as db:
            c = db.cursor()
            c.execute("SELECT MAX(id) FROM posts")
            max_id = c.fetchone()[0]
            file_id = (max_id or 0) + 1

        filepath = os.path.join(UPLOAD_FOLDER, f"{file_id}.zip")

        with open(filepath, "wb") as f:
            f.write(data)

        return file_id

    return None


@app.route("/files/<filename>")
def download_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)


# ---------- ROUTES ----------

@app.route("/")
def home():
    html = """
    <html><body style="background:black;color:white;font-family:Arial;">
    <h1>Fórum Programação</h1>
    <a href="/register">➕ Registar</a>
    """

    for cat in lista1:
        html += f'<a href="/{cat}">{cat}</a><br>'

    html += "</body></html>"
    return html


@app.route("/register", methods=["GET", "POST"])
def register():
    msg = ""

    if request.method == "POST":
        url = sanitize(request.form.get("url", ""))
        password = request.form.get("password", "")

        if url and password:
            try:
                create_user(url, password)
                msg = "✅ Registado! Aguarda aprovação."
            except:
                msg = "❌ Utilizador já existe"

    return f"""
    <body style="background:black;color:white;">
    <a href="/">⬅ Voltar</a>
    <h2>Registar</h2>
    <form method="POST">
        <input name="url" placeholder="URL"><br>
        <input type="password" name="password" placeholder="Password"><br>
        <button>Registar</button>
    </form>
    <p>{msg}</p>
    </body>
    """


@app.route("/activate/<int:user_id>/<key>")
def activate(user_id, key):
    with get_db() as db:
        c = db.cursor()
        c.execute("SELECT activation_key FROM users WHERE id=?", (user_id,))
        row = c.fetchone()

        if row and row[0] == key:
            c.execute("UPDATE users SET approved=1 WHERE id=?", (user_id,))
            db.commit()
            return "✅ Conta ativada!"

    return "❌ Link inválido"


@app.route("/<category>", methods=["GET", "POST"])
def category_page(category):
    if category not in lista1:
        return "Categoria inválida", 404

    page = request.args.get("page", 1, type=int)
    if page < 1:
        page = 1

    error = ""

    if request.method == "POST":
        url = sanitize(request.form.get("url", ""))
        message = sanitize(request.form.get("message", ""))
        password = request.form.get("password", "")
        file = request.files.get("file")

        if url and message and password:
            result = check_user(url, password)

            if result == "ok":
                file_id = save_file(file) if file else None
                save_post(category, url, message, file_id)
                return redirect(f"/{category}?page={page}")

            elif result == "wrong_pass":
                error = "❌ Password errada!"
            elif result == "not_approved":
                error = "⏳ Conta não ativada!"
            else:
                error = "❌ Utilizador não existe!"

    posts = load_posts(category, page)
    total = count_posts(category)
    total_pages = (total + 4) // 5 if total > 0 else 1

    html = f"""
    <body style="background:black;color:white;">
    <a href="/">⬅ Voltar</a>
    <h2>{category}</h2>

    <form method="POST" enctype="multipart/form-data">
        <input name="url" placeholder="URL"><br>
        <input type="password" name="password" placeholder="Password"><br>
        <textarea name="message"></textarea><br>
        <input type="file" name="file"><br>
        <button>Submit</button>
    </form>

    <p style="color:red;">{error}</p>
    <hr>
    """

    for url, msg, fid in posts:
        html += f"<b>{url}</b><br><p>{msg}</p>"
        if fid:
            html += f'<a href="/files/{fid}.zip">📥 Download ZIP</a>'
        html += "<hr>"

    html += f"Página {page} de {total_pages}<br>"

    if page > 1:
        html += f'<a href="/{category}?page={page-1}">⬅</a> '
    if page < total_pages:
        html += f'<a href="/{category}?page={page+1}">➡</a>'

    html += "</body>"
    return html


if __name__ == "__main__":
    init_db()
    app.run(debug=True, use_reloader=False)
