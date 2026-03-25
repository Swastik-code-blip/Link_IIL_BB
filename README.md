# 📡 DB Link Portal — Dainik Bhaskar Network Management

Pan India broadband, SIM card, ILL link management portal.

---

## 🚀 Local Setup (Windows/Linux/Mac)

### Step 1: Install Python (if not installed)
Download from: https://python.org/downloads

### Step 2: Install dependencies
```
pip install flask pandas
```

### Step 3: Run the app
```
python app.py
```

### Step 4: Open browser
```
http://localhost:5000
```

**Default Admin Login:**
- Username: `admin`
- Password: `admin123`

---

## 🌐 Free Hosting — Render.com (Recommended)

### Step 1: GitHub pe upload karo
1. GitHub.com pe free account banao
2. New repository banao: `db-link-portal`
3. Saari files upload karo (sab files ek saath)

### Step 2: Render pe deploy karo
1. https://render.com pe free account banao
2. "New Web Service" click karo
3. GitHub repo connect karo
4. Settings:
   - **Build Command:** `pip install flask pandas`
   - **Start Command:** `python app.py`
   - **Environment:** Python 3
5. "Create Web Service" click karo
6. 2-3 minute mein live URL milega!

### Step 3: Live URL
```
https://db-link-portal.onrender.com
```
(Ya jo bhi naam aap choose karo)

---

## 🌐 Alternative: PythonAnywhere (Easiest)

1. https://pythonanywhere.com pe free account banao
2. "Files" tab mein saari files upload karo
3. "Web" tab mein new web app banao
4. Flask select karo, `app.py` point karo
5. Done!

---

## 👥 Engineer Accounts Kaise Banayein

1. Admin se login karo
2. "Manage Engineers" menu mein jao
3. Engineer ka naam, username, password, aur **State** assign karo
4. Engineer sirf apni state ke links dekh aur edit kar payega

---

## 📋 Features

| Feature | Description |
|---------|-------------|
| 🔐 Role-Based Access | Admin = sab, Engineer = sirf apna state |
| 🔗 1327+ Links | CSV se import, filters ke saath browse |
| 📊 Performance Rating | Excellent / Good / Poor / Bad |
| 💰 Billing Tracking | Billing date, amount, recharge due track karo |
| 🔔 Auto Alerts | Recharge 7 din mein due ho to auto notification |
| 📥 CSV Export | Apne state ke links download karo |
| 📋 Activity Log | Har edit ka record |
| 📢 Admin Notifications | State-wise ya sab engineers ko message bhejo |

---

## 📁 File Structure

```
linkportal/
├── app.py              ← Main application
├── data.csv            ← Your link data (auto-imported)
├── linkportal.db       ← SQLite database (auto-created)
├── requirements.txt    ← Python packages
├── render.yaml         ← Render deployment config
├── Procfile            ← Heroku/Railway config
└── templates/
    ├── base.html       ← Common layout
    ├── login.html      ← Login page
    ├── dashboard.html  ← Main dashboard
    ├── links.html      ← Links list with filters
    ├── link_detail.html← Link detail view
    ├── edit_link.html  ← Edit performance/billing
    └── users.html      ← Engineer management
```

---

## 🔧 CSV Data Update Karna

Agar naya CSV data add karna ho:
1. `linkportal.db` file delete karo
2. Naya CSV `data.csv` naam se rakho
3. `python app.py` run karo — auto import ho jayega

---

## 📞 Support

Dainik Bhaskar IT Team
