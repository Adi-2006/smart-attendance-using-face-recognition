import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import cv2, os, csv, json, hashlib
import numpy as np
from PIL import Image, ImageTk
import pandas as pd
import datetime, time

# ============================================================
#  DEFAULT USERS  (only used when config.json does NOT exist)
# ============================================================
DEFAULT_USERS = {
    "Admin": {
        "password": hashlib.sha256("Admin123".encode()).hexdigest(),
        "role": "admin",
    }
}

CONFIG = {
    "camera_index": 1,
    "sample_count": 60,
    "confidence_threshold": 55,
    "attendance_cooldown": 300,
    "url": "http://10.86.129.28:4747/video",
}

USERS = {}
CURRENT_USER = None
CONFIG_FILE = "config.json"


# ============================================================
#  PERSIST
# ============================================================
def load_all_config():
    global USERS
    if os.path.isfile(CONFIG_FILE):
        try:
            with open(CONFIG_FILE) as f:
                data = json.load(f)
            for k in (
                "camera_index",
                "sample_count",
                "confidence_threshold",
                "attendance_cooldown",
            ):
                if k in data:
                    CONFIG[k] = data[k]
            if "users" in data and isinstance(data["users"], dict):
                USERS = data["users"]
                return
        except Exception as e:
            print(f"config.json error: {e}")
    USERS = {k: dict(v) for k, v in DEFAULT_USERS.items()}
    save_all_config()


def save_all_config():
    data = {
        k: CONFIG[k]
        for k in (
            "camera_index",
            "sample_count",
            "confidence_threshold",
            "attendance_cooldown",
        )
    }
    data["users"] = USERS
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=2)


# ============================================================
#  THEME
# ============================================================
C = {
    "bg": "#0d1117",
    "card": "#161b27",
    "card2": "#1a2035",
    "sidebar": "#0d1117",
    "input": "#1f2535",
    "blue": "#3b82f6",
    "green": "#10b981",
    "orange": "#f59e0b",
    "red": "#ef4444",
    "purple": "#8b5cf6",
    "cyan": "#06b6d4",
    "teal": "#14b8a6",
    "pink": "#ec4899",
    "txt": "#e2e8f0",
    "txt2": "#64748b",
    "border": "#1e2a3a",
    "hover": "#252f45",
    "hdr": "#0a0f1e",
}
F = {
    "title": ("Segoe UI", 18, "bold"),
    "head": ("Segoe UI", 13, "bold"),
    "sub": ("Segoe UI", 10, "bold"),
    "body": ("Segoe UI", 10),
    "small": ("Segoe UI", 9),
    "mono": ("Consolas", 10),
    "clock": ("Segoe UI", 26, "bold"),
    "btn": ("Segoe UI", 10, "bold"),
    "btnlg": ("Segoe UI", 11, "bold"),
    "num": ("Segoe UI", 22, "bold"),
}


# ============================================================
#  WIDGET HELPERS
# ============================================================
def sbtn(btn, bg, hbg=None, fg="#fff", font=None, w=None, h=None):
    hbg = hbg or C["hover"]
    btn.configure(
        bg=bg,
        fg=fg,
        font=font or F["btn"],
        relief=tk.FLAT,
        bd=0,
        activebackground=hbg,
        activeforeground=fg,
        cursor="hand2",
    )
    if w:
        btn.configure(width=w)
    if h:
        btn.configure(height=h)
    btn.bind("<Enter>", lambda _: btn.configure(bg=hbg))
    btn.bind("<Leave>", lambda _: btn.configure(bg=bg))


def mk_entry(parent, width=24, show=None):
    kw = {"show": show} if show else {}
    return tk.Entry(
        parent,
        width=width,
        bg=C["input"],
        fg=C["txt"],
        insertbackground=C["cyan"],
        relief=tk.FLAT,
        font=F["body"],
        bd=4,
        **kw,
    )


def mk_label(parent, text, fg=None, font=None, bg=None, **kw):
    return tk.Label(
        parent,
        text=text,
        bg=bg or C["card"],
        fg=fg or C["txt"],
        font=font or F["body"],
        **kw,
    )


def mk_card(parent, title="", bg=None, padx=15, pady=10):
    bg = bg or C["card"]
    return tk.LabelFrame(
        parent,
        text=f"  {title}  " if title else "",
        bg=bg,
        fg=C["txt2"],
        font=F["small"],
        padx=padx,
        pady=pady,
        relief=tk.FLAT,
        bd=1,
        highlightbackground=C["border"],
        highlightthickness=1,
    )


def tv_style(name, bg=None):
    bg = bg or C["card"]
    s = ttk.Style()
    s.theme_use("clam")
    s.configure(
        f"{name}.Treeview",
        background=bg,
        foreground=C["txt"],
        fieldbackground=bg,
        rowheight=26,
        font=F["body"],
    )
    s.configure(
        f"{name}.Treeview.Heading",
        background=C["sidebar"],
        foreground=C["cyan"],
        font=F["sub"],
    )
    s.map(f"{name}.Treeview", background=[("selected", C["blue"])])
    return name


# ── Combobox helper: fully dark-themed, works on all OS ──────
def mk_combo(parent, values, width=26, textvariable=None):
    """
    Returns a styled dark-theme Combobox.
    Uses a unique style name each call to avoid cross-window bleed.
    """
    style_name = f"Dark{id(parent)}.TCombobox"
    s = ttk.Style()
    s.theme_use("clam")
    s.configure(
        style_name,
        fieldbackground=C["input"],
        background=C["input"],
        foreground=C["txt"],
        selectbackground=C["blue"],
        selectforeground=C["txt"],
        arrowcolor=C["cyan"],
        bordercolor=C["border"],
        lightcolor=C["input"],
        darkcolor=C["input"],
        insertcolor=C["txt"],
    )
    s.map(
        style_name,
        fieldbackground=[("readonly", C["input"]), ("disabled", C["sidebar"])],
        foreground=[("readonly", C["txt"]), ("disabled", C["txt2"])],
        background=[("active", C["hover"]), ("pressed", C["hover"])],
    )
    kw = {"textvariable": textvariable} if textvariable else {}
    cb = ttk.Combobox(
        parent,
        values=values,
        state="readonly",
        style=style_name,
        font=F["body"],
        width=width,
        **kw,
    )
    # Force the popup listbox to be dark too
    cb.bind("<<ComboboxSelected>>", lambda e: cb.selection_clear())
    return cb


# ============================================================
#  DIRECTORIES / INIT
# ============================================================
def assure(path):
    os.makedirs(path, exist_ok=True)


def init_dirs():
    for d in [
        "TrainingImage",
        "StudentDetails",
        "Attendance",
        "TrainingImageLabel",
        "Logs",
        "Exports",
        "Backups",
    ]:
        assure(d)


def init_csv():
    p = "StudentDetails/StudentDetails.csv"
    if not os.path.isfile(p):
        with open(p, "w", newline="") as f:
            csv.writer(f).writerow(
                ["ID", "Name", "Email", "Department", "Session", "Enrollment Date"]
            )


def check_cascade():
    if not os.path.isfile("haarcascade_frontalface_default.xml"):
        messagebox.showerror(
            "Missing File",
            "haarcascade_frontalface_default.xml not found!\nDownload from OpenCV GitHub.",
        )
        return False
    return True


# ============================================================
#  LOGGING
# ============================================================
def log(action, detail=""):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    fn = f"Logs/activity_{datetime.datetime.now().strftime('%Y-%m')}.log"
    with open(fn, "a") as f:
        f.write(f"[{ts}] [{action}] {detail}\n")


# ============================================================
#  STATUS / STATS
# ============================================================
def setstatus(msg, color=None):
    status_label.config(text=f"  {msg}", fg=color or C["txt"])


def _dept_student_count(dept):
    try:
        if os.path.isfile("StudentDetails/StudentDetails.csv"):
            df = pd.read_csv("StudentDetails/StudentDetails.csv")
            if "Department" in df.columns:
                return len(df[df["Department"] == dept])
    except:
        pass
    return 0


def _dept_today_count(dept):
    try:
        today = datetime.datetime.now().strftime("%d-%m-%Y")
        af = f"Attendance/Attendance_{today}.csv"
        if os.path.isfile(af):
            df2 = pd.read_csv(af)
            if "Department" in df2.columns:
                return len(df2[df2["Department"] == dept])
    except:
        pass
    return 0


