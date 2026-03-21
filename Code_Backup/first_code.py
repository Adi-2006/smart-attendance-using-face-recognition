import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import cv2, os, csv, json, hashlib, smtplib
import numpy as np
from PIL import Image, ImageTk
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import pandas as pd
import datetime, time
from threading import Thread
import winsound  # For Windows; use alternative for other OS

# -------------------- CONFIGURATION --------------------
CONFIG = {
    "camera_index": 1,
    "sample_count": 60,
    "confidence_threshold": 55,
    "attendance_cooldown": 300,  # seconds before same person can mark again
    "email_notifications": False,
    # "admin_password_hash": hashlib.sha256("admin123".encode()).hexdigest(),
    "theme": "dark",
    "url" : "http://10.86.129.28:4747/video",
    "users": {
    "admin": {
        "password": hashlib.sha256("admin123".encode()).hexdigest(),
        "role": "admin"
    },
    "class1": {
        "password": hashlib.sha256("class123".encode()).hexdigest(),
        "role": "class"
    },
    "class2": {
        "password": hashlib.sha256("class123".encode()).hexdigest(),
        "role": "class"
    }
}
}

CURRENT_USER = None

# -------------------- PATH SETUP --------------------
def assure_path_exists(path):
    if not os.path.exists(path):
        os.makedirs(path)

def initialize_directories():
    directories = [
        "TrainingImage", 
        "StudentDetails", 
        "Attendance", 
        "TrainingImageLabel",
        "Logs",
        "Exports",
        "Backups"
    ]
    for directory in directories:
        assure_path_exists(directory)

# -------------------- LOGGING --------------------
def log_activity(action, details=""):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {action}: {details}\n"
    
    log_file = f"Logs/activity_{datetime.datetime.now().strftime('%Y-%m')}.log"
    with open(log_file, "a") as f:
        f.write(log_entry)

# -------------------- CLOCK --------------------
def tick():
    time_string = time.strftime('%H:%M:%S')
    date_string = time.strftime('%A, %B %d, %Y')
    clock.config(text=time_string)
    date_label.config(text=date_string)
    clock.after(1000, tick)

# -------------------- CHECK FILES --------------------
def check_haarcascadefile():
    if not os.path.isfile("haarcascade_frontalface_default.xml"):
        messagebox.showerror("Error", "Missing haarcascade file!\nDownload from OpenCV GitHub.")
        window.destroy()

def check_dependencies():
    check_haarcascadefile()
    initialize_directories()
    
    # Create StudentDetails.csv with headers if not exists
    if not os.path.isfile("StudentDetails/StudentDetails.csv"):
        with open("StudentDetails/StudentDetails.csv", "w", newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["ID", "Name", "Email", "Department", "Enrollment Date"])

# -------------------- CLEAR FUNCTIONS --------------------
def clear():
    txt.delete(0, 'end')
    
def clear2():
    txt2.delete(0, 'end')

def clear3():
    txt3.delete(0, 'end')

def clear4():
    txt4.delete(0, 'end')

def clear_all():
    txt.delete(0, 'end')
    txt2.delete(0, 'end')
    txt3.delete(0, 'end')
    txt4.delete(0, 'end')
    status_label.config(text="Fields cleared", fg="yellow")

# -------------------- VALIDATION --------------------
def validate_id(id_value):
    if not id_value.isdigit():
        messagebox.showerror("Error", "ID must be numeric!")
        return False
    
    # Check if ID already exists
    if os.path.isfile("StudentDetails/StudentDetails.csv"):
        df = pd.read_csv("StudentDetails/StudentDetails.csv")
        if int(id_value) in df['ID'].values:
            messagebox.showerror("Error", "ID already exists!")
            return False
    return True

def validate_name(name):
    if not name.replace(" ", "").isalpha():
        messagebox.showerror("Error", "Name should only contain alphabets!")
        return False
    if len(name) < 2:
        messagebox.showerror("Error", "Name is too short!")
        return False
    return True

def validate_email(email):
    if email and "@" not in email or "." not in email:
        messagebox.showerror("Error", "Invalid email format!")
        return False
    return True

