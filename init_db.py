import sqlite3

#users.dbに接続
conn = sqlite3.connect("users.db")
cursor = conn.cursor()

# usersテーブルを作成
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    password TEXT NOT NULL
)
""")

#passwordsテーブルを作成
cursor.execute("""
CREATE TABLE IF NOT EXISTS passwords (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    service_name TEXT NOT NULL,
    login_id TEXT NOT NULL,
    password_value TEXT NOT NULL,
    memo TEXT,
    FOREIGN KEY (user_id) REFERENCES users (id)
)
""")

#変更を保存
conn.commit()

#接続を閉じる
conn.close()

print("usersテーブルとpasswordsテーブルを作成しました。")