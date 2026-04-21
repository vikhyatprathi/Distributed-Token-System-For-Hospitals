from flask import Flask, request, redirect, render_template_string, session
import json, os, base64
from threading import Lock
import qrcode
from io import BytesIO

app = Flask(__name__)
app.secret_key = "secret123"

FILE = "bookings.json"
lock = Lock()
lamport_clock = 0

ADMIN_USER = "admin"
ADMIN_PASS = "1234"

DOCTORS = ["Orthopedic", "Pediatric", "ENT", "Dermatologist"]

# -------- Lamport Clock --------
def increment_clock():
    global lamport_clock
    lamport_clock += 1
    return lamport_clock

# -------- File Setup --------
if not os.path.exists(FILE):
    with open(FILE, "w") as f:
        json.dump({doc: [] for doc in DOCTORS}, f)

def load():
    with open(FILE) as f:
        return json.load(f)

def save(data):
    with open(FILE, "w") as f:
        json.dump(data, f, indent=2)

# -------- SHARED STYLES --------
BASE_STYLE = """
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Serif+Display&display=swap" rel="stylesheet">
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  :root {
    --bg: #0a0f1e;
    --surface: #111827;
    --surface2: #1a2235;
    --border: rgba(255,255,255,0.07);
    --border-light: rgba(255,255,255,0.12);
    --accent: #3b82f6;
    --accent-glow: rgba(59,130,246,0.15);
    --accent2: #06b6d4;
    --text: #f1f5f9;
    --text-muted: #94a3b8;
    --text-dim: #475569;
    --success: #10b981;
    --warning: #f59e0b;
    --danger: #ef4444;
    --radius: 12px;
    --radius-sm: 8px;
    --radius-lg: 18px;
    --font: 'DM Sans', sans-serif;
    --serif: 'DM Serif Display', serif;
  }

  body {
    background: var(--bg);
    color: var(--text);
    font-family: var(--font);
    min-height: 100vh;
    line-height: 1.6;
  }

  /* Subtle grid background */
  body::before {
    content: '';
    position: fixed;
    inset: 0;
    background-image:
      linear-gradient(rgba(59,130,246,0.03) 1px, transparent 1px),
      linear-gradient(90deg, rgba(59,130,246,0.03) 1px, transparent 1px);
    background-size: 40px 40px;
    pointer-events: none;
    z-index: 0;
  }

  .page-wrap {
    position: relative;
    z-index: 1;
    max-width: 560px;
    margin: 0 auto;
    padding: 48px 20px 64px;
  }

  .page-wrap-wide {
    position: relative;
    z-index: 1;
    max-width: 960px;
    margin: 0 auto;
    padding: 40px 24px 64px;
  }

  /* Header */
  .site-header {
    text-align: center;
    margin-bottom: 40px;
  }

  .site-header .badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: var(--accent-glow);
    border: 1px solid rgba(59,130,246,0.25);
    color: #93c5fd;
    font-size: 11px;
    font-weight: 500;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    padding: 5px 12px;
    border-radius: 100px;
    margin-bottom: 16px;
  }

  .site-header h1 {
    font-family: var(--serif);
    font-size: 2.1rem;
    font-weight: 400;
    color: var(--text);
    letter-spacing: -0.01em;
    line-height: 1.2;
    margin-bottom: 8px;
  }

  .site-header p {
    color: var(--text-muted);
    font-size: 14px;
  }

  /* Card */
  .card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius-lg);
    padding: 28px 28px;
    margin-bottom: 20px;
  }

  .card-title {
    font-size: 13px;
    font-weight: 500;
    color: var(--text-muted);
    letter-spacing: 0.05em;
    text-transform: uppercase;
    margin-bottom: 20px;
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .card-title::before {
    content: '';
    display: block;
    width: 3px;
    height: 13px;
    background: var(--accent);
    border-radius: 2px;
  }

  /* Form elements */
  .field {
    margin-bottom: 16px;
  }

  .field label {
    display: block;
    font-size: 13px;
    font-weight: 500;
    color: var(--text-muted);
    margin-bottom: 7px;
    letter-spacing: 0.03em;
  }

  .field input,
  .field select {
    width: 100%;
    padding: 11px 15px;
    background: var(--surface2);
    border: 1px solid var(--border-light);
    border-radius: var(--radius-sm);
    color: var(--text);
    font-family: var(--font);
    font-size: 15px;
    outline: none;
    transition: border-color 0.2s, box-shadow 0.2s;
    appearance: none;
    -webkit-appearance: none;
  }

  .field input:focus,
  .field select:focus {
    border-color: var(--accent);
    box-shadow: 0 0 0 3px var(--accent-glow);
  }

  .field input::placeholder { color: var(--text-dim); }

  .select-wrap { position: relative; }
  .select-wrap::after {
    content: '';
    position: absolute;
    right: 14px;
    top: 50%;
    transform: translateY(-50%);
    width: 0;
    height: 0;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid var(--text-muted);
    pointer-events: none;
  }

  /* Buttons */
  .btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    padding: 12px 24px;
    border-radius: var(--radius-sm);
    font-family: var(--font);
    font-size: 15px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
    border: none;
    text-decoration: none;
  }

  .btn-primary {
    background: var(--accent);
    color: white;
    width: 100%;
    margin-top: 4px;
  }

  .btn-primary:hover { background: #2563eb; transform: translateY(-1px); }
  .btn-primary:active { transform: translateY(0); }

  .btn-ghost {
    background: transparent;
    color: var(--text-muted);
    border: 1px solid var(--border-light);
    font-size: 13px;
    padding: 8px 16px;
  }

  .btn-ghost:hover { background: var(--surface2); color: var(--text); }

  .btn-danger {
    background: rgba(239,68,68,0.1);
    color: #fca5a5;
    border: 1px solid rgba(239,68,68,0.2);
    font-size: 12px;
    padding: 5px 12px;
    border-radius: 6px;
    text-decoration: none;
    transition: all 0.2s;
  }

  .btn-danger:hover { background: rgba(239,68,68,0.2); }

  /* Alert / Message */
  .alert {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 13px 16px;
    border-radius: var(--radius-sm);
    font-size: 14px;
    margin-bottom: 20px;
    animation: fadeSlide 0.3s ease;
  }

  .alert-success {
    background: rgba(16,185,129,0.1);
    border: 1px solid rgba(16,185,129,0.25);
    color: #6ee7b7;
  }

  .alert-error {
    background: rgba(239,68,68,0.1);
    border: 1px solid rgba(239,68,68,0.25);
    color: #fca5a5;
  }

  @keyframes fadeSlide {
    from { opacity: 0; transform: translateY(-8px); }
    to   { opacity: 1; transform: translateY(0); }
  }

  /* Token display */
  .token-display {
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: var(--surface2);
    border: 1px solid var(--border-light);
    border-radius: var(--radius-sm);
    padding: 14px 18px;
    margin-bottom: 16px;
  }

  .token-display .label {
    font-size: 12px;
    color: var(--text-muted);
    margin-bottom: 2px;
  }

  .token-display .value {
    font-size: 28px;
    font-family: var(--serif);
    color: var(--accent2);
    line-height: 1;
  }

  .token-display .doctor-name {
    font-size: 14px;
    font-weight: 500;
    color: var(--text);
  }

  /* QR container */
  .qr-wrap {
    text-align: center;
    background: white;
    border-radius: var(--radius);
    padding: 16px;
    display: inline-block;
    margin: 0 auto 20px;
    display: block;
  }

  /* Availability grid */
  .avail-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
    margin-top: 4px;
  }

  .avail-item {
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    padding: 14px 16px;
    display: flex;
    align-items: center;
    justify-content: space-between;
  }

  .avail-item .spec {
    font-size: 13px;
    color: var(--text-muted);
    font-weight: 500;
  }

  .avail-item .slots {
    font-size: 15px;
    font-weight: 600;
    color: var(--success);
  }

  .avail-item .slots.low { color: var(--warning); }
  .avail-item .slots.full { color: var(--danger); }

  /* Footer link */
  .footer-link {
    text-align: center;
    margin-top: 24px;
  }

  .footer-link a {
    font-size: 13px;
    color: var(--text-dim);
    text-decoration: none;
    transition: color 0.2s;
  }

  .footer-link a:hover { color: var(--accent); }

  /* Admin styles */
  .admin-nav {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 32px;
    padding-bottom: 20px;
    border-bottom: 1px solid var(--border);
  }

  .admin-nav h1 {
    font-family: var(--serif);
    font-size: 1.6rem;
    font-weight: 400;
  }

  .summary-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 12px;
    margin-bottom: 32px;
  }

  @media (max-width: 700px) {
    .summary-grid { grid-template-columns: repeat(2, 1fr); }
    .avail-grid { grid-template-columns: 1fr; }
  }

  .summary-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 16px 18px;
  }

  .summary-card .doc-label {
    font-size: 11px;
    font-weight: 500;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-bottom: 10px;
  }

  .summary-card .stat-row {
    display: flex;
    align-items: baseline;
    gap: 6px;
    margin-bottom: 4px;
  }

  .summary-card .stat-num {
    font-size: 22px;
    font-weight: 600;
    color: var(--text);
  }

  .summary-card .stat-label {
    font-size: 12px;
    color: var(--text-muted);
  }

  .summary-card .progress-bar {
    height: 3px;
    background: var(--border-light);
    border-radius: 2px;
    margin-top: 10px;
    overflow: hidden;
  }

  .summary-card .progress-fill {
    height: 100%;
    background: var(--accent);
    border-radius: 2px;
    transition: width 0.4s;
  }

  /* Booking tables */
  .section-label {
    font-size: 12px;
    font-weight: 500;
    color: var(--text-muted);
    letter-spacing: 0.07em;
    text-transform: uppercase;
    margin-bottom: 10px;
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .booking-table-wrap {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    overflow: hidden;
    margin-bottom: 20px;
  }

  .booking-table-wrap table {
    width: 100%;
    border-collapse: collapse;
    font-size: 14px;
  }

  .booking-table-wrap thead tr {
    background: var(--surface2);
  }

  .booking-table-wrap th {
    padding: 11px 16px;
    text-align: left;
    font-size: 11px;
    font-weight: 500;
    color: var(--text-muted);
    letter-spacing: 0.06em;
    text-transform: uppercase;
    border-bottom: 1px solid var(--border);
  }

  .booking-table-wrap td {
    padding: 12px 16px;
    border-bottom: 1px solid var(--border);
    color: var(--text);
    vertical-align: middle;
  }

  .booking-table-wrap tr:last-child td { border-bottom: none; }

  .booking-table-wrap tr:hover td { background: rgba(255,255,255,0.015); }

  .token-badge {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 28px;
    height: 28px;
    border-radius: 6px;
    background: var(--accent-glow);
    border: 1px solid rgba(59,130,246,0.2);
    color: #93c5fd;
    font-size: 12px;
    font-weight: 600;
  }

  .empty-state {
    text-align: center;
    padding: 24px;
    color: var(--text-dim);
    font-size: 13px;
  }
</style>
"""