def refresh_stats():
    if not CURRENT_USER or CURRENT_USER not in USERS:
        return
    role = USERS[CURRENT_USER]["role"]
    try:
        if os.path.isfile("StudentDetails/StudentDetails.csv"):
            df = pd.read_csv("StudentDetails/StudentDetails.csv")
            if role == "admin":
                stat_stu.config(text=str(len(df)))
            else:
                dept = USERS[CURRENT_USER].get("department", "")
                stat_stu.config(
                    text=(
                        str(len(df[df["Department"] == dept]))
                        if "Department" in df.columns
                        else "0"
                    )
                )
        else:
            stat_stu.config(text="0")
    except:
        stat_stu.config(text="–")
    try:
        today = datetime.datetime.now().strftime("%d-%m-%Y")
        af = f"Attendance/Attendance_{today}.csv"
        if os.path.isfile(af):
            df2 = pd.read_csv(af)
            if role == "admin":
                stat_att.config(text=str(len(df2)))
            else:
                dept = USERS[CURRENT_USER].get("department", "")
                stat_att.config(
                    text=(
                        str(len(df2[df2["Department"] == dept]))
                        if "Department" in df2.columns
                        else "0"
                    )
                )
        else:
            stat_att.config(text="0")
    except:
        stat_att.config(text="–")

    # refresh admin dashboard cards if visible
    if role == "admin" and "admin_dash_frame" in globals():
        try:
            _rebuild_admin_dash()
        except:
            pass

    window.after(10000, refresh_stats)


# ============================================================
#  VALIDATION
# ============================================================
def val_id(v):
    if not v.strip():
        messagebox.showerror("Validation", "Student ID cannot be empty!")
        return False
    if len(v.strip()) < 2:
        messagebox.showerror("Validation", "Student ID must be at least 2 characters!")
        return False
    if os.path.isfile("StudentDetails/StudentDetails.csv"):
        df = pd.read_csv("StudentDetails/StudentDetails.csv")
        if v.strip() in df["ID"].astype(str).values:
            messagebox.showerror("Validation", f"ID '{v}' already exists!")
            return False
    return True


def val_name(n):
    if not n.replace(" ", "").replace("-", "").isalpha():
        messagebox.showerror("Validation", "Name must contain alphabets only!")
        return False
    if len(n.strip()) < 2:
        messagebox.showerror("Validation", "Name too short!")
        return False
    return True


def val_email(e):
    if e and ("@" not in e or "." not in e):
        messagebox.showerror("Validation", "Invalid email!")
        return False
    return True


# ============================================================
#  CLOCK
# ============================================================
def tick():
    if clock_lbl.winfo_exists():
        clock_lbl.config(text=time.strftime("%H:%M:%S"))
        date_lbl.config(text=time.strftime("%A, %B %d, %Y"))
        clock_lbl.after(1000, tick)


# ============================================================
#  CLEAR
# ============================================================
def clear_all():
    for e in [ent_id, ent_name, ent_email]:
        e.delete(0, "end")
    if str(ent_dept.cget("state")) != "readonly":
        ent_dept.delete(0, "end")
    setstatus("Fields cleared", C["orange"])


