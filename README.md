# 🎓 Face Recognition Attendance System

A **Python-based GUI Attendance System** that uses **Face Recognition (OpenCV + LBPH Algorithm)** to automate student attendance management.

This project is designed for **college-level deployment**, supporting **Admin & Department roles**, student registration, attendance tracking, reporting, and data management.

---

## 🚀 Features

### 👤 Authentication System
- Secure login system (Admin & Department users)
- Passwords stored using **SHA-256 hashing**
- Role-based access control

### 🧑‍🎓 Student Management
- Add student details (ID, Name, Email, Department, Session)
- Capture face images using camera
- Store student data in CSV format
- Delete students (Admin only)

### 📸 Face Data Collection
- Capture multiple face samples per student
- Auto image flipping for better training
- Stores images in `TrainingImage/`

### 🧠 Face Recognition Model
- Uses **LBPH (Local Binary Pattern Histogram)**
- Trains model using captured images
- Saves trained model (`trainer.yml`)

### ✅ Attendance System
- Real-time face detection & recognition
- Marks attendance automatically
- Prevents duplicate entries using cooldown
- Saves attendance in CSV files

### 📊 Reports & Analytics
- Daily attendance records
- Student-wise attendance summary
- Department-wise filtering
- Export data to CSV / Excel

### 🏫 Admin Panel
- Create department logins
- Assign sessions
- Reset passwords
- View department strength

### ⚙️ Settings & Configuration
- Camera configuration (IP/Webcam)
- Sample count control
- Confidence threshold adjustment
- Attendance cooldown control

### 💾 Backup System
- Create backups of:
  - Student data
  - Attendance records
  - Model files

---

## 🛠️ Tech Stack

- Python  
- Tkinter (GUI)  
- OpenCV (Face Detection & Recognition)  
- NumPy  
- Pandas  
- PIL (Pillow)  

---

## 📂 Project Structure

```
📁 Face Recognition Attendance System
│
├── TrainingImage/              # Captured face images
├── TrainingImageLabel/         # Trained model + ID mapping
├── StudentDetails/             # Student CSV data
├── Attendance/                 # Attendance CSV files
├── Logs/                       # Activity logs
├── Exports/                    # Exported reports
├── Backups/                    # Backup data
├── config.json                 # System configuration
├── haarcascade_frontalface_default.xml
└── app.py                      # Main application file
```

---

## ⚙️ Installation & Setup

### 1️⃣ Clone Repository
```bash
git clone https://github.com/your-username/face-recognition-attendance.git
cd face-recognition-attendance
```

### 2️⃣ Install Dependencies
```bash
pip install opencv-python opencv-contrib-python numpy pandas pillow
```

### 3️⃣ Add Haar Cascade File
Download:
```
haarcascade_frontalface_default.xml
```
Place it in the root directory.

---

## ▶️ Run the Project

```bash
python main.py
```

---

## 🔐 Default Login

```
Username: Admin
Password: Admin123
```

---

## 👥 User Roles

### 👑 Admin
- Manage departments
- View all data
- Delete students
- Generate reports
- Backup system

### 🏫 Department User
- Register students
- Capture images
- Train model
- Take attendance
- View department data only

---

## 📸 How It Works

1. Register Student  
2. Capture face images  
3. Train model  
4. Take attendance automatically  

---

## 🧠 Face Recognition Algorithm

- Uses **LBPH (Local Binary Pattern Histogram)**
- Converts faces into feature vectors
- Matches with trained dataset
- Uses confidence threshold for accuracy

---

## 📊 Data Storage

- CSV Files → Student & Attendance data  
- JSON File → Configuration & Users  
- YML File → Trained model  

---

## ⚠️ Requirements

- Python 3.x  
- Webcam / IP Camera  
- Good lighting conditions  

---

## 🔧 Configuration (config.json)

```json
{
  "camera_index": 1,
  "sample_count": 60,
  "confidence_threshold": 55,
  "attendance_cooldown": 300
}
```

---

## 🚨 Limitations

- Works best in controlled lighting  
- Accuracy depends on training data  
- Local storage only (no cloud)  
- Single system usage  

---

## 🔮 Future Enhancements

- Cloud database (MongoDB / Firebase)  
- Web dashboard  
- Mobile app  
- AI-based recognition improvements  
- Multi-camera support  

---

## 📜 License

This project is for **educational purposes (BCA Final Year Project)**.

---

## 🙌 Acknowledgment

Developed as a **BCA Final Year Project**  
Idea enhanced with project team collaboration  

---

## 📧 Contact

**Aditya Kumar Dwivedi**  
BCA Student

---

⭐ If you like this project, give it a star on GitHub!
