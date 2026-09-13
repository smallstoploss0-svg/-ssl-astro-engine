import sqlite3
import os
import json
import csv
from datetime import datetime, timedelta

DB_DIR = r"D:\Projects\database"
os.makedirs(DB_DIR, exist_ok=True)
DB_PATH = os.path.join(DB_DIR, "astro_master.db")

class AstroDatabaseManager:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self.init_db()

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def init_db(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 1. Clients Subscription Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS clients (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    phone TEXT NOT NULL UNIQUE,
                    start_date TEXT NOT NULL,
                    end_date TEXT NOT NULL,
                    status TEXT DEFAULT 'ACTIVE',
                    active_session_token TEXT,
                    last_active TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            try:
                cursor.execute("ALTER TABLE clients ADD COLUMN active_session_token TEXT")
            except Exception:
                pass
            try:
                cursor.execute("ALTER TABLE clients ADD COLUMN last_active TIMESTAMP")
            except Exception:
                pass
            
            # 2. Daily Reversal Records Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS daily_records (
                    date_str TEXT NOT NULL,
                    instrument TEXT NOT NULL,
                    title TEXT,
                    sub TEXT,
                    grade TEXT,
                    nakshatra TEXT,
                    pada TEXT,
                    volatility TEXT,
                    degree TEXT,
                    sessions_json TEXT,
                    PRIMARY KEY (date_str, instrument)
                )
            ''')
            
            conn.commit()
            
            # Seed default clients if empty
            cursor.execute("SELECT COUNT(*) FROM clients")
            if cursor.fetchone()[0] == 0:
                default_clients = [
                    ('Rahul Sharma', '9876543210', '2026-09-01', '2026-10-01', 'ACTIVE'),
                    ('Amit Patel', '9812345678', '2026-08-15', '2026-11-15', 'ACTIVE'),
                    ('Vikas Kumar', '9711223344', '2026-08-01', '2026-09-01', 'EXPIRED')
                ]
                cursor.executemany('''
                    INSERT INTO clients (name, phone, start_date, end_date, status)
                    VALUES (?, ?, ?, ?, ?)
                ''', default_clients)
                conn.commit()

    # --- CLIENT MANAGEMENT METHODS ---
    def get_all_clients(self):
        today = datetime.now().date()
        
        def safe_parse_date(d_str):
            if not d_str:
                return today
            try:
                return datetime.strptime(str(d_str).strip(), '%Y-%m-%d').date()
            except Exception:
                pass
            import re
            parts = re.split(r'[\.\/\-]', str(d_str).strip())
            if len(parts) == 3:
                p1, p2, p3 = parts[0].zfill(2), parts[1].zfill(2), parts[2]
                try:
                    if len(p3) == 4:
                        return datetime.strptime(f"{p3}-{p2}-{p1}", '%Y-%m-%d').date()
                    elif len(p1) == 4:
                        return datetime.strptime(f"{p1}-{p2}-{p3}", '%Y-%m-%d').date()
                except Exception:
                    pass
            return today

        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM clients ORDER BY id ASC")
            rows = cursor.fetchall()
            
            clients = []
            for r in rows:
                c = dict(r)
                start = safe_parse_date(c['start_date'])
                end = safe_parse_date(c['end_date'])
                
                # Normalize stored strings in dict return
                c['start_date'] = start.strftime('%Y-%m-%d')
                c['end_date'] = end.strftime('%Y-%m-%d')
                
                total_duration = max(1, (end - start).days)
                days_used = max(0, (today - start).days)
                days_remaining = (end - today).days
                
                if days_remaining <= 0 and c['status'] != 'BLOCKED':
                    c['status'] = 'EXPIRED'
                elif c['status'] != 'BLOCKED':
                    c['status'] = 'ACTIVE'
                    
                c['total_duration'] = total_duration
                c['days_used'] = days_used
                c['days_remaining'] = days_remaining
                clients.append(c)
                
            return clients

    def add_client(self, name, phone, start_date, end_date, update_if_exists=False):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('''
                    INSERT INTO clients (name, phone, start_date, end_date, status)
                    VALUES (?, ?, ?, ?, 'ACTIVE')
                ''', (name, phone, start_date, end_date))
                conn.commit()
                return {"success": True, "message": f"Client {name} added successfully!"}
            except sqlite3.IntegrityError:
                if update_if_exists:
                    cursor.execute('''
                        UPDATE clients
                        SET name = ?, start_date = ?, end_date = ?, status = 'ACTIVE'
                        WHERE phone = ?
                    ''', (name, start_date, end_date, phone))
                    conn.commit()
                    return {"success": True, "message": f"Client {name} updated successfully!", "updated": True}
                return {"success": False, "message": f"Phone number {phone} is already registered!"}

    def extend_client(self, client_id, days=30):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT end_date FROM clients WHERE id = ?", (client_id,))
            row = cursor.fetchone()
            if not row:
                return {"success": False, "message": "Client not found"}
            
            current_end = datetime.strptime(row[0], '%Y-%m-%d').date()
            new_end = current_end + timedelta(days=days)
            new_end_str = new_end.strftime('%Y-%m-%d')
            
            cursor.execute('''
                UPDATE clients 
                SET end_date = ?, status = 'ACTIVE' 
                WHERE id = ?
            ''', (new_end_str, client_id))
            conn.commit()
            return {"success": True, "message": f"Extended access by {days} days until {new_end_str}!"}

    def block_client(self, client_id):
        today_str = datetime.now().strftime('%Y-%m-%d')
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE clients 
                SET end_date = ?, status = 'BLOCKED' 
                WHERE id = ?
            ''', (today_str, client_id))
            conn.commit()
            return {"success": True, "message": "Client blocked successfully!"}

    def delete_client(self, client_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM clients WHERE id = ?", (client_id,))
            conn.commit()
            return {"success": True, "message": "Subscriber removed and deleted from Database successfully!"}

    def unlock_client_device(self, client_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE clients SET active_session_token = NULL WHERE id = ?", (client_id,))
            conn.commit()
            return {"success": True, "message": "Subscriber device lock reset successfully! User can now login on a new device."}

    def logout_client(self, phone, session_token=None):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if session_token:
                cursor.execute("UPDATE clients SET active_session_token = NULL WHERE phone = ? AND active_session_token = ?", (phone.strip(), session_token))
            else:
                cursor.execute("UPDATE clients SET active_session_token = NULL WHERE phone = ?", (phone.strip(),))
            conn.commit()
            return {"success": True, "message": "Logged out successfully."}

    def check_client_access(self, phone, session_token=None, is_login=False):
        import uuid
        today = datetime.now().date()
        now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM clients WHERE phone = ?", (phone.strip(),))
            row = cursor.fetchone()
            if not row:
                return {"has_access": False, "reason": "Phone number not registered. Contact Admin for subscription."}
            
            c = dict(row)
            end = datetime.strptime(c['end_date'], '%Y-%m-%d').date()
            days_remaining = (end - today).days
            
            if c['status'] == 'BLOCKED' or days_remaining <= 0:
                return {"has_access": False, "client": c, "reason": f"Subscription Expired on {c['end_date']}. Contact Admin to renew."}
            
            active_token = c.get('active_session_token')
            
            # Explicit Login Action (Entering Mobile + Password) -> Claims active session for current device
            if is_login:
                new_token = f"sess_{uuid.uuid4().hex[:16]}"
                cursor.execute("UPDATE clients SET active_session_token = ?, last_active = ? WHERE id = ?", (new_token, now_str, c['id']))
                conn.commit()
                c['active_session_token'] = new_token
                return {"has_access": True, "client": c, "days_remaining": days_remaining, "session_token": new_token}

            # Background / Refresh Checks
            if active_token and active_token.strip():
                if session_token and session_token.strip() == active_token.strip():
                    cursor.execute("UPDATE clients SET last_active = ? WHERE id = ?", (now_str, c['id']))
                    conn.commit()
                    return {"has_access": True, "client": c, "days_remaining": days_remaining, "session_token": active_token}
                elif not session_token or not session_token.strip():
                    # Refresh fallback: Bind to existing active_token so user stays logged in on refresh
                    cursor.execute("UPDATE clients SET last_active = ? WHERE id = ?", (now_str, c['id']))
                    conn.commit()
                    return {"has_access": True, "client": c, "days_remaining": days_remaining, "session_token": active_token}
                else:
                    return {
                        "has_access": False, 
                        "error": "device_locked", 
                        "reason": "❌ Logged in on another device! Please login again with password to claim this device."
                    }
            
            # Fallback if no active token exists
            new_token = f"sess_{uuid.uuid4().hex[:16]}"
            cursor.execute("UPDATE clients SET active_session_token = ?, last_active = ? WHERE id = ?", (new_token, now_str, c['id']))
            conn.commit()
            c['active_session_token'] = new_token
            return {"has_access": True, "client": c, "days_remaining": days_remaining, "session_token": new_token}

    def export_clients_csv(self, output_path=None):
        if not output_path:
            output_path = os.path.join(r"C:\Users\welcome\Desktop", "astro_clients_backup.csv")
        
        clients = self.get_all_clients()
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['ID', 'Name', 'Phone', 'Start Date', 'End Date', 'Status', 'Days Used', 'Days Remaining', 'Total Duration'])
            for c in clients:
                writer.writerow([c['id'], c['name'], c['phone'], c['start_date'], c['end_date'], c['status'], c['days_used'], c['days_remaining'], c['total_duration']])
        return output_path

    def import_clients_from_file(self, file_path):
        import pandas as pd
        import re
        added_count = 0
        updated_count = 0
        skipped_count = 0
        try:
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            else:
                df = pd.read_excel(file_path)

            df.columns = [str(col).strip().lower().replace(' ', '_') for col in df.columns]
            
            # Map column names
            name_col = next((c for c in df.columns if any(k in c for k in ['name', 'client', 'subscriber', 'customer'])), None)
            phone_col = next((c for c in df.columns if any(k in c for k in ['phone', 'mobile', 'number', 'cell'])), None)
            start_col = next((c for c in df.columns if any(k in c for k in ['start', 'from', 'begin'])), None)
            end_col = next((c for c in df.columns if any(k in c for k in ['end', 'expiry', 'expire', 'until', 'validity', 'valid']) or c == 'to'), None)

            today_str = datetime.now().strftime('%Y-%m-%d')
            default_end_str = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')

            def parse_phone(val):
                if pd.isna(val): return ''
                try:
                    num_int = int(round(float(val)))
                    phone_str = str(num_int)
                except Exception:
                    phone_str = str(val)
                phone_str = ''.join(filter(str.isdigit, phone_str))
                if len(phone_str) > 10:
                    phone_str = phone_str[-10:]
                return phone_str if len(phone_str) == 10 else ''

            def parse_date(val, fallback_str):
                if pd.isna(val): return fallback_str
                val_str = str(val).strip().split(' ')[0]
                try:
                    dt = pd.to_datetime(val_str, dayfirst=True)
                    return dt.strftime('%Y-%m-%d')
                except Exception:
                    pass
                parts = re.split(r'[\.\/\-]', val_str)
                if len(parts) == 3:
                    p1, p2, p3 = parts[0].zfill(2), parts[1].zfill(2), parts[2]
                    if len(p3) == 4:
                        return f'{p3}-{p2}-{p1}'
                    elif len(p1) == 4:
                        return f'{p1}-{p2}-{p3}'
                return fallback_str

            for _, row in df.iterrows():
                name = str(row[name_col]).strip() if name_col and pd.notna(row[name_col]) else ''
                phone = parse_phone(row[phone_col]) if phone_col else ''
                
                if not phone or len(phone) < 10 or name.lower() in ['nan', 'none', '']:
                    skipped_count += 1
                    continue

                start_date = parse_date(row[start_col], today_str) if start_col else today_str
                end_date = parse_date(row[end_col], default_end_str) if end_col else default_end_str

                res = self.add_client(name, phone, start_date, end_date, update_if_exists=True)
                if res.get('success'):
                    if res.get('updated'):
                        updated_count += 1
                    else:
                        added_count += 1
                else:
                    skipped_count += 1

            msg = f"Import Complete! Added {added_count} new subscribers"
            if updated_count > 0:
                msg += f", updated {updated_count} existing subscribers"
            if skipped_count > 0:
                msg += f", skipped {skipped_count} invalid/empty rows"
            msg += "."

            return {"success": True, "added": added_count, "updated": updated_count, "skipped": skipped_count, "message": msg}
        except Exception as e:
            return {"success": False, "message": f"Error importing Excel file: {str(e)}"}

    # --- DAILY REVERSAL RECORDS METHODS ---
    def save_daily_record(self, date_str, instrument, record_dict):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            sessions_json = json.dumps(record_dict.get('sessions', []))
            cursor.execute('''
                INSERT OR REPLACE INTO daily_records 
                (date_str, instrument, title, sub, grade, nakshatra, pada, volatility, degree, sessions_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                date_str,
                instrument,
                record_dict.get('title', ''),
                record_dict.get('sub', ''),
                record_dict.get('grade', ''),
                record_dict.get('nakshatra', ''),
                record_dict.get('pada', ''),
                record_dict.get('volatility', ''),
                record_dict.get('degree', ''),
                sessions_json
            ))
            conn.commit()

    def get_daily_record(self, date_str, instrument):
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM daily_records WHERE date_str = ? AND instrument = ?", (date_str, instrument))
            row = cursor.fetchone()
            if not row:
                return None
            res = dict(row)
            res['sessions'] = json.loads(res['sessions_json'])
            return res

if __name__ == '__main__':
    db = AstroDatabaseManager()
    print("Database Initialized Successfully at:", db.db_path)
    print("Active Clients Count:", len(db.get_all_clients()))
    csv_file = db.export_clients_csv()
    print("CSV Export Test Success:", csv_file)
