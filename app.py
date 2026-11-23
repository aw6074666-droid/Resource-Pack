@app.get("/ticket/<int:ticket_id>")
def ticket_page(ticket_id):
    db = get_db()
    ticket = db.execute(
        "SELECT t.*, s.title AS service_title, st.full_name FROM tickets t "
        "JOIN students st ON st.id=t.student_id "
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
