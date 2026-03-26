# 📡 DB Link Manager Portal
## Dainik Bhaskar — Pan India IT Network Management

---

## 🚀 Features

- **ILL / Broadband Links** — 421+ records manage karein
- **MPLS / PRI Links** — MPLS aur PRI connections track karein  
- **P2P Links** — Point to Point links manage karein
- **SIM / Data Cards** — 1326+ SIM card records
- **State-wise Access** — Engineer sirf apne state ke links dekhe
- **Performance Tracking** — Excellent / Good / Poor / Bad set karein
- **Renewal Notifications** — 60 din pehle alert milega
- **Reports & Charts** — ISP-wise, state-wise, category-wise analytics
- **New Link Add** — Naya link directly portal se add karein
- **User Management** — Admin users banaye aur manage kare

---

## 🔑 Default Login Credentials

| Role | Username | Password |
|------|----------|----------|
| 👑 Admin | `admin` | `admin123` |
| 🔧 Engineer GJ | `eng_gj` | `eng123` |
| 🔧 Engineer MH | `eng_mh` | `eng123` |
| 🔧 Engineer RJ | `eng_rj` | `eng123` |
| 🔧 Engineer HR | `eng_hr` | `eng123` |
| 🔧 Engineer NCR | `eng_ncr` | `eng123` |
| 🔧 Engineer MPCG | `eng_mpcg` | `eng123` |
| 🔧 Engineer BR&JH | `eng_br_jh` | `eng123` |
| 🔧 Engineer CPH | `eng_cph` | `eng123` |

---

## 🌐 Free Hosting — Render.com (Recommended)

### Step 1: GitHub pe upload karein
1. GitHub account banao: https://github.com
2. New repository banao: `db-link-portal`
3. Ye saari files upload karo (portal.db bhi)

### Step 2: Render.com pe deploy karein
1. https://render.com pe jaao — free account banao
2. "New +" → "Web Service" click karo
3. Apna GitHub repo select karo
4. Settings:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
   - **Plan:** Free
5. "Create Web Service" click karo
6. 2-3 minute mein live ho jayega!

### Step 3: URL milega
`https://db-link-portal.onrender.com` jaisa kuch URL milega — ye share karo engineers ke saath!

---

## 💻 Local Machine pe chalane ke liye

```bash
# Python install hona chahiye (3.8+)
pip install -r requirements.txt

# Database initialize karo (pehli baar)
python init_db.py

# Portal start karo
python app.py

# Browser mein jaao
# http://localhost:5000
```

---

## 📁 File Structure

```
db_portal/
├── app.py              # Main Flask application
├── init_db.py          # Database setup + data import
├── portal.db           # SQLite database (auto-created)
├── requirements.txt    # Python dependencies
├── Procfile            # Deployment config
├── render.yaml         # Render.com config
└── templates/
    ├── base.html       # Common layout
    ├── login.html      # Login page
    ├── dashboard.html  # Main dashboard
    ├── links.html      # Links list
    ├── link_detail.html# Link detail + edit
    ├── add_link.html   # New link form
    ├── sim_cards.html  # SIM cards
    ├── notifications.html
    ├── reports.html    # Analytics
    └── users.html      # User management
```

---

## 🔧 Engineer Permissions

| Feature | Admin | Engineer |
|---------|-------|---------|
| Sab states ke links dekhna | ✅ | ❌ (sirf apna state) |
| Link edit karna | ✅ | ❌ |
| Performance set karna | ✅ | ✅ |
| Naya link add karna | ✅ | ✅ |
| User manage karna | ✅ | ❌ |
| Renewal check karna | ✅ | ❌ |

---

*Built for Dainik Bhaskar IT Team — Pan India Network Management*
