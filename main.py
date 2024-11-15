from flask import Flask, render_template, session, request, redirect, url_for
from flask_socketio import SocketIO, send, join_room, leave_room
import random
from string import ascii_uppercase

app = Flask(__name__)
app.config["SECRET_KEY"] = "berry_key"
socketio = SocketIO(app)

rooms = {}


def generate_unique_code(length):
    while True:
        code = ""
        for i in range(length):
            code += random.choice(ascii_uppercase)
        if code not in rooms:
            break
    return code


@app.route("/", methods=["POST", "GET"])
def home():
    session.clear()
    if request.method == "POST":
        name = request.form.get("name")
        code = request.form.get("code")
        join = request.form.get("join", False)
        create = request.form.get("create", False)
        if not name:
            return render_template("home.html", error="Please insert a name")
        elif join is not False and not code:
            return render_template("home.html", error="Insert a room code")

        room = code
        if create is not False:
            room = generate_unique_code(5)
            rooms[room] = {"members": 0, "messages": []}
        elif code not in rooms:
            return render_template("home.html", error="Insert a valid code")
        session["name"] = name
        session["room"] = room
        return redirect(url_for("handle_room"))
    return render_template("home.html")


@app.route("/room")
def handle_room():
    room = session.get("room")
    if room not in rooms:
        return redirect(url_for("home"))
    return render_template("room.html", code=room)


@socketio.on("connect")
def handle_connect():
    name = session.get("name")
    room = session.get("room")
    if not name or not room:
        return
    elif room not in rooms:
        leave_room(room)
        return

    join_room(room)
    send({"name": name, "message": "has entered room"}, to=room)
    rooms[room]["members"] += 1
    print(f"{name} joined room {room}")


@socketio.on("disconnect")
def handle_disconnect():
    name = session.get("name")
    room = session.get("room")
    leave_room(room)

    if room in rooms:
        rooms[room]["members"] -= 1
        if rooms[room]["members"] <= 0:
            del rooms[room]
    send({"name": name, "message": "has left the room"}, to=room)
    print(f"{name} has left the room {room}")


@socketio.on("message")
def message(data):
    room = session.get("room")

    if room not in rooms:
        return

    content = {
        "name": session.get("name"),
        "message": data["data"]
    }

    send(content, to=room)
    print(f"{session.get('name')}: {data['data']}")


if __name__ == "__main__":
    socketio.run(app, debug=True)

