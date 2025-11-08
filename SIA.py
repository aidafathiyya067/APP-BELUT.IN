from flask import Flask, render_template_string, request, redirect, url_for, session
from supabase import create_client, Client
from dotenv import load_dotenv
from email.message import EmailMessage
import smtplib, ssl, random, os

# ---------------------------
# KONFIGURASI DASAR
# ---------------------------
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# KONFIGURASI EMAIL GMAIL
EMAIL_SENDER = os.getenv("EMAIL_SENDER")      # silviaremitazahra@gmail.com
EMAIL_APP_PASSWORD = os.getenv("EMAIL_APP_PASSWORD")  # lczt eekj hlqu cqha

app = Flask(_name_)
app.secret_key = os.urandom(24)

# ---------------------------
# TEMPLATE HTML
# ---------------------------
login_page = """
<!doctype html>
<html>
<head>
    <title>BELUT.IN — Login</title>
    <style>
        body { font-family: Arial; background: #f0f2f5; text-align: center; margin-top: 80px; }
        .card { background: white; display: inline-block; padding: 40px; border-radius: 10px;
                box-shadow: 0 3px 10px rgba(0,0,0,0.2); width: 350px; }
        img { width: 100px; }
        input, select { width: 90%; padding: 10px; margin: 10px 0; }
        button { background: #007bff; color: white; padding: 10px 20px; border: none;
                 border-radius: 5px; cursor: pointer; }
        button:hover { background: #0056b3; }
        .msg { color: red; }
    </style>
</head>
<body>
    <div class="card">
        <img src="/static/logo.png" alt="Logo BELUT.IN"><br>
        <h2>🐍 BELUT.IN Login</h2>
        <form method="POST" action="/auth">
            <label>Pilih Tindakan:</label><br>
            <select name="action">
                <option value="login">Masuk</option>
                <option value="signup">Daftar</option>
            </select><br>
            <input type="email" name="email" placeholder="Email" required><br>
            <input type="password" name="password" placeholder="Password" required><br>
            <button type="submit">Lanjut</button>
        </form>
        {% if message %}<p class="msg">{{ message }}</p>{% endif %}
    </div>
</body>
</html>
"""

otp_page = """
<!doctype html>
<html>
<head><title>Verifikasi OTP</title></head>
<body style="text-align:center; font-family:Arial; margin-top:100px;">
    <h2>Masukkan Kode OTP yang Dikirim ke Email</h2>
    <form method="POST" action="/verify_otp">
        <input type="text" name="otp_input" placeholder="Masukkan 6 digit OTP" required><br><br>
        <button type="submit">Verifikasi</button>
    </form>
    {% if message %}<p style="color:red;">{{ message }}</p>{% endif %}
</body>
</html>
"""

dashboard_page = """
<!doctype html>
<html>
<head>
    <title>BELUT.IN — Dashboard</title>
    <style>
        body { font-family: Arial; background: #f9f9f9; margin: 0; }
        .navbar { background: #007bff; color: white; padding: 15px; }
        .navbar a { color: white; margin: 0 15px; text-decoration: none; }
        .content { padding: 30px; text-align: center; }
    </style>
</head>
<body>
    <div class="navbar">
        <b>BELUT.IN</b> |
        <a href="/">Home</a>
        <a href="/produksi">Produksi</a>
        <a href="/stok">Stok</a>
        <a href="/penjualan">Penjualan</a>
        <a href="/laporan">Laporan Keuangan</a>
        <a href="/logout" style="color: yellow;">Logout</a>
    </div>
    <div class="content">
        {% block content %}
        <h1>Selamat Datang di Sistem Manajemen Akuntansi Budidaya Belut 🐍</h1>
        <p>Silakan pilih menu di atas untuk mulai bekerja.</p>
        {% endblock %}
    </div>
</body>
</html>
"""

# ---------------------------
# FUNGSI BANTUAN
# ---------------------------
def send_otp_via_email(recipient_email, otp_code):
    msg = EmailMessage()
    msg["Subject"] = "Kode OTP Login BELUT.IN"
    msg["From"] = EMAIL_SENDER
    msg["To"] = recipient_email
    msg.set_content(f"Halo! 👋\n\nKode OTP kamu adalah: {otp_code}\nJangan bagikan ke siapa pun ya!\n\n- Tim BELUT.IN")

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(EMAIL_SENDER, EMAIL_APP_PASSWORD)
        server.send_message(msg)

# ---------------------------
# ROUTES
# ---------------------------
@app.route("/", methods=["GET"])
def home():
    if session.get("user_email"):
        return render_template_string(dashboard_page)
    return render_template_string(login_page)

@app.route("/auth", methods=["POST"])
def auth():
    email = request.form.get("email")
    password = request.form.get("password")
    action = request.form.get("action")

    try:
        if action == "signup":
            supabase.auth.sign_up({"email": email, "password": password})
            msg = "Pendaftaran berhasil! Cek email kamu untuk verifikasi."
            return render_template_string(login_page, message=msg)
        elif action == "login":
            user = supabase.auth.sign_in_with_password({"email": email, "password": password})
            if user and user.user:
                otp = random.randint(100000, 999999)
                session["pending_email"] = user.user.email
                session["otp_code"] = str(otp)
                send_otp_via_email(user.user.email, otp)
                return render_template_string(otp_page)
            else:
                msg = "Login gagal! Coba lagi."
        else:
            msg = "Tindakan tidak dikenal."
    except Exception as e:
        msg = f"Error: {e}"

    return render_template_string(login_page, message=msg)

@app.route("/verify_otp", methods=["POST"])
def verify_otp():
    otp_input = request.form.get("otp_input")
    if otp_input == session.get("otp_code"):
        session["user_email"] = session.get("pending_email")
        session.pop("otp_code", None)
        session.pop("pending_email", None)
        return redirect("/")
    return render_template_string(otp_page, message="Kode OTP salah!")

@app.route("/logout")
def logout():
    session.clear()
    supabase.auth.sign_out()
    return redirect("/")

@app.route("/produksi")
def produksi():
    return render_template_string(dashboard_page.replace("{% block content %}", "").replace("{% endblock %}", "<h2>📊 Halaman Produksi</h2>"))

@app.route("/stok")
def stok():
    return render_template_string(dashboard_page.replace("{% block content %}", "").replace("{% endblock %}", "<h2>📦 Manajemen Stok</h2>"))

@app.route("/penjualan")
def penjualan():
    return render_template_string(dashboard_page.replace("{% block content %}", "").replace("{% endblock %}", "<h2>💰 Data Penjualan</h2>"))

@app.route("/laporan")
def laporan():
    return render_template_string(dashboard_page.replace("{% block content %}", "").replace("{% endblock %}", "<h2>📑 Laporan Keuangan</h2>"))

# ---------------------------
# JALANKAN APP
# ---------------------------
if _name_ == "_main_":
    app.run(debug=True)
