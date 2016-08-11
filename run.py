from app.kydo import create_app

prep = create_app()
app = prep[0]
socketio = prep[1]
socketio.run(app)
