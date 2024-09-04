from flask import Flask, render_template, redirect, url_for, request, session
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_socketio import SocketIO, emit
import uuid

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
socketio = SocketIO(app)

# In-memory storage for users and roles by room
rooms_users = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/new-meeting')
def new_meeting():
    room_id = str(uuid.uuid4())  # Generate a unique room ID
    return redirect(url_for('meeting', room=room_id))

@app.route('/meeting/<room>', methods=['GET', 'POST'])
def meeting(room):
    if request.method == 'POST':
        username = request.form['username']
        session['username'] = username
        if room not in rooms_users:
            rooms_users[room] = []
            session['role'] = 'Host'
        else:
            session['role'] = 'Guest'
        
        rooms_users[room].append({'username': username, 'role': session['role']})
        
        return render_template('meeting.html', room=room, users=rooms_users[room])
    return render_template('join_meeting.html', room=room)

@socketio.on('join')
def handle_join(data):
    room = data['room']
    username = session.get('username')
    join_room(room)
    emit('message', f"{username} has joined the room {room}", room=room)
    emit('update_users', rooms_users[room], room=room)

@socketio.on('leave')
def handle_leave(data):
    room = data['room']
    username = session.get('username')
    leave_room(room)
    if room in rooms_users:
        rooms_users[room] = [user for user in rooms_users[room] if user['username'] != username]
        if not rooms_users[room]:
            del rooms_users[room]  # Clean up empty rooms
    emit('message', f"{username} has left the room {room}", room=room)
    emit('update_users', rooms_users[room], room=room)

if __name__ == '__main__':
    socketio.run(app, debug=True)
    
# Initialize Flask-SocketIO
socketio = SocketIO(app, cors_allowed_origins="*")

@socketio.on('chat_message')
def handle_chat_message(data):
    room = data['room']
    message = data['message']
    emit('chat_message', {'username': 'User', 'message': message}, room=room)
