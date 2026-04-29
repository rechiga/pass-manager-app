from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "my_secret_key"  # セッションを暗号化するためのキー

@app.route("/")
def home():
    return render_template("login.html")

@app.route("/register", methods=["GET","POST"])
def register():

    #POST(フォーム送信)のときだけ実行
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        #未入力チェック
        if not username or not password:
            flash("ユーザ名とパスワードを入力してください")
            return redirect(url_for("register"))

        #パスワードをハッシュ化
        hashed_password = generate_password_hash(password)

        #DB接続
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()

        #既存のユーザかどうかを確認
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        existing_user = cursor.fetchone()

        if existing_user:
            conn.close()
            flash("そのユーザ名はすでに使われています")
            return redirect(url_for("register"))

        #登録データを保存する
        cursor.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, hashed_password)
        )

        #保存を確定して接続を閉じる
        conn.commit()
        conn.close()

        flash("新規登録が完了しました。ログインしてください")
        return redirect(url_for("home"))

    #GETのときは登録画面を表示
    return render_template("register.html")

@app.route("/login", methods=["POST"])
def login():
    username = request.form.get("username")
    password = request.form.get("password")

    #未入力チェック
    if not username or not password:
        flash("ユーザ名とパスワードを入力してください")
        return redirect(url_for("home"))

    #DBに接続
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    #入力されたユーザ名のデータを1件だけ取り出す
    cursor.execute("SELECT * FROM users WHERE username = ?",(username,))
    user = cursor.fetchone()

    conn.close()

    #userが存在するときだけパスワード照合
    if user:
        #usersテーブルの列順は id, username, password
        saved_hashed_password = user[2]

        #照合
        if check_password_hash(saved_hashed_password, password):
            #sessionにユーザIDとユーザ名を保存してダッシュボードへリダイレクト
            session["user_id"] = user[0]
            session["username"] = user[1]
            flash("ログインしました")
            return redirect(url_for("dashboard"))
        else:
            flash("パスワードが間違っています")   
            return redirect(url_for("home"))

    #ユーザー名が見つからなかった場合もログイン失敗としてホームにリダイレクト
    flash("ユーザ名が存在しません")
    return redirect(url_for("home"))

@app.route("/dashboard")
def dashboard():
    #sessionにユーザIDがないときは未ログインと判断
    if "user_id" not in session:
        return redirect(url_for("home"))
    
    #ログイン中ユーザーのidを取得
    user_id = session["user_id"]

    #DBに接続
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    #ログイン中ユーザーのパスワード情報のみ取得
    cursor.execute("""
        SELECT * FROM passwords WHERE user_id = ?
    """, (user_id,))

    #取得したデータをすべて取り出す
    password_list = cursor.fetchall()

    #接続を閉じる
    conn.close()

    #dashboard.htmlにパスワード情報を渡して表示
    return render_template("dashboard.html", password_list=password_list)

@app.route("/logout")
def logout():
    #sessionをクリアしてホームにリダイレクト
    session.clear()
    return redirect(url_for("home"))

@app.route("/add_password", methods=["GET", "POST"])
def add_password():
    #未ログインならホームにリダイレクト
    if "user_id" not in session:
        return redirect(url_for("home"))

    #フォーム送信された場合
    if request.method == "POST":
        #フォームから入力された値を取得
        service_name = request.form.get("service_name")
        login_id = request.form.get("login_id")
        password_value = request.form.get("password_value")
        memo = request.form.get("memo")

        #必須項目チェック
        if not service_name or not login_id or not password_value:
            flash("サービス名、ログインID、パスワードは必須です")
            return redirect(url_for("add_password"))

        #ログイン中ユーザーのidを取得
        user_id = session["user_id"]

        # DBに接続
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()

        # パスワード情報を保存
        cursor.execute("""
            INSERT INTO passwords (user_id, service_name, login_id, password_value, memo)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, service_name, login_id, password_value, memo))

        # 保存を確定して接続を閉じる
        conn.commit()
        conn.close()

        flash("パスワード情報を追加しました")
        #保存後はダッシュボードへリダイレクト
        return redirect(url_for("dashboard"))

    #GETのときはパスワード追加フォームを表示
    return render_template("add_password.html")

#編集画面と更新処理
@app.route("/edit_password/<int:password_id>", methods=["GET", "POST"])
def edit_password(password_id):
    #未ログインならホームにリダイレクト
    if "user_id" not in session:
        return redirect(url_for("home"))

    #ログイン中ユーザーのidを取得
    user_id = session["user_id"]

    #DBに接続
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    #更新処理
    if request.method == "POST":
        #フォームから入力された値を取得
        service_name = request.form.get("service_name")
        login_id = request.form.get("login_id")
        password_value = request.form.get("password_value")
        memo = request.form.get("memo")

        #必須項目チェック
        if not service_name or not login_id or not password_value:
            conn.close()
            flash("サービス名、ログインID、パスワードは必須です")
            return redirect(url_for("edit_password", password_id=password_id))

        #パスワード情報を更新
        cursor.execute("""
            UPDATE passwords
            SET service_name = ?, login_id = ?, password_value = ?, memo = ?
            WHERE id = ? AND user_id = ?
        """, (service_name, login_id, password_value, memo, password_id, user_id))

        #保存を確定して接続を閉じる
        conn.commit()
        conn.close()

        flash("パスワード情報を更新しました")
        #更新後はダッシュボードへリダイレクト
        return redirect(url_for("dashboard"))

    #画面表示
    else:
        #GETのときは編集フォームを表示するために既存のデータを取得
        cursor.execute("""
            SELECT * FROM passwords WHERE id = ? AND user_id = ?
        """, (password_id, user_id))

        data = cursor.fetchone()
        conn.close()

        if data is None:
            flash("パスワード情報が見つかりません")
            return redirect(url_for("dashboard"))

        return render_template("edit_password.html", data=data)

#指定されたidのパスワード情報を削除する処理
@app.route("/delete_password/<int:password_id>", methods=["POST"])
def delete_password(password_id):
    #未ログインならホームにリダイレクト
    if "user_id" not in session:
        return redirect(url_for("home"))

    #ログイン中ユーザーのidを取得
    user_id = session["user_id"]

    #DBに接続
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    #自分のパスワード情報だけ削除できるように
    cursor.execute("""
        DELETE FROM passwords
        WHERE id = ? AND user_id = ?
    """, (password_id, user_id))

    #保存を確定して接続を閉じる
    conn.commit()
    conn.close()

    flash("パスワード情報を削除しました")
    #ダッシュボードへリダイレクト
    return redirect(url_for("dashboard"))

if __name__ == "__main__":
    app.run(debug=True)

