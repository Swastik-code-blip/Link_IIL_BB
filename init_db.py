import sqlite3, pandas as pd
from werkzeug.security import generate_password_hash

DB = 'portal.db'

def to_float(v):
    try:
        return float(str(v).replace(',','').strip())
    except:
        return 0.0

def clean(v):
    s = str(v) if v is not None else ''
    return '' if s in ('nan','None','NaT') else s.strip()

conn = sqlite3.connect(DB)
c = conn.cursor()

c.executescript("""
DROP TABLE IF EXISTS notifications;
DROP TABLE IF EXISTS link_performance;
DROP TABLE IF EXISTS sim_cards;
DROP TABLE IF EXISTS links;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'engineer',
    state TEXT DEFAULT '',
    full_name TEXT DEFAULT '',
    email TEXT DEFAULT '',
    created_at TEXT DEFAULT (datetime('now','localtime'))
);

CREATE TABLE links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT DEFAULT 'ILL/BB',
    state TEXT DEFAULT '',
    engineer_location TEXT DEFAULT '',
    link_location TEXT DEFAULT '',
    office_type TEXT DEFAULT '',
    isp_name TEXT DEFAULT '',
    link_type TEXT DEFAULT '',
    link_status TEXT DEFAULT 'Active',
    circuit_id TEXT DEFAULT '',
    media_type TEXT DEFAULT '',
    speed_mbps TEXT DEFAULT '',
    yearly_cost REAL DEFAULT 0,
    link_ip TEXT DEFAULT '',
    postal_address TEXT DEFAULT '',
    po_number TEXT DEFAULT '',
    po_date TEXT DEFAULT '',
    billing_cycle TEXT DEFAULT '',
    next_renewal_date TEXT DEFAULT '',
    payment_location TEXT DEFAULT '',
    payment_status TEXT DEFAULT '',
    remark TEXT DEFAULT '',
    performance TEXT DEFAULT 'Good',
    created_at TEXT DEFAULT (datetime('now','localtime')),
    updated_at TEXT DEFAULT (datetime('now','localtime'))
);

CREATE TABLE sim_cards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    wan_id TEXT DEFAULT '',
    center TEXT DEFAULT '',
    location TEXT DEFAULT '',
    division TEXT DEFAULT '',
    office_type TEXT DEFAULT '',
    employee_id TEXT DEFAULT '',
    employee_name TEXT DEFAULT '',
    sim_number TEXT DEFAULT '',
    service_provider TEXT DEFAULT '',
    card_type TEXT DEFAULT '',
    emp_status TEXT DEFAULT 'Active',
    designation TEXT DEFAULT '',
    department TEXT DEFAULT '',
    arc REAL DEFAULT 0,
    state TEXT DEFAULT '',
    created_at TEXT DEFAULT (datetime('now','localtime'))
);

CREATE TABLE link_performance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    link_id INTEGER NOT NULL,
    performance TEXT NOT NULL,
    note TEXT DEFAULT '',
    recorded_by TEXT DEFAULT '',
    recorded_at TEXT DEFAULT (datetime('now','localtime')),
    FOREIGN KEY (link_id) REFERENCES links(id)
);

CREATE TABLE notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    link_id INTEGER DEFAULT 0,
    message TEXT NOT NULL,
    type TEXT DEFAULT 'info',
    is_read INTEGER DEFAULT 0,
    state TEXT DEFAULT '',
    created_at TEXT DEFAULT (datetime('now','localtime'))
);
""")

xl = pd.ExcelFile('/mnt/user-data/uploads/Pan_India_ILL_and_BB_Link_25-26__1_.xlsx')

