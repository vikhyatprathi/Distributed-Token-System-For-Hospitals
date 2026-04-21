Multi-Doctor Distributed Token Management System

A **distributed hospital queue management system** that allows patients to book tokens for multiple doctors independently, with real-time synchronization, admin control, and QR-based verification.

Features
**Multi-Doctor Token System**

  * Orthopedic
  * Pediatric
  * ENT
  * Dermatologist

**Independent Queues**

  * Each doctor has a separate token sequence

**Admin Dashboard**

  * Secure login
  * View all queues
  * Cancel bookings
  * Real-time statistics

**QR Code Generation**

  * Contains:

    * Patient name
    * Doctor
    * Token number
    * Queue position

**Concurrency Control**

  * Prevents duplicate tokens using locks

**Lamport Logical Clock**

  * Maintains event ordering in distributed system

**Distributed Access**

  * Accessible across devices using ngrok

System Architecture
Client (Browser / Mobile)
          ↓
   Flask Server (Coordinator)
          ↓
     bookings.json


* `coordinator.py` → Main server (handles logic)
* `bookings.json` → Data storage
* Clients connect via browser or ngrok

---

Tech Stack

* **Language:** Python

* **Framework:** Flask

* **Libraries:**

  * qrcode
  * threading
  * json

* **Tools:**

  * ngrok
  * Postman

---

Installation

1. Clone the repository

```bash
git clone https://github.com/your-username/token-system.git
cd token-system
```

---

2. Install dependencies

```bash
pip install flask qrcode[pil]
```

---

3. Run the server
bash
python coordinator.py

Open in browser:
http://127.0.0.1:5000


**Run with ngrok (Distributed Access)**
bash
ngrok http 5000

Copy the public URL and open on another device.

**Usage**

Patient:
* Enter name
* Select doctor
* Book token
* Receive QR code

Admin:
* Go to `/login`
* Credentials:
```
Username: admin
Password: 1234
```

Key Concepts Demonstrated

* Distributed Systems
* Concurrency Control
* Lamport Logical Clocks
* Client-Server Architecture
* Multi-Queue Management
* QR-based Identification


Just tell 👍
