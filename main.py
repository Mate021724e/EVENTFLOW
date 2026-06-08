"""
EventFlow REST API  —  з Swagger UI
Run:  python main.py
Docs: http://localhost:5000/apidocs
"""
import sys
sys.path.insert(0, '.')

from flask import Flask, request, jsonify
from flasgger import Swagger, swag_from
from datetime import datetime

from src.storage.in_memory import (
    InMemoryEventRepository,
    InMemoryUserRepository,
    InMemoryRegistrationRepository,
)
from src.services.event_service import EventService
from src.services.user_service import UserService
from src.services.registration_service import RegistrationService
from src.services.calendar_service import CalendarService
from src.models.event import EventCategory
from src.models.user import UserRole, User
from src.utils.id_generator import generate_user_id
from src.utils.exceptions import EventFlowError

# ── Init ──────────────────────────────────────────────────────────────────────
app = Flask(__name__)

swagger_config = {
    "headers": [],
    "specs": [{"endpoint": "apispec", "route": "/apispec.json"}],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/apidocs",
}
swagger_template = {
    "info": {
        "title": "EventFlow API",
        "description": "REST API для управління подіями, учасниками та реєстраціями.\n\n"
                       "**Швидкий старт:**\n"
                       "1. `POST /users/organizer` — створити організатора\n"
                       "2. `POST /events` — створити подію\n"
                       "3. `POST /events/{id}/publish` — опублікувати\n"
                       "4. `POST /users/participant` — створити учасника\n"
                       "5. `POST /registrations` — зареєструватися\n\n"
                       "ℹ️ Admin ID для seed-даних доступний у відповіді `GET /admin-id`",
        "version": "1.0.0",
    },
    "tags": [
        {"name": "users",         "description": "Управління користувачами"},
        {"name": "events",        "description": "Управління подіями"},
        {"name": "registrations", "description": "Реєстрації на події"},
        {"name": "calendar",      "description": "Календар та фільтри"},
    ],
}
Swagger(app, config=swagger_config, template=swagger_template)

user_repo  = InMemoryUserRepository()
event_repo = InMemoryEventRepository()
reg_repo   = InMemoryRegistrationRepository()

user_svc  = UserService(user_repo)
event_svc = EventService(event_repo)
reg_svc   = RegistrationService(reg_repo, event_repo, user_repo)
cal_svc   = CalendarService(event_repo)

_admin = User(id=generate_user_id(), name="Admin", email="admin@eventflow.dev", role=UserRole.ADMIN)
user_repo.add(_admin)
ADMIN_ID = _admin.id

# ── Helpers ───────────────────────────────────────────────────────────────────
def ok(data=None):
    return jsonify({"ok": True, "data": data})

def err(msg, code=400):
    return jsonify({"ok": False, "error": msg}), code

def su(u):
    return {"id": u.id, "name": u.name, "email": u.email,
            "role": u.role.value, "status": u.status.value,
            "registrations_count": len(u.registrations)}

def se(e):
    return {"id": e.id, "title": e.title, "description": e.description,
            "category": e.category.value, "status": e.status.value,
            "location": e.location, "capacity": e.capacity,
            "registered_count": e.registered_count, "spots_left": e.spots_left(),
            "price": e.price, "tags": e.tags,
            "start_dt": e.start_dt.isoformat(), "end_dt": e.end_dt.isoformat(),
            "organizer_id": e.organizer_id}

def sr(r):
    return {"id": r.id, "user_id": r.user_id, "event_id": r.event_id,
            "status": r.status.value, "ticket_number": r.ticket_number,
            "registered_at": r.registered_at.isoformat()}

# ── System ────────────────────────────────────────────────────────────────────
@app.route("/admin-id")
def admin_id():
    """
    Отримати Admin ID (seed-дані)
    ---
    tags: [users]
    responses:
      200:
        description: Admin ID для використання в інших запитах
        schema:
          type: object
          properties:
            admin_id: {type: string, example: "USR-xxxx"}
    """
    return jsonify({"admin_id": ADMIN_ID})