# ILL/BB
df = pd.read_excel(xl, sheet_name='ILL').dropna(subset=['State','ISP Name'])
for _, r in df.iterrows():
    c.execute("""INSERT INTO links (category,state,engineer_location,link_location,office_type,isp_name,
        link_type,link_status,circuit_id,media_type,speed_mbps,yearly_cost,link_ip,postal_address,
        po_number,po_date,billing_cycle,next_renewal_date,payment_location,payment_status,remark)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (
        'ILL/BB', clean(r.get('State')), clean(r.get('IT Engineer Location')),
        clean(r.get('Link Location ')), clean(r.get('Office Type')), clean(r.get('ISP Name')),
        clean(r.get('Link Type')), clean(r.get('Link Status')) or 'Active',
        clean(r.get('Circuit ID')), clean(r.get('Fiber / RF/Copper')), clean(r.get('SPEED MBPS')),
        to_float(r.get('Yearly Cost')), clean(r.get(' Link IP Address ')),
        clean(r.get('Link Postal Address ')), clean(r.get('PO No')), clean(r.get('PO Date')),
        clean(r.get('Billing Cycle -Anum /Qtr')), clean(r.get('Next Renewal Date')),
        clean(r.get('Payment Location Local/State/Corp')), clean(r.get('Payment status till Jan-25')),
        clean(r.get('Remark'))))

# MPLS/PRI
df = pd.read_excel(xl, sheet_name='MPLS').dropna(subset=['State','ISP'])
for _, r in df.iterrows():
    c.execute("""INSERT INTO links (category,state,engineer_location,link_location,office_type,isp_name,
        link_type,link_status,media_type,speed_mbps,yearly_cost,billing_cycle)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""", (
        'MPLS/PRI', clean(r.get('State')), clean(r.get('Center')), clean(r.get('Location')),
        clean(r.get('Type')), clean(r.get('ISP')), clean(r.get('Services')),
        clean(r.get('Status')) or 'Active', clean(r.get('Media Type')), clean(r.get('BW')),
        to_float(r.get('ARC (Yearly)')), clean(r.get('Plan'))))

# P2P
df = pd.read_excel(xl, sheet_name='P2P').dropna(subset=['State','ISP'])
for _, r in df.iterrows():
    c.execute("""INSERT INTO links (category,state,engineer_location,link_location,office_type,isp_name,
        link_type,link_status,circuit_id,media_type,speed_mbps,yearly_cost,billing_cycle)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""", (
        'P2P', clean(r.get('State')), clean(r.get('Center')), clean(r.get('Location')),
        clean(r.get('Type')), clean(r.get('ISP')), clean(r.get('Services')),
        'Active', clean(r.get('Circuit\xa0ID')), clean(r.get('Media Type')), clean(r.get('BW')),
        to_float(r.get('ARC (Yearly)')), clean(r.get('Plan'))))

# SIM Cards
df = pd.read_excel(xl, sheet_name='Data Card SIM').dropna(subset=['Center','Sim Number'])
for _, r in df.iterrows():
    c.execute("""INSERT INTO sim_cards (wan_id,center,location,division,office_type,employee_id,
        employee_name,sim_number,service_provider,card_type,emp_status,designation,department,arc,state)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (
        clean(r.get('Wan\xa0Id')), clean(r.get('Center')), clean(r.get('Location')),
        clean(r.get('Division')), clean(r.get('Office Type')), clean(r.get('EmployeeId')),
        clean(r.get('EmployeeName')), clean(r.get('Sim Number')), clean(r.get('Service\xa0Provider')),
        clean(r.get('Card\xa0Type')), clean(r.get('EmpStatus')) or 'Active',
        clean(r.get('Designation')), clean(r.get('Department')), to_float(r.get('ARC')), ''))

# Users
c.execute("INSERT INTO users (username,password_hash,role,full_name,email) VALUES (?,?,?,?,?)",
    ('admin', generate_password_hash('admin123'), 'admin', 'Admin — DB IT', 'admin@dainikbhaskar.com'))

states = [
    ('GJ', 'Gujarat'), ('MH', 'Maharashtra'), ('RJ', 'Rajasthan'),
    ('HR', 'Haryana'), ('NCR', 'NCR Delhi'), ('MPCG', 'MP & CG'),
    ('BR&JH', 'Bihar & Jharkhand'), ('CPH', 'Chandigarh Punjab HP'),
]
for code, name in states:
    uname = 'eng_' + code.lower().replace('&','_').replace(' ','_')
    c.execute("INSERT INTO users (username,password_hash,role,state,full_name,email) VALUES (?,?,?,?,?,?)",
        (uname, generate_password_hash('eng123'), 'engineer', code,
         f'Engineer {name}', f'{uname}@dainikbhaskar.com'))

# Sample notifications
c.execute("INSERT INTO notifications (link_id,message,type,state) VALUES (?,?,?,?)",
    (1,'Link renewal 30 din mein due hai — ILL Ahmedabad (TATA)','renewal','GJ'))
c.execute("INSERT INTO notifications (link_id,message,type,state) VALUES (?,?,?,?)",
    (2,'Payment verify karein — ILL Ahmedabad (ISHAN)','payment','GJ'))

conn.commit()
conn.close()
print("DB ready!")
