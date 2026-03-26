from flask import (Flask, render_template, request, redirect,
                   url_for, session, jsonify, flash)
from werkzeug.security import check_password_hash, generate_password_hash
import sqlite3, os, functools
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'dainikbhaskar_portal_2025_secure'
DB_PATH = os.path.join(os.path.dirname(__file__), 'portal.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def qone(conn, sql, params=()):
    row = conn.execute(sql, list(params)).fetchone()
    return row[0] if row else 0

def rows_to_dicts(rows):
    return [dict(r) for r in rows]

def and_where(where):
    return 'AND' if where else 'WHERE'

def login_required(f):
    @functools.wraps(f)
    def wrap(*a, **kw):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*a, **kw)
    return wrap

def admin_required(f):
    @functools.wraps(f)
    def wrap(*a, **kw):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        if session.get('role') != 'admin':
            flash('Sirf Admin ye kar sakta hai', 'error')
            return redirect(url_for('dashboard'))
        return f(*a, **kw)
    return wrap

def get_state_filter():
    if session.get('role') == 'engineer' and session.get('state'):
        return 'WHERE state=?', [session['state']]
    return '', []

@app.route('/')
def index():
    return redirect(url_for('dashboard') if 'user_id' in session else url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        db = get_db()
        user = db.execute('SELECT * FROM users WHERE username=?', (username,)).fetchone()
        db.close()
        if user and check_password_hash(user['password_hash'], password):
            session.clear()
            session['user_id']   = user['id']
            session['username']  = user['username']
            session['role']      = user['role']
            session['state']     = user['state'] or ''
            session['full_name'] = user['full_name'] or user['username']
            return redirect(url_for('dashboard'))
        flash('Username ya password galat hai', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    db = get_db()
    where, params = get_state_filter()
    aw = and_where(where)

    stats = {
        'total': qone(db, f'SELECT COUNT(*) FROM links {where}', params),
        'active': qone(db, f'SELECT COUNT(*) FROM links {where} {aw} link_status=?', params + ['Active']),
        'cost': qone(db, f'SELECT COALESCE(SUM(yearly_cost),0) FROM links {where}', params),
        'ill': qone(db, f'SELECT COUNT(*) FROM links {where} {aw} category=?', params + ['ILL/BB']),
        'mpls': qone(db, f'SELECT COUNT(*) FROM links {where} {aw} category=?', params + ['MPLS/PRI']),
        'p2p': qone(db, f'SELECT COUNT(*) FROM links {where} {aw} category=?', params + ['P2P']),
        'sim': qone(db, 'SELECT COUNT(*) FROM sim_cards'),
    }

    perf_rows = db.execute(f'SELECT performance, COUNT(*) as cnt FROM links {where} GROUP BY performance', params).fetchall()
    perf_data = {r['performance']: r['cnt'] for r in perf_rows}

    isp_rows = db.execute(
        f'SELECT isp_name, COUNT(*) as cnt FROM links {where} GROUP BY isp_name ORDER BY cnt DESC LIMIT 10', params
    ).fetchall()

    state_rows = db.execute(
        'SELECT state, COUNT(*) as cnt, COALESCE(SUM(yearly_cost),0) as cost FROM links GROUP BY state ORDER BY cnt DESC'
    ).fetchall()

    nw = 'WHERE is_read=0'
    np = []
    if session.get('role') == 'engineer' and session.get('state'):
        nw += ' AND state=?'
        np.append(session['state'])
    notifs = db.execute(f'SELECT * FROM notifications {nw} ORDER BY created_at DESC LIMIT 8', np).fetchall()

    db.close()
    return render_template('dashboard.html',
        stats=stats, perf_data=perf_data,
        isp_rows=rows_to_dicts(isp_rows),
        state_rows=rows_to_dicts(state_rows),
        notifs=notifs)

@app.route('/links')
@login_required
def links():
    db       = get_db()
    category = request.args.get('category', '')
    search   = request.args.get('search', '').strip()
    state_f  = request.args.get('state', '') if session['role'] == 'admin' else session.get('state', '')
    page     = max(1, int(request.args.get('page', 1) or 1))
    per_page = 30

    conds, params = [], []
    if state_f:
        conds.append('state=?'); params.append(state_f)
    if category:
        conds.append('category=?'); params.append(category)
    if search:
        conds.append('(isp_name LIKE ? OR link_location LIKE ? OR circuit_id LIKE ? OR link_ip LIKE ? OR engineer_location LIKE ?)')
        params += [f'%{search}%'] * 5

    where  = ('WHERE ' + ' AND '.join(conds)) if conds else ''
    total  = qone(db, f'SELECT COUNT(*) FROM links {where}', params)
    offset = (page - 1) * per_page
    link_rows = db.execute(
        f'SELECT * FROM links {where} ORDER BY state, link_location LIMIT ? OFFSET ?',
        params + [per_page, offset]
    ).fetchall()

    all_states = db.execute('SELECT DISTINCT state FROM links WHERE state!="" ORDER BY state').fetchall()
    db.close()
    total_pages = max(1, (total + per_page - 1) // per_page)
    return render_template('links.html',
        links=link_rows, total=total, page=page, per_page=per_page,
        total_pages=total_pages, category=category, search=search,
        state_f=state_f, all_states=all_states)

@app.route('/links/add', methods=['GET', 'POST'])
@login_required
def add_link():
    if request.method == 'POST':
        db = get_db()
        try:
            cost_str = request.form.get('yearly_cost', '0') or '0'
            try:
                cost = float(cost_str.replace(',', ''))
            except:
                cost = 0.0
            db.execute("""INSERT INTO links
                (category,state,engineer_location,link_location,office_type,isp_name,link_type,
                 link_status,circuit_id,media_type,speed_mbps,yearly_cost,link_ip,postal_address,
                 po_number,po_date,billing_cycle,next_renewal_date,payment_location,payment_status,remark)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (
                request.form.get('category', 'ILL/BB'),
                request.form.get('state', ''),
                request.form.get('engineer_location', ''),
                request.form.get('link_location', ''),
                request.form.get('office_type', ''),
                request.form.get('isp_name', ''),
                request.form.get('link_type', ''),
                request.form.get('link_status', 'Active'),
                request.form.get('circuit_id', ''),
                request.form.get('media_type', ''),
                request.form.get('speed_mbps', ''),
                cost,
                request.form.get('link_ip', ''),
                request.form.get('postal_address', ''),
                request.form.get('po_number', ''),
                request.form.get('po_date', ''),
                request.form.get('billing_cycle', ''),
                request.form.get('next_renewal_date', ''),
                request.form.get('payment_location', ''),
                request.form.get('payment_status', ''),
                request.form.get('remark', ''),
            ))
            db.commit()
            db.close()
            flash('Naya link successfully add ho gaya!', 'success')
            return redirect(url_for('links'))
        except Exception as e:
            db.close()
            flash(f'Error: {e}', 'error')

    db = get_db()
    all_states = db.execute('SELECT DISTINCT state FROM links WHERE state!="" ORDER BY state').fetchall()
    db.close()
    return render_template('add_link.html', all_states=all_states)

@app.route('/links/<int:lid>', methods=['GET', 'POST'])
@login_required
def link_detail(lid):
    db   = get_db()
    link = db.execute('SELECT * FROM links WHERE id=?', (lid,)).fetchone()
    if not link:
        db.close()
        flash('Link nahi mila', 'error')
        return redirect(url_for('links'))
    if session['role'] == 'engineer' and link['state'] != session.get('state'):
        db.close()
        flash('Is link ko dekhne ki permission nahi', 'error')
        return redirect(url_for('links'))

    if request.method == 'POST':
        action = request.form.get('action', '')
        if action == 'set_performance':
            perf = request.form.get('performance', 'Good')
            note = request.form.get('note', '')
            db.execute("UPDATE links SET performance=?, updated_at=datetime('now','localtime') WHERE id=?", (perf, lid))
            db.execute("INSERT INTO link_performance (link_id,performance,note,recorded_by) VALUES (?,?,?,?)",
                       (lid, perf, note, session['username']))
            db.commit()
            flash('Performance update ho gayi!', 'success')
        elif action == 'edit_link' and session['role'] == 'admin':
            try:
                cost = float(request.form.get('yearly_cost', '0') or '0')
            except:
                cost = 0.0
            db.execute("""UPDATE links SET link_status=?,isp_name=?,link_type=?,speed_mbps=?,
                yearly_cost=?,next_renewal_date=?,billing_cycle=?,payment_status=?,remark=?,
                link_ip=?,circuit_id=?,media_type=?,updated_at=datetime('now','localtime') WHERE id=?""", (
                request.form.get('link_status',''), request.form.get('isp_name',''),
                request.form.get('link_type',''), request.form.get('speed_mbps',''),
                cost, request.form.get('next_renewal_date',''),
                request.form.get('billing_cycle',''), request.form.get('payment_status',''),
                request.form.get('remark',''), request.form.get('link_ip',''),
                request.form.get('circuit_id',''), request.form.get('media_type',''), lid))
            db.commit()
            flash('Link update ho gaya!', 'success')
        db.close()
        return redirect(url_for('link_detail', lid=lid))

    history = db.execute(
        'SELECT * FROM link_performance WHERE link_id=? ORDER BY recorded_at DESC LIMIT 15', (lid,)
    ).fetchall()
    db.close()
    return render_template('link_detail.html', link=link, history=history)

@app.route('/sim-cards')
@login_required
def sim_cards():
    db       = get_db()
    search   = request.args.get('search', '').strip()
    page     = max(1, int(request.args.get('page', 1) or 1))
    per_page = 30

    conds, params = [], []
    if search:
        conds.append('(employee_name LIKE ? OR sim_number LIKE ? OR center LIKE ? OR service_provider LIKE ?)')
        params += [f'%{search}%'] * 4

    where  = ('WHERE ' + ' AND '.join(conds)) if conds else ''
    total  = qone(db, f'SELECT COUNT(*) FROM sim_cards {where}', params)
    offset = (page - 1) * per_page
    sims   = db.execute(
        f'SELECT * FROM sim_cards {where} ORDER BY center LIMIT ? OFFSET ?',
        params + [per_page, offset]
    ).fetchall()
    db.close()
    total_pages = max(1, (total + per_page - 1) // per_page)
    return render_template('sim_cards.html',
        sims=sims, total=total, page=page, per_page=per_page,
        total_pages=total_pages, search=search)

@app.route('/notifications')
@login_required
def notifications():
    db = get_db()
    conds, params = ['1=1'], []
    if session['role'] == 'engineer' and session.get('state'):
        conds.append('state=?'); params.append(session['state'])
    where = 'WHERE ' + ' AND '.join(conds)
    notifs = db.execute(f'SELECT * FROM notifications {where} ORDER BY created_at DESC', params).fetchall()
    unread = qone(db, f'SELECT COUNT(*) FROM notifications {where} AND is_read=0', params)
    db.close()
    return render_template('notifications.html', notifs=notifs, unread=unread)

@app.route('/notifications/read/<int:nid>', methods=['POST'])
@login_required
def mark_read(nid):
    db = get_db()
    db.execute('UPDATE notifications SET is_read=1 WHERE id=?', (nid,))
    db.commit()
    db.close()
    return jsonify({'ok': True})

@app.route('/notifications/read-all', methods=['POST'])
@login_required
def mark_all_read():
    db = get_db()
    if session['role'] == 'engineer' and session.get('state'):
        db.execute('UPDATE notifications SET is_read=1 WHERE state=?', (session['state'],))
    else:
        db.execute('UPDATE notifications SET is_read=1')
    db.commit()
    db.close()
    return redirect(url_for('notifications'))

@app.route('/api/check-renewals', methods=['POST'])
@admin_required
def check_renewals():
    db    = get_db()
    lnks  = db.execute("SELECT * FROM links WHERE next_renewal_date!=''").fetchall()
    count = 0
    today = datetime.now()
    for lnk in lnks:
        rd = (lnk['next_renewal_date'] or '').strip()
        if not rd or rd in ('nan','None'):
            continue
        for fmt in ('%d/%m/%Y','%Y-%m-%d','%d-%m-%Y'):
            try:
                renewal = datetime.strptime(rd.split(' ')[0], fmt)
                days = (renewal - today).days
                if 0 < days <= 60:
                    exists = db.execute(
                        'SELECT id FROM notifications WHERE link_id=? AND type="renewal" AND is_read=0', (lnk['id'],)
                    ).fetchone()
                    if not exists:
                        loc = lnk['link_location'] or lnk['engineer_location'] or '?'
                        db.execute('INSERT INTO notifications (link_id,message,type,state) VALUES (?,?,?,?)', (
                            lnk['id'],
                            f'Renewal {days} din mein due — {lnk["category"]} {loc} ({lnk["isp_name"]})',
                            'renewal', lnk['state']))
                        count += 1
                break
            except:
                continue
    db.commit()
    db.close()
    return jsonify({'ok': True, 'created': count, 'message': f'{count} renewal notifications bani'})

@app.route('/reports')
@login_required
def reports():
    db = get_db()
    where, params = get_state_filter()
    aw = and_where(where)

    by_cat    = rows_to_dicts(db.execute(f'SELECT category, COUNT(*) as cnt, COALESCE(SUM(yearly_cost),0) as cost FROM links {where} GROUP BY category', params).fetchall())
    by_isp    = rows_to_dicts(db.execute(f'SELECT isp_name, COUNT(*) as cnt, COALESCE(SUM(yearly_cost),0) as cost FROM links {where} GROUP BY isp_name ORDER BY cnt DESC LIMIT 15', params).fetchall())
    by_perf   = rows_to_dicts(db.execute(f'SELECT performance, COUNT(*) as cnt FROM links {where} GROUP BY performance', params).fetchall())
    by_status = rows_to_dicts(db.execute(f'SELECT link_status, COUNT(*) as cnt FROM links {where} GROUP BY link_status', params).fetchall())
    by_state  = rows_to_dicts(db.execute('SELECT state, COUNT(*) as cnt, COALESCE(SUM(yearly_cost),0) as cost FROM links GROUP BY state ORDER BY cost DESC').fetchall())
    # media type - needs extra condition
    media_params = params + [''] if params else ['']
    by_media  = rows_to_dicts(db.execute(
        f'SELECT media_type, COUNT(*) as cnt FROM links {where} {aw} media_type!=? GROUP BY media_type ORDER BY cnt DESC',
        params + ['']
    ).fetchall())

    db.close()
    return render_template('reports.html',
        by_cat=by_cat, by_isp=by_isp, by_perf=by_perf,
        by_status=by_status, by_state=by_state, by_media=by_media)

@app.route('/users')
@admin_required
def users():
    db    = get_db()
    users = db.execute('SELECT * FROM users ORDER BY role DESC, username').fetchall()
    db.close()
    return render_template('users.html', users=users)

@app.route('/users/add', methods=['POST'])
@admin_required
def add_user():
    db = get_db()
    try:
        db.execute('INSERT INTO users (username,password_hash,role,state,full_name,email) VALUES (?,?,?,?,?,?)', (
            request.form['username'].strip(),
            generate_password_hash(request.form['password']),
            request.form['role'],
            request.form.get('state', ''),
            request.form['full_name'].strip(),
            request.form.get('email', '').strip()))
        db.commit()
        flash('User add ho gaya!', 'success')
    except Exception as e:
        flash(f'Error: {e}', 'error')
    db.close()
    return redirect(url_for('users'))

@app.route('/users/delete/<int:uid>', methods=['POST'])
@admin_required
def delete_user(uid):
    if uid == session['user_id']:
        flash('Apna account delete nahi kar sakte', 'error')
        return redirect(url_for('users'))
    db = get_db()
    db.execute('DELETE FROM users WHERE id=?', (uid,))
    db.commit()
    db.close()
    flash('User delete ho gaya', 'success')
    return redirect(url_for('users'))

@app.route('/users/change-password', methods=['POST'])
@login_required
def change_password():
    old = request.form.get('old_password', '')
    new = request.form.get('new_password', '')
    db  = get_db()
    user = db.execute('SELECT * FROM users WHERE id=?', (session['user_id'],)).fetchone()
    if not check_password_hash(user['password_hash'], old):
        flash('Purana password galat hai', 'error')
    elif len(new) < 4:
        flash('Password kam se kam 4 characters ka hona chahiye', 'error')
    else:
        db.execute('UPDATE users SET password_hash=? WHERE id=?',
                   (generate_password_hash(new), session['user_id']))
        db.commit()
        flash('Password change ho gaya!', 'success')
    db.close()
    return redirect(url_for('users'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)