# ============================================================
#  TAKE IMAGES
# ============================================================
def TakeImages():
    if USERS[CURRENT_USER]["role"] == "admin":
        messagebox.showerror(
            "Access Denied",
            "Admin cannot register students.\nLog in as a department account.",
        )
        return
    if not check_cascade():
        return
    sid = ent_id.get().strip()
    name = ent_name.get().strip()
    email = ent_email.get().strip()
    dept = ent_dept.get().strip()
    if not sid or not name:
        messagebox.showerror("Input Error", "ID and Name are required!")
        return
    if not val_id(sid):
        return
    if not val_name(name):
        return
    if email and not val_email(email):
        return
    if not dept:
        messagebox.showerror("Input Error", "Department is required!")
        return
    allowed = USERS[CURRENT_USER].get("department", "")
    if dept != allowed:
        messagebox.showerror("Access Denied", f"You can only register for:\n{allowed}")
        return
    session = USERS[CURRENT_USER].get("session", "")
    setstatus("Opening camera…", C["cyan"])
    window.update()
    cam = cv2.VideoCapture(CONFIG["url"])
    if not cam.isOpened():
        setstatus("IP camera failed – trying webcam…", C["orange"])
        window.update()
        cam = cv2.VideoCapture(CONFIG["camera_index"])
    if not cam.isOpened():
        messagebox.showerror("Camera Error", "Cannot access any camera!")
        setstatus("Camera failed", C["red"])
        return
    detector = cv2.CascadeClassifier("haarcascade_frontalface_default.xml")
    count = 0
    total = CONFIG["sample_count"]
    pw = tk.Toplevel(window)
    pw.title("Capturing")
    pw.geometry("360x130")
    pw.configure(bg=C["card"])
    pw.resizable(False, False)
    pw.grab_set()
    mk_label(pw, f"Capturing for: {name}", font=F["sub"]).pack(pady=(14, 4))
    plbl = mk_label(pw, "0 / 0", fg=C["cyan"], font=F["body"])
    plbl.pack()
    ss = ttk.Style()
    ss.theme_use("clam")
    ss.configure(
        "G.Horizontal.TProgressbar",
        troughcolor=C["bg"],
        background=C["green"],
        thickness=16,
    )
    pb = ttk.Progressbar(
        pw, length=310, mode="determinate", style="G.Horizontal.TProgressbar"
    )
    pb.pack(pady=8)
    while True:
        ret, img = cam.read()
        if not ret:
            break
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = detector.detectMultiScale(gray, 1.3, 5, minSize=(100, 100))
        for x, y, w, h in faces:
            count += 1
            fi = gray[y : y + h, x : x + w]
            cv2.imwrite(f"TrainingImage/{name}.{sid}.{count}.jpg", fi)
            if count <= total // 2:
                cv2.imwrite(
                    f"TrainingImage/{name}.{sid}.{count}_flip.jpg", cv2.flip(fi, 1)
                )
            cv2.rectangle(img, (x, y), (x + w, y + h), (59, 130, 246), 2)
            cv2.putText(
                img,
                f"Sample {count}/{total}",
                (x, y - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (16, 185, 129),
                2,
            )
            pb["value"] = (count / total) * 100
            plbl.config(text=f"{count} / {total}")
            pw.update()
        cv2.putText(
            img,
            f"Faces: {len(faces)}",
            (10, 28),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            2,
        )
        cv2.putText(
            img,
            "Press Q to stop",
            (10, 55),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (180, 180, 180),
            1,
        )
        cv2.imshow("Image Capture – Look at Camera", img)
        if cv2.waitKey(1) == ord("q") or count >= total:
            break
    cam.release()
    cv2.destroyAllWindows()
    pw.destroy()
    if count > 0:
        edate = datetime.datetime.now().strftime("%Y-%m-%d")
        with open("StudentDetails/StudentDetails.csv", "a", newline="") as f:
            csv.writer(f).writerow([sid, name, email, dept, session, edate])
        log("REGISTER", f"{name} ID:{sid} Dept:{dept} Session:{session}")
        messagebox.showinfo("Done", f"✅ {count} images captured for {name}")
        setstatus(f"Images saved for {name}", C["green"])
        clear_all()
        refresh_stats()
        if messagebox.askyesno("Train Now", "Train model with new data?"):
            TrainImages()
    else:
        messagebox.showwarning("No Faces", "No faces detected. Try again.")
        setstatus("No faces captured", C["red"])


# ============================================================
#  TRAIN
# ============================================================
def TrainImages():
    if not check_cascade():
        return
    setstatus("Training model…", C["cyan"])
    window.update()
    rec = cv2.face.LBPHFaceRecognizer_create()
    faces, ids = _get_images("TrainingImage")
    if not faces:
        messagebox.showerror("Error", "No training images found!")
        setstatus("Training failed", C["red"])
        return
    tw = tk.Toplevel(window)
    tw.title("Training")
    tw.geometry("340x100")
    tw.configure(bg=C["card"])
    tw.resizable(False, False)
    tw.grab_set()
    mk_label(
        tw,
        f"Training on {len(faces)} images for {len(set(ids))} students…",
        font=F["body"],
    ).pack(pady=14)
    s2 = ttk.Style()
    s2.theme_use("clam")
    s2.configure(
        "B.Horizontal.TProgressbar",
        troughcolor=C["bg"],
        background=C["blue"],
        thickness=16,
    )
    pb2 = ttk.Progressbar(
        tw, length=310, mode="indeterminate", style="B.Horizontal.TProgressbar"
    )
    pb2.pack(pady=4)
    pb2.start(14)
    tw.update()
    rec.train(faces, np.array(ids))
    rec.save("TrainingImageLabel/trainer.yml")
    pb2.stop()
    tw.destroy()
    u = len(set(ids))
    log("TRAIN", f"{len(faces)} images, {u} students")
    messagebox.showinfo(
        "Done", f"✅ Model trained!\nImages: {len(faces)}  Students: {u}"
    )
    setstatus(f"Model trained – {u} students", C["green"])


def _get_images(path):
    """
    Returns (faces, numeric_labels).
    Because OpenCV's LBPH needs integer labels, we map each unique student ID
    string to a stable integer using a sidecar file: TrainingImageLabel/id_map.json
    """
    # Load or build the ID→int map
    map_file = "TrainingImageLabel/id_map.json"
    if os.path.isfile(map_file):
        with open(map_file) as f:
            id_map = json.load(f)  # {"BCA001": 1, "CS-22": 2, ...}
    else:
        id_map = {}

    faces, labels = [], []
    next_int = max(id_map.values(), default=0) + 1

    for fn in os.listdir(path):
        if not fn.lower().endswith((".jpg", ".png", ".jpeg")):
            continue
        try:
            # filename format: Name.StudentID.SampleNum.jpg
            parts = fn.split(".")
            # parts[1] is the student ID (may contain anything except ".")
            sid = parts[-3]
            if sid not in id_map:
                id_map[sid] = next_int
                next_int += 1
            img = Image.open(os.path.join(path, fn)).convert("L")
            faces.append(np.array(img, "uint8"))
            labels.append(id_map[sid])
        except Exception as e:
            print(f"Skip {fn}: {e}")

    # Persist updated map
    assure("TrainingImageLabel")
    with open(map_file, "w") as f:
        json.dump(id_map, f, indent=2)

    return faces, labels


# ============================================================
#  TAKE ATTENDANCE  (department only)
# ============================================================
def TrackImages():
    if USERS[CURRENT_USER]["role"] == "admin":
        messagebox.showerror(
            "Access Denied",
            "Admin cannot mark attendance.\nPlease log in as a department account.",
        )
        return
    if not check_cascade():
        return
    if not os.path.isfile("TrainingImageLabel/trainer.yml"):
        messagebox.showerror("No Model", "Train the model first!")
        return
    if not os.path.isfile("StudentDetails/StudentDetails.csv"):
        messagebox.showerror("No Data", "No student data found!")
        return
    cur_dept = USERS[CURRENT_USER].get("department", "")
    rec = cv2.face.LBPHFaceRecognizer_create()
    rec.read("TrainingImageLabel/trainer.yml")
    casc = cv2.CascadeClassifier("haarcascade_frontalface_default.xml")
    df = pd.read_csv("StudentDetails/StudentDetails.csv")
    dept_df = df[df["Department"] == cur_dept] if "Department" in df.columns else df

    # Load int→string ID reverse map
    map_file = "TrainingImageLabel/id_map.json"
    int_to_sid = {}
    if os.path.isfile(map_file):
        with open(map_file) as f:
            raw = json.load(f)
        int_to_sid = {v: k for k, v in raw.items()}  # {1: "BCA001", 2: "CS-22", ...}
    if len(dept_df) == 0:
        messagebox.showwarning("No Students", f"No students found for:\n{cur_dept}")
        return
    cam = cv2.VideoCapture(CONFIG["url"])
    if not cam.isOpened():
        setstatus("IP camera failed – trying webcam…", C["orange"])
        window.update()
        cam = cv2.VideoCapture(CONFIG["camera_index"])
    if not cam.isOpened():
        messagebox.showerror("Camera Error", "Cannot access any camera!")
        return
    today = datetime.datetime.now().strftime("%d-%m-%Y")
    att_file = f"Attendance/Attendance_{today}.csv"
    marked = {}
    if not os.path.isfile(att_file):
        with open(att_file, "w", newline="") as f:
            csv.writer(f).writerow(
                ["ID", "Name", "Department", "Session", "Date", "Time", "Confidence"]
            )
    else:
        try:
            ex = pd.read_csv(att_file)
            for idx in ex["ID"].values:
                marked[str(idx)] = time.time() - CONFIG["attendance_cooldown"] - 1
        except:
            pass
    setstatus(f"Attendance in progress ({cur_dept})…", C["cyan"])
    window.update()
    fc = 0
    lf = []
    lr = []
    while True:
        ret, img = cam.read()
        if not ret:
            break
        fc += 1
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        if fc % 3 == 0:
            lf = casc.detectMultiScale(gray, 1.2, 5, minSize=(100, 100))
        faces = lf
        if fc % 3 == 0:
            res = []
            for x, y, w, h in faces:
                Id, conf = rec.predict(gray[y : y + h, x : x + w])
                res.append((x, y, w, h, Id, conf))
            lr = res
        cur = lr
        cv2.rectangle(img, (0, 0), (330, 70), (10, 15, 40), -1)
        cv2.putText(
            img,
            f"Dept: {cur_dept}",
            (8, 22),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.52,
            (180, 200, 255),
            1,
        )
        cv2.putText(
            img,
            f"Date: {today}  Marked: {len(marked)}",
            (8, 46),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.52,
            (80, 220, 180),
            1,
        )
        for x, y, w, h, Id, conf in cur:
            confidence = round(100 - conf, 2)
            # Convert numeric OpenCV label back to string student ID
            sid_str = int_to_sid.get(Id, None)
            if conf < CONFIG["confidence_threshold"] and sid_str is not None:
                stu = dept_df.loc[dept_df["ID"].astype(str) == sid_str]
                if len(stu) == 0:
                    cv2.rectangle(img, (x, y), (x + w, y + h), (100, 100, 240), 2)
                    cv2.rectangle(
                        img, (x, y - 32), (x + w, y), (100, 100, 240), cv2.FILLED
                    )
                    cv2.putText(
                        img,
                        f"Other Dept ({confidence}%)",
                        (x + 4, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        (255, 255, 255),
                        1,
                    )
                    continue
                sname = str(stu["Name"].values[0])
                sdept = str(stu["Department"].values[0])
                ssess = (
                    str(stu["Session"].values[0]) if "Session" in stu.columns else ""
                )
                now = time.time()
                if (
                    sid_str not in marked
                    or (now - marked[sid_str]) > CONFIG["attendance_cooldown"]
                ):
                    marked[sid_str] = now
                    ts = datetime.datetime.now()
                    with open(att_file, "a", newline="") as f:
                        csv.writer(f).writerow(
                            [
                                sid_str,
                                sname,
                                sdept,
                                ssess,
                                ts.strftime("%d-%m-%Y"),
                                ts.strftime("%H:%M:%S"),
                                confidence,
                            ]
                        )
                    log("ATTENDANCE", f"{sname} ID:{Id} {sdept}")
                    try:
                        import winsound

                        winsound.Beep(1000, 180)
                    except:
                        pass
                    color = (22, 211, 120)
                else:
                    color = (255, 180, 40)
                label = f"{sname}  {confidence}%"
            else:
                label = f"Unknown  {confidence}%"
                color = (80, 80, 240)
            cv2.rectangle(img, (x, y), (x + w, y + h), color, 2)
            cv2.rectangle(img, (x, y - 34), (x + w, y), color, cv2.FILLED)
            cv2.putText(
                img,
                label,
                (x + 5, y - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.52,
                (255, 255, 255),
                2,
            )
        cv2.imshow(f"Attendance [{cur_dept}] – Q to Exit", img)
        if cv2.waitKey(1) == ord("q"):
            break
    cam.release()
    cv2.destroyAllWindows()
    messagebox.showinfo(
        "Done", f"✅ Session ended.\nMarked today ({cur_dept}): {len(marked)}"
    )
    setstatus(f"Done – {len(marked)} marked ({cur_dept})", C["green"])
    refresh_stats()


# ============================================================
#  VIEW ATTENDANCE  – with dept filter dropdown for dept users
# ============================================================
def ViewAttendance():
    vw = tk.Toplevel(window)
    vw.title("View Attendance")
    vw.geometry("940x580")
    vw.configure(bg=C["bg"])
    mk_label(
        vw, "📊  Attendance Records", fg=C["txt"], font=F["head"], bg=C["bg"]
    ).pack(pady=(14, 4))

    top = tk.Frame(vw, bg=C["bg"])
    top.pack(fill=tk.X, padx=15, pady=5)

    # Date entry
    mk_label(top, "Date:", fg=C["txt2"], font=F["body"], bg=C["bg"]).pack(
        side=tk.LEFT, padx=(5, 2)
    )
    de = mk_entry(top, width=13)
    de.insert(0, datetime.datetime.now().strftime("%d-%m-%Y"))
    de.pack(side=tk.LEFT, padx=(0, 12))

    # Department filter – only shown for department users
    role = USERS[CURRENT_USER]["role"]
    dept_filter_var = tk.StringVar()
    if role == "department":
        my_dept = USERS[CURRENT_USER].get("department", "")
        # option 1: All (all dates combined for their dept)
        # option 2: their department name
        filter_options = ["All Records", my_dept]
        mk_label(top, "Filter:", fg=C["txt2"], font=F["body"], bg=C["bg"]).pack(
            side=tk.LEFT, padx=(0, 2)
        )
        dept_cb = mk_combo(
            top, values=filter_options, width=22, textvariable=dept_filter_var
        )
        dept_cb.current(0)
        dept_cb.pack(side=tk.LEFT, padx=(0, 12))

    clbl = mk_label(top, "", fg=C["cyan"], font=F["body"], bg=C["bg"])
    clbl.pack(side=tk.LEFT, padx=10)

    tf = tk.Frame(vw, bg=C["bg"])
    tf.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)
    sn = tv_style("AV", C["card"])
    cols = ("ID", "Name", "Department", "Session", "Date", "Time", "Confidence")
    tree = ttk.Treeview(tf, columns=cols, show="headings", style=f"{sn}.Treeview")
    for col, w in zip(cols, (60, 160, 150, 90, 100, 80, 90)):
        tree.heading(col, text=col)
        tree.column(col, width=w, anchor=tk.CENTER)
    sb2 = ttk.Scrollbar(tf, orient=tk.VERTICAL, command=tree.yview)
    tree.configure(yscrollcommand=sb2.set)
    tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    sb2.pack(side=tk.RIGHT, fill=tk.Y)

    def load():
        for i in tree.get_children():
            tree.delete(i)
        role2 = USERS[CURRENT_USER]["role"]
        fp = f"Attendance/Attendance_{de.get()}.csv"
        if not os.path.isfile(fp):
            clbl.config(text="No records for this date")
            return
        dfa = pd.read_csv(fp)
        if role2 == "department":
            my_dept2 = USERS[CURRENT_USER].get("department", "")
            sel = dept_filter_var.get()
            # Both options filter to this dept (dept can never see others)
            if "Department" in dfa.columns:
                dfa = dfa[dfa["Department"] == my_dept2]
        for _, row in dfa.iterrows():
            vals = list(row)
            if len(vals) == 6:
                vals.insert(3, "–")
            tree.insert("", tk.END, values=vals)
        clbl.config(text=f"Total: {len(dfa)} records")

    def export():
        fp = f"Attendance/Attendance_{de.get()}.csv"
        if not os.path.isfile(fp):
            messagebox.showinfo("Info", "No file to export")
            return
        out = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv"), ("Excel", "*.xlsx")],
            initialfile=f"Attendance_{de.get()}",
        )
        if out:
            if out.endswith(".xlsx"):
                pd.read_csv(fp).to_excel(out, index=False)
            else:
                import shutil

                shutil.copy(fp, out)
            messagebox.showinfo("Exported", f"Saved to:\n{out}")

    br = tk.Frame(vw, bg=C["bg"])
    br.pack(pady=6)
    b1 = tk.Button(br, text="🔍  Load", command=load)
    sbtn(b1, C["blue"], w=12)
    b1.pack(side=tk.LEFT, padx=8)
    b2 = tk.Button(br, text="📥  Export", command=export)
    sbtn(b2, C["green"], w=12)
    b2.pack(side=tk.LEFT, padx=8)
    load()


# ============================================================
#  VIEW STUDENTS
# ============================================================
def ViewStudents():
    sw = tk.Toplevel(window)
    sw.title("Students")
    sw.geometry("820x480")
    sw.configure(bg=C["bg"])
    mk_label(
        sw, "👥  Registered Students", fg=C["txt"], font=F["head"], bg=C["bg"]
    ).pack(pady=(14, 4))
    if not os.path.isfile("StudentDetails/StudentDetails.csv"):
        mk_label(sw, "No students registered yet.", fg=C["txt2"], bg=C["bg"]).pack(
            pady=50
        )
        return
    df = pd.read_csv("StudentDetails/StudentDetails.csv")
    if USERS[CURRENT_USER]["role"] == "department":
        d = USERS[CURRENT_USER].get("department", "")
        df = df[df["Department"] == d] if "Department" in df.columns else df
    tf = tk.Frame(sw, bg=C["bg"])
    tf.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)
    sn = tv_style("ST", C["card"])
    cols = list(df.columns)
    tree = ttk.Treeview(tf, columns=cols, show="headings", style=f"{sn}.Treeview")
    for col in cols:
        tree.heading(col, text=col)
        tree.column(col, width=130, anchor=tk.CENTER)
    sb3 = ttk.Scrollbar(tf, orient=tk.VERTICAL, command=tree.yview)
    tree.configure(yscrollcommand=sb3.set)
    tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    sb3.pack(side=tk.RIGHT, fill=tk.Y)
    for _, row in df.iterrows():
        tree.insert("", tk.END, values=list(row))
    mk_label(sw, f"Total: {len(df)} students", fg=C["cyan"], bg=C["bg"]).pack(pady=3)

    def delete_stu():
        if USERS[CURRENT_USER]["role"] != "admin":
            messagebox.showerror("Access Denied", "Only admin can delete students.")
            return
        sel = tree.selection()
        if not sel:
            messagebox.showwarning("Select", "Select a student first.")
            return
        if not messagebox.askyesno(
            "Confirm", "Delete this student and training images?"
        ):
            return
        sid = tree.item(sel[0])["values"][0]
        full = pd.read_csv("StudentDetails/StudentDetails.csv")
        full[full["ID"] != sid].to_csv("StudentDetails/StudentDetails.csv", index=False)
        for fn in os.listdir("TrainingImage"):
            if f".{sid}." in fn:
                os.remove(os.path.join("TrainingImage", fn))
        tree.delete(sel[0])
        log("DELETE", f"ID {sid}")
        messagebox.showinfo("Deleted", "Student deleted. Retrain model.")
        refresh_stats()

    bd = tk.Button(sw, text="🗑️  Delete Selected", command=delete_stu)
    sbtn(bd, C["red"], w=20)
    bd.pack(pady=8)