# -------------------- TAKE IMAGES --------------------
def TakeImages():
    check_haarcascadefile()
    
    Id = txt.get().strip()
    name = txt2.get().strip()
    email = txt3.get().strip()
    department = txt4.get().strip()
    
    if not Id or not name:
        messagebox.showerror("Error", "ID and Name are required!")
        return
    
    if not validate_id(Id):
        return
    if not validate_name(name):
        return
    if email and not validate_email(email):
        return

    status_label.config(text="Starting camera...", fg="cyan")
    window.update()
    
    # cam = cv2.VideoCapture(CONFIG["camera_index"])
    cam = cv2.VideoCapture(CONFIG["url"])

    
    if not cam.isOpened():
        messagebox.showerror("Error", "Cannot access camera!")
        return
    
    detector = cv2.CascadeClassifier("haarcascade_frontalface_default.xml")
    
    sampleNum = 0
    total_samples = CONFIG["sample_count"]
    
    # Create progress window
    progress_window = tk.Toplevel(window)
    progress_window.title("Capturing Images")
    progress_window.geometry("300x100")
    progress_window.configure(bg="#2e2e2e")
    
    progress_label = tk.Label(progress_window, text="Capturing...", bg="#2e2e2e", fg="white")
    progress_label.pack(pady=10)
    
    progress_bar = ttk.Progressbar(progress_window, length=250, mode='determinate')
    progress_bar.pack(pady=10)
    
    while True:
        ret, img = cam.read()
        if not ret:
            break
            
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = detector.detectMultiScale(gray, 1.3, 5, minSize=(100, 100))
        
        for (x, y, w, h) in faces:
            sampleNum += 1
            
            # Save multiple variations for better training
            face_img = gray[y:y+h, x:x+w]
            
            # Original
            cv2.imwrite(f"TrainingImage/{name}.{Id}.{sampleNum}.jpg", face_img)
            
            # Flipped (for more training data)
            if sampleNum <= total_samples // 2:
                flipped = cv2.flip(face_img, 1)
                cv2.imwrite(f"TrainingImage/{name}.{Id}.{sampleNum}_flip.jpg", flipped)
            
            cv2.rectangle(img, (x, y), (x+w, y+h), (255, 0, 0), 2)
            cv2.putText(img, f"Captured: {sampleNum}/{total_samples}", (x, y-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            # Update progress
            progress_bar['value'] = (sampleNum / total_samples) * 100
            progress_label.config(text=f"Capturing: {sampleNum}/{total_samples}")
            progress_window.update()
        
        # Show face count on screen
        cv2.putText(img, f"Faces detected: {len(faces)}", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        cv2.putText(img, "Press 'Q' to quit early", (10, 60), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        cv2.imshow("Taking Images - Look at Camera", img)
        
        if cv2.waitKey(1) == ord('q') or sampleNum >= total_samples:
            break
    
    cam.release()
    cv2.destroyAllWindows()
    progress_window.destroy()
    
    if sampleNum > 0:
        # Save student details
        enrollment_date = datetime.datetime.now().strftime("%Y-%m-%d")
        
        with open("StudentDetails/StudentDetails.csv", "a", newline='') as f:
            writer = csv.writer(f)
            writer.writerow([Id, name, email, department, enrollment_date])
        
        log_activity("REGISTRATION", f"New student registered: {name} (ID: {Id})")
        
        messagebox.showinfo("Success", f"Successfully captured {sampleNum} images for {name}")
        status_label.config(text=f"Images saved for {name}", fg="green")
        clear_all()
        
        # Auto-train option
        if messagebox.askyesno("Train Model", "Do you want to train the model now?"):
            TrainImages()
    else:
        messagebox.showwarning("Warning", "No faces captured!")
        status_label.config(text="No faces captured", fg="red")

# -------------------- TRAIN --------------------
def TrainImages():
    check_haarcascadefile()
    
    status_label.config(text="Training model...", fg="cyan")
    window.update()
    
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    faces, Ids = getImagesAndLabels("TrainingImage")
    
    if len(faces) == 0:
        messagebox.showerror("Error", "No training images found!")
        status_label.config(text="Training failed", fg="red")
        return
    
    # Train with progress indication
    train_window = tk.Toplevel(window)
    train_window.title("Training")
    train_window.geometry("300x80")
    train_window.configure(bg="#2e2e2e")
    
    tk.Label(train_window, text=f"Training on {len(faces)} images...", 
            bg="#2e2e2e", fg="white").pack(pady=20)
    train_window.update()
    
    recognizer.train(faces, np.array(Ids))
    recognizer.save("TrainingImageLabel/trainer.yml")
    
    train_window.destroy()
    
    # Get unique student count
    unique_ids = len(set(Ids))
    
    log_activity("TRAINING", f"Model trained with {len(faces)} images for {unique_ids} students")
    
    messagebox.showinfo("Success", f"Model trained successfully!\n\nTotal Images: {len(faces)}\nStudents: {unique_ids}")
    status_label.config(text="Model trained successfully", fg="green")

# -------------------- GET IMAGES --------------------
def getImagesAndLabels(path):
    imagePaths = [os.path.join(path, f) for f in os.listdir(path) if f.endswith(('.jpg', '.png', '.jpeg'))]
    faces = []
    Ids = []
    
    for imagePath in imagePaths:
        try:
            img = Image.open(imagePath).convert('L')
            imgNp = np.array(img, 'uint8')
            
            # Extract ID from filename (format: Name.ID.SampleNum.jpg)
            filename = os.path.split(imagePath)[-1]
            Id = int(filename.split(".")[1])
            
            faces.append(imgNp)
            Ids.append(Id)
        except Exception as e:
            print(f"Error processing {imagePath}: {e}")
            continue
    
    return faces, Ids

# -------------------- TRACK/ATTENDANCE --------------------
def TrackImages():
    check_haarcascadefile()

    # 🔴 ADD THIS BLOCK HERE (NOT ABOVE FUNCTION, NOT OUTSIDE)
    if CONFIG["users"][CURRENT_USER]["role"] == "admin":
        messagebox.showerror("Access Denied", "Admin cannot mark attendance!")
        return
    
    if not os.path.isfile("TrainingImageLabel/trainer.yml"):
        messagebox.showerror("Error", "Train model first!")
        return
    
    if not os.path.isfile("StudentDetails/StudentDetails.csv"):
        messagebox.showerror("Error", "No student data found!")
        return
    
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.read("TrainingImageLabel/trainer.yml")
    faceCascade = cv2.CascadeClassifier("haarcascade_frontalface_default.xml")
    
    df = pd.read_csv("StudentDetails/StudentDetails.csv")
    
    # Taking Attendence
    cam = cv2.VideoCapture(CONFIG["url"])
    
    if not cam.isOpened():
        messagebox.showerror("Error", "Cannot access camera!")
        return
    
    attendance_marked = {}  # {id: timestamp}
    today = datetime.datetime.now().strftime("%d-%m-%Y")
    attendance_file = f"Attendance/Attendance_{today}.csv"
    
    # Create attendance file with headers if not exists
    if not os.path.isfile(attendance_file):
        with open(attendance_file, "w", newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["ID", "Name", "Department", "Date", "Time", "Confidence"])
    
    # Load already marked attendance for today
    if os.path.isfile(attendance_file):
        existing = pd.read_csv(attendance_file)
        if len(existing) > 0:
            for idx in existing['ID'].values:
                attendance_marked[idx] = time.time()
    
    status_label.config(text="Attendance in progress...", fg="cyan")
    
    frame_count = 0
    last_faces = [] # Ading For Removing blinking Visual while Taking Attendence
    last_results = [] #Adding for better UI & Make cpu Prpcesing fast
    
    while True:
        ret, img = cam.read()
        if not ret:
            break
        
        frame_count += 1
                
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # faces = faceCascade.detectMultiScale(gray, 1.2, 5, minSize=(100, 100))
        if frame_count % 3 == 0:
            faces = faceCascade.detectMultiScale(gray, 1.2, 5, minSize=(100, 100))
            last_faces = faces
        else:
            faces = last_faces
        
        # Display info on screen
        cv2.putText(img, f"Date: {today}", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(img, f"Marked Today: {len(attendance_marked)}", (10, 60), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        
        # Adding New Code for the Better CPU Performance 
        if frame_count % 3 == 0:
            current_results = []
            for (x, y, w, h) in faces:
                 Id, conf = recognizer.predict(gray[y:y+h, x:x+w])
                 current_results.append((x, y, w, h, Id, conf))
            last_results = current_results
        else:
            current_results = last_results

        for (x, y, w, h, Id, conf) in current_results:
            confidence = round(100 - conf, 2)
            
            if conf < CONFIG["confidence_threshold"]:
                # Get student details

                student = df.loc[df['ID'] == Id]

# 🔴 ADD THIS BLOCK EXACTLY HERE
                if len(student) > 0:
                    user_class = CURRENT_USER
                    student_class = str(student['Department'].values[0])

                    # if CONFIG["users"][CURRENT_USER]["role"] == "class" and user_class != student_class:
                    #     continue

                
                
                if len(student) > 0:
                    name = str(student['Name'].values[0])
                    department = str(student['Department'].values[0]) if 'Department' in df.columns else "N/A"
                    
                    current_time = time.time()
                    
                    # Check cooldown
                    if Id not in attendance_marked or (current_time - attendance_marked[Id]) > CONFIG["attendance_cooldown"]:
                        attendance_marked[Id] = current_time
                        
                        now = datetime.datetime.now()
                        date = now.strftime("%d-%m-%Y")
                        timeStamp = now.strftime("%H:%M:%S")
                        
                        with open(attendance_file, "a", newline='') as f:
                            writer = csv.writer(f)
                            writer.writerow([Id, name, department, date, timeStamp, confidence])
                        
                        log_activity("ATTENDANCE", f"{name} (ID: {Id}) marked present")
                        
                        # Play sound notification (Windows)
                        try:
                            winsound.Beep(1000, 200)
                        except:
                            pass
                        
                        color = (0, 255, 0)  # Green for just marked
                    else:
                        color = (0, 255, 255)  # Yellow for already marked
                    
                    label = f"{name} ({confidence}%)"
                else:
                    label = f"ID:{Id} ({confidence}%)"
                    color = (0, 165, 255)  # Orange
            else:
                label = f"Unknown ({confidence}%)"
                color = (0, 0, 255)  # Red
            
            cv2.rectangle(img, (x, y), (x+w, y+h), color, 2)
            cv2.rectangle(img, (x, y-35), (x+w, y), color, cv2.FILLED)
            cv2.putText(img, label, (x+6, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        cv2.imshow("Attendance - Press 'Q' to Exit", img)
        
        if cv2.waitKey(1) == ord('q'):
            break
    
    cam.release()
    cv2.destroyAllWindows()
    
    messagebox.showinfo("Attendance Complete", f"Total attendance marked today: {len(attendance_marked)}")
    status_label.config(text=f"Attendance complete: {len(attendance_marked)} students", fg="green")

# -------------------- VIEW ATTENDANCE --------------------
def ViewAttendance():
    view_window = tk.Toplevel(window)
    view_window.title("View Attendance")
    view_window.geometry("800x500")
    view_window.configure(bg="#1e1e1e")
    
    # Date selector
    date_frame = tk.Frame(view_window, bg="#1e1e1e")
    date_frame.pack(pady=10)
    
    tk.Label(date_frame, text="Select Date:", bg="#1e1e1e", fg="white").pack(side=tk.LEFT, padx=5)
    
    date_entry = tk.Entry(date_frame, width=15)
    date_entry.insert(0, datetime.datetime.now().strftime("%d-%m-%Y"))
    date_entry.pack(side=tk.LEFT, padx=5)
    
    # Treeview for attendance
    tree_frame = tk.Frame(view_window)
    tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    columns = ("ID", "Name", "Department", "Date", "Time", "Confidence")
    tree = ttk.Treeview(tree_frame, columns=columns, show="headings")
    
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=100)
    
    scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    
    tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def load_attendance():
        # Clear existing data
        for item in tree.get_children():
            tree.delete(item)
        
        date = date_entry.get()
        file_path = f"Attendance/Attendance_{date}.csv"
        
        if os.path.isfile(file_path):
            df = pd.read_csv(file_path)
            for _, row in df.iterrows():
                tree.insert("", tk.END, values=list(row))
            
            count_label.config(text=f"Total: {len(df)} records")
        else:
            messagebox.showinfo("Info", f"No attendance record for {date}")
            count_label.config(text="No records found")
    
    tk.Button(date_frame, text="Load", command=load_attendance, bg="#4CAF50", fg="white").pack(side=tk.LEFT, padx=5)
    
    count_label = tk.Label(view_window, text="", bg="#1e1e1e", fg="cyan")
    count_label.pack(pady=5)
    
    # Export button
    def export_attendance():
        date = date_entry.get()
        file_path = f"Attendance/Attendance_{date}.csv"
        
        if os.path.isfile(file_path):
            export_path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("Excel files", "*.xlsx")],
                initialfile=f"Attendance_{date}"
            )
            if export_path:
                if export_path.endswith('.xlsx'):
                    df = pd.read_csv(file_path)
                    df.to_excel(export_path, index=False)
                else:
                    import shutil
                    shutil.copy(file_path, export_path)
                messagebox.showinfo("Success", f"Exported to {export_path}")
    
    tk.Button(view_window, text="Export", command=export_attendance, bg="#2196F3", fg="white", width=15).pack(pady=5)
    
    load_attendance()

# -------------------- VIEW STUDENTS --------------------
def ViewStudents():
    student_window = tk.Toplevel(window)
    student_window.title("Registered Students")
    student_window.geometry("700x400")
    student_window.configure(bg="#1e1e1e")
    
    if not os.path.isfile("StudentDetails/StudentDetails.csv"):
        tk.Label(student_window, text="No students registered", bg="#1e1e1e", fg="white").pack(pady=50)
        return
    
    df = pd.read_csv("StudentDetails/StudentDetails.csv")
    
    tree_frame = tk.Frame(student_window)
    tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    columns = list(df.columns)
    tree = ttk.Treeview(tree_frame, columns=columns, show="headings")
    
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=120)
    
    scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    
    tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    for _, row in df.iterrows():
        tree.insert("", tk.END, values=list(row))
    
    tk.Label(student_window, text=f"Total Students: {len(df)}", bg="#1e1e1e", fg="cyan").pack(pady=5)
    
    # Delete student function
    def delete_student():
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Select a student to delete")
            return
        
        if messagebox.askyesno("Confirm", "Are you sure you want to delete this student?"):
            item = tree.item(selected[0])
            student_id = item['values'][0]
            
            # Remove from CSV
            df_updated = df[df['ID'] != student_id]
            df_updated.to_csv("StudentDetails/StudentDetails.csv", index=False)
            
            # Remove training images
            for f in os.listdir("TrainingImage"):
                if f".{student_id}." in f:
                    os.remove(os.path.join("TrainingImage", f))
            
            tree.delete(selected[0])
            log_activity("DELETE", f"Student ID {student_id} deleted")
            messagebox.showinfo("Success", "Student deleted. Please retrain the model.")
    
    tk.Button(student_window, text="Delete Selected", command=delete_student, bg="red", fg="white").pack(pady=5)

# -------------------- ATTENDANCE REPORT --------------------
def GenerateReport():
    report_window = tk.Toplevel(window)
    report_window.title("Attendance Report")
    report_window.geometry("600x400")
    report_window.configure(bg="#1e1e1e")
    
    tk.Label(report_window, text="Attendance Report Generator", bg="#1e1e1e", fg="white", 
            font=("Arial", 14, "bold")).pack(pady=10)
    
    frame = tk.Frame(report_window, bg="#2e2e2e")
    frame.pack(pady=20, padx=20, fill=tk.X)
    
    tk.Label(frame, text="From Date (DD-MM-YYYY):", bg="#2e2e2e", fg="white").grid(row=0, column=0, pady=5)
    from_date = tk.Entry(frame)
    from_date.grid(row=0, column=1, pady=5)
    
    tk.Label(frame, text="To Date (DD-MM-YYYY):", bg="#2e2e2e", fg="white").grid(row=1, column=0, pady=5)
    to_date = tk.Entry(frame)
    to_date.insert(0, datetime.datetime.now().strftime("%d-%m-%Y"))
    to_date.grid(row=1, column=1, pady=5)
    
    report_text = tk.Text(report_window, height=15, width=70, bg="#3e3e3e", fg="white")
    report_text.pack(pady=10, padx=10)
    
    def generate():
        report_text.delete(1.0, tk.END)
        
        attendance_files = [f for f in os.listdir("Attendance") if f.endswith('.csv')]
        
        if not attendance_files:
            report_text.insert(tk.END, "No attendance records found.")
            return
        
        all_attendance = []
        
        for file in attendance_files:
            try:
                df = pd.read_csv(f"Attendance/{file}")
                all_attendance.append(df)
            except:
                continue
        
        if not all_attendance:
            report_text.insert(tk.END, "No valid attendance records.")
            return
        
        combined = pd.concat(all_attendance, ignore_index=True)
        
        report_text.insert(tk.END, "=" * 50 + "\n")
        report_text.insert(tk.END, "       ATTENDANCE SUMMARY REPORT\n")
        report_text.insert(tk.END, "=" * 50 + "\n\n")
        
        report_text.insert(tk.END, f"Total Records: {len(combined)}\n")
        report_text.insert(tk.END, f"Unique Students: {combined['ID'].nunique()}\n\n")
        
        report_text.insert(tk.END, "-" * 50 + "\n")
        report_text.insert(tk.END, "Attendance Count by Student:\n")
        report_text.insert(tk.END, "-" * 50 + "\n")
        
        summary = combined.groupby(['ID', 'Name']).size().reset_index(name='Days Present')
        summary = summary.sort_values('Days Present', ascending=False)
        
        for _, row in summary.iterrows():
            report_text.insert(tk.END, f"  {row['Name']} (ID: {row['ID']}): {row['Days Present']} days\n")
        
        report_text.insert(tk.END, "\n" + "=" * 50 + "\n")
    
    tk.Button(report_window, text="Generate Report", command=generate, bg="#4CAF50", fg="white", width=20).pack(pady=10)

# -------------------- SETTINGS --------------------
def OpenSettings():
    settings_window = tk.Toplevel(window)
    settings_window.title("Settings")
    settings_window.geometry("400x350")
    settings_window.configure(bg="#1e1e1e")
    
    tk.Label(settings_window, text="Settings", bg="#1e1e1e", fg="white", 
            font=("Arial", 14, "bold")).pack(pady=10)
    
    frame = tk.Frame(settings_window, bg="#2e2e2e")
    frame.pack(pady=20, padx=20, fill=tk.BOTH, expand=True)
    
    tk.Label(frame, text="Camera Index:", bg="#2e2e2e", fg="white").grid(row=0, column=0, pady=5, sticky='w')
    camera_entry = tk.Entry(frame, width=10)
    camera_entry.insert(0, str(CONFIG["camera_index"]))
    camera_entry.grid(row=0, column=1, pady=5)
    
    tk.Label(frame, text="Sample Count:", bg="#2e2e2e", fg="white").grid(row=1, column=0, pady=5, sticky='w')
    sample_entry = tk.Entry(frame, width=10)
    sample_entry.insert(0, str(CONFIG["sample_count"]))
    sample_entry.grid(row=1, column=1, pady=5)
    
    tk.Label(frame, text="Confidence Threshold:", bg="#2e2e2e", fg="white").grid(row=2, column=0, pady=5, sticky='w')
    conf_entry = tk.Entry(frame, width=10)
    conf_entry.insert(0, str(CONFIG["confidence_threshold"]))
    conf_entry.grid(row=2, column=1, pady=5)
    
    tk.Label(frame, text="Cooldown (seconds):", bg="#2e2e2e", fg="white").grid(row=3, column=0, pady=5, sticky='w')
    cooldown_entry = tk.Entry(frame, width=10)
    cooldown_entry.insert(0, str(CONFIG["attendance_cooldown"]))
    cooldown_entry.grid(row=3, column=1, pady=5)
    
    def save_settings():
        CONFIG["camera_index"] = int(camera_entry.get())
        CONFIG["sample_count"] = int(sample_entry.get())
        CONFIG["confidence_threshold"] = int(conf_entry.get())
        CONFIG["attendance_cooldown"] = int(cooldown_entry.get())
        
        messagebox.showinfo("Success", "Settings saved!")
        settings_window.destroy()
    
    tk.Button(settings_window, text="Save Settings", command=save_settings, bg="#4CAF50", fg="white", width=20).pack(pady=20)

# -------------------- BACKUP --------------------
def BackupData():
    import shutil
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_folder = f"Backups/backup_{timestamp}"
    
    assure_path_exists(backup_folder)
    
    folders_to_backup = ["StudentDetails", "Attendance", "TrainingImageLabel"]
    
    for folder in folders_to_backup:
        if os.path.exists(folder):
            shutil.copytree(folder, f"{backup_folder}/{folder}")
    
    log_activity("BACKUP", f"Data backed up to {backup_folder}")
    messagebox.showinfo("Success", f"Backup created: {backup_folder}")

# -------------------- CAMERA TEST --------------------
def TestCamera():
    cam = cv2.VideoCapture(CONFIG["url"])
    
    if not cam.isOpened():
        messagebox.showerror("Error", "Cannot access camera!")
        return
    
    messagebox.showinfo("Camera Test", "Camera will open. Press 'Q' to close.")
    
    while True:
        ret, frame = cam.read()
        if not ret:
            break
        
        cv2.putText(frame, "Camera Test - Press Q to exit", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.imshow("Camera Test", frame)
        
        if cv2.waitKey(1) == ord('q'):
            break
    
    cam.release()
    cv2.destroyAllWindows()

# 🔴 👉 ADD ADMIN PANEL FUNCTION HERE 👇
def AdminPanel():
    if CONFIG["users"][CURRENT_USER]["role"] != "admin":
        messagebox.showerror("Access Denied", "Only admin can access this!")
        return

    admin_win = tk.Toplevel(window)
    admin_win.title("Admin Panel")
    admin_win.geometry("400x400")
    admin_win.configure(bg="#1e1e1e")

    tk.Label(admin_win, text="Admin Controls", font=("Arial", 16, "bold"),
             bg="#1e1e1e", fg="white").pack(pady=10)

    # CHANGE PASSWORD
    def change_password():
        new_pass = simpledialog.askstring("New Password", "Enter new password:", show="*")
        if new_pass:
            CONFIG["users"]["admin"]["password"] = hashlib.sha256(new_pass.encode()).hexdigest()
            messagebox.showinfo("Success", "Password updated!")

    tk.Button(admin_win, text="Change Admin Password",
              command=change_password, bg="#4CAF50", fg="white", width=25).pack(pady=10)

    # ADD CLASS
    def add_class():
        class_name = simpledialog.askstring("Class Name", "Enter class (e.g. class3):")
        if class_name:
            if class_name in CONFIG["users"]:
                messagebox.showerror("Error", "Already exists!")
            else:
                CONFIG["users"][class_name] = {
                    "password": hashlib.sha256("class123".encode()).hexdigest(),
                    "role": "class"
                }
                messagebox.showinfo("Success", f"{class_name} added!")

    tk.Button(admin_win, text="Add New Class",
              command=add_class, bg="#2196F3", fg="white", width=25).pack(pady=10)

    # CLASS STRENGTH
    def view_strength():
        if not os.path.isfile("StudentDetails/StudentDetails.csv"):
            messagebox.showinfo("Info", "No data found!")
            return

        df = pd.read_csv("StudentDetails/StudentDetails.csv")

        if "Department" not in df.columns:
            messagebox.showerror("Error", "Department missing!")
            return

        summary = df['Department'].value_counts()

        result = "Class Strength:\n\n"
        for cls, count in summary.items():
            result += f"{cls}: {count}\n"

        messagebox.showinfo("Class Strength", result)

    tk.Button(admin_win, text="View Class Strength",
              command=view_strength, bg="#FF9800", fg="white", width=25).pack(pady=10)

# Adding Login option
def login_screen():
    global CURRENT_USER

    login_win = tk.Tk()
    login_win.title("Login - Attendance System")
    login_win.geometry("350x280")
    login_win.configure(bg="#1e1e1e")

    tk.Label(login_win, text="Multi-User Login", font=("Arial", 16, "bold"),
             bg="#1e1e1e", fg="white").pack(pady=15)

    tk.Label(login_win, text="Select User", bg="#1e1e1e", fg="white").pack()

    user_var = tk.StringVar()
    user_dropdown = ttk.Combobox(login_win,
                                 textvariable=user_var,
                                 values=list(CONFIG["users"].keys()),
                                 state="readonly")
    user_dropdown.pack(pady=5)
    user_dropdown.current(0)

    tk.Label(login_win, text="Password", bg="#1e1e1e", fg="white").pack()
    password_entry = tk.Entry(login_win, show="*")
    password_entry.pack(pady=5)

    def check_login():
        global CURRENT_USER

        user = user_var.get()
        password = password_entry.get()

        hashed = hashlib.sha256(password.encode()).hexdigest()

        if user in CONFIG["users"] and CONFIG["users"][user]["password"] == hashed:
            CURRENT_USER = user
            login_win.destroy()
        else:
            messagebox.showerror("Error", "Invalid Password")

    tk.Button(login_win, text="Login",
              command=check_login,
              bg="#4CAF50", fg="white",
              width=15).pack(pady=15)

    login_win.mainloop()

# -------------------- GUI --------------------
# Login GUi
login_screen()   # 🔐 Login first
window = tk.Tk()
window.title("Face Recognition Attendance System v2.0")
window.geometry("900x650")
window.configure(bg="#1e1e1e")
window.resizable(True, True)

# Header
header_frame = tk.Frame(window, bg="#0d47a1", height=80)
header_frame.pack(fill=tk.X)

title = tk.Label(header_frame, text="🎓 Face Recognition Attendance System", 
                bg="#0d47a1", fg="white", font=("Arial", 22, "bold"))
title.pack(pady=15)

# Adding More Line
user_label = tk.Label(header_frame, text="", 
                      bg="#0d47a1", fg="white", font=("Arial", 10))
user_label.pack()

# Clock and Date
time_frame = tk.Frame(window, bg="#1e1e1e")
time_frame.pack(pady=10)

clock = tk.Label(time_frame, fg="cyan", bg="#1e1e1e", font=("Arial", 24, "bold"))
clock.pack()

date_label = tk.Label(time_frame, fg="white", bg="#1e1e1e", font=("Arial", 12))
date_label.pack()

tick()

# Input Frame
input_frame = tk.LabelFrame(window, text="Student Registration", bg="#2e2e2e", fg="white", 
                           font=("Arial", 12, "bold"), padx=20, pady=15)
input_frame.pack(pady=15, padx=20, fill=tk.X)

# Row 1
tk.Label(input_frame, text="Student ID:", bg="#2e2e2e", fg="white", font=("Arial", 10)).grid(row=0, column=0, padx=10, pady=8, sticky='e')
txt = tk.Entry(input_frame, width=25, font=("Arial", 11))
txt.grid(row=0, column=1, padx=10, pady=8)
tk.Button(input_frame, text="Clear", command=clear, bg="#f44336", fg="white", width=8).grid(row=0, column=2, padx=5)

tk.Label(input_frame, text="Name:", bg="#2e2e2e", fg="white", font=("Arial", 10)).grid(row=0, column=3, padx=10, pady=8, sticky='e')
txt2 = tk.Entry(input_frame, width=25, font=("Arial", 11))
txt2.grid(row=0, column=4, padx=10, pady=8)
tk.Button(input_frame, text="Clear", command=clear2, bg="#f44336", fg="white", width=8).grid(row=0, column=5, padx=5)

# Row 2
tk.Label(input_frame, text="Email:", bg="#2e2e2e", fg="white", font=("Arial", 10)).grid(row=1, column=0, padx=10, pady=8, sticky='e')
txt3 = tk.Entry(input_frame, width=25, font=("Arial", 11))
txt3.grid(row=1, column=1, padx=10, pady=8)
tk.Button(input_frame, text="Clear", command=clear3, bg="#f44336", fg="white", width=8).grid(row=1, column=2, padx=5)

tk.Label(input_frame, text="Department:", bg="#2e2e2e", fg="white", font=("Arial", 10)).grid(row=1, column=3, padx=10, pady=8, sticky='e')
txt4 = tk.Entry(input_frame, width=25, font=("Arial", 11))
txt4.grid(row=1, column=4, padx=10, pady=8)
tk.Button(input_frame, text="Clear", command=clear4, bg="#f44336", fg="white", width=8).grid(row=1, column=5, padx=5)

# Clear All Button
tk.Button(input_frame, text="Clear All Fields", command=clear_all, bg="#9c27b0", fg="white", 
         width=15).grid(row=2, column=2, columnspan=2, pady=10)

# Button Frame
button_frame = tk.Frame(window, bg="#1e1e1e")
button_frame.pack(pady=15)

# Main Action Buttons
main_buttons = [
    ("📸 Take Images", TakeImages, "#2196F3"),
    ("🧠 Train Model", TrainImages, "#FF9800"),
    ("✅ Take Attendance", TrackImages, "#4CAF50"),
]

for i, (text, command, color) in enumerate(main_buttons):
    btn = tk.Button(button_frame, text=text, command=command, bg=color, fg="white", 
                   font=("Arial", 12, "bold"), width=18, height=2)
    btn.grid(row=0, column=i, padx=10, pady=5)

# Secondary Buttons Frame
secondary_frame = tk.Frame(window, bg="#1e1e1e")
secondary_frame.pack(pady=10)

secondary_buttons = [
    ("📊 View Attendance", ViewAttendance, "#607D8B"),
    ("👥 View Students", ViewStudents, "#795548"),
    ("📈 Generate Report", GenerateReport, "#9C27B0"),
    ("⚙️ Settings", OpenSettings, "#455A64"),
    ("👑 Admin Panel", AdminPanel, "#E91E63"),
]

for i, (text, command, color) in enumerate(secondary_buttons):
    btn = tk.Button(secondary_frame, text=text, command=command, bg=color, fg="white", 
                   font=("Arial", 10), width=16, height=1)
    btn.grid(row=0, column=i, padx=8, pady=5)

# Utility Buttons Frame
utility_frame = tk.Frame(window, bg="#1e1e1e")
utility_frame.pack(pady=10)

utility_buttons = [
    ("📷 Test Camera", TestCamera, "#00BCD4"),
    ("💾 Backup Data", BackupData, "#8BC34A"),
    ("❌ Exit", window.destroy, "#f44336"),
]

for i, (text, command, color) in enumerate(utility_buttons):
    btn = tk.Button(utility_frame, text=text, command=command, bg=color, fg="white", 
                   font=("Arial", 10), width=14)
    btn.grid(row=0, column=i, padx=10, pady=5)

# Status Bar
status_frame = tk.Frame(window, bg="#0d47a1", height=30)
status_frame.pack(side=tk.BOTTOM, fill=tk.X)

status_label = tk.Label(status_frame, text="Ready", bg="#0d47a1", fg="white", font=("Arial", 10))
status_label.pack(side=tk.LEFT, padx=10, pady=5)

version_label = tk.Label(status_frame, text="v2.0", bg="#0d47a1", fg="white", font=("Arial", 10))
version_label.pack(side=tk.RIGHT, padx=10, pady=5)

# Initialize
check_dependencies()
user_label.config(text=f"Logged in as: {CURRENT_USER.upper()}")
window.mainloop()