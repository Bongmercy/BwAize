"""
EduConnect — Classroom Management App
Teachers: upload notes, post announcements, view attendance
Learners: mark attendance with student ID, view notes and announcements

Run with:
    streamlit run educonnect.py
"""

import json
import os
import hashlib
from datetime import datetime, date
import streamlit as st

# ── Page config ────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="BwAize EduConnect",
    page_icon="🎓",
    layout="centered",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    .stApp { background-color: #0d1117; color: #e6edf3; font-family: 'Inter', sans-serif; }
    #MainMenu, footer, header { visibility: hidden; }

    /* Cards */
    .card {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 18px 20px;
        margin-bottom: 12px;
    }
    .card-title { font-size: 15px; font-weight: 600; margin-bottom: 4px; color: #e6edf3; }
    .card-meta  { font-size: 12px; color: #8b949e; margin-bottom: 8px; }
    .card-body  { font-size: 14px; color: #c9d1d9; line-height: 1.6; }

    /* Badges */
    .badge {
        display: inline-block;
        font-size: 11px;
        font-weight: 600;
        padding: 3px 9px;
        border-radius: 20px;
        margin-right: 6px;
    }
    .badge-announce { background: rgba(88,166,255,0.15); color: #58a6ff; }
    .badge-note     { background: rgba(63,185,80,0.15);  color: #3fb950; }
    .badge-present  { background: rgba(63,185,80,0.15);  color: #3fb950; }
    .badge-absent   { background: rgba(248,81,73,0.15);  color: #f85149; }

    /* Role cards on login */
    .role-card {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 24px;
        text-align: center;
        cursor: pointer;
        transition: border-color 0.2s;
    }
    .role-card:hover { border-color: #58a6ff; }
    .role-icon { font-size: 40px; margin-bottom: 10px; }
    .role-title { font-size: 16px; font-weight: 600; }
    .role-desc  { font-size: 13px; color: #8b949e; margin-top: 4px; }

    /* Stat boxes */
    .stat-box {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 10px;
        padding: 16px;
        text-align: center;
    }
    .stat-num   { font-size: 32px; font-weight: 700; }
    .stat-label { font-size: 12px; color: #8b949e; margin-top: 2px; }

    /* Section headers */
    .section-header {
        font-size: 13px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: #8b949e;
        margin: 1.5rem 0 0.75rem;
    }

    /* Success / error banners */
    .banner-success {
        background: rgba(63,185,80,0.12);
        border: 1px solid #3fb950;
        border-radius: 8px;
        padding: 12px 16px;
        color: #3fb950;
        font-size: 14px;
        margin-bottom: 12px;
    }
    .banner-error {
        background: rgba(248,81,73,0.12);
        border: 1px solid #f85149;
        border-radius: 8px;
        padding: 12px 16px;
        color: #f85149;
        font-size: 14px;
        margin-bottom: 12px;
    }

    div[data-testid="stTextInput"] input,
    div[data-testid="stNumberInput"] input,
    div[data-testid="stTextArea"] textarea {
        background-color: #161b22 !important;
        color: #e6edf3 !important;
        border: 1px solid #30363d !important;
        border-radius: 8px !important;
        font-family: 'Inter', sans-serif !important;
    }
    div[data-testid="stSelectbox"] > div {
        background-color: #161b22 !important;
        border: 1px solid #30363d !important;
        border-radius: 8px !important;
    }

    .stButton button {
        background-color: #238636 !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 500 !important;
        font-family: 'Inter', sans-serif !important;
        padding: 8px 18px !important;
    }
    .stButton button:hover { background-color: #2ea043 !important; }

    .stTabs [data-baseweb="tab-list"] {
        background: #161b22;
        border-radius: 10px;
        padding: 4px;
        gap: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        background: transparent !important;
        border-radius: 7px !important;
        color: #8b949e !important;
        font-family: 'Inter', sans-serif !important;
    }
    .stTabs [aria-selected="true"] {
        background: #0d1117 !important;
        color: #e6edf3 !important;
    }
</style>
""", unsafe_allow_html=True)


# ── Data storage (JSON files) ──────────────────────────────────────────────────

DATA_DIR = "educonnect_data"
os.makedirs(DATA_DIR, exist_ok=True)

USERS_FILE       = os.path.join(DATA_DIR, "users.json")
POSTS_FILE       = os.path.join(DATA_DIR, "posts.json")
ATTENDANCE_FILE  = os.path.join(DATA_DIR, "attendance.json")
CLASSES_FILE     = os.path.join(DATA_DIR, "classes.json")


def load_json(path, default):
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return default

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

def hash_password(pw):
    return hashlib.sha256(pw.encode()).hexdigest()


# ── Seed default data ──────────────────────────────────────────────────────────

def seed_defaults():
    users = load_json(USERS_FILE, {})
    if not users:
        users = {
            "teacher1": {
                "name": "Ms Dlamini",
                "role": "teacher",
                "password": hash_password("teach123"),
                "class": "Grade 10A"
            },
            "STU001": {
                "name": "Sipho Nkosi",
                "role": "learner",
                "password": hash_password("learn123"),
                "class": "Grade 10A",
                "student_id": "STU001"
            },
            "STU002": {
                "name": "Ayanda Mokoena",
                "role": "learner",
                "password": hash_password("learn123"),
                "class": "Grade 10A",
                "student_id": "STU002"
            },
            "STU003": {
                "name": "Lerato Khumalo",
                "role": "learner",
                "password": hash_password("learn123"),
                "class": "Grade 10A",
                "student_id": "STU003"
            },
        }
        save_json(USERS_FILE, users)

    if not os.path.exists(POSTS_FILE):
        save_json(POSTS_FILE, [])
    if not os.path.exists(ATTENDANCE_FILE):
        save_json(ATTENDANCE_FILE, {})
    if not os.path.exists(CLASSES_FILE):
        save_json(CLASSES_FILE, ["Grade 10A"])

seed_defaults()


# ── Auth helpers ───────────────────────────────────────────────────────────────

def login(username, password):
    users = load_json(USERS_FILE, {})
    u = users.get(username)
    if u and u["password"] == hash_password(password):
        return u
    return None

def get_learners_in_class(class_name):
    users = load_json(USERS_FILE, {})
    return {k: v for k, v in users.items() if v["role"] == "learner" and v.get("class") == class_name}


# ── Session state ──────────────────────────────────────────────────────────────

if "user" not in st.session_state:
    st.session_state.user = None
if "page" not in st.session_state:
    st.session_state.page = "login"


# ══════════════════════════════════════════════════════════════════════════════
# LOGIN PAGE
# ══════════════════════════════════════════════════════════════════════════════

def show_login():
    st.markdown("# 🎓BwAize EduConnect")
    st.markdown("**Classroom management for teachers and learners**")
    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        <div class="role-card">
            <div class="role-icon">👩‍🏫</div>
            <div class="role-title">Teacher</div>
            <div class="role-desc">Post notes & announcements, manage your class</div>
        </div>""", unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class="role-card">
            <div class="role-icon">🧑‍🎓</div>
            <div class="role-title">Learner</div>
            <div class="role-desc">View notes, mark attendance with your student ID</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### Sign in")

    username = st.text_input("Username / Student ID", placeholder="e.g. teacher1 or STU001")
    password = st.text_input("Password", type="password", placeholder="Enter your password")

    if st.button("Sign in →", use_container_width=True):
        if not username or not password:
            st.error("Please enter both username and password.")
        else:
            user = login(username.strip(), password.strip())
            if user:
                st.session_state.user = user
                st.session_state.user["username"] = username.strip()
                st.session_state.page = "dashboard"
                st.rerun()
            else:
                st.error("Incorrect username or password. Try again.")

    st.markdown("---")
    st.caption("**Demo accounts** — Teacher: `teacher1` / `teach123` · Learner: `STU001` / `learn123`")


# ══════════════════════════════════════════════════════════════════════════════
# TEACHER DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════

def show_teacher_dashboard():
    user = st.session_state.user
    today = date.today().isoformat()

    # Header
    col_h1, col_h2 = st.columns([3, 1])
    with col_h1:
        st.markdown(f"# 👩‍🏫 {user['name']}")
        st.markdown(f"**{user['class']}** · Teacher")
    with col_h2:
        if st.button("Sign out"):
            st.session_state.user = None
            st.session_state.page = "login"
            st.rerun()

    st.markdown("---")

    # Stats
    posts       = load_json(POSTS_FILE, [])
    attendance  = load_json(ATTENDANCE_FILE, {})
    learners    = get_learners_in_class(user["class"])
    today_att   = attendance.get(today, {})
    present_today = sum(1 for v in today_att.values() if v == "present")

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"""<div class="stat-box">
            <div class="stat-num" style="color:#58a6ff;">{len(learners)}</div>
            <div class="stat-label">Learners enrolled</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class="stat-box">
            <div class="stat-num" style="color:#3fb950;">{present_today}</div>
            <div class="stat-label">Present today</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        my_posts = [p for p in posts if p.get("class") == user["class"]]
        st.markdown(f"""<div class="stat-box">
            <div class="stat-num" style="color:#d2a8ff;">{len(my_posts)}</div>
            <div class="stat-label">Posts published</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("")

    # Tabs
    tab_post, tab_attendance, tab_learners, tab_teachers = st.tabs([
        "📢  Post notes & announcements",
        "📋  Attendance register",
        "👥  Manage learners"
    ])

    # ── Tab 1: Post ──────────────────────────────────────────────────────────
    with tab_post:
        st.markdown('<div class="section-header">New post</div>', unsafe_allow_html=True)

        post_type = st.selectbox("Post type", ["Announcement", "Notes"])
        post_title = st.text_input("Title", placeholder="e.g. Chapter 4 Summary / Test reminder")
        post_body  = st.text_area("Content", height=150, placeholder="Write your notes or announcement here…")

        uploaded_file = st.file_uploader("Attach a file (optional)", type=["pdf", "txt", "docx", "png", "jpg"])

        if st.button("Publish →", use_container_width=True):
            if not post_title or not post_body:
                st.error("Please add a title and content.")
            else:
                posts = load_json(POSTS_FILE, [])
                new_post = {
                    "id":        len(posts) + 1,
                    "type":      post_type,
                    "title":     post_title,
                    "body":      post_body,
                    "author":    user["name"],
                    "class":     user["class"],
                    "timestamp": datetime.now().strftime("%d %b %Y, %H:%M"),
                    "filename":  uploaded_file.name if uploaded_file else None,
                }
                posts.insert(0, new_post)
                save_json(POSTS_FILE, posts)
                st.markdown('<div class="banner-success">✅ Post published successfully!</div>', unsafe_allow_html=True)
                st.rerun()

        # Existing posts
        st.markdown('<div class="section-header">Published posts</div>', unsafe_allow_html=True)
        my_posts = [p for p in load_json(POSTS_FILE, []) if p.get("class") == user["class"]]
        if not my_posts:
            st.caption("No posts yet. Publish your first one above.")
        for p in my_posts:
            badge = "badge-announce" if p["type"] == "Announcement" else "badge-note"
            st.markdown(f"""
            <div class="card">
                <div class="card-meta">
                    <span class="badge {badge}">{p['type']}</span>
                    {p['timestamp']}
                    {f"· 📎 {p['filename']}" if p.get('filename') else ""}
                </div>
                <div class="card-title">{p['title']}</div>
                <div class="card-body">{p['body']}</div>
            </div>""", unsafe_allow_html=True)

    # ── Tab 2: Attendance ────────────────────────────────────────────────────
    with tab_attendance:
        st.markdown('<div class="section-header">Attendance register</div>', unsafe_allow_html=True)

        selected_date = st.date_input("Select date", value=date.today())
        date_key = selected_date.isoformat()

        attendance  = load_json(ATTENDANCE_FILE, {})
        day_record  = attendance.get(date_key, {})
        learners    = get_learners_in_class(user["class"])

        if not learners:
            st.caption("No learners enrolled in this class yet.")
        else:
            present = sum(1 for sid in learners if day_record.get(sid) == "present")
            absent  = len(learners) - present

            ca, cb = st.columns(2)
            with ca:
                st.markdown(f"""<div class="stat-box">
                    <div class="stat-num" style="color:#3fb950;">{present}</div>
                    <div class="stat-label">Present</div>
                </div>""", unsafe_allow_html=True)
            with cb:
                st.markdown(f"""<div class="stat-box">
                    <div class="stat-num" style="color:#f85149;">{absent}</div>
                    <div class="stat-label">Absent</div>
                </div>""", unsafe_allow_html=True)

            st.markdown("")
            for sid, ldata in learners.items():
                status = day_record.get(sid, "absent")
                badge  = "badge-present" if status == "present" else "badge-absent"
                label  = "✅ Present" if status == "present" else "❌ Absent"
                st.markdown(f"""
                <div class="card" style="display:flex; align-items:center; justify-content:space-between;">
                    <div>
                        <div class="card-title">{ldata['name']}</div>
                        <div class="card-meta">ID: {sid}</div>
                    </div>
                    <span class="badge {badge}">{label}</span>
                </div>""", unsafe_allow_html=True)

            # Manual override
            st.markdown('<div class="section-header">Manual override</div>', unsafe_allow_html=True)
            override_id     = st.selectbox("Select learner", options=list(learners.keys()),
                                           format_func=lambda x: f"{learners[x]['name']} ({x})")
            override_status = st.selectbox("Set status", ["present", "absent"])
            if st.button("Update attendance"):
                attendance = load_json(ATTENDANCE_FILE, {})
                if date_key not in attendance:
                    attendance[date_key] = {}
                attendance[date_key][override_id] = override_status
                save_json(ATTENDANCE_FILE, attendance)
                st.success(f"Updated {learners[override_id]['name']} to {override_status}.")
                st.rerun()

    # ── Tab 3: Manage learners ───────────────────────────────────────────────
    with tab_learners:
        st.markdown('<div class="section-header">Enrolled learners</div>', unsafe_allow_html=True)

        learners = get_learners_in_class(user["class"])
        for sid, ldata in learners.items():
            st.markdown(f"""
            <div class="card">
                <div class="card-title">{ldata['name']}</div>
                <div class="card-meta">Student ID: {sid} · {ldata['class']}</div>
            </div>""", unsafe_allow_html=True)

        st.markdown('<div class="section-header">Add a new learner</div>', unsafe_allow_html=True)
        new_name = st.text_input("Full name",    placeholder="e.g. Thabo Sithole")
        new_id   = st.text_input("Student ID",   placeholder="e.g. STU004")
        new_pass = st.text_input("Set password", placeholder="Learner's login password", type="password")

        if st.button("Add learner →", use_container_width=True):
            if not new_name or not new_id or not new_pass:
                st.error("Please fill in all fields.")
            else:
                users = load_json(USERS_FILE, {})
                if new_id in users:
                    st.error("A learner with that ID already exists.")
                else:
                    users[new_id] = {
                        "name":       new_name,
                        "role":       "learner",
                        "password":   hash_password(new_pass),
                        "class":      user["class"],
                        "student_id": new_id,
                    }
                    save_json(USERS_FILE, users)
                    st.success(f"✅ {new_name} added with ID {new_id}.")
                    st.rerun()

    # ── Tab 4: Manage teachers ───────────────────────────────────────────────
    with tab_teachers:
        st.markdown('<div class="section-header">Enrolled teachers</div>', unsafe_allow_html=True)

        teachers = get_teachers_in_class(user["class"])
        for tid, tdata in teachers.items():
            st.markdown(f"""
            <div class="card">
                <div class="card-title">{tdata['name']}</div>
                <div class="card-meta">Teacher ID: {tid} · {tdata['class']}</div>
            </div>""", unsafe_allow_html=True)

        st.markdown('<div class="section-header">Add a new teacher</div>', unsafe_allow_html=True)
        new_name = st.text_input("Full name",    placeholder="e.g. Thabo Sithole")
        new_id   = st.text_input("Teacher ID",   placeholder="e.g. TCH001")
        new_pass = st.text_input("Set password", placeholder="Teacher's login password", type="password")

        if st.button("Add teacher →", use_container_width=True):
            if not new_name or not new_id or not new_pass:
                st.error("Please fill in all fields.")
            else:
                users = load_json(USERS_FILE, {})
                if new_id in users:
                    st.error("A teacher with that ID already exists.")
                else:
                    users[new_id] = {
                        "name":       new_name,
                        "role":       "teacher",
                        "password":   hash_password(new_pass),
                        "class":      user["class"],
                        "student_id": new_id,
                    }
                    save_json(USERS_FILE, users)
                    st.success(f"✅ {new_name} added with ID {new_id}.")
                    st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# LEARNER DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════

def show_learner_dashboard():
    user  = st.session_state.user
    today = date.today().isoformat()
    sid   = user.get("student_id") or st.session_state.user.get("username")

    # Header
    col_h1, col_h2 = st.columns([3, 1])
    with col_h1:
        st.markdown(f"# 🧑‍🎓 {user['name']}")
        st.markdown(f"**{user['class']}** · Student ID: `{sid}`")
    with col_h2:
        if st.button("Sign out"):
            st.session_state.user = None
            st.session_state.page = "login"
            st.rerun()

    st.markdown("---")

    # Attendance status today
    attendance = load_json(ATTENDANCE_FILE, {})
    today_status = attendance.get(today, {}).get(sid)

    if today_status == "present":
        st.markdown('<div class="banner-success">✅ You have marked your attendance today.</div>',
                    unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="background:rgba(210,168,255,0.1);border:1px solid #d2a8ff;border-radius:8px;
                    padding:14px 18px;margin-bottom:16px;color:#d2a8ff;font-size:14px;">
            📌 You haven't marked your attendance yet today.
        </div>""", unsafe_allow_html=True)

    # Tabs
    tab_attend, tab_feed = st.tabs(["✅  Mark attendance", "📚  Notes & announcements"])

    # ── Tab 1: Mark attendance ───────────────────────────────────────────────
    with tab_attend:
        st.markdown('<div class="section-header">Mark your attendance</div>', unsafe_allow_html=True)
        st.markdown(f"Today: **{date.today().strftime('%A, %d %B %Y')}**")

        confirm_id = st.text_input("Enter your student ID to confirm", placeholder="e.g. STU001")

        if st.button("Mark present →", use_container_width=True):
            if confirm_id.strip().upper() != sid.upper():
                st.markdown('<div class="banner-error">❌ Student ID does not match your account.</div>',
                            unsafe_allow_html=True)
            else:
                attendance = load_json(ATTENDANCE_FILE, {})
                if today not in attendance:
                    attendance[today] = {}
                if attendance[today].get(sid) == "present":
                    st.info("You already marked your attendance today.")
                else:
                    attendance[today][sid] = "present"
                    save_json(ATTENDANCE_FILE, attendance)
                    st.markdown(
                        f'<div class="banner-success">✅ Attendance marked! Welcome, {user["name"]}.</div>',
                        unsafe_allow_html=True)
                    st.rerun()

        # Attendance history
        st.markdown('<div class="section-header">Your attendance history</div>', unsafe_allow_html=True)
        attendance = load_json(ATTENDANCE_FILE, {})
        history = [(d, r.get(sid, "absent")) for d, r in sorted(attendance.items(), reverse=True)]

        if not history:
            st.caption("No attendance records yet.")
        else:
            present_count = sum(1 for _, s in history if s == "present")
            total = len(history)
            rate  = int((present_count / total) * 100) if total else 0

            st.markdown(f"""<div class="stat-box" style="margin-bottom:12px;">
                <div class="stat-num" style="color:#3fb950;">{rate}%</div>
                <div class="stat-label">Attendance rate ({present_count}/{total} days)</div>
            </div>""", unsafe_allow_html=True)

            for d, status in history[:10]:
                badge = "badge-present" if status == "present" else "badge-absent"
                label = "Present" if status == "present" else "Absent"
                try:
                    formatted = datetime.strptime(d, "%Y-%m-%d").strftime("%A, %d %B %Y")
                except:
                    formatted = d
                st.markdown(f"""
                <div class="card" style="display:flex;align-items:center;justify-content:space-between;padding:12px 16px;">
                    <div class="card-body">{formatted}</div>
                    <span class="badge {badge}">{label}</span>
                </div>""", unsafe_allow_html=True)

    # ── Tab 2: Notes & announcements ─────────────────────────────────────────
    with tab_feed:
        posts    = load_json(POSTS_FILE, [])
        my_posts = [p for p in posts if p.get("class") == user["class"]]

        filter_type = st.selectbox("Filter", ["All", "Announcement", "Notes"])
        if filter_type != "All":
            my_posts = [p for p in my_posts if p["type"] == filter_type]

        if not my_posts:
            st.caption("Nothing posted yet. Check back later.")
        for p in my_posts:
            badge = "badge-announce" if p["type"] == "Announcement" else "badge-note"
            st.markdown(f"""
            <div class="card">
                <div class="card-meta">
                    <span class="badge {badge}">{p['type']}</span>
                    {p['timestamp']} · {p['author']}
                    {f"· 📎 {p['filename']}" if p.get('filename') else ""}
                </div>
                <div class="card-title">{p['title']}</div>
                <div class="card-body">{p['body']}</div>
            </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# ROUTER
# ══════════════════════════════════════════════════════════════════════════════

if st.session_state.user is None:
    show_login()
elif st.session_state.user["role"] == "teacher":
    show_teacher_dashboard()
elif st.session_state.user["role"] == "learner":
    show_learner_dashboard()
