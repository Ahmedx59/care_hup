# Healthcare Management System

This repository contains the backend for a healthcare management system. The system provides a robust platform for managing healthcare professionals, patients, and bookings, along with advanced search and authentication functionalities.

---

## Features

### APIs for Doctors, Nurses, and Patients
- Manage profiles for doctors, nurses, and patients.
- View and update detailed information, including contact details, specialties, and availability.

### Advanced Search
- Search for patients by name, ID, or medical history.
- Find doctors and nurses by specialty, location, or availability.
- Locate nearby hospitals based on geographical data.

### Authentication
- Full-featured user authentication system.
- Token-based authentication using JWT (JSON Web Tokens).
- Secure login, registration, and password reset functionalities.

### Articles Section
- Browse and manage healthcare-related articles.
- Useful for educational purposes or providing relevant health tips.

### Booking System
- Schedule appointments with doctors or nurses.
- View booking history and manage reschedules or cancellations.

### Notifications and Background Tasks
- Send notifications to users for upcoming appointments and reminders.
- Use Celery and Redis for task queuing and asynchronous operations.

---

## Tech Stack

### Core Technologies
- **Python**: The primary programming language for the backend.
- **Django**: A powerful web framework for rapid development.
- **Django REST Framework (DRF)**: Used to build scalable RESTful APIs.

### Authentication
- **JWT (JSON Web Tokens)**: For secure token-based authentication.

### Databases
- **SQLite**: For development and testing environments.
- **PostgreSQL**: A robust, scalable database for production.

### Containerization and Deployment
- **Docker**: For containerized application deployment.
- **Docker Compose**: To manage multi-container setups for development and production.

### Asynchronous Processing
- **Celery**: For background task processing (e.g., sending notifications, report generation).
- **Redis**: As a message broker for Celery tasks.

### Development Tools
- **Postman**: For API testing and documentation.
- **pytest**: For writing and running unit tests.
- **coverage.py**: For measuring code test coverage.

---

## Installation

### Prerequisites

- Python 3.9+
- Docker (for containerized deployment)
- PostgreSQL (for production database)

### Installation and Usage

To set up and run the Dj-Amazon-Clone project locally, please follow the instructions below:
1. Clone the repository:
   ```bash
   git clone https://github.com/Ahmedx59/Care-Hup-using-DRF.git
   ```
2. Navigate into the project directory:
   ```bash
   cd Care-Hup-using-DRF
   ```
3. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Set up the database:
   - If using SQLite:
     ```bash
     python manage.py migrate
     ```
   - If using PostgreSQL:
     ```bash
     # Update the database settings in settings.py to match your PostgreSQL configuration
     python manage.py migrate
     ```
5. Start the development server:
   ```bash
   python manage.py runserver
   ```
6. Access the API endpoints at `http://localhost:8000/api/`.

