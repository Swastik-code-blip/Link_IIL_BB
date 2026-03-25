"""
DB Link Portal - Dainik Bhaskar Network Management
Run: python app.py
Default login: admin / admin123
"""

from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash, Response
import sqlite3, hashlib, csv, os, io
from datetime import datetime, date
from functools import wraps

app = Flask(__name__)
app.secret_key = 'dblink_dainik_bhaskar_2025_secure'
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'linkportal.db')

CITY_STATE = {
    'AHMEDABAD':'Gujarat','BARODA':'Gujarat','BHAVNAGAR':'Gujarat','BHUJ':'Gujarat',
    'JUNAGARH':'Gujarat','MEHSANA':'Gujarat','RAJKOT':'Gujarat','SURAT':'Gujarat','VAPI':'Gujarat',
    'AJMER':'Rajasthan','ALWAR':'Rajasthan','BANSWARA':'Rajasthan','BARMER':'Rajasthan',
    'BHARATPUR':'Rajasthan','BHILWARA':'Rajasthan','BIKANER':'Rajasthan','JAIPUR':'Rajasthan',
    'JODHPUR':'Rajasthan','KOTA':'Rajasthan','NAGOUR':'Rajasthan','PALI':'Rajasthan',
    'SIKAR':'Rajasthan','SRIGANGANAGAR':'Rajasthan','UDAIPUR':'Rajasthan',
    'BHOPAL':'Madhya Pradesh','GUNA':'Madhya Pradesh','GWALIOR':'Madhya Pradesh',
    'HOSHANGABAD':'Madhya Pradesh','INDORE':'Madhya Pradesh','KHANDWA':'Madhya Pradesh',
    'RATLAM':'Madhya Pradesh','SAGAR':'Madhya Pradesh','UJJAIN':'Madhya Pradesh',
    'AMRITSAR':'Punjab','BATHINDA':'Punjab','JALANDHAR':'Punjab','LUDHIANA':'Punjab',
    'CHANDIGARH':'Chandigarh','FARIDABAD':'Haryana','GURGAON':'Haryana','HISAR':'Haryana',
    'PANIPAT':'Haryana','REWARI':'Haryana','ROHTAK':'Haryana',
    'NOIDA':'Uttar Pradesh','NOIDA FC':'Uttar Pradesh','LUCKNOW':'Uttar Pradesh',
    'PATNA':'Bihar','BHAGALPUR':'Bihar','MUZAFFERPUR':'Bihar',
    'RANCHI':'Jharkhand','JAMSHEDPUR':'Jharkhand','DHANBAD':'Jharkhand',
    'RAIPUR':'Chhattisgarh','BHILAI':'Chhattisgarh','BILASPUR':'Chhattisgarh','RAIGARH':'Chhattisgarh',
    'AURANGABAD':'Maharashtra','JALGAON':'Maharashtra','NASIK':'Maharashtra',
    'SOLAPUR':'Maharashtra','BKC MUMBAI':'Maharashtra','MAHIM MUMBAI':'Maharashtra','AKOLA':'Maharashtra',
    'BANGLORE':'Karnataka','HARIDWAR':'Uttarakhand',
}

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def log_activity(user, action, link_id=None, details=''):
    try:
        conn = get_db()
        conn.execute("INSERT INTO activity_log (user,action,link_id,details) VALUES (?,?,?,?)",
                     (user, action, link_id, details))
        conn.commit(); conn.close()
    except: pass

