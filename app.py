from flask import Flask, render_template, request, redirect, url_for, session
from datetime import datetime
import re

app = Flask(__name__)
app.secret_key = "secret123"

USER = {
    "username": "admin",
    "password": "123456"
}

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if (request.form["username"] == USER["username"] and
            request.form["password"] == USER["password"]):
            session["user"] = USER["username"]
            return redirect(url_for("age"))
        else:
            return render_template("login.html", error="Sai tài khoản hoặc mật khẩu")
    return render_template("login.html")

@app.route("/age", methods=["GET", "POST"])
def age():
    if "user" not in session:
        return redirect(url_for("login"))

    age = None
    error = None

    if request.method == "POST":
        birth_year_raw = request.form.get("birth_year", "")

        # 1. Không được để trống
        if birth_year_raw.strip() == "":
            error = "Không được để trống năm sinh"

        # 2. Không cho ký tự đặc biệt hoặc khoảng trắng
        elif re.search(r"[^\w]", birth_year_raw):
            error = "Không được chứa ký tự đặc biệt hoặc khoảng trắng"

        else:
            # 3. Lấy số (cho phép nhập chữ)
            numbers = re.findall(r"\d+", birth_year_raw)

            if not numbers:
                error = "Năm sinh phải chứa số"

            else:
                birth_year = int(numbers[0])
                current_year = datetime.now().year

                # 4. Kiểm tra biên
                if birth_year < 1900:
                    error = "Năm sinh phải từ 1900 trở lên"

                elif birth_year > current_year:
                    error = "Năm sinh không được lớn hơn năm hiện tại"

                else:
                    age = current_year - birth_year

    return render_template("age.html", age=age, error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True)
