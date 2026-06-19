import customtkinter as ctk
from tkinter import ttk, messagebox as mess
import tkinter.simpledialog as tsd
import cv2, os, csv, time, datetime, pickle
import numpy as np
from database import Database
from insightface.app import FaceAnalysis

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")


class AttendanceApp:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("Smart Face Attendance")
        self.root.geometry("1280x720")
        self.root.minsize(1100, 650)

        self.db = Database()
        self.training_status = False
        self.face_app = None

        self.setup_style()
        self.build_ui()
        self.load_initial_stats()

    def setup_style(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", font=("Segoe UI", 11), rowheight=30)
        style.configure("Treeview.Heading", font=("Segoe UI", 12, "bold"))
        style.map("Treeview", background=[("selected", "#2E86AB")],
                  foreground=[("selected", "white")])

    def build_ui(self):
        self.root.grid_rowconfigure(0, weight=0)
        self.root.grid_rowconfigure(1, weight=0)
        self.root.grid_rowconfigure(2, weight=1)
        self.root.grid_rowconfigure(3, weight=0)
        self.root.grid_columnconfigure(0, weight=1)

        self.build_menubar()
        self.build_header()
        self.build_body()
        self.build_statusbar()

    def build_menubar(self):
        menubar = ctk.CTkFrame(self.root, height=28, corner_radius=0)
        menubar.grid(row=0, column=0, sticky="ew")
        menubar.grid_propagate(False)

        btn_font = ("Segoe UI", 11)
        ctk.CTkButton(menubar, text="File", font=btn_font, width=50, height=24,
                      fg_color="transparent", text_color=("#2C3E50", "#aaa"),
                      hover_color=("#D6EAF8", "#333"), corner_radius=4,
                      command=lambda: self.show_file_menu(menubar)).pack(side="left", padx=(4, 0))
        ctk.CTkButton(menubar, text="Help", font=btn_font, width=50, height=24,
                      fg_color="transparent", text_color=("#2C3E50", "#aaa"),
                      hover_color=("#D6EAF8", "#333"), corner_radius=4,
                      command=self.contact).pack(side="left", padx=(2, 0))

        self.menu_bar = menubar

    def show_file_menu(self, parent):
        menu_win = ctk.CTkToplevel(self.root)
        menu_win.title("")
        menu_win.geometry("180x120")
        menu_win.resizable(False, False)
        menu_win.attributes("-topmost", True)
        menu_win.transient(self.root)

        x = parent.winfo_rootx() + 4
        y = parent.winfo_rooty() + parent.winfo_height() + 2
        menu_win.geometry(f"+{x}+{y}")

        btn_style = {"font": ("Segoe UI", 12), "height": 32, "anchor": "w",
                     "fg_color": "transparent", "text_color": ("#2C3E50", "#ddd"),
                     "hover_color": ("#E8F0FE", "#333"), "corner_radius": 4}

        ctk.CTkButton(menu_win, text="  Change Password", command=lambda: [menu_win.destroy(), self.change_pass()],
                      **btn_style).pack(fill="x", padx=4, pady=(4, 0))
        ctk.CTkButton(menu_win, text="  Export Report", command=lambda: [menu_win.destroy(), self.export_report()],
                      **btn_style).pack(fill="x", padx=4, pady=(2, 0))
        ctk.CTkButton(menu_win, text="  Exit", command=lambda: [menu_win.destroy(), self.root.destroy()],
                      **btn_style).pack(fill="x", padx=4, pady=(2, 4))

    def build_header(self):
        hdr = ctk.CTkFrame(self.root, height=68, corner_radius=0)
        hdr.grid(row=1, column=0, sticky="ew")
        hdr.grid_propagate(False)
        hdr.grid_columnconfigure(0, weight=1)
        hdr.grid_columnconfigure(1, weight=0)

        title_frame = ctk.CTkFrame(hdr, fg_color="transparent")
        title_frame.grid(row=0, column=0, sticky="w", padx=24, pady=6)

        ctk.CTkLabel(title_frame, text="Smart Face Attendance",
                     font=("Segoe UI", 24, "bold"),
                     text_color=("#1a5c7a", "#5bb8e8")).pack(anchor="w")
        ctk.CTkLabel(title_frame, text="Face Recognition Based",
                     font=("Segoe UI", 13),
                     text_color=("#7F8C8D", "#a0a0a0")).pack(anchor="w")

        right_frame = ctk.CTkFrame(hdr, fg_color="transparent")
        right_frame.grid(row=0, column=1, sticky="e", padx=24, pady=6)

        self.clock_label = ctk.CTkLabel(right_frame, text="",
                                        font=("Segoe UI", 15, "bold"),
                                        text_color=("#E67E22", "#F39C12"))
        self.clock_label.pack(anchor="e")
        self.tick_clock()

        self.theme_switch = ctk.CTkSwitch(right_frame, text="Dark Mode",
                                          command=self.toggle_theme,
                                          font=("Segoe UI", 12))
        self.theme_switch.pack(anchor="e", pady=(2, 0))

    def tick_clock(self):
        now = datetime.datetime.now().strftime("%d-%m-%Y  %H:%M:%S")
        self.clock_label.configure(text=now)
        self.root.after(1000, self.tick_clock)

    def toggle_theme(self):
        mode = "dark" if self.theme_switch.get() else "light"
        ctk.set_appearance_mode(mode)
        self.update_status(f"Theme switched to {mode}")

    def build_body(self):
        body = ctk.CTkFrame(self.root, fg_color="transparent")
        body.grid(row=2, column=0, sticky="nsew", padx=12, pady=(4, 4))
        body.grid_columnconfigure(0, weight=1, uniform="col")
        body.grid_columnconfigure(1, weight=1, uniform="col")
        body.grid_rowconfigure(0, weight=1)

        self.build_left_panel(body)
        self.build_right_panel(body)

    def build_left_panel(self, parent):
        left = ctk.CTkFrame(parent, corner_radius=14)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 6))

        ctk.CTkLabel(left, text="Student Registration",
                     font=("Segoe UI", 18, "bold"),
                     text_color=("#1a5c7a", "#5bb8e8")).pack(anchor="w", padx=20, pady=(16, 4))

        sep = ctk.CTkFrame(left, height=2, corner_radius=1)
        sep.pack(fill="x", padx=20)
        sep.configure(fg_color=("#D5D8DC", "#333"))

        form = ctk.CTkFrame(left, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=20, pady=12)
        form.grid_columnconfigure(0, weight=1)
        form.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(form, text="Student ID", font=("Segoe UI", 13, "bold")).grid(row=0, column=0, sticky="w", pady=(12, 2))
        self.id_entry = ctk.CTkEntry(form, height=38, font=("Segoe UI", 13), placeholder_text="Enter student ID")
        self.id_entry.grid(row=1, column=0, sticky="ew", padx=(0, 6), pady=(0, 8))

        ctk.CTkLabel(form, text="Student Name", font=("Segoe UI", 13, "bold")).grid(row=0, column=1, sticky="w", pady=(12, 2))
        self.name_entry = ctk.CTkEntry(form, height=38, font=("Segoe UI", 13), placeholder_text="Enter student name")
        self.name_entry.grid(row=1, column=1, sticky="ew", padx=(6, 0), pady=(0, 8))

        ctk.CTkLabel(form, text="Capture Progress", font=("Segoe UI", 12, "bold"),
                     text_color=("#7F8C8D", "#aaa")).grid(row=2, column=0, columnspan=2, sticky="w", pady=(16, 2))

        self.progress_bar = ctk.CTkProgressBar(form, height=10, corner_radius=5)
        self.progress_bar.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(4, 4))
        self.progress_bar.set(0)

        self.progress_label = ctk.CTkLabel(form, text="Ready to capture images",
                                           font=("Segoe UI", 12),
                                           text_color=("#95A5A6", "#888"))
        self.progress_label.grid(row=4, column=0, columnspan=2, sticky="w", pady=(0, 10))

        btn_row = ctk.CTkFrame(form, fg_color="transparent")
        btn_row.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(8, 4))
        btn_row.grid_columnconfigure(0, weight=1)
        btn_row.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(btn_row, text="Take Images", command=self.TakeImages,
                      font=("Segoe UI", 13, "bold"), height=40, corner_radius=8).grid(row=0, column=0, sticky="ew", padx=(0, 4))
        ctk.CTkButton(btn_row, text="Clear", command=self.clear,
                      font=("Segoe UI", 13, "bold"), height=40, corner_radius=8,
                      fg_color="#E74C3C", hover_color="#C0392B").grid(row=0, column=1, sticky="ew", padx=(4, 0))

        status_card = ctk.CTkFrame(form, fg_color=("#F0F3F5", "#2a2a2a"), corner_radius=8)
        status_card.grid(row=6, column=0, columnspan=2, sticky="ew", pady=(12, 0), ipady=8)

        self.reg_status = ctk.CTkLabel(status_card, text="1) Take Images  2) Save Profile",
                                       font=("Segoe UI", 12),
                                       text_color=("#7F8C8D", "#aaa"))
        self.reg_status.pack(anchor="w", padx=12, pady=(8, 2))
        self.reg_message = ctk.CTkLabel(status_card, text="", font=("Segoe UI", 12),
                                        text_color=("#E67E22", "#F39C12"))
        self.reg_message.pack(anchor="w", padx=12, pady=(0, 8))

    def build_right_panel(self, parent):
        right = ctk.CTkFrame(parent, corner_radius=14)
        right.grid(row=0, column=1, sticky="nsew", padx=(6, 0))

        ctk.CTkLabel(right, text="Attendance Tracking",
                     font=("Segoe UI", 18, "bold"),
                     text_color=("#1a5c7a", "#5bb8e8")).pack(anchor="w", padx=20, pady=(16, 4))

        sep = ctk.CTkFrame(right, height=2, corner_radius=1)
        sep.pack(fill="x", padx=20)
        sep.configure(fg_color=("#D5D8DC", "#333"))

        stats = ctk.CTkFrame(right, fg_color="transparent")
        stats.pack(fill="x", padx=20, pady=(12, 4))

        self.stat_total = ctk.CTkLabel(stats, text="Total: 0",
                                       font=("Segoe UI", 15, "bold"),
                                       text_color=("#2E86AB", "#5bb8e8"))
        self.stat_total.pack(side="left", padx=(0, 24))

        self.stat_today = ctk.CTkLabel(stats, text="Today: 0",
                                       font=("Segoe UI", 15, "bold"),
                                       text_color=("#27AE60", "#2ECC71"))
        self.stat_today.pack(side="left", padx=(0, 24))

        self.stat_rate = ctk.CTkLabel(stats, text="Rate: 0%",
                                      font=("Segoe UI", 15, "bold"),
                                      text_color=("#E67E22", "#F39C12"))
        self.stat_rate.pack(side="left")

        act = ctk.CTkFrame(right, fg_color="transparent")
        act.pack(fill="x", padx=20, pady=(6, 10))
        act.grid_columnconfigure(0, weight=1)
        act.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(act, text="Save Profile", command=self.psw,
                      font=("Segoe UI", 13, "bold"), height=40, corner_radius=8,
                      fg_color="#27AE60", hover_color="#1E8449").grid(row=0, column=0, sticky="ew", padx=(0, 4))
        ctk.CTkButton(act, text="Take Attendance", command=self.TrackImages,
                      font=("Segoe UI", 13, "bold"), height=40, corner_radius=8,
                      fg_color="#8E44AD", hover_color="#6C3483").grid(row=0, column=1, sticky="ew", padx=(4, 0))

        table_container = ctk.CTkFrame(right, fg_color="transparent")
        table_container.pack(fill="both", expand=True, padx=14, pady=(0, 4))

        tree_frame = ctk.CTkFrame(table_container, corner_radius=8)
        tree_frame.pack(fill="both", expand=True)

        cols = ("id", "name", "date", "time")
        self.att_tree = ttk.Treeview(tree_frame, columns=cols, show="headings", height=10)
        self.att_tree.heading("id", text="ID")
        self.att_tree.heading("name", text="Name")
        self.att_tree.heading("date", text="Date")
        self.att_tree.heading("time", text="Time")
        self.att_tree.column("id", width=70, anchor="center")
        self.att_tree.column("name", width=140, anchor="center")
        self.att_tree.column("date", width=100, anchor="center")
        self.att_tree.column("time", width=100, anchor="center")
        self.att_tree.pack(side="left", fill="both", expand=True, padx=4, pady=4)

        scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.att_tree.yview)
        scroll.pack(side="right", fill="y", pady=4)
        self.att_tree.configure(yscrollcommand=scroll.set)

        ctrl = ctk.CTkFrame(right, fg_color="transparent")
        ctrl.pack(fill="x", padx=14, pady=(6, 14))
        ctrl.grid_columnconfigure(0, weight=1)
        ctrl.grid_columnconfigure(1, weight=1)
        ctrl.grid_columnconfigure(2, weight=1)

        ctk.CTkButton(ctrl, text="Export Report", command=self.export_report,
                      font=("Segoe UI", 12), height=34, corner_radius=6,
                      fg_color="transparent", text_color=("#2E86AB", "#5bb8e8"),
                      hover_color=("#D6EAF8", "#1a3a4a"),
                      border_width=1, border_color=("#2E86AB", "#5bb8e8")
                      ).grid(row=0, column=0, sticky="ew", padx=2)
        ctk.CTkButton(ctrl, text="Refresh", command=self.refresh_attendance,
                      font=("Segoe UI", 12), height=34, corner_radius=6,
                      fg_color="transparent", text_color=("#2E86AB", "#5bb8e8"),
                      hover_color=("#D6EAF8", "#1a3a4a"),
                      border_width=1, border_color=("#2E86AB", "#5bb8e8")
                      ).grid(row=0, column=1, sticky="ew", padx=2)
        ctk.CTkButton(ctrl, text="Clear All", command=self.clear_attendance,
                      font=("Segoe UI", 12), height=34, corner_radius=6,
                      fg_color="#E74C3C", hover_color="#C0392B"
                      ).grid(row=0, column=2, sticky="ew", padx=2)

    def build_statusbar(self):
        sb = ctk.CTkFrame(self.root, height=30, corner_radius=0)
        sb.grid(row=3, column=0, sticky="ew")
        sb.grid_propagate(False)

        self.status_var = ctk.StringVar(value="Ready")
        ctk.CTkLabel(sb, textvariable=self.status_var,
                     font=("Segoe UI", 10),
                     text_color=("#7F8C8D", "#aaa")).pack(side="left", padx=14)

    def update_status(self, msg):
        self.status_var.set(msg)

    def assure_path_exists(self, path):
        d = os.path.dirname(path)
        if not os.path.exists(d):
            os.makedirs(d)

    def get_face_app(self):
        if self.face_app is None:
            try:
                self.face_app = FaceAnalysis(name='buffalo_sc', providers=['CPUExecutionProvider'])
                self.face_app.prepare(ctx_id=0, det_size=(320, 320))
            except Exception as e:
                mess._show(title="Model Error",
                           message=f"Failed to load face recognition model.\nMake sure you have internet for first-time download.\nError: {e}")
                return None
        return self.face_app

    def getImagesAndLabels(self, path):
        if not os.path.isdir(path):
            return [], []
        imagePaths = [os.path.join(path, f) for f in os.listdir(path) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        if not imagePaths:
            return [], []
        app = self.get_face_app()
        if app is None:
            return [], []
        encodings, Ids = [], []
        for ip in imagePaths:
            try:
                img = cv2.imread(ip)
                if img is None:
                    continue
                if len(img.shape) == 2:
                    img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
                pad = max(img.shape[0], img.shape[1])
                padded = cv2.copyMakeBorder(img, pad, pad, pad, pad, cv2.BORDER_REPLICATE)
                faces = app.get(padded)
                if not faces:
                    continue
                serial = int(os.path.split(ip)[-1].split(".")[1])
                encodings.append(faces[0].normed_embedding)
                Ids.append(serial)
            except (ValueError, IndexError, OSError):
                continue
        return encodings, Ids

    def clear(self):
        self.id_entry.delete(0, "end")
        self.name_entry.delete(0, "end")
        self.progress_bar.set(0)
        self.progress_label.configure(text="Ready to capture images")
        self.reg_message.configure(text="")

    def TakeImages(self):
        self.assure_path_exists("TrainingImage/")
        serial = self.db.get_next_serial()
        Id = self.id_entry.get().strip()
        name = self.name_entry.get().strip()
        if not name.replace(" ", "").isalpha():
            self.reg_message.configure(text="Enter a valid name (letters only)")
            return
        if not Id.isdigit():
            self.reg_message.configure(text="Enter a numeric ID")
            return
        app = self.get_face_app()
        if app is None:
            return
        cam = cv2.VideoCapture(0)
        if not cam.isOpened():
            mess._show(title="Camera Error", message="Could not open webcam!")
            return
        sampleNum = 0
        self.progress_label.configure(text="Look at the camera...")
        while True:
            ret, img = cam.read()
            if not ret:
                break
            faces = app.get(img)
            for face in faces:
                bbox = face.bbox.astype(int)
                x1, y1, x2, y2 = bbox[0], bbox[1], bbox[2], bbox[3]
                x1, y1 = max(0, x1), max(0, y1)
                x2, y2 = min(img.shape[1], x2), min(img.shape[0], y2)
                cv2.rectangle(img, (x1, y1), (x2, y2), (255, 0, 0), 2)
                sampleNum += 1
                face_crop = img[y1:y2, x1:x2]
                cv2.imwrite(
                    f"TrainingImage/{name}.{serial}.{Id}.{sampleNum}.jpg",
                    face_crop)
                cv2.imshow("Capturing Face Images - Press Q to quit early", img)
            if cv2.waitKey(100) & 0xFF == ord("q") or sampleNum > 100:
                break
            self.progress_bar.set(min(sampleNum / 100, 1))
            self.progress_label.configure(text=f"Captured {sampleNum}/100 images")
            self.root.update()
        cam.release()
        cv2.destroyAllWindows()
        if sampleNum < 10:
            mess._show(title="Warning", message=f"Only captured {sampleNum} images. Try again with better lighting.")
            return
        self.db.add_student(serial, Id, name)
        self.reg_status.configure(text=f"Images captured for ID: {Id}")
        self.progress_bar.set(1)
        self.progress_label.configure(text=f"Done: {sampleNum} images for {name}")
        self.refresh_attendance_stats()
        self.update_status(f"Student {name} (ID: {Id}) registered with {sampleNum} images")

    def TrainImages(self):
        self.assure_path_exists("TrainingImageLabel/")
        encodings, IDs = self.getImagesAndLabels("TrainingImage")
        if not encodings or not IDs:
            mess._show(title="No Data", message="Capture images first!\nClick 'Take Images' to register a student.")
            return
        pkl_path = os.path.join(os.path.dirname(__file__), "TrainingImageLabel", "encodings.pkl")
        with open(pkl_path, "wb") as f:
            pickle.dump({"encodings": encodings, "ids": IDs}, f)
        self.training_status = True
        count = len(set(IDs))
        self.reg_status.configure(text=f"Profile Saved - {count} student(s) trained")
        self.refresh_attendance_stats()
        self.update_status(f"Model trained for {count} student(s)")

    def psw(self):
        self.assure_path_exists("TrainingImageLabel/")
        key = self.db.get_setting("password")
        if key is None:
            new_pas = tsd.askstring("Set Password", "Create a password to protect the model:", show="*")
            if not new_pas:
                mess._show(title="No Password", message="Password not set!")
                return
            confirm = tsd.askstring("Confirm Password", "Re-enter password:", show="*")
            if new_pas != confirm:
                mess._show(title="Error", message="Passwords do not match!")
                return
            self.db.set_setting("password", new_pas)
            mess._show(title="Success", message="Password registered!")
            return
        pw = tsd.askstring("Password Required", "Enter password to save profile:", show="*")
        if pw == key:
            self.TrainImages()
        elif pw is None:
            return
        else:
            mess._show(title="Wrong Password", message="Incorrect password!")

    def TrackImages(self):
        for item in self.att_tree.get_children():
            self.att_tree.delete(item)
        pkl_path = os.path.join(os.path.dirname(__file__), "TrainingImageLabel", "encodings.pkl")
        if not os.path.isfile(pkl_path):
            mess._show(title="No Trained Model",
                       message="Click 'Save Profile' first to train the face model,\nthen try 'Take Attendance'.")
            return
        with open(pkl_path, "rb") as f:
            data = pickle.load(f)
        known_encodings = np.array(data["encodings"])
        known_ids = data["ids"]
        app = self.get_face_app()
        if app is None:
            return
        cam = cv2.VideoCapture(0)
        if not cam.isOpened():
            mess._show(title="Camera Error", message="Could not open webcam!")
            return
        students = self.db.get_all_students()
        if not students:
            mess._show(title="No Students", message="No students registered!")
            cam.release()
            return
        serial_to_student = {}
        for s in students:
            serial_to_student[s["serial"]] = s
        seen_ids = set()
        self.update_status("Attendance in progress... Press Q in camera window to stop")
        mess._show(title="Attendance", message="Camera opening.\nPress 'Q' in the camera window to stop.")
        while True:
            ret, im = cam.read()
            if not ret:
                break
            faces = app.get(im)
            for face in faces:
                bbox = face.bbox.astype(int)
                x1, y1, x2, y2 = bbox[0], bbox[1], bbox[2], bbox[3]
                cv2.rectangle(im, (x1, y1), (x2, y2), (225, 0, 0), 2)
                emb = face.normed_embedding
                distances = np.linalg.norm(known_encodings - emb, axis=1)
                best_idx = np.argmin(distances)
                best_dist = distances[best_idx]
                label = "Unknown"
                if best_dist < 0.55:
                    serial = known_ids[best_idx]
                    student = serial_to_student.get(serial)
                    if student:
                        sid = student["student_id"]
                        sname = student["name"]
                        if sid not in seen_ids:
                            ts = time.time()
                            date = datetime.datetime.fromtimestamp(ts).strftime("%d-%m-%Y")
                            timeStamp = datetime.datetime.fromtimestamp(ts).strftime("%H:%M:%S")
                            self.db.add_attendance(sid, sname, date, timeStamp)
                            seen_ids.add(sid)
                            self.att_tree.insert("", 0, values=(sid, sname, date, timeStamp))
                            self.save_attendance_csv(sid, sname, date, timeStamp)
                        label = sname
                cv2.putText(im, label, (x1, y2 + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            cv2.imshow("Taking Attendance - Press Q to quit", im)
            if cv2.waitKey(1) == ord("q"):
                break
        cam.release()
        cv2.destroyAllWindows()
        marked = len(seen_ids)
        self.update_status(f"Attendance done. {marked} student(s) marked present.")
        self.refresh_attendance_stats()
        if marked == 0:
            mess._show(title="No Match", message="No faces recognized.\nTry better lighting or retrain the model.")

    def contact(self):
        mess._show(title="Contact", message="Developer: Astik Pawar\nEmail: astikpawar007@gmail.com")

    def change_pass(self):
        key = self.db.get_setting("password")
        if key is None:
            mess._show(title="No Password", message="No password set yet. Save Profile to set one.")
            return

        win = ctk.CTkToplevel(self.root)
        win.title("Change Password")
        win.geometry("360x190")
        win.resizable(False, False)
        win.transient(self.root)

        ctk.CTkLabel(win, text="Old Password", font=("Segoe UI", 12)).grid(row=0, column=0, padx=12, pady=(14, 2), sticky="w")
        old_e = ctk.CTkEntry(win, width=180, show="*")
        old_e.grid(row=0, column=1, padx=12, pady=(14, 2))

        ctk.CTkLabel(win, text="New Password", font=("Segoe UI", 12)).grid(row=1, column=0, padx=12, pady=2, sticky="w")
        new_e = ctk.CTkEntry(win, width=180, show="*")
        new_e.grid(row=1, column=1, padx=12, pady=2)

        ctk.CTkLabel(win, text="Confirm New", font=("Segoe UI", 12)).grid(row=2, column=0, padx=12, pady=2, sticky="w")
        cn_e = ctk.CTkEntry(win, width=180, show="*")
        cn_e.grid(row=2, column=1, padx=12, pady=2)

        def save():
            k = self.db.get_setting("password")
            if old_e.get() != k:
                mess._show(title="Error", message="Wrong old password!")
                return
            if new_e.get() != cn_e.get():
                mess._show(title="Error", message="New passwords do not match!")
                return
            if not new_e.get():
                mess._show(title="Error", message="Password cannot be empty!")
                return
            self.db.set_setting("password", new_e.get())
            mess._show(title="Success", message="Password changed successfully!")
            win.destroy()

        btn_frame = ctk.CTkFrame(win, fg_color="transparent")
        btn_frame.grid(row=3, column=0, columnspan=2, pady=14)
        ctk.CTkButton(btn_frame, text="Save", command=save,
                      fg_color="#27AE60", hover_color="#1E8449",
                      font=("Segoe UI", 12, "bold")).pack(side="left", padx=6)
        ctk.CTkButton(btn_frame, text="Cancel", command=win.destroy,
                      fg_color="#E74C3C", hover_color="#C0392B",
                      font=("Segoe UI", 12, "bold")).pack(side="left", padx=6)

    def load_initial_stats(self):
        total = self.db.get_student_count()
        self.stat_total.configure(text=f"Total: {total}")
        today = self.db.get_today_count()
        self.stat_today.configure(text=f"Today: {today}")
        pkl_path = os.path.join(os.path.dirname(__file__), "TrainingImageLabel", "encodings.pkl")
        if os.path.isfile(pkl_path):
            self.training_status = True
            self.reg_status.configure(text="Model loaded. Ready for attendance.")

    def load_today_attendance(self):
        today = datetime.datetime.now().strftime("%d-%m-%Y")
        records = self.db.get_attendance_by_date(today)
        for r in records:
            self.att_tree.insert("", 0, values=(r["student_id"], r["name"], r["date"], r["time"]))

    def save_attendance_csv(self, student_id, name, date, time, status="Present"):
        self.assure_path_exists("Attendance/")
        fname = f"Attendance/Attendance_{date}.csv"
        file_exists = os.path.isfile(fname)
        with open(fname, "a+", newline="") as f:
            w = csv.writer(f)
            if not file_exists:
                w.writerow(["ID", "Name", "Date", "Time", "Status"])
            w.writerow([student_id, name, date, time, status])

    def export_report(self):
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        fn = f"attendance_report_{ts}.csv"
        records = self.db.get_all_attendance()
        if not records:
            self.update_status("No attendance records to export")
            return
        with open(fn, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["ID", "Name", "Date", "Time", "Status"])
            for r in records:
                w.writerow([r["student_id"], r["name"], r["date"], r["time"], r["status"]])
        mess._show(title="Exported", message=f"Report saved as:\n{fn}")
        self.update_status(f"Report saved: {fn}")

    def refresh_attendance(self):
        self.att_tree.delete(*self.att_tree.get_children())
        self.load_today_attendance()
        self.update_status("Attendance refreshed")

    def clear_attendance(self):
        result = mess.askyesno("Confirm", "Delete all attendance records?")
        if result:
            self.att_tree.delete(*self.att_tree.get_children())
            self.db.clear_attendance()
            self.update_status("All attendance records deleted")
            self.stat_today.configure(text="Today: 0")

    def refresh_attendance_stats(self):
        total = self.db.get_student_count()
        self.stat_total.configure(text=f"Total: {total}")
        today = self.db.get_today_count()
        self.stat_today.configure(text=f"Today: {today}")

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = AttendanceApp()
    app.run()