def init_db():
    conn = get_db(); c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL, role TEXT DEFAULT 'engineer',
        state TEXT, name TEXT, email TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS links (
        id INTEGER PRIMARY KEY AUTOINCREMENT, wan_id TEXT, center TEXT, location TEXT,
        state TEXT, division TEXT, office_type TEXT, employee_id TEXT, employee_name TEXT,
        sim_number TEXT, service_provider TEXT, card_type TEXT, emp_status TEXT,
        designation TEXT, department TEXT, arc REAL, link_type TEXT DEFAULT 'SIM/Data',
        performance TEXT DEFAULT 'Good', billing_date TEXT, billing_amount REAL,
        recharge_date TEXT, recharge_due_date TEXT, notes TEXT,
        last_updated TEXT DEFAULT CURRENT_TIMESTAMP, updated_by TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT, link_id INTEGER, state TEXT,
        message TEXT, type TEXT DEFAULT 'info', is_read INTEGER DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS activity_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user TEXT, action TEXT,
        link_id INTEGER, details TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP)''')
    try:
        c.execute("INSERT INTO users (username,password,role,name) VALUES (?,?,?,?)",
                  ('admin', hash_pw('admin123'), 'admin', 'Administrator'))
    except: pass
    conn.commit(); conn.close()

def import_csv():
    conn = get_db()
    if conn.execute("SELECT COUNT(*) FROM links").fetchone()[0] > 0:
        conn.close(); return
    conn.close()
    paths = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data.csv'),
        '/mnt/user-data/uploads/Pan_India_ILL_and_BB_Link_25-26_Data_Card_SIM_.csv'
    ]
    csv_path = next((p for p in paths if os.path.exists(p)), None)
    if not csv_path:
        print("No CSV found — start with empty DB"); return
    try:
        import pandas as pd
        df = pd.read_csv(csv_path, encoding='latin1')
        df.columns = [c.replace('\xa0',' ').strip() for c in df.columns]
        df = df.dropna(subset=['Center'])
        conn = get_db()
        for _, row in df.iterrows():
            center = str(row.get('Center','')).strip().upper()
            state = CITY_STATE.get(center, 'Other')
            card_type = str(row.get('Card Type','')).strip()
            arc_val = None
            try: arc_val = float(str(row.get('ARC','')).replace(',','').strip())
            except: pass
            conn.execute('''INSERT INTO links
                (wan_id,center,location,state,division,office_type,employee_id,employee_name,
                 sim_number,service_provider,card_type,emp_status,designation,department,arc,link_type)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', (
                str(row.get('Wan Id','')).strip(), center, str(row.get('Location','')).strip(),
                state, str(row.get('Division','')).strip(), str(row.get('Office Type','')).strip(),
                str(row.get('EmployeeId','')).strip(), str(row.get('EmployeeName','')).strip(),
                str(row.get('Sim Number','')).strip(), str(row.get('Service Provider','')).strip(),
                card_type, str(row.get('EmpStatus','')).strip(),
                str(row.get('Designation','')).strip(), str(row.get('Department','')).strip(),
                arc_val, card_type))
        conn.commit(); conn.close()
        print(f"Imported {len(df)} records from CSV")
    except Exception as e:
        print(f"CSV import error: {e}")

# ── Decorators ──────────────────────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def d(*a,**k):
        if 'user_id' not in session: return redirect(url_for('login'))
        return f(*a,**k)
    return d

def admin_required(f):
    @wraps(f)
    def d(*a,**k):
        if 'user_id' not in session: return redirect(url_for('login'))
        if session.get('role') != 'admin': flash('Admin access required','danger'); return redirect(url_for('dashboard'))
        return f(*a,**k)
    return d

