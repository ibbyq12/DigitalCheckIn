# Digital Check-In
A conceptual prototype for a digital check-in system that is tailored to the University of the West of England.

This application eliminates difficulty in the situation of a university student needing assistance from a support staff member.

It allows meetings to be arranged and students to ask questions whilst receiving the response to their email.

This application uses packages such as Socket.io, Flask, Flask-SQLAlchemy + SQLite DB, Flask-Session.

This project was signed off by a client who works at UWE that I produced this work for.

## Requirements 

Make sure all the relevant packages are installed by importing the 'venv' folder into the project directory.

Run 'app.py' which will start the Flask server.

Input your SMTP info within 'app.py' so that Flask-Mail can work. You can register for free smtp services.

The SQLite DB is created within the 'instance' folder when the server is started for the first time.
