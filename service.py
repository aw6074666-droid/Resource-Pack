from database import get_db

class QueueError(ValueError):
    pass

ALLOWED_STATUSES = {"waiting", "serving", "done"}

def create_ticket(name, service):
    name = (name or "").strip()
    service = (service or "").strip()
    if len(name) < 2 or len(name) > 80:
        raise QueueError("Введите имя длиной от 2 до 80 символов.")
    if not service:
        raise QueueError("Выберите услугу.")
    with get_db() as db:
        service_row = db.execute("SELECT id FROM services WHERE title=?", (service,)).fetchone()
        if service_row is None:
            raise QueueError("Выбранная услуга не найдена.")
        number = db.execute("SELECT COALESCE(MAX(ticket_number), 0)+1 FROM tickets").fetchone()[0]
        student_id = db.execute("INSERT INTO students(full_name) VALUES (?)", (name,)).lastrowid
        ticket_id = db.execute(
            "INSERT INTO tickets(student_id, service_id, ticket_number) VALUES (?, ?, ?)",
            (student_id, service_row["id"], number)
        ).lastrowid
        return ticket_id

def list_tickets():
    with get_db() as db:
        return db.execute("""
            SELECT t.id, t.ticket_number, s.full_name, v.title AS service,
                   t.status, t.created_at
            FROM tickets t JOIN students s ON s.id=t.student_id
            JOIN services v ON v.id=t.service_id
            ORDER BY CASE t.status WHEN 'serving' THEN 0 WHEN 'waiting' THEN 1 ELSE 2 END,
                     t.ticket_number
        """).fetchall()

def change_ticket_status(ticket_id, status):
    if status not in ALLOWED_STATUSES:
        raise QueueError("Недопустимый статус талона.")
    with get_db() as db:
        cur = db.execute("UPDATE tickets SET status=? WHERE id=?", (status, ticket_id))
        if cur.rowcount == 0:
            raise QueueError("Талон не найден.")

def estimate_wait(waiting_count, minutes_per_person=10):
    if waiting_count < 0 or minutes_per_person < 0:
        raise QueueError("Количество и время не могут быть отрицательными.")
    return waiting_count * minutes_per_person