# ── Users ─────────────────────────────────────────────────────────────────────
@app.route("/users/participant", methods=["POST"])
def create_participant():
    """
    Зареєструвати учасника
    ---
    tags: [users]
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [name, email]
          properties:
            name:  {type: string, example: "Олег Коваль"}
            email: {type: string, example: "oleg@example.com"}
    responses:
      201:
        description: Учасника створено
      400:
        description: Email вже існує або невалідні дані
    """
    d = request.json or {}
    try:
        return ok(su(user_svc.register_participant(d["name"], d["email"]))), 201
    except EventFlowError as e:
        return err(str(e))

@app.route("/users/organizer", methods=["POST"])
def create_organizer():
    """
    Зареєструвати організатора
    ---
    tags: [users]
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [name, email]
          properties:
            name:  {type: string, example: "Марія Шевченко"}
            email: {type: string, example: "maria@example.com"}
    responses:
      201:
        description: Організатора створено
      400:
        description: Email вже існує
    """
    d = request.json or {}
    try:
        return ok(su(user_svc.register_organizer(d["name"], d["email"]))), 201
    except EventFlowError as e:
        return err(str(e))

@app.route("/users", methods=["GET"])
def list_users():
    """
    Список усіх користувачів
    ---
    tags: [users]
    responses:
      200:
        description: Масив користувачів
    """
    return ok([su(u) for u in user_svc.get_all_users()])

@app.route("/users/<uid>", methods=["GET"])
def get_user(uid):
    """
    Отримати користувача за ID
    ---
    tags: [users]
    parameters:
      - in: path
        name: uid
        type: string
        required: true
        description: ID користувача
    responses:
      200:
        description: Дані користувача
      404:
        description: Не знайдено
    """
    try:
        return ok(su(user_svc.get_user(uid)))
    except EventFlowError as e:
        return err(str(e), 404)

@app.route("/users/<uid>/block", methods=["POST"])
def block_user(uid):
    """
    Заблокувати користувача
    ---
    tags: [users]
    parameters:
      - in: path
        name: uid
        type: string
        required: true
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [admin_id, reason]
          properties:
            admin_id: {type: string, example: "USR-xxxx"}
            reason:   {type: string, example: "Порушення правил"}
    responses:
      200:
        description: Користувача заблоковано
      400:
        description: Недостатньо прав
    """
    d = request.json or {}
    try:
        return ok(su(user_svc.block_user(uid, d.get("reason", ""), d["admin_id"])))
    except EventFlowError as e:
        return err(str(e))

@app.route("/users/<uid>/unblock", methods=["POST"])
def unblock_user(uid):
    """
    Розблокувати користувача
    ---
    tags: [users]
    parameters:
      - in: path
        name: uid
        type: string
        required: true
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [admin_id]
          properties:
            admin_id: {type: string, example: "USR-xxxx"}
    responses:
      200:
        description: Розблоковано
    """
    d = request.json or {}
    try:
        return ok(su(user_svc.unblock_user(uid, d["admin_id"])))
    except EventFlowError as e:
        return err(str(e))