# ============================================================
#  REPORT
# ============================================================
def GenerateReport():
    rw = tk.Toplevel(window)
    rw.title("Report")
    rw.geometry("660x500")
    rw.configure(bg=C["bg"])
    mk_label(
        rw, "📈  Attendance Summary Report", fg=C["txt"], font=F["head"], bg=C["bg"]
    ).pack(pady=(14, 6))
    rt = tk.Text(
        rw,
        height=24,
        width=74,
        bg=C["card"],
        fg=C["txt"],
        font=F["mono"],
        relief=tk.FLAT,
        bd=0,
        padx=10,
        pady=10,
        insertbackground="white",
    )
    rt.pack(padx=14, pady=4)

    def gen():
        rt.delete(1.0, tk.END)
        files = [f for f in os.listdir("Attendance") if f.endswith(".csv")]
        if not files:
            rt.insert(tk.END, "  No records found.\n")
            return
        dfs = []
        for fn in files:
            try:
                dfs.append(pd.read_csv(f"Attendance/{fn}"))
            except:
                pass
        if not dfs:
            rt.insert(tk.END, "  No valid records.\n")
            return
        comb = pd.concat(dfs, ignore_index=True)
        if USERS[CURRENT_USER]["role"] == "department":
            d = USERS[CURRENT_USER].get("department", "")
            comb = (
                comb[comb["Department"] == d] if "Department" in comb.columns else comb
            )
        rt.insert(
            tk.END,
            "═" * 60 + "\n        ATTENDANCE SUMMARY REPORT\n" + "═" * 60 + "\n\n",
        )
        rt.insert(
            tk.END,
            f"  Generated  : {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}\n",
        )
        rt.insert(tk.END, f"  Total Records   : {len(comb)}\n")
        rt.insert(tk.END, f"  Unique Students : {comb['ID'].nunique()}\n")
        if USERS[CURRENT_USER]["role"] == "department":
            rt.insert(
                tk.END, f"  Department : {USERS[CURRENT_USER].get('department','')}\n"
            )
        rt.insert(
            tk.END, "\n" + "─" * 60 + "\n  Student-wise Count\n" + "─" * 60 + "\n"
        )
        summ = comb.groupby(["ID", "Name"]).size().reset_index(name="Days")
        summ = summ.sort_values("Days", ascending=False)
        for _, row in summ.iterrows():
            rt.insert(
                tk.END,
                f"  [{row['ID']:>4}]  {str(row['Name']):<26}  {row['Days']} days\n",
            )
        rt.insert(tk.END, "\n" + "═" * 60 + "\n")

    gb = tk.Button(rw, text="⚡  Generate", command=gen)
    sbtn(gb, C["purple"], w=20)
    gb.pack(pady=8)


