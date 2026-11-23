import hmac
import os
from flask import Flask, render_template, request, redirect, url_for, flash, session, Response
from database import init_db, get_db
from service import create_ticket, list_tickets, change_ticket_status, estimate_wait, QueueError

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "local-development-key-change-before-deploy")

@app.before_request
def protect_operator():
    # Set OPERATOR_PASSWORD in the hosting dashboard before publishing.
    password = os.environ.get("OPERATOR_PASSWORD")
    if request.path.startswith("/operator") and password:
        auth = request.authorization
        if not auth or auth.username != "operator" or not hmac.compare_digest(auth.password or "", password):
            return Response("Требуется вход оператора", 401, {"WWW-Authenticate": 'Basic realm="Панель деканата"'})

@app.before_request
def setup():
    init_db()

@app.get("/")
def index():
    lang = request.args.get("lang", session.get("lang", "ru"))
    if lang not in ("ru", "kk"):
        lang = "ru"
    session["lang"] = lang
    return render_template("index.html", lang=lang)

@app.post("/ticket")
def ticket_create():
    name = request.form.get("name", "").strip()
    service = request.form.get("service", "").strip()
    try:
        ticket_id = create_ticket(name, service)
        return redirect(url_for("ticket_page", ticket_id=ticket_id))
    except QueueError as exc:
        flash(str(exc), "error")
        return redirect(url_for("index"))

@app.get("/ticket/<int:ticket_id>")
def ticket_page(ticket_id):
    db = get_db()
    ticket = db.execute(
        "SELECT t.*, s.title AS service_title FROM tickets t "
        "JOIN services s ON s.id=t.service_id WHERE t.id=?", (ticket_id,)
    ).fetchone()
    if ticket is None:
        return render_template("error.html", message="Талон не найден / Талон табылмады"), 404
    waiting = db.execute(
        "SELECT COUNT(*) FROM tickets WHERE status='waiting' AND ticket_number < ?",
        (ticket["ticket_number"],)
    ).fetchone()[0]
    return render_template("ticket.html", ticket=ticket, wait=estimate_wait(waiting),
                           lang=session.get("lang", "ru"))

@app.get("/operator")
def operator():
    return render_template("operator.html", tickets=list_tickets(),
                           lang=session.get("lang", "ru"))

@app.post("/operator/<int:ticket_id>")
def operator_update(ticket_id):
    status = request.form.get("status", "")
    try:
        change_ticket_status(ticket_id, status)
    except QueueError as exc:
        flash(str(exc), "error")
    return redirect(url_for("operator"))

@app.get("/health")
def health():
    return {"status": "ok"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5001)), debug=False)
