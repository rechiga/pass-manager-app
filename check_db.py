import sqlite3

# users.db に接続
conn = sqlite3.connect("users.db")
cursor = conn.cursor()

print("=== users テーブル ===")
cursor.execute("SELECT * FROM users")
users = cursor.fetchall()

for user in users:
    print(user)

print("\n=== passwords テーブル ===")
cursor.execute("SELECT * FROM passwords")
passwords = cursor.fetchall()

for password_data in passwords:
    print(password_data)

# 接続を閉じる
conn.close()