# ── Events ────────────────────────────────────────────────────────────────────
@app.route("/events", methods=["POST"])
def create_event():
    """
    Створити подію
    ---
    tags: [events]
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [title, organizer_id, category, start_dt, end_dt, location, capacity]
          properties:
            title:        {type: string,  example: "Python Meetup Lviv"}
            description:  {type: string,  example: "Щомісячна зустріч Python-спільноти"}
            organizer_id: {type: string,  example: "USR-xxxx"}
            category:
              type: string
              enum: [conference, workshop, concert, meetup, webinar, sport, exhibition, other]
              example: meetup
            start_dt: {type: string, example: "2026-08-10T18:00:00"}
            end_dt:   {type: string, example: "2026-08-10T21:00:00"}
            location: {type: string, example: "Львів, вул. Шевченка 1"}
            capacity: {type: integer, example: 50}
            price:    {type: number,  example: 0}
            tags:
              type: array
              items: {type: string}
              example: ["python", "lviv"]
    responses:
      201:
        description: Подію створено (статус draft)
      400:
        description: Невалідні дані
    """
    d = request.json or {}
    try:
        e = event_svc.create_event(
            title=d["title"], description=d.get("description", ""),
            organizer_id=d["organizer_id"], category=EventCategory(d["category"]),
            start_dt=datetime.fromisoformat(d["start_dt"]),
            end_dt=datetime.fromisoformat(d["end_dt"]),
            location=d["location"], capacity=int(d["capacity"]),
            price=float(d.get("price", 0)), tags=d.get("tags", []),
        )
        return ok(se(e)), 201
    except EventFlowError as e:
        return err(str(e))
    except (KeyError, ValueError) as e:
        return err(f"Bad input: {e}")

@app.route("/events", methods=["GET"])
def list_events():
    """
    Список усіх подій
    ---
    tags: [events]
    responses:
      200:
        description: Масив подій
    """
    return ok([se(e) for e in event_svc.get_all_events()])

@app.route("/events/<eid>", methods=["GET"])
def get_event(eid):
    """
    Отримати подію за ID
    ---
    tags: [events]
    parameters:
      - in: path
        name: eid
        type: string
        required: true
    responses:
      200:
        description: Дані події
      404:
        description: Не знайдено
    """
    try:
        return ok(se(event_svc.get_event(eid)))
    except EventFlowError as e:
        return err(str(e), 404)

@app.route("/events/<eid>/publish", methods=["POST"])
def publish_event(eid):
    """
    Опублікувати подію (draft → published)
    ---
    tags: [events]
    parameters:
      - in: path
        name: eid
        type: string
        required: true
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [organizer_id]
          properties:
            organizer_id: {type: string, example: "USR-xxxx"}
    responses:
      200:
        description: Подію опубліковано
      400:
        description: Немає прав або неправильний статус
    """
    d = request.json or {}
    try:
        return ok(se(event_svc.publish_event(eid, d["organizer_id"])))
    except EventFlowError as e:
        return err(str(e))
    except KeyError:
        return err("organizer_id required")

@app.route("/events/<eid>/cancel", methods=["POST"])
def cancel_event(eid):
    """
    Скасувати подію
    ---
    tags: [events]
    parameters:
      - in: path
        name: eid
        type: string
        required: true
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [organizer_id]
          properties:
            organizer_id: {type: string, example: "USR-xxxx"}
    responses:
      200:
        description: Подію скасовано
    """
    d = request.json or {}
    try:
        return ok(se(event_svc.cancel_event(eid, d["organizer_id"])))
    except EventFlowError as e:
        return err(str(e))
    except KeyError:
        return err("organizer_id required")

@app.route("/events/<eid>/registrations", methods=["GET"])
def event_registrations(eid):
    """
    Реєстрації на подію
    ---
    tags: [events]
    parameters:
      - in: path
        name: eid
        type: string
        required: true
    responses:
      200:
        description: Список реєстрацій
    """
    return ok([sr(r) for r in reg_svc.get_event_registrations(eid)])

@app.route("/events/<eid>/waitlist", methods=["GET"])
def event_waitlist(eid):
    """
    Список очікування на подію
    ---
    tags: [events]
    parameters:
      - in: path
        name: eid
        type: string
        required: true
    responses:
      200:
        description: Список очікування
    """
    return ok([sr(r) for r in reg_svc.get_waitlist(eid)])

@app.route("/events/<eid>/stats", methods=["GET"])
def event_stats(eid):
    """
    Статистика реєстрацій на подію
    ---
    tags: [events]
    parameters:
      - in: path
        name: eid
        type: string
        required: true
    responses:
      200:
        description: Статистика (confirmed, waitlisted, cancelled тощо)
    """
    return ok(reg_svc.get_statistics(eid))