# ── Auth ─────────────────────────────────────────────────────────────────────
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        u,p = request.form['username'].strip(), hash_pw(request.form['password'])
        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE username=? AND password=?",(u,p)).fetchone()
        conn.close()
        if user:
            session.update({'user_id':user['id'],'username':user['username'],'role':user['role'],
                            'state':user['state'],'name':user['name'] or user['username']})
            log_activity(u,'LOGIN')
            return redirect(url_for('dashboard'))
        flash('Invalid credentials','danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    log_activity(session.get('username',''),'LOGOUT'); session.clear()
    return redirect(url_for('login'))

# ── Dashboard ─────────────────────────────────────────────────────────────────
@app.route('/')
@login_required
def dashboard():
    conn = get_db()
    role,state = session.get('role'),session.get('state')
    if role == 'admin':
        total   = conn.execute("SELECT COUNT(*) FROM links").fetchone()[0]
        by_type = conn.execute("SELECT card_type,COUNT(*) cnt FROM links GROUP BY card_type").fetchall()
        by_state= conn.execute("SELECT state,COUNT(*) cnt FROM links GROUP BY state ORDER BY cnt DESC").fetchall()
        by_prov = conn.execute("SELECT service_provider,COUNT(*) cnt FROM links GROUP BY service_provider ORDER BY cnt DESC").fetchall()
        by_perf = conn.execute("SELECT performance,COUNT(*) cnt FROM links GROUP BY performance ORDER BY cnt DESC").fetchall()
        notifs  = conn.execute("SELECT * FROM notifications WHERE is_read=0 ORDER BY created_at DESC LIMIT 25").fetchall()
        recent  = conn.execute("SELECT * FROM activity_log ORDER BY created_at DESC LIMIT 12").fetchall()
    else:
        total   = conn.execute("SELECT COUNT(*) FROM links WHERE state=?",(state,)).fetchone()[0]
        by_type = conn.execute("SELECT card_type,COUNT(*) cnt FROM links WHERE state=? GROUP BY card_type",(state,)).fetchall()
        by_state= []
        by_prov = conn.execute("SELECT service_provider,COUNT(*) cnt FROM links WHERE state=? GROUP BY service_provider ORDER BY cnt DESC",(state,)).fetchall()
        by_perf = conn.execute("SELECT performance,COUNT(*) cnt FROM links WHERE state=? GROUP BY performance ORDER BY cnt DESC",(state,)).fetchall()
        notifs  = conn.execute("SELECT * FROM notifications WHERE (state=? OR state='') AND is_read=0 ORDER BY created_at DESC LIMIT 25",(state,)).fetchall()
        recent  = conn.execute("SELECT * FROM activity_log WHERE user=? ORDER BY created_at DESC LIMIT 12",(session['username'],)).fetchall()
    conn.close()
    return render_template('dashboard.html', total=total, by_type=by_type, by_state=by_state,
                           by_provider=by_prov, by_perf=by_perf, notifs=notifs,
                           recent_activity=recent, notif_count=len(notifs))

# ── Links list ────────────────────────────────────────────────────────────────
@app.route('/links')
@login_required
def links():
    conn = get_db()
    role,state = session.get('role'),session.get('state')
    page,per_page = max(1,int(request.args.get('page',1))), 50
    filters,params = [],[]
    if role != 'admin': filters.append("state=?"); params.append(state)
    for k,col in [('state','state'),('center','center'),('card_type','card_type'),
                  ('provider','service_provider'),('performance','performance')]:
        v = request.args.get(k,'')
        if v and (k!='state' or role=='admin'): filters.append(f"{col}=?"); params.append(v)
    s = request.args.get('search','')
    if s:
        filters.append("(wan_id LIKE ? OR employee_name LIKE ? OR sim_number LIKE ? OR center LIKE ?)")
        params += [f'%{s}%']*4
    where = ('WHERE '+' AND '.join(filters)) if filters else ''
    total_count = conn.execute(f"SELECT COUNT(*) FROM links {where}",params).fetchone()[0]
    rows = conn.execute(f"SELECT * FROM links {where} ORDER BY state,center LIMIT ? OFFSET ?",
                        params+[per_page,(page-1)*per_page]).fetchall()
    all_states  = conn.execute("SELECT DISTINCT state FROM links ORDER BY state").fetchall()
    all_centers = conn.execute("SELECT DISTINCT center FROM links ORDER BY center").fetchall()
    conn.close()
    f = {k:request.args.get(k,'') for k in ['state','center','card_type','provider','performance','search']}
    return render_template('links.html', links=rows, page=page,
                           total_pages=(total_count+per_page-1)//per_page,
                           total_count=total_count, all_states=all_states,
                           all_centers=all_centers, filters=f)

# ── Link detail & edit ────────────────────────────────────────────────────────
@app.route('/link/<int:lid>')
@login_required
def link_detail(lid):
    conn = get_db()
    link = conn.execute("SELECT * FROM links WHERE id=?",(lid,)).fetchone()
    if not link: conn.close(); flash('Not found','danger'); return redirect(url_for('links'))
    if session['role']!='admin' and link['state']!=session['state']:
        conn.close(); flash('Access denied','danger'); return redirect(url_for('links'))
    history = conn.execute("SELECT * FROM activity_log WHERE link_id=? ORDER BY created_at DESC LIMIT 20",(lid,)).fetchall()
    conn.close()
    return render_template('link_detail.html', link=link, history=history)

@app.route('/link/<int:lid>/edit', methods=['GET','POST'])
@login_required
def edit_link(lid):
    conn = get_db()
    link = conn.execute("SELECT * FROM links WHERE id=?",(lid,)).fetchone()
    if not link: conn.close(); flash('Not found','danger'); return redirect(url_for('links'))
    if session['role']!='admin' and link['state']!=session['state']:
        conn.close(); flash('Access denied','danger'); return redirect(url_for('links'))
    if request.method == 'POST':
        f = request.form
        ba = None
        try: ba = float(f.get('billing_amount','')) if f.get('billing_amount') else None
        except: pass
        conn.execute('''UPDATE links SET performance=?,billing_date=?,billing_amount=?,
            recharge_date=?,recharge_due_date=?,notes=?,service_provider=?,
            emp_status=?,last_updated=?,updated_by=? WHERE id=?''',
            (f.get('performance'),f.get('billing_date'),ba,f.get('recharge_date'),
             f.get('recharge_due_date'),f.get('notes'),f.get('service_provider'),
             f.get('emp_status'),datetime.now().isoformat(),session['username'],lid))
        rd = f.get('recharge_due_date','')
        if rd:
            try:
                days = (datetime.strptime(rd,'%Y-%m-%d').date()-date.today()).days
                if days <= 7:
                    msg = f"⚠️ {link['wan_id']} ({link['center']}) — Recharge due in {days} day(s)!"
                    conn.execute("INSERT INTO notifications (link_id,state,message,type) VALUES (?,?,?,?)",
                                 (lid,link['state'],msg,'warning'))
            except: pass
        conn.commit()
        log_activity(session['username'],'EDIT_LINK',lid,f"Perf={f.get('performance')}")
        conn.close(); flash('Updated successfully!','success')
        return redirect(url_for('link_detail',lid=lid))
    conn.close()
    return render_template('edit_link.html', link=link)

# ── Notifications ─────────────────────────────────────────────────────────────
@app.route('/notifications/read/<int:nid>')
@login_required
def mark_read(nid):
    conn = get_db(); conn.execute("UPDATE notifications SET is_read=1 WHERE id=?",(nid,)); conn.commit(); conn.close()
    return redirect(request.referrer or url_for('dashboard'))

@app.route('/notifications/read_all')
@login_required
def mark_all_read():
    conn = get_db()
    if session['role']=='admin': conn.execute("UPDATE notifications SET is_read=1")
    else: conn.execute("UPDATE notifications SET is_read=1 WHERE state=?",(session['state'],))
    conn.commit(); conn.close(); return redirect(url_for('dashboard'))

# ── Admin: Users ──────────────────────────────────────────────────────────────
@app.route('/admin/users')
@admin_required
def manage_users():
    conn = get_db()
    users = conn.execute("SELECT * FROM users ORDER BY role,username").fetchall(); conn.close()
    return render_template('users.html', users=users, all_states=sorted(set(CITY_STATE.values())))

@app.route('/admin/users/add', methods=['POST'])
@admin_required
def add_user():
    f = request.form; conn = get_db()
    try:
        conn.execute("INSERT INTO users (username,password,role,state,name,email) VALUES (?,?,?,?,?,?)",
                     (f['username'],hash_pw(f['password']),f['role'],f.get('state',''),f.get('name',''),f.get('email','')))
        conn.commit(); flash(f"User '{f['username']}' created!",'success')
    except: flash('Username already exists','danger')
    conn.close(); return redirect(url_for('manage_users'))

@app.route('/admin/users/delete/<int:uid>')
@admin_required
def delete_user(uid):
    conn = get_db(); conn.execute("DELETE FROM users WHERE id=? AND username!='admin'",(uid,)); conn.commit(); conn.close()
    flash('User deleted','info'); return redirect(url_for('manage_users'))

@app.route('/admin/notify', methods=['POST'])
@admin_required
def send_notification():
    f = request.form; conn = get_db()
    conn.execute("INSERT INTO notifications (state,message,type) VALUES (?,?,?)",
                 (f.get('state',''),f.get('message',''),f.get('type','info')))
    conn.commit(); conn.close(); flash('Notification sent!','success')
    return redirect(url_for('dashboard'))

# ── Export ────────────────────────────────────────────────────────────────────
@app.route('/export/csv')
@login_required
def export_csv():
    conn = get_db()
    role,state = session.get('role'),session.get('state')
    rows = conn.execute("SELECT * FROM links ORDER BY state,center").fetchall() if role=='admin' \
           else conn.execute("SELECT * FROM links WHERE state=? ORDER BY center",(state,)).fetchall()
    conn.close()
    out = io.StringIO(); w = csv.writer(out)
    w.writerow(['ID','WAN ID','Center','Location','State','Division','Office Type','Emp ID',
                'Employee Name','SIM Number','Provider','Card Type','Status','Designation',
                'Department','ARC','Performance','Billing Date','Billing Amt','Recharge Date',
                'Recharge Due','Notes','Last Updated'])
    for r in rows:
        w.writerow([r['id'],r['wan_id'],r['center'],r['location'],r['state'],r['division'],
                    r['office_type'],r['employee_id'],r['employee_name'],r['sim_number'],
                    r['service_provider'],r['card_type'],r['emp_status'],r['designation'],
                    r['department'],r['arc'],r['performance'],r['billing_date'],
                    r['billing_amount'],r['recharge_date'],r['recharge_due_date'],
                    r['notes'],r['last_updated']])
    return Response(out.getvalue(), mimetype='text/csv',
                    headers={'Content-Disposition':'attachment; filename=db_links_export.csv'})

if __name__ == '__main__':
    init_db(); import_csv()
    port = int(os.environ.get('PORT',5000))
    print(f"\n{'='*50}\n  DB Link Portal — Dainik Bhaskar\n  http://localhost:{port}\n  Login: admin / admin123\n{'='*50}\n")
    app.run(host='0.0.0.0', port=port, debug=(os.environ.get('FLASK_ENV')!='production'))