# -------- HOME --------
@app.route("/", methods=["GET", "POST"])
def home():
    message = ""
    qr_img = ""
    token_info = ""
    doctor_booked = ""

    data = load()

    if request.method == "POST":
        name = request.form["name"]
        doctor = request.form["doctor"]

        lock.acquire()

        token = len(data[doctor]) + 1
        time = increment_clock()

        data[doctor].append({
            "name": name,
            "token": token,
            "lamport_time": time
        })

        save(data)
        lock.release()

        # QR
        qr_data = json.dumps({
            "name": name,
            "doctor": doctor,
            "token": token,
            "ahead": token - 1
        })

        img = qrcode.make(qr_data)
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        qr_img = base64.b64encode(buffer.getvalue()).decode()

        message = f"Token booked successfully for {name}!"
        token_info = f"#{token}"
        doctor_booked = doctor

    availability = {doc: 50 - len(data[doc]) for doc in DOCTORS}
    options = "".join([f'<option value="{doc}">{doc}</option>' for doc in DOCTORS])

    success_block = ""
    if message:
        success_block = f"""
        <div class="alert alert-success">
          <svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M20 6L9 17l-5-5"/></svg>
          {message}
        </div>
        <div class="token-display">
          <div>
            <div class="label">Your Token Number</div>
            <div class="value">{token_info}</div>
          </div>
          <div style="text-align:right">
            <div class="label">Department</div>
            <div class="doctor-name">{doctor_booked}</div>
          </div>
        </div>
        <div class="qr-wrap">
          <img src="data:image/png;base64,{qr_img}" width="180" style="display:block;"/>
        </div>
        <p style="text-align:center;font-size:12px;color:var(--text-dim);margin-bottom:20px;">Scan QR code at the reception desk</p>
        """

    avail_items = ""
    for doc in DOCTORS:
        slots = availability[doc]
        cls = "full" if slots == 0 else ("low" if slots < 10 else "")
        avail_items += f"""
        <div class="avail-item">
          <span class="spec">{doc}</span>
          <span class="slots {cls}">{slots} left</span>
        </div>
        """

    return render_template_string(f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  {BASE_STYLE}
  <title>Hospital Token System</title>
</head>
<body>
<div class="page-wrap">

  <div class="site-header">
    <div class="badge">
      <svg width="8" height="8" viewBox="0 0 8 8"><circle cx="4" cy="4" r="4" fill="#3b82f6"/></svg>
      Live Token System
    </div>
    <h1>Hospital Token Booking</h1>
    <p>Reserve your consultation slot in seconds</p>
  </div>

  <div class="card">
    <div class="card-title">Book Appointment</div>

    {success_block}

    <form method="post">
      <div class="field">
        <label>Full Name</label>
        <input name="name" placeholder="Enter your full name" required>
      </div>
      <div class="field">
        <label>Select Department</label>
        <div class="select-wrap">
          <select name="doctor">{options}</select>
        </div>
      </div>
      <button class="btn btn-primary" type="submit">
        <svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M12 5v14M5 12h14"/></svg>
        Book Token
      </button>
    </form>
  </div>

  <div class="card">
    <div class="card-title">Slot Availability</div>
    <div class="avail-grid">{avail_items}</div>
  </div>

  <div class="footer-link">
    <a href="/login">Admin Access &rarr;</a>
  </div>

</div>
</body>
</html>
""")


# -------- LOGIN --------
@app.route("/login", methods=["GET","POST"])
def login():
    error = ""

    if request.method == "POST":
        if request.form["user"] == ADMIN_USER and request.form["pass"] == ADMIN_PASS:
            session["admin"] = True
            return redirect("/admin")
        else:
            error = "Invalid username or password."

    error_block = f"""
    <div class="alert alert-error">
      <svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><path d="M12 8v4M12 16h.01"/></svg>
      {error}
    </div>
    """ if error else ""

    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  {BASE_STYLE}
  <title>Admin Login</title>
</head>
<body>
<div class="page-wrap" style="max-width:420px;">

  <div class="site-header">
    <div class="badge">
      <svg width="8" height="8" viewBox="0 0 8 8"><circle cx="4" cy="4" r="4" fill="#3b82f6"/></svg>
      Secure Access
    </div>
    <h1>Admin Login</h1>
    <p>Sign in to manage hospital bookings</p>
  </div>

  <div class="card">
    <div class="card-title">Credentials</div>

    {error_block}

    <form method="post">
      <div class="field">
        <label>Username</label>
        <input name="user" placeholder="Enter username" autocomplete="username" required>
      </div>
      <div class="field">
        <label>Password</label>
        <input type="password" name="pass" placeholder="Enter password" autocomplete="current-password" required>
      </div>
      <button class="btn btn-primary" type="submit">
        <svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M15 3h4a2 2 0 012 2v14a2 2 0 01-2 2h-4M10 17l5-5-5-5M15 12H3"/></svg>
        Sign In
      </button>
    </form>
  </div>

  <div class="footer-link">
    <a href="/">&larr; Back to Booking</a>
  </div>

</div>
</body>
</html>
"""


# -------- ADMIN --------
@app.route("/admin")
def admin():
    if not session.get("admin"):
        return redirect("/login")

    data = load()

    # Summary cards
    summary_cards = ""
    for doc in DOCTORS:
        booked = len(data[doc])
        available = 50 - booked
        pct = int((booked / 50) * 100)
        summary_cards += f"""
        <div class="summary-card">
          <div class="doc-label">{doc}</div>
          <div class="stat-row">
            <span class="stat-num">{booked}</span>
            <span class="stat-label">booked</span>
          </div>
          <div style="font-size:12px;color:var(--text-muted);">{available} of 50 remaining</div>
          <div class="progress-bar">
            <div class="progress-fill" style="width:{pct}%"></div>
          </div>
        </div>
        """

    # Booking tables
    tables = ""
    for doc in DOCTORS:
        rows = ""
        if data[doc]:
            for d in data[doc]:
                rows += f"""
                <tr>
                  <td><span class="token-badge">{d['token']}</span></td>
                  <td style="font-weight:500;">{d['name']}</td>
                  <td style="color:var(--text-muted);font-size:12px;">{d['lamport_time']}</td>
                  <td><a href="/cancel/{doc}/{d['token']}" class="btn-danger">Cancel</a></td>
                </tr>
                """
        else:
            rows = '<tr><td colspan="4" class="empty-state">No bookings yet</td></tr>'

        tables += f"""
        <div class="section-label">{doc}</div>
        <div class="booking-table-wrap">
          <table>
            <thead>
              <tr>
                <th style="width:60px;">Token</th>
                <th>Patient Name</th>
                <th>Lamport Time</th>
                <th style="width:80px;">Action</th>
              </tr>
            </thead>
            <tbody>{rows}</tbody>
          </table>
        </div>
        """

    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  {BASE_STYLE}
  <title>Admin Dashboard</title>
</head>
<body>
<div class="page-wrap-wide">

  <div class="admin-nav">
    <div>
      <div style="font-size:11px;letter-spacing:0.07em;text-transform:uppercase;color:var(--text-muted);margin-bottom:4px;">Admin Dashboard</div>
      <h1>Booking Overview</h1>
    </div>
    <a href="/logout" class="btn btn-ghost">
      <svg width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4M16 17l5-5-5-5M21 12H9"/></svg>
      Sign Out
    </a>
  </div>

  <div class="summary-grid">{summary_cards}</div>

  {tables}

</div>
</body>
</html>
"""


# -------- CANCEL --------
@app.route("/cancel/<doctor>/<int:token>")
def cancel(doctor, token):
    if not session.get("admin"):
        return redirect("/login")

    lock.acquire()
    data = load()
    data[doctor] = [d for d in data[doctor] if d["token"] != token]
    for i, d in enumerate(data[doctor]):
        d["token"] = i + 1
    save(data)
    lock.release()

    return redirect("/admin")


# -------- LOGOUT --------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# -------- RUN --------
if __name__ == "__main__":
    print("Server starting...")
    app.run(port=5000, debug=True)