# ── Registrations ─────────────────────────────────────────────────────────────
@app.route("/registrations", methods=["POST"])
def register():
    """
    Зареєструватися на подію
    ---
    tags: [registrations]
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [user_id, event_id]
          properties:
            user_id:  {type: string, example: "USR-xxxx"}
            event_id: {type: string, example: "EVT-xxxx"}
    responses:
      201:
        description: Реєстрацію підтверджено (або потрапив у waitlist)
      400:
        description: Помилка (заблокований, вже зареєстрований, ліміт тощо)
    """
    d = request.json or {}
    try:
        return ok(sr(reg_svc.register(d["user_id"], d["event_id"]))), 201
    except EventFlowError as e:
        return err(str(e))

@app.route("/registrations/<rid>", methods=["GET"])
def get_reg(rid):
    """
    Отримати реєстрацію за ID
    ---
    tags: [registrations]
    parameters:
      - in: path
        name: rid
        type: string
        required: true
    responses:
      200:
        description: Дані реєстрації
      404:
        description: Не знайдено
    """
    try:
        return ok(sr(reg_svc.get_registration(rid)))
    except EventFlowError as e:
        return err(str(e), 404)

@app.route("/registrations/<rid>/cancel", methods=["POST"])
def cancel_reg(rid):
    """
    Скасувати реєстрацію
    ---
    tags: [registrations]
    parameters:
      - in: path
        name: rid
        type: string
        required: true
    responses:
      200:
        description: Реєстрацію скасовано. Наступний у waitlist отримує місце автоматично.
    """
    try:
        return ok(sr(reg_svc.cancel_registration(rid)))
    except EventFlowError as e:
        return err(str(e))

@app.route("/registrations/<rid>/checkin", methods=["POST"])
def checkin(rid):
    """
    Відмітити відвідування (check-in)
    ---
    tags: [registrations]
    parameters:
      - in: path
        name: rid
        type: string
        required: true
    responses:
      200:
        description: Check-in виконано
    """
    try:
        return ok(sr(reg_svc.check_in(rid)))
    except EventFlowError as e:
        return err(str(e))

# ── Calendar ──────────────────────────────────────────────────────────────────
@app.route("/calendar/upcoming", methods=["GET"])
def upcoming():
    """
    Найближчі опубліковані події
    ---
    tags: [calendar]
    responses:
      200:
        description: Список майбутніх подій
    """
    return ok([se(e) for e in cal_svc.get_upcoming_events()])

@app.route("/calendar/month", methods=["GET"])
def by_month():
    """
    Події за місяць
    ---
    tags: [calendar]
    parameters:
      - in: query
        name: year
        type: integer
        example: 2026
      - in: query
        name: month
        type: integer
        example: 8
    responses:
      200:
        description: Список подій за вказаний місяць
    """
    year  = int(request.args.get("year",  datetime.now().year))
    month = int(request.args.get("month", datetime.now().month))
    return ok([se(e) for e in cal_svc.get_events_by_month(year, month)])

@app.route("/calendar/free", methods=["GET"])
def free_events():
    """
    Безкоштовні доступні події
    ---
    tags: [calendar]
    responses:
      200:
        description: Список безкоштовних подій
    """
    return ok([se(e) for e in cal_svc.get_free_events()])

@app.route("/calendar/location", methods=["GET"])
def by_location():
    """
    Пошук подій за локацією
    ---
    tags: [calendar]
    parameters:
      - in: query
        name: q
        type: string
        example: Львів
    responses:
      200:
        description: Список подій за локацією
    """
    return ok([se(e) for e in cal_svc.get_events_by_location(request.args.get("q", ""))])

# ── Run ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"\n🚀  EventFlow API  →  http://localhost:5002")
    print(f"📖  Swagger UI    →  http://localhost:5002/apidocs")
    print(f"🔑  Admin ID      →  {ADMIN_ID}\n")
    app.run(debug=True, port=5002)