# ============================================================
#  SETTINGS
# ============================================================
def OpenSettings():
    sw = tk.Toplevel(window)
    sw.title("Settings")
    sw.geometry("420x320")
    sw.configure(bg=C["bg"])
    mk_label(sw, "⚙️  System Settings", fg=C["txt"], font=F["head"], bg=C["bg"]).pack(
        pady=(14, 8)
    )
    card = mk_card(sw, "")
    card.pack(padx=22, pady=6, fill=tk.BOTH, expand=True)
    fields = [
        ("Camera Index", "camera_index"),
        ("Sample Count", "sample_count"),
        ("Confidence Threshold", "confidence_threshold"),
        ("Cooldown (seconds)", "attendance_cooldown"),
    ]
    ents = {}
    for i, (lbl, key) in enumerate(fields):
        mk_label(card, lbl + ":", fg=C["txt2"], font=F["body"]).grid(
            row=i, column=0, padx=12, pady=7, sticky="e"
        )
        e = mk_entry(card, width=14)
        e.insert(0, str(CONFIG[key]))
        e.grid(row=i, column=1, padx=12, pady=7, sticky="w")
        ents[key] = e

    def save():
        for key, e in ents.items():
            v = e.get().strip()
            if not v.isdigit():
                messagebox.showerror("Error", f"{key} must be a number!")
                return
            CONFIG[key] = int(v)
        save_all_config()
        messagebox.showinfo("Saved", "Settings saved!")
        sw.destroy()

    sb4 = tk.Button(sw, text="💾  Save", command=save)
    sbtn(sb4, C["green"], w=18)
    sb4.pack(pady=14)


# ============================================================
#  BACKUP
# ============================================================
def BackupData():
    if not messagebox.askyesno("Backup", "Create a backup now?"):
        return
    import shutil

    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    folder = f"Backups/backup_{ts}"
    assure(folder)
    for d in ["StudentDetails", "Attendance", "TrainingImageLabel"]:
        if os.path.exists(d):
            shutil.copytree(d, f"{folder}/{d}")
    log("BACKUP", f"Saved to {folder}")
    messagebox.showinfo("Done", f"✅ Backup created:\n{folder}")


# ============================================================
#  CAMERA TEST
# ============================================================
def TestCamera():
    cam = cv2.VideoCapture(CONFIG["url"])
    used = "IP Camera"
    if not cam.isOpened():
        cam = cv2.VideoCapture(CONFIG["camera_index"])
        used = "Webcam"
    if not cam.isOpened():
        messagebox.showerror("Error", "No camera found!")
        return
    messagebox.showinfo("Camera", f"Using: {used}\nPress Q to close.")
    while True:
        ret, frame = cam.read()
        if not ret:
            break
        cv2.putText(
            frame,
            f"Camera Test [{used}] – Q to Exit",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (22, 211, 120),
            2,
        )
        cv2.imshow("Camera Test", frame)
        if cv2.waitKey(1) == ord("q"):
            break
    cam.release()
    cv2.destroyAllWindows()


# ============================================================
#  ADMIN PANEL
# ============================================================
def AdminPanel():
    if USERS[CURRENT_USER]["role"] != "admin":
        messagebox.showerror("Access Denied", "Admin only!")
        return
    aw = tk.Toplevel(window)
    aw.title("Admin Panel")
    aw.geometry("720x680")
    aw.configure(bg=C["bg"])
    mk_label(
        aw,
        "👑  Admin Panel – Department & Session Management",
        fg=C["orange"],
        font=F["head"],
        bg=C["bg"],
    ).pack(pady=(14, 4))

    lc = mk_card(aw, "All Departments / Sessions")
    lc.pack(padx=20, pady=8, fill=tk.BOTH, expand=True)
    sn = tv_style("AD", C["card"])
    cols = ("Login Username", "Department Name", "Session", "Students")
    dt = ttk.Treeview(
        lc, columns=cols, show="headings", height=7, style=f"{sn}.Treeview"
    )
    for col, w in zip(cols, (160, 210, 110, 80)):
        dt.heading(col, text=col)
        dt.column(col, width=w, anchor=tk.CENTER)
    scr = ttk.Scrollbar(lc, orient=tk.VERTICAL, command=dt.yview)
    dt.configure(yscrollcommand=scr.set)
    dt.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scr.pack(side=tk.RIGHT, fill=tk.Y)

    def refresh_dt():
        for i in dt.get_children():
            dt.delete(i)
        counts = {}
        if os.path.isfile("StudentDetails/StudentDetails.csv"):
            try:
                sdf = pd.read_csv("StudentDetails/StudentDetails.csv")
                if "Department" in sdf.columns:
                    counts = sdf["Department"].value_counts().to_dict()
            except:
                pass
        for uname, udata in USERS.items():
            if udata["role"] == "department":
                dept = udata.get("department", "–")
                dt.insert(
                    "",
                    tk.END,
                    values=(
                        uname,
                        dept,
                        udata.get("session", "–"),
                        counts.get(dept, 0),
                    ),
                )

    refresh_dt()

    ac = mk_card(aw, "Add New Department / Session")
    ac.pack(padx=20, pady=6, fill=tk.X)
    r = tk.Frame(ac, bg=C["card"])
    r.pack(fill=tk.X, pady=4)

    def _lbl(p, t):
        return mk_label(p, t, fg=C["txt2"], font=F["small"])

    _lbl(r, "Login Username:").grid(row=0, column=0, padx=8, pady=5, sticky="e")
    e_user = mk_entry(r, width=13)
    e_user.grid(row=0, column=1, padx=5, pady=5, sticky="w")
    _lbl(r, "Dept (e.g. BCA):").grid(row=0, column=2, padx=8, pady=5, sticky="e")
    e_dept = mk_entry(r, width=13)
    e_dept.grid(row=0, column=3, padx=5, pady=5, sticky="w")
    _lbl(r, "Session (e.g. 2023-26):").grid(row=1, column=0, padx=8, pady=5, sticky="e")
    e_sess = mk_entry(r, width=13)
    e_sess.grid(row=1, column=1, padx=5, pady=5, sticky="w")
    _lbl(r, "Password:").grid(row=1, column=2, padx=8, pady=5, sticky="e")
    e_pwd = mk_entry(r, width=13, show="●")
    e_pwd.grid(row=1, column=3, padx=5, pady=5, sticky="w")

    def add_dept():
        uname = e_user.get().strip()
        dname = e_dept.get().strip()
        sess = e_sess.get().strip()
        pwd = e_pwd.get().strip()
        if not all([uname, dname, sess, pwd]):
            messagebox.showerror("Error", "All fields required!")
            return
        if uname in USERS:
            messagebox.showerror("Error", f"Username '{uname}' already exists!")
            return
        full = f"{dname} {sess}"
        USERS[uname] = {
            "password": hashlib.sha256(pwd.encode()).hexdigest(),
            "role": "department",
            "department": full,
            "session": sess,
        }
        save_all_config()
        refresh_dt()
        for e in [e_user, e_dept, e_sess, e_pwd]:
            e.delete(0, "end")
        messagebox.showinfo(
            "Created",
            f"✅ Department created!\n\nLogin    : {uname}\nDept     : {full}\nSession  : {sess}",
        )
        log("ADMIN", f"Created dept: {full} login:{uname}")

    badd = tk.Button(ac, text="➕  Add Department", command=add_dept)
    sbtn(badd, C["green"], w=22)
    badd.pack(pady=(4, 6))

    xc = mk_card(aw, "Actions on Selected Row")
    xc.pack(padx=20, pady=6, fill=tk.X)
    xr = tk.Frame(xc, bg=C["card"])
    xr.pack(pady=6)

    def sel():
        s = dt.selection()
        if not s:
            messagebox.showwarning("Select", "Select a department row first.")
            return None
        return dt.item(s[0])["values"][0]

    def del_dept():
        uname = sel()
        if not uname:
            return
        if not messagebox.askyesno(
            "Confirm", f"Delete login '{uname}'?\n(Student records kept)"
        ):
            return
        del USERS[uname]
        save_all_config()
        refresh_dt()
        log("ADMIN", f"Deleted dept login: {uname}")
        messagebox.showinfo("Deleted", f"Login '{uname}' removed.")

    def reset_pwd():
        uname = sel()
        if not uname:
            return
        new = simpledialog.askstring(
            "Reset", f"New password for '{uname}':", show="*", parent=aw
        )
        if not new:
            return
        if len(new) < 4:
            messagebox.showerror("Error", "Min 4 chars!")
            return
        USERS[uname]["password"] = hashlib.sha256(new.encode()).hexdigest()
        save_all_config()
        messagebox.showinfo("Done", f"Password reset for '{uname}'")

    def view_strength():
        if not os.path.isfile("StudentDetails/StudentDetails.csv"):
            messagebox.showinfo("Info", "No student data.")
            return
        df = pd.read_csv("StudentDetails/StudentDetails.csv")
        if "Session" not in df.columns:
            messagebox.showinfo("Info", "No session data in CSV.")
            return
        summ = df.groupby(["Department", "Session"]).size().reset_index(name="Count")
        msg = "Session-wise Strength:\n\n"
        for _, row in summ.iterrows():
            msg += f"  {str(row['Department']):<30} Session: {str(row['Session']):<12} → {row['Count']} students\n"
        messagebox.showinfo("Strength", msg)

    for txt2b, cmd, col in [
        ("🗑️  Delete Dept", del_dept, C["red"]),
        ("🔑  Reset Password", reset_pwd, C["orange"]),
        ("📊  Session Strength", view_strength, C["blue"]),
    ]:
        b = tk.Button(xr, text=txt2b, command=cmd)
        sbtn(b, col, w=20)
        b.pack(side=tk.LEFT, padx=8)

    pc = mk_card(aw, "Change Admin Password")
    pc.pack(padx=20, pady=6, fill=tk.X)

    def chg_pwd():
        old = simpledialog.askstring(
            "Old Password", "Current admin password:", show="*", parent=aw
        )
        if not old:
            return
        if hashlib.sha256(old.encode()).hexdigest() != USERS["admin"]["password"]:
            messagebox.showerror("Wrong", "Incorrect current password!")
            return
        new = simpledialog.askstring(
            "New Password", "Enter new password:", show="*", parent=aw
        )
        if not new or len(new) < 4:
            messagebox.showerror("Error", "Min 4 chars!")
            return
        USERS["admin"]["password"] = hashlib.sha256(new.encode()).hexdigest()
        save_all_config()
        messagebox.showinfo("Updated", "Admin password changed!")

    bcp = tk.Button(pc, text="🔒  Change Admin Password", command=chg_pwd)
    sbtn(bcp, C["purple"], w=26)
    bcp.pack(pady=5)


