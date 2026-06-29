# Student Support Check-In System

A real-time booking kiosk built for University of the West of England (UWE) student support services. Students book meetings from a shared screen; support staff see live queue status and receive email notifications.

**Client:** Signed off by UWE IT staff after delivery.

## What it does

- **Kiosk booking** — students book support sessions from a shared display; average booking time dropped from ~10 minutes to ~2 minutes
- **Live staff dashboard** — real-time queue and status updates via WebSockets
- **Email notifications** — meeting confirmations and responses sent through SMTP (Flask-Mail)
- **Team delivery** — 3-person Agile team (Jira, Git); final demo presented to Head of IT

## Tech stack

- **Backend:** Python, Flask, Flask-SQLAlchemy, Flask-Session
- **Database:** SQLite
- **Realtime:** Socket.io
- **Email:** Flask-Mail (SMTP)

## Getting started

### Prerequisites

- Python 3.10+
- pip

### Setup

```bash
git clone https://github.com/ibrahim-qi/student-support-booking-system.git
cd student-support-booking-system
python -m venv venv
```

**Windows:**
```bash
venv\Scripts\activate
pip install -r requirements.txt
```

**macOS / Linux:**
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Configuration

Set SMTP credentials via environment variables (do not commit secrets):

```bash
export MAIL_SERVER=smtp.example.com
export MAIL_USERNAME=your@email.com
export MAIL_PASSWORD=your-app-password
```

### Run

```bash
python app.py
```

On first run, SQLite creates the database under `instance/`.

## Screenshots

![Kiosk view](https://github.com/ibbyq12/DigitalCheckIn/assets/100475296/36ef295e-9315-499c-bbfb-a9b5699fb6cf)
![Booking flow](https://github.com/ibbyq12/DigitalCheckIn/assets/100475296/33d8693d-f5cc-4bd5-a990-f905e123be85)
![Staff dashboard](https://github.com/ibbyq12/DigitalCheckIn/assets/100475296/286c81fb-9f27-4771-a9e6-139c99e6421a)
![Queue status](https://github.com/ibbyq12/DigitalCheckIn/assets/100475296/b5a175b3-72d9-4127-8a76-da8138018169)
![Meeting details](https://github.com/ibbyq12/DigitalCheckIn/assets/100475296/ceeae3c0-c556-417d-8847-ebb49411efb5)
![Email notification](https://github.com/ibbyq12/DigitalCheckIn/assets/100475296/b8bc7fe3-951d-43cf-bc13-485ab809f01d)