# ============================================================
#  ADMIN DASHBOARD  (info cards shown when admin is logged in)
# ============================================================
admin_dash_frame = None  # global ref so refresh_stats can rebuild it


def _rebuild_admin_dash():
    """Rebuild the scrollable department info cards inside admin_dash_frame."""
    global admin_dash_frame
    if not admin_dash_frame or not admin_dash_frame.winfo_exists():
        return
    for w in admin_dash_frame.winfo_children():
        w.destroy()
    today = datetime.datetime.now().strftime("%d-%m-%Y")

    dept_users = [(u, d) for u, d in USERS.items() if d["role"] == "department"]
    if not dept_users:
        tk.Label(
            admin_dash_frame,
            text="No departments added yet. Use Admin Panel to add departments.",
            bg=C["bg"],
            fg=C["txt2"],
            font=F["body"],
        ).pack(pady=20)
        return

    # Grid of cards: 3 per row
    row_f = None
    accent_cycle = [
        C["blue"],
        C["green"],
        C["orange"],
        C["purple"],
        C["cyan"],
        C["pink"],
        C["teal"],
    ]
    for idx, (uname, udata) in enumerate(dept_users):
        if idx % 3 == 0:
            row_f = tk.Frame(admin_dash_frame, bg=C["bg"])
            row_f.pack(fill=tk.X, padx=4, pady=4)
        acc = accent_cycle[idx % len(accent_cycle)]
        dept_name = udata.get("department", "–")
        session = udata.get("session", "–")
        strength = _dept_student_count(dept_name)
        present = _dept_today_count(dept_name)
        absent = max(0, strength - present)

        # Card frame
        card = tk.Frame(
            row_f, bg=C["card2"], bd=0, highlightbackground=acc, highlightthickness=2
        )
        card.pack(side=tk.LEFT, padx=6, pady=2, fill=tk.BOTH, expand=True)

        # Top accent bar
        top_bar = tk.Frame(card, bg=acc, height=4)
        top_bar.pack(fill=tk.X)

        # Dept name
        tk.Label(
            card,
            text=dept_name,
            bg=C["card2"],
            fg=C["txt"],
            font=("Segoe UI", 11, "bold"),
        ).pack(pady=(8, 1), padx=10, anchor="w")
        # Session badge
        sess_fr = tk.Frame(card, bg=C["card2"])
        sess_fr.pack(anchor="w", padx=10)
        tk.Label(sess_fr, text="📅", bg=C["card2"], fg=acc, font=F["small"]).pack(
            side=tk.LEFT
        )
        tk.Label(
            sess_fr,
            text=f" Session: {session}",
            bg=C["card2"],
            fg=C["txt2"],
            font=F["small"],
        ).pack(side=tk.LEFT)

        # Username badge
        u_fr = tk.Frame(card, bg=C["card2"])
        u_fr.pack(anchor="w", padx=10, pady=(2, 0))
        tk.Label(u_fr, text="👤", bg=C["card2"], fg=acc, font=F["small"]).pack(
            side=tk.LEFT
        )
        tk.Label(
            u_fr, text=f" Login: {uname}", bg=C["card2"], fg=C["txt2"], font=F["small"]
        ).pack(side=tk.LEFT)

        # Separator
        tk.Frame(card, bg=C["border"], height=1).pack(fill=tk.X, padx=10, pady=6)

        # Stats row
        stats_fr = tk.Frame(card, bg=C["card2"])
        stats_fr.pack(fill=tk.X, padx=10, pady=(0, 10))

        def stat_mini(parent, label, value, color):
            f = tk.Frame(parent, bg=C["card2"])
            f.pack(side=tk.LEFT, expand=True)
            tk.Label(
                f,
                text=str(value),
                bg=C["card2"],
                fg=color,
                font=("Segoe UI", 16, "bold"),
            ).pack()
            tk.Label(
                f, text=label, bg=C["card2"], fg=C["txt2"], font=("Segoe UI", 7)
            ).pack()

        stat_mini(stats_fr, "Students", strength, C["blue"])
        stat_mini(stats_fr, "Present", present, C["green"])
        stat_mini(stats_fr, "Absent", absent, C["red"])


# ============================================================
#  LOGOUT
# ============================================================
def logout():
    global CURRENT_USER
    if not messagebox.askyesno("Logout", "Log out and return to login?"):
        return
    CURRENT_USER = None
    window.withdraw()
    load_all_config()
    login_screen()
    if CURRENT_USER:
        # Role can change (admin → dept or vice versa) which changes the UI layout.
        # Cleanest fix: destroy window and restart the script so the full UI rebuilds.
        window.destroy()
        import subprocess, sys

        subprocess.Popen([sys.executable] + sys.argv)
    else:
        window.destroy()


# ============================================================
#  LOGIN SCREEN  –  fixed combobox colors
# ============================================================
def login_screen():
    global CURRENT_USER

    lw = tk.Tk()
    lw.title("Login – Attendance System")
    lw.geometry("440x520")
    lw.configure(bg=C["bg"])
    lw.resizable(False, False)
    lw.update_idletasks()
    lw.geometry(
        f"440x520+{(lw.winfo_screenwidth()-440)//2}+{(lw.winfo_screenheight()-520)//2}"
    )

    # ── Header strip ──────────────────────────────────────────
    hf = tk.Frame(lw, bg=C["hdr"], height=120)
    hf.pack(fill=tk.X)
    hf.pack_propagate(False)
    tk.Label(hf, text="🎓", bg=C["hdr"], font=("Segoe UI", 36)).pack(pady=(10, 0))
    tk.Label(
        hf,
        text="Face Recognition Attendance",
        bg=C["hdr"],
        fg=C["txt"],
        font=("Segoe UI", 13, "bold"),
    ).pack()
    tk.Label(
        hf,
        text="Attendance Management System  v1.0",
        bg=C["hdr"],
        fg=C["txt2"],
        font=("Segoe UI", 8),
    ).pack()

    # ── Card body ─────────────────────────────────────────────
    cf = tk.Frame(lw, bg=C["card"])
    cf.pack(padx=36, pady=20, fill=tk.BOTH, expand=True)
    tk.Label(
        cf, text="Sign In", bg=C["card"], fg=C["txt"], font=("Segoe UI", 16, "bold")
    ).pack(pady=(18, 2))
    tk.Label(
        cf,
        text="Select account and enter password",
        bg=C["card"],
        fg=C["txt2"],
        font=F["small"],
    ).pack(pady=(0, 16))

    # Account label + combobox
    tk.Label(cf, text="Account", bg=C["card"], fg=C["txt2"], font=F["small"]).pack(
        anchor="w", padx=22
    )

    # ── FIX: use a Canvas+Listbox approach for fully dark combo ──
    # We draw the combobox manually as Entry + Button + Toplevel popup
    # so there are zero white-background issues on any Windows version.
    user_var = tk.StringVar(value=list(USERS.keys())[0])
    combo_frame = tk.Frame(
        cf, bg=C["input"], bd=0, highlightbackground=C["border"], highlightthickness=1
    )
    combo_frame.pack(padx=22, pady=(2, 12), fill=tk.X, ipady=3)

    combo_display = tk.Label(
        combo_frame,
        textvariable=user_var,
        bg=C["input"],
        fg=C["txt"],
        font=F["body"],
        anchor="w",
        cursor="hand2",
    )
    combo_display.pack(side=tk.LEFT, padx=8, fill=tk.X, expand=True)
    combo_arrow = tk.Label(
        combo_frame,
        text="▾",
        bg=C["input"],
        fg=C["cyan"],
        font=("Segoe UI", 11),
        cursor="hand2",
    )
    combo_arrow.pack(side=tk.RIGHT, padx=6)

    popup_open = [False]

    def open_popup(event=None):
        if popup_open[0]:
            return
        popup_open[0] = True

        pop = tk.Toplevel(lw)
        pop.overrideredirect(True)
        pop.configure(bg=C["border"])

        # Position below combo_frame
        lw.update_idletasks()
        x = combo_frame.winfo_rootx()
        y = combo_frame.winfo_rooty() + combo_frame.winfo_height() + 1
        w = combo_frame.winfo_width()
        pop.geometry(f"{w}x{min(len(USERS)*28+4, 200)}+{x}+{y}")
        pop.lift()

        lb = tk.Listbox(
            pop,
            bg=C["input"],
            fg=C["txt"],
            selectbackground=C["blue"],
            selectforeground=C["txt"],
            font=F["body"],
            relief=tk.FLAT,
            bd=0,
            highlightthickness=0,
            activestyle="none",
        )
        lb.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
        for u in USERS.keys():
            lb.insert(tk.END, u)

        # highlight current
        try:
            idx = list(USERS.keys()).index(user_var.get())
            lb.selection_set(idx)
            lb.see(idx)
        except:
            pass

        def on_select(event=None):
            sel = lb.curselection()
            if sel:
                user_var.set(lb.get(sel[0]))
            popup_open[0] = False
            pop.destroy()

        def on_close(event=None):
            popup_open[0] = False
            pop.destroy()

        lb.bind("<<ListboxSelect>>", on_select)
        lb.bind("<Return>", on_select)
        pop.bind("<FocusOut>", on_close)
        pop.bind("<Escape>", on_close)
        lb.focus_set()

    combo_display.bind("<Button-1>", open_popup)
    combo_arrow.bind("<Button-1>", open_popup)
    combo_frame.bind("<Button-1>", open_popup)

    # Password
    tk.Label(cf, text="Password", bg=C["card"], fg=C["txt2"], font=F["small"]).pack(
        anchor="w", padx=22, pady=(4, 0)
    )
    pe = tk.Entry(
        cf,
        show="●",
        bg=C["input"],
        fg=C["txt"],
        insertbackground=C["cyan"],
        relief=tk.FLAT,
        bd=0,
        font=F["body"],
        width=30,
        highlightbackground=C["border"],
        highlightthickness=1,
    )
    pe.pack(padx=22, pady=(3, 4), fill=tk.X, ipady=7)

    elbl = tk.Label(cf, text="", bg=C["card"], fg=C["red"], font=F["small"])
    elbl.pack(pady=3)

    def do_login(event=None):
        global CURRENT_USER
        u = user_var.get().strip()
        p = pe.get()
        hsh = hashlib.sha256(p.encode()).hexdigest()
        if u in USERS and USERS[u]["password"] == hsh:
            CURRENT_USER = u
            log("LOGIN", f"{u} logged in")
            lw.destroy()
        else:
            elbl.config(text="❌  Invalid password. Try again.")
            pe.delete(0, "end")

    pe.bind("<Return>", do_login)
    lb2 = tk.Button(
        cf, text="Login  →", command=do_login, font=("Segoe UI", 11, "bold")
    )
    sbtn(lb2, C["blue"], hbg=C["cyan"], w=22)
    lb2.pack(pady=(6, 4), ipady=7)
    tk.Label(
        cf,
        text="Default Admin: Admin / Admin123",
        bg=C["card"],
        fg=C["txt2"],
        font=("Segoe UI", 8),
    ).pack(side=tk.BOTTOM, pady=10)
    lw.protocol("WM_DELETE_WINDOW", lw.destroy)
    lw.mainloop()


# ============================================================
#  BOOTSTRAP
# ============================================================
load_all_config()
init_dirs()
init_csv()
login_screen()

if not CURRENT_USER:
    import sys

    sys.exit(0)

# ============================================================
#  MAIN WINDOW
# ============================================================
window = tk.Tk()
window.title("Face Recognition Attendance System  v1.0")
window.configure(bg=C["bg"])
window.resizable(True, True)

role_now = USERS[CURRENT_USER]["role"]

# Choose window size: admin gets taller for dashboard cards
if role_now == "admin":
    window.geometry("1020x820")
    window.update_idletasks()
    window.geometry(
        f"1020x820+{(window.winfo_screenwidth()-1020)//2}+{(window.winfo_screenheight()-820)//2}"
    )
else:
    window.geometry("980x720")
    window.update_idletasks()
    window.geometry(
        f"980x720+{(window.winfo_screenwidth()-980)//2}+{(window.winfo_screenheight()-720)//2}"
    )

# ── HEADER ───────────────────────────────────────────────────
hdr = tk.Frame(window, bg=C["hdr"], height=66)
hdr.pack(fill=tk.X)
hdr.pack_propagate(False)
tk.Label(
    hdr,
    text="🎓  Face Recognition Attendance System",
    bg=C["hdr"],
    fg=C["txt"],
    font=("Segoe UI", 17, "bold"),
).pack(side=tk.LEFT, padx=20, pady=16)
lgout = tk.Button(
    hdr,
    text="⏻  Logout",
    command=logout,
    font=("Segoe UI", 9, "bold"),
    bg=C["red"],
    fg="white",
    relief=tk.FLAT,
    activebackground="#b91c1c",
    cursor="hand2",
    bd=0,
)
lgout.pack(side=tk.RIGHT, padx=10, pady=16, ipadx=8, ipady=3)
user_lbl = tk.Label(
    hdr,
    text=f"  👤  {CURRENT_USER.upper()}",
    bg=C["hdr"],
    fg=C["cyan"],
    font=("Segoe UI", 10, "bold"),
)
user_lbl.pack(side=tk.RIGHT, padx=6, pady=16)

# ── STATS BAR ─────────────────────────────────────────────────
sf = tk.Frame(window, bg=C["sidebar"], height=50)
sf.pack(fill=tk.X)
sf.pack_propagate(False)


def _sb(parent, label, vc):
    f = tk.Frame(parent, bg=C["sidebar"])
    f.pack(side=tk.LEFT, padx=26, pady=7)
    tk.Label(f, text=label, bg=C["sidebar"], fg=C["txt2"], font=F["small"]).pack()
    v = tk.Label(f, text="–", bg=C["sidebar"], fg=vc, font=("Segoe UI", 13, "bold"))
    v.pack()
    return v


stat_stu = _sb(sf, "📚  Total Students", C["blue"])
stat_att = _sb(sf, "✅  Today Attendance", C["green"])

# Extra stats for department users
if role_now == "department":
    _sb(sf, f"🏫  {USERS[CURRENT_USER].get('department','')}", C["cyan"])
    _sb(sf, f"📅  Session: {USERS[CURRENT_USER].get('session','')}", C["orange"])

# ── CLOCK ─────────────────────────────────────────────────────
tframe = tk.Frame(window, bg=C["bg"])
tframe.pack(pady=(8, 4))
clock_lbl = tk.Label(tframe, fg=C["cyan"], bg=C["bg"], font=F["clock"])
clock_lbl.pack()
date_lbl = tk.Label(tframe, fg=C["txt2"], bg=C["bg"], font=F["small"])
date_lbl.pack()
tick()

# ── ADMIN DASHBOARD CARDS (only when admin logged in) ─────────
if role_now == "admin":
    dash_outer = tk.LabelFrame(
        window,
        text="  📋  Department Overview",
        bg=C["bg"],
        fg=C["cyan"],
        font=("Segoe UI", 10, "bold"),
        padx=8,
        pady=8,
        relief=tk.FLAT,
        bd=1,
        highlightbackground=C["border"],
        highlightthickness=1,
    )
    dash_outer.pack(padx=24, pady=(4, 6), fill=tk.X)

    # Scrollable canvas for many departments
    dash_canvas = tk.Canvas(
        dash_outer, bg=C["bg"], height=170, highlightthickness=0, bd=0
    )
    dash_scroll = ttk.Scrollbar(
        dash_outer, orient=tk.HORIZONTAL, command=dash_canvas.xview
    )
    dash_canvas.configure(xscrollcommand=dash_scroll.set)
    dash_scroll.pack(side=tk.BOTTOM, fill=tk.X)
    dash_canvas.pack(fill=tk.BOTH, expand=True)

    admin_dash_frame = tk.Frame(dash_canvas, bg=C["bg"])
    dash_canvas_win = dash_canvas.create_window(
        (0, 0), window=admin_dash_frame, anchor="nw"
    )

    def _on_dash_configure(event):
        dash_canvas.configure(scrollregion=dash_canvas.bbox("all"))

    admin_dash_frame.bind("<Configure>", _on_dash_configure)

    _rebuild_admin_dash()


# ── REGISTRATION CARD  (hidden for admin) ─────────────────────
def _rf(parent, lbl, r, co):
    mk_label(parent, lbl, fg=C["txt2"], font=F["body"]).grid(
        row=r, column=co, padx=(8, 4), pady=7, sticky="e"
    )
    e = mk_entry(parent, width=26)
    e.grid(row=r, column=co + 1, padx=4, pady=7, sticky="w")
    xb = tk.Button(
        parent,
        text="✕",
        bg=C["input"],
        fg=C["txt2"],
        font=("Segoe UI", 8),
        relief=tk.FLAT,
        bd=0,
        cursor="hand2",
        command=lambda _e=e: _e.delete(0, "end"),
    )
    xb.grid(row=r, column=co + 2, padx=1)
    return e


# Dummy entry vars so clear_all() / logout() don't crash even for admin
ent_id = tk.Entry(window)
ent_name = tk.Entry(window)
ent_email = tk.Entry(window)
ent_dept = tk.Entry(window)

if role_now != "admin":
    reg_card = tk.LabelFrame(
        window,
        text="  Student Registration",
        bg=C["card"],
        fg=C["cyan"],
        font=("Segoe UI", 10, "bold"),
        padx=20,
        pady=12,
        relief=tk.FLAT,
        bd=1,
        highlightbackground=C["border"],
        highlightthickness=1,
    )
    reg_card.pack(padx=24, pady=(4, 8), fill=tk.X)

    ent_id = _rf(reg_card, "Student ID *", 0, 0)
    ent_name = _rf(reg_card, "Full Name *", 0, 3)
    ent_email = _rf(reg_card, "Email", 1, 0)
    ent_dept = _rf(reg_card, "Department *", 1, 3)

    if role_now == "department":
        dv = USERS[CURRENT_USER].get("department", "")
        ent_dept.insert(0, dv)
        # ent_dept.configure(state="readonly",bg=C["sidebar"])
        ent_dept.configure(
            state="readonly",
            fg=C["txt"],
            readonlybackground=C["input"],  # same as other fields
            insertbackground=C["cyan"],
        )

    cab = tk.Button(reg_card, text="🗑️  Clear All", command=clear_all)
    sbtn(cab, C["orange"], w=14)
    cab.grid(row=2, column=2, columnspan=3, pady=6)

# ── MAIN BUTTONS  (Capture / Train / Attendance – hidden for admin) ────
if role_now != "admin":
    mf = tk.Frame(window, bg=C["bg"])
    mf.pack(pady=4, padx=24, fill=tk.X)
    for i, (t, cmd, col) in enumerate(
        [
            ("📸  Capture Images", TakeImages, C["blue"]),
            ("🧠  Train Model", TrainImages, C["orange"]),
            ("✅  Take Attendance", TrackImages, C["green"]),
        ]
    ):
        b = tk.Button(mf, text=t, command=cmd)
        sbtn(b, col, font=F["btnlg"], w=20, h=2)
        b.grid(row=0, column=i, padx=10, pady=4, sticky="ew")
        mf.columnconfigure(i, weight=1)

# ── SECONDARY BUTTONS ─────────────────────────────────────────
sf2 = tk.Frame(window, bg=C["bg"])
sf2.pack(pady=4, padx=24, fill=tk.X)
for i, (t, cmd, fg2) in enumerate(
    [
        ("📊  Attendance", ViewAttendance, C["cyan"]),
        ("👥  Students", ViewStudents, C["blue"]),
        ("📈  Report", GenerateReport, C["purple"]),
        ("⚙️  Settings", OpenSettings, C["txt2"]),
        ("👑  Admin Panel", AdminPanel, C["orange"]),
    ]
):
    b = tk.Button(
        sf2,
        text=t,
        command=cmd,
        font=("Segoe UI", 9, "bold"),
        bg=C["card"],
        fg=fg2,
        relief=tk.FLAT,
        bd=1,
        highlightbackground=C["border"],
        highlightthickness=1,
        cursor="hand2",
        width=15,
        activebackground=C["hover"],
        activeforeground=fg2,
    )
    b.grid(row=0, column=i, padx=7, pady=4, ipady=5)
    b.bind("<Enter>", lambda e, _b=b: _b.configure(bg=C["hover"]))
    b.bind("<Leave>", lambda e, _b=b: _b.configure(bg=C["card"]))
    sf2.columnconfigure(i, weight=1)

# ── UTILITY BUTTONS ───────────────────────────────────────────
uf = tk.Frame(window, bg=C["bg"])
uf.pack(pady=4, padx=24)
for t, cmd, col in [
    ("📷  Test Camera", TestCamera, C["teal"]),
    ("💾  Backup", BackupData, "#607d8b"),
    ("❌  Exit", window.destroy, C["red"]),
]:
    b = tk.Button(uf, text=t, command=cmd)
    sbtn(b, col, w=15)
    b.grid(row=0, column=uf.grid_size()[0], padx=9, pady=4, ipady=3)

# ── STATUS BAR ────────────────────────────────────────────────
sbf = tk.Frame(window, bg=C["sidebar"], height=26)
sbf.pack(side=tk.BOTTOM, fill=tk.X)
sbf.pack_propagate(False)
status_label = tk.Label(
    sbf, text="  ✔  System Ready", bg=C["sidebar"], fg=C["green"], font=F["small"]
)
status_label.pack(side=tk.LEFT, padx=10, pady=4)
tk.Label(
    sbf,
    text="Face Recognition Attendance System  v1.0  |  OpenCV + Python",
    bg=C["sidebar"],
    fg=C["txt2"],
    font=F["small"],
).pack(side=tk.RIGHT, padx=10, pady=4)

# ── INIT ──────────────────────────────────────────────────────
if not os.path.isfile("haarcascade_frontalface_default.xml"):
    setstatus("⚠  haarcascade_frontalface_default.xml not found!", C["red"])

refresh_stats()
window.mainloop()
