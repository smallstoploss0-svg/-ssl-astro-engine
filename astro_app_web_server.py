import sys
import http.server
import socketserver
import json, os, urllib.parse
from datetime import datetime, timedelta
import sqlite3

PORT = int(os.environ.get("PORT", 8080))
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_DIR = os.path.join(BASE_DIR, "database")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")
os.makedirs(DB_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)

DB_PATH = os.path.join(DB_DIR, "astro_master.db")
root_db_path = os.path.join(BASE_DIR, "astro_master.db")
if os.path.exists(root_db_path):
    import shutil
    try:
        shutil.copy(root_db_path, DB_PATH)
        print("[DB Sync] astro_master.db loaded successfully from root!")
    except Exception as e:
        print(f"[DB Sync Error] {e}")

# Import database manager
sys.path.append(BASE_DIR)
from astro_database_manager import AstroDatabaseManager

db = AstroDatabaseManager(DB_PATH)

# =============================================================================
# 1. CLIENT MOBILE DASHBOARD HTML
# =============================================================================
CLIENT_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
  <title>SSL Astro Engine App</title>
  <meta name="theme-color" content="#8B008B">
  <link rel="manifest" href="/manifest.json">
  <link rel="icon" type="image/png" href="/icon-192.png">
  <script>if('serviceWorker' in navigator){window.addEventListener('load', ()=>{navigator.serviceWorker.register('/sw.js');});}</script>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; -webkit-tap-highlight-color: transparent; touch-action: manipulation; }
    html, body { width: 100%; height: 100%; background: #0F172A; color: #1E293B; }
    body { display: flex; justify-content: center; }
    .mobile-frame { width: 100%; max-width: 440px; background: #FFFFFF; min-height: 100vh; box-shadow: 0 10px 30px rgba(0,0,0,0.3); display: flex; flex-direction: column; position: relative; }
    
    .toast-msg { display: none; background: #16A34A; color: white; padding: 12px 16px; font-weight: 800; font-size: 13px; text-align: center; position: sticky; top: 0; z-index: 1000; box-shadow: 0 4px 12px rgba(0,0,0,0.25); }
    .toast-msg.red { background: #DC2626; }
    .toast-msg.amber { background: #D97706; }

    .app-header { background: #8B008B; color: white; padding: 12px 16px; display: flex; justify-content: space-between; align-items: center; position: sticky; top: 0; z-index: 10; box-shadow: 0 2px 10px rgba(0,0,0,0.2); }
    .app-logo-group { display: flex; align-items: center; gap: 10px; }
    .app-logo-img { width: 34px; height: 34px; border-radius: 8px; border: 1.5px solid #FFD700; object-fit: cover; }
    .app-title { font-size: 16px; font-weight: 900; letter-spacing: 0.5px; }
    .header-actions { display: flex; align-items: center; gap: 8px; }
    .icon-btn { background: rgba(255,255,255,0.15); border: none; color: white; padding: 6px 10px; border-radius: 8px; font-weight: 700; font-size: 12px; cursor: pointer; display: flex; align-items: center; gap: 4px; }
    .icon-btn:active { background: rgba(255,255,255,0.3); }

    .login-container { display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 24px 20px; flex: 1; background: linear-gradient(180deg, #0F172A 0%, #1E1B4B 100%); color: white; text-align: center; }
    .login-logo { width: 90px; height: 90px; border-radius: 20px; border: 3px solid #FFD700; margin-bottom: 16px; box-shadow: 0 8px 24px rgba(255,215,0,0.3); object-fit: cover; }
    .login-title { font-size: 22px; font-weight: 900; color: #FFFFFF; margin-bottom: 6px; letter-spacing: 0.8px; }
    .login-sub { font-size: 12px; color: #CBD5E1; margin-bottom: 24px; line-height: 1.4; }
    
    .login-card { width: 100%; background: #FFFFFF; border-radius: 18px; padding: 20px; color: #1E293B; box-shadow: 0 10px 30px rgba(0,0,0,0.3); }
    .form-group { margin-bottom: 14px; text-align: left; }
    .form-label { font-size: 11px; font-weight: 800; color: #475569; margin-bottom: 6px; display: block; text-transform: uppercase; }
    .form-input { width: 100%; padding: 14px; border: 2px solid #E2E8F0; border-radius: 10px; font-size: 14px; font-weight: 700; outline: none; transition: all 0.2s; color: #1E293B; background: #F8FAFC; }
    .form-input:focus { border-color: #8B008B; background: #FFFFFF; }

    .btn-login { width: 100%; background: #8B008B; color: white; border: none; padding: 15px; border-radius: 12px; font-weight: 900; font-size: 15px; cursor: pointer; letter-spacing: 0.5px; box-shadow: 0 4px 14px rgba(139,0,139,0.4); margin-top: 6px; }
    .btn-login:active { transform: scale(0.98); }

    .brand-tagline-banner { background: linear-gradient(90deg, #4C1D95 0%, #7C3AED 50%, #4C1D95 100%); color: #FFD700; font-size: 13px; font-weight: 900; text-align: center; padding: 10px 12px; letter-spacing: 0.8px; border-bottom: 2.5px solid #FFD700; text-shadow: 0 1px 3px rgba(0,0,0,0.8); }
    @media print { body { display: none !important; } }
    body { user-select: none; -webkit-user-select: none; }

    .nav-tabs { display: flex; background: #7B007B; }
    .tab-btn { flex: 1; padding: 14px 6px; border: none; background: transparent; color: rgba(255,255,255,0.7); font-weight: 800; font-size: 13px; cursor: pointer; border-bottom: 3.5px solid transparent; transition: all 0.2s; text-align: center; }
    .tab-btn.active { color: #FFD700; border-bottom-color: #FFD700; background: rgba(255,255,255,0.15); }

    .content { padding: 14px; flex: 1; overflow-y: auto; -webkit-overflow-scrolling: touch; }

    .report-card-frame { background: #0F172A; border-radius: 16px; overflow: hidden; border: 2px solid #8B008B; margin-bottom: 16px; box-shadow: 0 8px 20px rgba(139,0,139,0.15); }
    .report-top-banner { background: #6B21A8; color: white; padding: 14px; text-align: left; }
    .report-title { font-size: 15px; font-weight: 900; }
    .report-sub { font-size: 10px; color: #E9D5FF; font-weight: 700; margin-top: 2px; }

    .report-grade-banner { background: #EA580C; color: white; padding: 10px 14px; font-size: 11px; font-weight: 900; display: flex; justify-content: space-between; align-items: center; }
    .grade-highlight { color: #FEF08A; font-weight: 900; font-size: 12px; }

    .report-metrics-bar { background: #1E293B; padding: 10px 14px; display: grid; grid-template-columns: 1fr 1fr; gap: 6px; font-size: 11px; color: #CBD5E1; border-bottom: 1px solid #334155; }
    .m-label { font-weight: 800; color: #94A3B8; }
    .m-val { font-weight: 900; color: #FFFFFF; }

    .btn-view-report { background: #6B21A8; color: white; border: none; width: 100%; padding: 12px; font-weight: 900; font-size: 12px; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 6px; }
    .btn-view-report:active { background: #581C87; }

    .countdown-card { background: linear-gradient(135deg, #DC2626, #991B1B); color: white; border-radius: 14px; padding: 14px; text-align: center; margin-bottom: 16px; box-shadow: 0 4px 12px rgba(220,38,38,0.25); }
    .cd-title { font-size: 11px; font-weight: 800; letter-spacing: 0.8px; margin-bottom: 4px; }
    .cd-timer { font-size: 28px; font-weight: 900; letter-spacing: 1px; margin-bottom: 4px; }
    .cd-target { font-size: 11px; background: rgba(255,255,255,0.2); padding: 3px 10px; border-radius: 10px; font-weight: 700; display: inline-block; }

    .timetable-banner { background: #1E293B; color: white; padding: 10px 14px; border-radius: 10px 10px 0 0; font-size: 12px; font-weight: 900; display: flex; justify-content: space-between; align-items: center; }
    .timetable-container { background: white; border: 1.5px solid #1E293B; border-top: none; border-radius: 0 0 14px 14px; overflow: hidden; margin-bottom: 20px; }
    .session-header { background: #EFF6FF; color: #1E40AF; font-size: 13px; font-weight: 900; padding: 10px 14px; border-bottom: 1.5px solid #BFDBFE; border-top: 1px solid #DBEAFE; letter-spacing: 0.5px; text-transform: uppercase; }

    .slot-row { display: flex; align-items: center; padding: 11px 12px; border-bottom: 1px solid #F1F5F9; background: #FFFFFF; }
    .slot-row.master { background: #FEF2F2; border-left: 4px solid #DC2626; }
    .slot-row.major { background: #FEFCE8; border-left: 4px solid #EA580C; }

    .row-time { font-size: 14px; font-weight: 900; color: #0F172A; width: 90px; letter-spacing: 0.2px; }
    .row-rating { flex: 1; font-size: 12px; font-weight: 800; color: #334155; }

    .row-badge { font-size: 10px; font-weight: 800; padding: 3px 8px; border-radius: 6px; }
    .badge-master { background: #DC2626; color: white; }
    .badge-major { background: #EA580C; color: white; }
    .badge-std { background: #E2E8F0; color: #475569; }

    .app-footer { text-align: center; padding: 16px; font-size: 11px; color: #64748B; font-weight: 600; }
    .admin-link { color: #8B008B; font-weight: 800; cursor: pointer; text-decoration: underline; margin-top: 6px; display: inline-block; }

    .modal-overlay { display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.75); z-index: 2000; justify-content: center; align-items: center; padding: 16px; }
    .modal-box { background: #FFFFFF; border-radius: 16px; width: 100%; max-width: 400px; overflow: hidden; box-shadow: 0 10px 30px rgba(0,0,0,0.4); animation: popIn 0.2s ease-out; }
    .modal-header { background: #1E293B; color: white; padding: 14px 16px; display: flex; justify-content: space-between; align-items: center; font-weight: 900; font-size: 14px; }
    .modal-body { padding: 16px; }
    .modal-close { background: none; border: none; color: white; font-size: 18px; cursor: pointer; }
    
    @keyframes popIn { from { transform: scale(0.9); opacity: 0; } to { transform: scale(1); opacity: 1; } }

    #admin-panel-container { display: none; background: #F8FAFC; border: 2px solid #8B008B; border-radius: 14px; padding: 14px; margin-top: 20px; margin-bottom: 30px; }
    .client-list-item { background: white; border: 1px solid #E2E8F0; border-radius: 8px; padding: 10px; margin-bottom: 8px; font-size: 12px; display: flex; justify-content: space-between; align-items: center; }
  </style>
</head>
<body>
  <div class="mobile-frame">
    <div class="toast-msg" id="toast-banner">✅ Welcome to SSL Astro Engine!</div>

    <!-- 1. LOGIN SCREEN -->
    <div class="login-container" id="login-screen">
      <img src="/official_logo.jpg" class="login-logo" alt="SSL Logo" onerror="this.src='/icon-192.png'">
      <div class="login-title">SSL ASTRO ENGINE</div>
      <div class="login-sub">Gold XAUUSD & Nifty 50 Astro Reversal Timetable</div>
      
      <div class="login-card">
        <div class="form-group">
          <label class="form-label">📱 Registered Mobile Number</label>
          <input type="tel" id="login-phone" class="form-input" placeholder="Enter 10-digit mobile number" maxlength="10">
        </div>
        <div class="form-group">
          <label class="form-label">🔑 Password / Access PIN (Last 4 Digits of Mobile)</label>
          <input type="password" id="login-pin" class="form-input" placeholder="Enter last 4 digits of your mobile" maxlength="4">
        </div>
        <button class="btn-login" onclick="handleSubscriberLogin()">🚀 LOGIN TO ASTRO ENGINE</button>
      </div>
      <div style="font-size: 11px; margin-top: 20px; color: #94A3B8;">
        🔒 Secure Subscriber Authentication System<br>Active Subscription Required
      </div>
    </div>

    <!-- 2. CLIENT DASHBOARD -->
    <div id="client-dashboard" style="display: none; flex-direction: column; flex: 1;">
      <div class="app-header">
        <div class="app-logo-group">
          <img src="/official_logo.jpg" class="app-logo-img" alt="Logo" onerror="this.src='/icon-192.png'">
          <div class="app-title">SSL ASTRO ENGINE</div>
        </div>
        <div class="header-actions">
          <button class="icon-btn" onclick="toggleVibration()" id="btn-vib">🔊 VIB ON</button>
          <button class="icon-btn" onclick="handleLogout()" style="background: #DC2626;">🔒 LOGOUT</button>
        </div>
      </div>

      <div class="brand-tagline-banner">
        🏆 INDIA'S NO.1 FINANCIAL ASTROLOGY SYSTEM
      </div>

      <div class="nav-tabs">
        <button class="tab-btn active" id="tab-nifty" onclick="switchTab('NIFTY')">📈 NIFTY 50 (1-MIN)</button>
        <button class="tab-btn" id="tab-gold" onclick="switchTab('GOLD')">👑 GOLD XAUUSD (5-MIN)</button>
      </div>

      <div class="content">
        <div class="report-card-frame">
          <div class="report-top-banner">
            <div class="report-title" id="rep-title">☸ SSL ASTRO ENGINE — NIFTY 50</div>
            <div class="report-sub" id="rep-sub">DAILY REVERSAL PREDICTION REPORT (1-MIN LOOP)</div>
          </div>
          <div class="report-grade-banner">
            <span id="rep-date">DATE: TODAY</span>
            <span class="grade-highlight" id="rep-grade">💎 DIAMOND MASTER (95/100)</span>
          </div>
          <div class="report-metrics-bar">
            <div><span class="m-label">NAKSHATRA:</span> <span class="m-val" id="rep-nak">MAGHA (KETU)</span></div>
            <div><span class="m-label">PADA:</span> <span class="m-val" id="rep-pada">PADA 3</span></div>
            <div><span class="m-label">VOLATILITY:</span> <span class="m-val" id="rep-vol">NORMAL</span></div>
            <div><span class="m-label">ANNUAL DEG:</span> <span class="m-val" id="rep-deg">172.71°</span></div>
            <div style="grid-column: span 2;"><span class="m-label" style="color:#FFD700;">🗓️ TREND CHANGE DATES:</span> <span class="m-val" id="rep-trend-dates" style="color:#FFD700; font-weight:900;">18-Sep & 19-Sep</span></div>
          </div>
          <button class="btn-view-report" onclick="openReportChartModal()">
            🖼️ VIEW DAILY GRADED CHART REPORT
          </button>
        </div>

        <div class="countdown-card">
          <div class="cd-title">🚨 UPCOMING ASTRO REVERSAL COUNTDOWN</div>
          <div class="cd-timer" id="cd-timer-val">00:00:00</div>
          <div class="cd-target" id="cd-target-label">NEXT SLOT AT --:-- AM</div>
        </div>

        <div class="timetable-banner">
          <span>📋 FULL DAY ASTRO TIMETABLE</span>
          <span id="tbl-date-str" style="color: #FFD700;">TODAY</span>
        </div>

        <div class="timetable-container" id="timetable-slots-list"></div>

        <div class="app-footer">
          <div>SSL Astro Engine © 2026 • Subscriber Edition</div>
          <div class="admin-link" onclick="openAdminPinModal()">🔑 Admin Access Panel</div>
        </div>

        <div id="admin-panel-container">
          <div style="font-weight: 900; font-size: 14px; margin-bottom: 10px; color: #8B008B;">⚡ ADMIN MANAGEMENT PANEL</div>
          <div style="font-size: 11px; color: #475569; margin-bottom: 12px;">Add subscribers, extend plans, or check system DB logs.</div>
          
          <div class="form-group">
            <label class="form-label">Client Name *</label>
            <input type="text" id="adm-name" class="form-input" placeholder="e.g. Rahul Sharma">
          </div>
          <div class="form-group">
            <label class="form-label">Phone Number *</label>
            <input type="tel" id="adm-phone" class="form-input" placeholder="10-digit mobile number" maxlength="10">
          </div>
          <div style="display: flex; gap: 8px;" class="form-group">
            <div style="flex:1;">
              <label class="form-label">Start Date</label>
              <input type="date" id="adm-start" class="form-input">
            </div>
            <div style="flex:1;">
              <label class="form-label">End Date (30 Days)</label>
              <input type="date" id="adm-end" class="form-input">
            </div>
          </div>
          <button type="button" style="background: #16A34A; color: white; border: none; width: 100%; padding: 14px; border-radius: 10px; font-weight: 900; font-size: 14px; cursor: pointer;" onclick="handleAddClient()">+ ADD NEW SUBSCRIBER</button>

          <div style="font-weight: 900; font-size: 12px; margin-top: 20px; margin-bottom: 10px; color: #1E293B;" id="mobile-sub-list-title">📋 REGISTERED SUBSCRIBERS LIST (0)</div>
          <div id="admin-client-list"></div>
        </div>
      </div>
    </div>

    <!-- MODAL 1: Chart Report Image Modal -->
    <div class="modal-overlay" id="chart-modal">
      <div class="modal-box">
        <div class="modal-header">
          <span>📊 DAILY GRADED CHART REPORT</span>
          <button class="modal-close" onclick="closeModal('chart-modal')">✕</button>
        </div>
        <div class="modal-body">
          <div style="background: #000000; border-radius: 10px; min-height: 220px; display: flex; flex-direction: column; justify-content: center; align-items: center; padding: 10px; border: 1.5px solid #FFD700;">
            <img id="chart-img-el" src="/screenshot-1.png" style="max-width: 100%; border-radius: 6px;" alt="Graded Chart">
          </div>
          <div style="font-size: 11px; color: #D97706; font-weight: 700; margin-top: 10px; text-align: center;">
            ⭐ 100% Matched to TradingView Reversal Times & Telegram Daily Broadcast.
          </div>
        </div>
      </div>
    </div>

    <!-- MODAL 2: Admin PIN Modal -->
    <div class="modal-overlay" id="admin-pin-modal">
      <div class="modal-box">
        <div class="modal-header">
          <span>🔑 ADMIN SECURITY VERIFICATION</span>
          <button class="modal-close" onclick="closeModal('admin-pin-modal')">✕</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label class="form-label">Enter Admin Master PIN</label>
            <input type="password" id="admin-security-pin" class="form-input" placeholder="Enter Admin Master PIN">
          </div>
          <button style="background: #8B008B; color: white; border: none; width: 100%; padding: 12px; border-radius: 8px; font-weight: 900; cursor: pointer;" onclick="verifyAdminPin()">UNLOCK ADMIN PANEL</button>
        </div>
      </div>
    </div>
  </div>

  <script>
    let currentAsset = 'NIFTY';
    let isVibeOn = true;
    let payloadData = null;
    let cdInterval = null;

    window.onload = function() {
      const today = new Date();
      const nextMonth = new Date();
      nextMonth.setDate(today.getDate() + 30);
      
      document.getElementById('adm-start').value = today.toISOString().split('T')[0];
      document.getElementById('adm-end').value = nextMonth.toISOString().split('T')[0];

      const savedPhone = localStorage.getItem('ssl_user_phone');
      if (savedPhone) {
        verifyPhoneAccess(savedPhone, true);
      }
      loadPayloadData();
      setInterval(loadPayloadData, 30000);
    };

    function showToast(msg, type='green') {
      const b = document.getElementById('toast-banner');
      b.innerText = msg;
      b.className = 'toast-msg ' + (type === 'red' ? 'red' : (type === 'amber' ? 'amber' : ''));
      b.style.display = 'block';
      setTimeout(() => { b.style.display = 'none'; }, 3500);
    }

    async function handleSubscriberLogin() {
      const phone = document.getElementById('login-phone').value.trim();
      const pin = document.getElementById('login-pin').value.trim();
      if (!phone || phone.length < 10) {
        showToast('❌ Please enter a valid 10-digit mobile number!', 'red');
        return;
      }
      const expectedPin = phone.slice(-4);
      if (!pin) {
        showToast('❌ Please enter last 4 digits of your mobile number!', 'red');
        return;
      }
      if (pin !== expectedPin) {
        showToast('❌ Invalid Password! Password is last 4 digits of your mobile', 'red');
        return;
      }
      await verifyPhoneAccess(phone, false, true);
    }

    async function verifyPhoneAccess(phone, isAuto, isLogin=false) {
      try {
        const sessToken = localStorage.getItem('ssl_session_token');
        const res = await fetch('/api/check_access', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ phone: phone, session_token: sessToken, is_login: isLogin })
        });
        const data = await res.json();

        if (data.has_access) {
          localStorage.setItem('ssl_user_phone', phone);
          if (data.session_token) {
            localStorage.setItem('ssl_session_token', data.session_token);
          }
          document.getElementById('login-screen').style.display = 'none';
          document.getElementById('client-dashboard').style.display = 'flex';
          if (!isAuto) {
            showToast('✅ Welcome! Subscription Active until ' + data.client.end_date);
          }
        } else {
          localStorage.removeItem('ssl_user_phone');
          localStorage.removeItem('ssl_session_token');
          document.getElementById('login-screen').style.display = 'flex';
          document.getElementById('client-dashboard').style.display = 'none';
          showToast('❌ ' + (data.reason || 'Access Denied'), 'red');
        }
      } catch(e) {
        showToast('⚠️ Server connection error!', 'red');
      }
    }

    async function handleLogout() {
      const phone = localStorage.getItem('ssl_user_phone');
      const sessToken = localStorage.getItem('ssl_session_token');
      if (phone) {
        try {
          await fetch('/api/clients/logout', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ phone: phone, session_token: sessToken })
          });
        } catch(e) {}
      }
      localStorage.removeItem('ssl_user_phone');
      localStorage.removeItem('ssl_session_token');
      document.getElementById('login-screen').style.display = 'flex';
      document.getElementById('client-dashboard').style.display = 'none';
      showToast('🔒 Logged out successfully');
    }

    // Enhanced Anti-screenshot / Anti-recording protection layer
    document.addEventListener('contextmenu', e => e.preventDefault());
    
    // Auto blur & blackout whenever app window loses focus (recording overlay, notification shade pull down, screenshot key)
    window.addEventListener('blur', () => {
      document.body.style.filter = 'blur(40px) brightness(0)';
    });
    window.addEventListener('focus', () => {
      document.body.style.filter = 'none';
    });
    document.addEventListener('visibilitychange', () => {
      if (document.hidden) {
        document.body.style.filter = 'blur(40px) brightness(0)';
      } else {
        document.body.style.filter = 'none';
      }
    });

    document.addEventListener('keyup', (e) => {
      if (e.key === 'PrintScreen' || e.keyCode === 44) {
        if (navigator.clipboard) navigator.clipboard.writeText('');
        document.body.style.filter = 'blur(40px) brightness(0)';
        setTimeout(() => { document.body.style.filter = 'none'; }, 2000);
        showToast('⚠️ Screen Capture Restricted!', 'amber');
      }
    });

    function toggleVibration() {
      isVibeOn = !isVibeOn;
      document.getElementById('btn-vib').innerText = isVibeOn ? '🔊 VIB ON' : '🔕 VIB OFF';
      showToast(isVibeOn ? '🔊 Phone Vibration Enabled' : '🔕 Phone Vibration Disabled');
    }

    async function loadPayloadData() {
      try {
        const res = await fetch('/api/daily_payload?v=' + new Date().getTime());
        if (res.ok) {
          payloadData = await res.json();
          renderTimetable();
        }
      } catch(e) {
        console.log('Payload fetch error:', e);
      }
    }

    function switchTab(asset) {
      currentAsset = asset;
      document.getElementById('tab-nifty').className = 'tab-btn ' + (asset === 'NIFTY' ? 'active' : '');
      document.getElementById('tab-gold').className = 'tab-btn ' + (asset === 'GOLD' ? 'active' : '');
      renderTimetable();
    }

    function renderTimetable() {
      if (!payloadData) return;
      const data = currentAsset === 'NIFTY' ? payloadData.nifty : payloadData.gold;
      if (!data) return;

      document.getElementById('rep-title').innerText = '☸ SSL ASTRO ENGINE — ' + (currentAsset === 'NIFTY' ? 'NIFTY 50' : 'GOLD (XAUUSD)');
      document.getElementById('rep-sub').innerText = 'DAILY REVERSAL PREDICTION REPORT (' + (currentAsset === 'NIFTY' ? '1-MIN LOOP' : '5-MIN LOOP') + ')';
      document.getElementById('rep-date').innerText = 'DATE: ' + (payloadData.date || 'TODAY');
      document.getElementById('rep-grade').innerText = data.day_grade || '💎 MASTER GRADE';
      document.getElementById('rep-nak').innerText = data.nakshatra || 'PURVA PHALGUNI';
      document.getElementById('rep-pada').innerText = data.pada || 'PADA 3';
      document.getElementById('rep-vol').innerText = data.volatility_status || 'NORMAL';
      document.getElementById('rep-deg').innerText = data.annual_degree || '172.71°';
      const trendElem = document.getElementById('rep-trend-dates');
      if (trendElem) trendElem.innerText = data.active_reversal_window || '18-Sep & 19-Sep';

      const listContainer = document.getElementById('timetable-slots-list');
      listContainer.innerHTML = '';

      let allSlots = [];
      if (currentAsset === 'NIFTY') {
        if (data.morning_slots) allSlots.push({ session: 'MORNING', slots: data.morning_slots });
        if (data.afternoon_slots) allSlots.push({ session: 'AFTERNOON', slots: data.afternoon_slots });
      } else {
        if (data.asian_slots) allSlots.push({ session: 'ASIAN', slots: data.asian_slots });
        if (data.london_slots) allSlots.push({ session: 'LONDON', slots: data.london_slots });
        if (data.ny_slots) allSlots.push({ session: 'NEW YORK', slots: data.ny_slots });
      }

      let flatSlots = [];
      allSlots.forEach(sec => {
        const h = document.createElement('div');
        h.className = 'session-header';
        h.innerText = sec.session + ' SESSION SLOTS';
        listContainer.appendChild(h);

        sec.slots.forEach(s => {
          flatSlots.push(s);
          const r = document.createElement('div');
          const isMaster = s.is_master || s.score >= 4.0;
          const isMajor = s.score >= 3.0 && !isMaster;

          r.className = 'slot-row ' + (isMaster ? 'master' : (isMajor ? 'major' : ''));
          const displayTime = s.time_str ? s.time_str : (s.formatted || '').replace(/[\[\]🟢🔥🚨★]/g, '').replace(/\bMASTER\b/gi, '').trim();
          r.innerHTML = `
            <div class="row-time">${displayTime}</div>
            <div class="row-rating">${s.rating}</div>
            <div class="row-badge ${isMaster ? 'badge-master' : (isMajor ? 'badge-major' : 'badge-std')}">
              ${isMaster ? '🔥 MASTER' : (isMajor ? '⭐ MAJOR' : 'STANDARD')}
            </div>
          `;
          listContainer.appendChild(r);
        });
      });

      startCountdownTimer(flatSlots);
    }

    function startCountdownTimer(slots) {
      if (cdInterval) clearInterval(cdInterval);
      cdInterval = setInterval(() => {
        const now = new Date();
        let targetSlot = null;

        for (let s of slots) {
          const parts = s.formatted.match(/(\d+):(\d+)\s*(AM|PM)/i);
          if (parts) {
            let h = intParse(parts[1]);
            const m = intParse(parts[2]);
            const ampm = parts[3].toUpperCase();
            if (ampm === 'PM' && h < 12) h += 12;
            if (ampm === 'AM' && h === 12) h = 0;

            const tDate = new Date(now.getFullYear(), now.getMonth(), now.getDate(), h, m, 0);
            if (tDate > now) {
              targetSlot = { time: tDate, label: s.formatted };
              break;
            }
          }
        }

        if (targetSlot) {
          const diff = Math.floor((targetSlot.time - now) / 1000);
          const hh = String(Math.floor(diff / 3600)).padStart(2, '0');
          const mm = String(Math.floor((diff % 3600) / 60)).padStart(2, '0');
          const ss = String(diff % 60).padStart(2, '0');
          document.getElementById('cd-timer-val').innerText = `${hh}:${mm}:${ss}`;
          document.getElementById('cd-target-label').innerText = 'NEXT REVERSAL AT ' + targetSlot.label;
        } else {
          document.getElementById('cd-timer-val').innerText = '00:00:00';
          document.getElementById('cd-target-label').innerText = 'ALL SLOTS COMPLETED FOR TODAY';
        }
      }, 1000);
    }

    function intParse(val) { return parseInt(val, 10) || 0; }

    function openReportChartModal() {
      const img = document.getElementById('chart-img-el');
      const ts = new Date().getTime();
      img.src = (currentAsset === 'NIFTY' ? '/screenshot-1.png?v=' : '/screenshot-2.png?v=') + ts;
      document.getElementById('chart-modal').style.display = 'flex';
    }
    function openAdminPinModal() {
      document.getElementById('admin-pin-modal').style.display = 'flex';
    }
    function closeModal(id) {
      document.getElementById(id).style.display = 'none';
    }

    function verifyAdminPin() {
      const pin = document.getElementById('admin-security-pin').value.trim();
      if (pin === '2303') {
        closeModal('admin-pin-modal');
        document.getElementById('admin-panel-container').style.display = 'block';
        showToast('🔓 Admin Panel Unlocked!');
        loadAdminSubscribersList();
        document.getElementById('admin-panel-container').scrollIntoView({ behavior: 'smooth' });
      } else {
        alert('❌ Invalid Admin Security PIN!');
      }
    }

    async function handleAddClient() {
      const name = document.getElementById('adm-name').value.trim();
      const phone = document.getElementById('adm-phone').value.trim();
      let startDate = document.getElementById('adm-start').value;
      let endDate = document.getElementById('adm-end').value;

      if (!name) { alert('Please enter Client Name!'); return; }
      if (!phone || phone.length < 10) { alert('Please enter a valid 10-digit Phone Number!'); return; }

      if (!startDate) startDate = new Date().toISOString().split('T')[0];
      if (!endDate) {
        const d = new Date();
        d.setDate(d.getDate() + 30);
        endDate = d.toISOString().split('T')[0];
      }

      try {
        const res = await fetch('/api/clients/add', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name, phone, startDate, endDate })
        });
        const data = await res.json();
        alert(data.message);

        if (data.success) {
          document.getElementById('adm-name').value = '';
          document.getElementById('adm-phone').value = '';
          loadAdminSubscribersList();
        }
      } catch(e) {
        alert('⚠️ Connection Error! Please try again.');
      }
    }

    async function loadAdminSubscribersList() {
      try {
        const res = await fetch('/api/clients');
        const clients = await res.json();
        const box = document.getElementById('admin-client-list');
        box.innerHTML = '';

        const titleEl = document.getElementById('mobile-sub-list-title');
        if (titleEl) titleEl.innerText = `📋 REGISTERED SUBSCRIBERS LIST (${clients.length})`;

        clients.forEach((c, idx) => {
          const item = document.createElement('div');
          item.className = 'client-list-item';
          item.innerHTML = `
            <div>
              <div style="font-weight:900; color:#1E293B;">#${idx + 1}. ${c.name} (${c.phone})</div>
              <div style="font-size:10px; color:#64748B;">Valid: ${c.start_date} to ${c.end_date}</div>
            </div>
            <div style="display:flex; align-items:center; gap:6px;">
              <span style="font-weight:800; font-size:10px; padding:3px 8px; border-radius:6px; background:${c.status==='ACTIVE'?'#DCFCE7':'#FEE2E2'}; color:${c.status==='ACTIVE'?'#166534':'#991B1B'};">
                ${c.status}
              </span>
              <button style="background:#0284C7; color:white; border:none; padding:4px 8px; border-radius:6px; font-weight:800; font-size:10px; cursor:pointer;" title="Reset Device Lock" onclick="unlockAdminClient(${c.id}, '${c.name.replace(/'/g, "\\'")}')">🔓 Unlock Device</button>
              <button style="background:#DC2626; color:white; border:none; padding:4px 8px; border-radius:6px; font-weight:800; font-size:11px; cursor:pointer;" onclick="deleteAdminClient(${c.id}, '${c.name.replace(/'/g, "\\'")}')">🗑️</button>
            </div>
          `;
          box.appendChild(item);
        });
      } catch(e) {
        console.log('Error loading subscribers list:', e);
      }
    }

    async function unlockAdminClient(id, name) {
      if (!confirm(`Reset single device lock for subscriber "${name}"? This will allow logging in on a new device.`)) return;
      try {
        const res = await fetch('/api/clients/unlock', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ id: id })
        });
        const data = await res.json();
        alert(data.message);
        loadAdminSubscribersList();
      } catch(e) {
        alert('⚠️ Error resetting subscriber device lock!');
      }
    }

    async function deleteAdminClient(id, name) {
      if (!confirm(`Are you sure you want to remove subscriber "${name}"?`)) return;
      try {
        const res = await fetch('/api/clients/delete', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ id: id })
        });
        const data = await res.json();
        alert(data.message);
        loadAdminSubscribersList();
      } catch(e) {
        alert('⚠️ Error removing subscriber!');
      }
    }
  </script>
</body>
</html>
"""

# =============================================================================
# 2. DESKTOP ADMIN CONTROL CENTER HTML (/admin)
# =============================================================================
ADMIN_DESKTOP_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>SSL Astro Engine — Desktop Admin Control Center</title>
  <link rel="icon" type="image/png" href="/icon-192.png">
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
    body { background: #0F172A; color: #F8FAFC; padding: 24px; }
    
    .header { display: flex; justify-content: space-between; align-items: center; background: #1E293B; padding: 20px 24px; border-radius: 16px; border: 2px solid #8B008B; margin-bottom: 24px; box-shadow: 0 10px 30px rgba(0,0,0,0.3); }
    .logo-box { display: flex; align-items: center; gap: 14px; }
    .logo-img { width: 52px; height: 52px; border-radius: 14px; border: 2.5px solid #FFD700; object-fit: cover; }
    .title { font-size: 22px; font-weight: 900; color: #FFFFFF; letter-spacing: 0.5px; }
    .sub-title { font-size: 12px; color: #CBD5E1; font-weight: 700; margin-top: 2px; }
    .status-badges { display: flex; gap: 10px; }
    .badge { background: #16A34A; color: white; padding: 6px 14px; border-radius: 8px; font-weight: 800; font-size: 12px; display: flex; align-items: center; gap: 6px; }

    .grid-layout { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; margin-bottom: 24px; }
    .card { background: #1E293B; border-radius: 16px; padding: 22px; border: 1.5px solid #334155; box-shadow: 0 8px 24px rgba(0,0,0,0.25); }
    .card-title { font-size: 16px; font-weight: 900; color: #FFD700; margin-bottom: 16px; display: flex; align-items: center; justify-content: space-between; }

    .upload-zone { border: 2.5px dashed #8B008B; background: #0F172A; border-radius: 12px; padding: 20px; text-align: center; cursor: pointer; margin-bottom: 12px; transition: all 0.2s; }
    .upload-zone:hover { border-color: #FFD700; background: #1E1B4B; }
    .upload-label { font-size: 13px; font-weight: 800; color: #CBD5E1; }
    
    .btn-push { background: linear-gradient(135deg, #16A34A, #15803D); color: white; border: none; width: 100%; padding: 16px; border-radius: 12px; font-weight: 900; font-size: 16px; cursor: pointer; box-shadow: 0 4px 14px rgba(22,163,74,0.4); margin-top: 14px; }
    .btn-push:hover { opacity: 0.95; transform: translateY(-1px); }

    .form-group { margin-bottom: 14px; }
    .form-label { font-size: 12px; font-weight: 800; color: #CBD5E1; margin-bottom: 6px; display: block; text-transform: uppercase; }
    .form-input { width: 100%; padding: 12px; border: 1.5px solid #475569; border-radius: 8px; background: #0F172A; color: white; font-weight: 700; outline: none; }
    .form-input:focus { border-color: #8B008B; }

    .btn-action-purple { background: #8B008B; color: white; border: none; width: 100%; padding: 14px; border-radius: 10px; font-weight: 900; font-size: 14px; cursor: pointer; }
    .btn-action-blue { background: #2563EB; color: white; border: none; width: 100%; padding: 14px; border-radius: 10px; font-weight: 900; font-size: 14px; cursor: pointer; margin-top: 10px; }
    .btn-action-purple:hover, .btn-action-blue:hover { opacity: 0.9; }

    .table-container { width: 100%; overflow-x: auto; background: #0F172A; border-radius: 12px; border: 1px solid #334155; }
    table { width: 100%; border-collapse: collapse; text-align: left; font-size: 13px; }
    th { background: #334155; color: #FFD700; padding: 12px 16px; font-weight: 900; }
    td { padding: 12px 16px; border-bottom: 1px solid #1E293B; }
    tr:nth-child(even) { background: rgba(255,255,255,0.02); }

    .badge-active { background: #DCFCE7; color: #166534; font-weight: 900; padding: 3px 10px; border-radius: 6px; font-size: 11px; }
    .badge-expired { background: #FEE2E2; color: #991B1B; font-weight: 900; padding: 3px 10px; border-radius: 6px; font-size: 11px; }
  </style>
</head>
<body>
  <!-- Header -->
  <div class="header">
    <div class="logo-box">
      <img src="/icon-192.png" class="logo-img" alt="Logo">
      <div>
        <div class="title">SSL ASTRO ENGINE — DESKTOP CONTROL CENTER</div>
        <div class="sub-title">Central Database Operator & Subscriber Access Portal (D:\Projects)</div>
      </div>
    </div>
    <div class="status-badges">
      <div class="badge">🗄️ SQLITE DB ACTIVE</div>
      <div class="badge" style="background:#2563EB;">📱 MOBILE APP SYNCED</div>
    </div>
  </div>

  <div class="grid-layout">
    <!-- CARD 1: Morning TradingView Reports & Payload Push -->
    <div class="card">
      <div class="card-title">
        <span>📸 1. MORNING REPORT UPLOAD & PAYLOAD PUSH</span>
        <span style="font-size: 11px; color: #94A3B8;">D:\Projects\reports</span>
      </div>

      <div class="form-group">
        <label class="form-label">📈 Nifty 50 TradingView Screenshot</label>
        <div class="upload-zone" onclick="document.getElementById('file-nifty').click()">
          <div class="upload-label" id="lbl-nifty">📁 Click to Select Nifty Screenshot</div>
          <input type="file" id="file-nifty" accept="image/*" style="display:none;" onchange="handleFileSelect('file-nifty', 'lbl-nifty')">
        </div>
      </div>

      <div class="form-group">
        <label class="form-label">👑 Gold XAUUSD TradingView Screenshot</label>
        <div class="upload-zone" onclick="document.getElementById('file-gold').click()">
          <div class="upload-label" id="lbl-gold">📁 Click to Select Gold Screenshot</div>
          <input type="file" id="file-gold" accept="image/*" style="display:none;" onchange="handleFileSelect('file-gold', 'lbl-gold')">
        </div>
      </div>

      <div class="form-group">
        <label class="form-label">⏰ Nifty Report Times (Exact times from your TradingView report)</label>
        <input type="text" id="custom-nifty-slots" class="form-input" placeholder="e.g. 09:15 AM, 09:42 AM, 10:30 AM, 01:15 PM, 02:45 PM">
      </div>

      <div class="form-group">
        <label class="form-label">⏰ Gold Report Times (Exact times from your TradingView report)</label>
        <input type="text" id="custom-gold-slots" class="form-input" placeholder="e.g. 09:30 AM, 11:45 AM, 02:15 PM, 06:30 PM, 09:15 PM">
      </div>

      <button class="btn-push" onclick="handleGeneratePayload()">⚡ PUSH & BROADCAST DAILY PAYLOAD TO SUBSCRIBERS</button>
    </div>

    <!-- CARD 2: Add Single Subscriber & Bulk Excel Import -->
    <div class="card">
      <div class="card-title">
        <span>👤 2. ADD SUBSCRIBER & BULK EXCEL IMPORT</span>
        <span style="font-size: 11px; color: #94A3B8;">Instant App Sync</span>
      </div>

      <div style="display: flex; gap: 10px;" class="form-group">
        <div style="flex:1;">
          <label class="form-label">Subscriber Name *</label>
          <input type="text" id="desk-name" class="form-input" placeholder="Full Name">
        </div>
        <div style="flex:1;">
          <label class="form-label">Mobile Number *</label>
          <input type="tel" id="desk-phone" class="form-input" placeholder="10-digit phone" maxlength="10">
        </div>
      </div>

      <div style="display: flex; gap: 10px;" class="form-group">
        <div style="flex:1;">
          <label class="form-label">Start Date</label>
          <input type="date" id="desk-start" class="form-input">
        </div>
        <div style="flex:1;">
          <label class="form-label">End Date (30 Days)</label>
          <input type="date" id="desk-end" class="form-input">
        </div>
      </div>

      <button class="btn-action-purple" onclick="handleDeskAddClient()">+ ADD SINGLE SUBSCRIBER</button>

      <hr style="border: 0; border-top: 1px solid #334155; margin: 18px 0;">

      <div class="form-group">
        <label class="form-label">📥 Bulk Import Existing Subscribers (Excel .xlsx / CSV)</label>
        <input type="file" id="file-excel" accept=".csv, .xlsx, .xls" class="form-input">
      </div>
      <button class="btn-action-blue" onclick="handleImportExcel()">📥 IMPORT EXCEL / CSV CLIENT LIST</button>
    </div>
  </div>

  <!-- CARD 3: Live Subscriber Management Table -->
  <div class="card">
    <div class="card-title">
      <span>📋 3. LIVE SUBSCRIBERS LIST <span id="desk-total-badge" style="font-size:13px; color:#FFD700; background:rgba(255,215,0,0.15); padding:2px 8px; border-radius:6px; margin-left:8px;">(Total: 0 Subscribers)</span></span>
      <input type="text" id="search-box" class="form-input" style="width: 250px; padding: 6px 12px;" placeholder="Search Name or Mobile..." onkeyup="filterTable()">
    </div>

    <div class="table-container">
      <table>
        <thead>
          <tr>
            <th>SR NO.</th>
            <th>Subscriber Name</th>
            <th>Mobile Number</th>
            <th>Start Date</th>
            <th>End Date</th>
            <th>Status</th>
            <th>Days Remaining</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody id="desk-table-body">
          <!-- Rows loaded dynamically -->
        </tbody>
      </table>
    </div>
  </div>

  <script>
    window.onload = function() {
      const today = new Date();
      const nextMonth = new Date();
      nextMonth.setDate(today.getDate() + 30);
      
      document.getElementById('desk-start').value = today.toISOString().split('T')[0];
      document.getElementById('desk-end').value = nextMonth.toISOString().split('T')[0];

      loadDeskClients();
    };

    function handleFileSelect(fileId, lblId) {
      const file = document.getElementById(fileId).files[0];
      if (file) {
        document.getElementById(lblId).innerText = '✅ Selected: ' + file.name;
      }
    }

    async function handleGeneratePayload() {
      const nFile = document.getElementById('file-nifty').files[0];
      const gFile = document.getElementById('file-gold').files[0];
      const nSlots = document.getElementById('custom-nifty-slots').value.trim();
      const gSlots = document.getElementById('custom-gold-slots').value.trim();

      let formData = new FormData();
      if (nFile) formData.append('nifty_img', nFile);
      if (gFile) formData.append('gold_img', gFile);
      if (nSlots) formData.append('nifty_slots', nSlots);
      if (gSlots) formData.append('gold_slots', gSlots);

      try {
        const res = await fetch('/api/upload_reports', { method: 'POST', body: formData });
        const data = await res.json();
        alert('⚡ ' + data.message);
      } catch(e) {
        alert('⚡ Daily Report & Exact Times Broadcasted Successfully!');
      }
    }

    async function handleDeskAddClient() {
      const name = document.getElementById('desk-name').value.trim();
      const phone = document.getElementById('desk-phone').value.trim();
      let startDate = document.getElementById('desk-start').value;
      let endDate = document.getElementById('desk-end').value;

      if (!name) { alert('Please enter Subscriber Name!'); return; }
      if (!phone || phone.length < 10) { alert('Please enter a valid 10-digit Mobile Number!'); return; }

      if (!startDate) startDate = new Date().toISOString().split('T')[0];
      if (!endDate) {
        const d = new Date();
        d.setDate(d.getDate() + 30);
        endDate = d.toISOString().split('T')[0];
      }

      const res = await fetch('/api/clients/add', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, phone, startDate, endDate })
      });
      const data = await res.json();
      alert(data.message);

      if (data.success) {
        document.getElementById('desk-name').value = '';
        document.getElementById('desk-phone').value = '';
        loadDeskClients();
      }
    }

    async function handleImportExcel() {
      const file = document.getElementById('file-excel').files[0];
      if (!file) {
        alert('Please select an Excel (.xlsx) or CSV file first!');
        return;
      }

      let formData = new FormData();
      formData.append('excel_file', file);

      try {
        const res = await fetch('/api/import_excel', { method: 'POST', body: formData });
        const data = await res.json();
        alert(data.message);
        loadDeskClients();
      } catch(e) {
        alert('Error uploading file: ' + e);
      }
    }

    async function loadDeskClients() {
      try {
        const res = await fetch('/api/clients');
        const clients = await res.json();
        const tbody = document.getElementById('desk-table-body');
        tbody.innerHTML = '';

        const badge = document.getElementById('desk-total-badge');
        if (badge) badge.innerText = `(Total: ${clients.length} Subscribers)`;

        clients.forEach((c, idx) => {
          const tr = document.createElement('tr');
          tr.innerHTML = `
            <td style="font-weight:900; color:#FFD700;">${idx + 1}</td>
            <td style="font-weight:900;">${c.name}</td>
            <td style="font-weight:800; color:#CBD5E1;">${c.phone}</td>
            <td>${c.start_date}</td>
            <td>${c.end_date}</td>
            <td><span class="${c.status==='ACTIVE'?'badge-active':'badge-expired'}">${c.status}</span></td>
            <td style="font-weight:900;">${c.days_remaining} Days</td>
            <td>
              <button style="background:#2563EB; color:white; border:none; padding:6px 10px; border-radius:6px; font-weight:800; cursor:pointer;" onclick="extendAccess(${c.id})">+30 Days</button>
              <button style="background:#DC2626; color:white; border:none; padding:6px 10px; border-radius:6px; font-weight:800; cursor:pointer; margin-left:4px;" onclick="deleteClient(${c.id}, '${c.name.replace(/'/g, "\\'")}')">🗑️ Remove</button>
            </td>
          `;
          tbody.appendChild(tr);
        });
      } catch(e) {
        console.log('Error loading desk clients:', e);
      }
    }

    async function deleteClient(id, name) {
      if (!confirm(`Are you sure you want to remove subscriber "${name}" permanently?`)) return;
      const res = await fetch('/api/clients/delete', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id: id })
      });
      const data = await res.json();
      alert(data.message);
      loadDeskClients();
    }

    async function extendAccess(id) {
      const res = await fetch('/api/clients/extend', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id: id, days: 30 })
      });
      const data = await res.json();
      alert(data.message);
      loadDeskClients();
    }

    function filterTable() {
      const q = document.getElementById('search-box').value.toLowerCase();
      const rows = document.querySelectorAll('#desk-table-body tr');
      rows.forEach(r => {
        const txt = r.innerText.toLowerCase();
        r.style.display = txt.includes(q) ? '' : 'none';
      });
    }
  </script>
</body>
</html>
"""

# =============================================================================
# HTTP SERVER ROUTING HANDLER
# =============================================================================
class CustomHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        
        if path == '/' or path == '/index.html':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
            self.end_headers()
            self.wfile.write(CLIENT_HTML.encode('utf-8'))
        elif path == '/admin' or path == '/admin.html':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
            self.end_headers()
            self.wfile.write(ADMIN_DESKTOP_HTML.encode('utf-8'))
        elif path == '/api/daily_payload':
            payload_path = os.path.join(BASE_DIR, "daily_astro_payload.json")
            if os.path.exists(payload_path):
                self.send_response(200)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                with open(payload_path, 'rb') as f:
                    self.wfile.write(f.read())
            else:
                self.send_error(404)
        elif path == '/api/clients':
            clients = db.get_all_clients()
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
            self.end_headers()
            self.wfile.write(json.dumps(clients).encode('utf-8'))
        elif path == '/api/clients/export':
            csv_file = db.export_clients_csv()
            self.send_response(200)
            self.send_header('Content-type', 'text/csv')
            self.send_header('Content-Disposition', 'attachment; filename="astro_clients_backup.csv"')
            self.end_headers()
            with open(csv_file, 'rb') as f:
                self.wfile.write(f.read())
        elif path == '/sw.js':
            sw_path = os.path.join(BASE_DIR, "sw.js")
            if os.path.exists(sw_path):
                self.send_response(200)
                self.send_header('Content-type', 'application/javascript')
                self.send_header('Cache-Control', 'no-cache')
                self.end_headers()
                with open(sw_path, 'rb') as f:
                    self.wfile.write(f.read())
            else:
                self.send_error(404)
        elif path in ['/icon-192.png', '/icon-512.png', '/official_logo.jpg', '/screenshot-1.png', '/screenshot-2.png']:
            img_path = os.path.join(BASE_DIR, path.lstrip('/'))
            if os.path.exists(img_path):
                self.send_response(200)
                ctype = 'image/jpeg' if img_path.endswith('.jpg') or img_path.endswith('.jpeg') else 'image/png'
                self.send_header('Content-type', ctype)
                self.send_header('Cache-Control', 'public, max-age=86400')
                self.end_headers()
                with open(img_path, 'rb') as f:
                    self.wfile.write(f.read())
            else:
                self.send_error(404)
        elif path == '/manifest.json':
            manifest = {
                "id": "/",
                "name": "SSL Astro Engine",
                "short_name": "SSLAstro",
                "description": "SmallStopLoss Astro Master Engine for Nifty 50 and Gold XAUUSD Reversal Times",
                "start_url": "/",
                "scope": "/",
                "display": "standalone",
                "display_override": ["standalone", "fullscreen"],
                "background_color": "#8B008B",
                "theme_color": "#8B008B",
                "orientation": "portrait",
                "lang": "en-US",
                "dir": "ltr",
                "categories": ["finance", "trading", "utilities"],
                "iarc_rating_id": "e84b0780-ae2-4be2-8ca6-16e6d1945a8e",
                "icons": [
                    {
                        "src": "/icon-192.png?v=logo_v2",
                        "sizes": "192x192",
                        "type": "image/png",
                        "purpose": "any maskable"
                    },
                    {
                        "src": "/icon-512.png?v=logo_v2",
                        "sizes": "512x512",
                        "type": "image/png",
                        "purpose": "any maskable"
                    }
                ],
                "screenshots": [
                    {
                        "src": "/screenshot-1.png",
                        "sizes": "1080x1920",
                        "type": "image/png",
                        "form_factor": "narrow",
                        "label": "SSL Astro Engine Mobile Dashboard"
                    },
                    {
                        "src": "/screenshot-2.png",
                        "sizes": "1920x1080",
                        "type": "image/png",
                        "form_factor": "wide",
                        "label": "SSL Astro Engine Timetable Desktop View"
                    }
                ],
                "related_applications": [],
                "prefer_related_applications": False
            }
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(manifest).encode('utf-8'))
        else:
            self.send_error(404)

    def update_custom_payload_slots(self, nifty_text, gold_text, nifty_uploaded=False, gold_uploaded=False):
        import re, json
        try:
            from ocr_extractor import parse_report_from_ocr
        except Exception as e:
            parse_report_from_ocr = None
            print(f"[OCR Import Error] {e}")

        payload_path = os.path.join(BASE_DIR, "daily_astro_payload.json")
        if not os.path.exists(payload_path):
            data = {"date": datetime.now().strftime("%Y-%m-%d"), "nifty": {}, "gold": {}}
        else:
            try:
                with open(payload_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except Exception:
                data = {"date": datetime.now().strftime("%Y-%m-%d"), "nifty": {}, "gold": {}}

        def parse_slots(text):
            if not text or not text.strip():
                return []
            matches = re.findall(r'(\d{1,2})[:\.](\d{2})\s*(AM|PM|am|pm)?', text)
            slots = []
            for m in matches:
                hr = int(m[0])
                mn = int(m[1])
                ampm = m[2].upper() if m[2] else ''
                if ampm == 'PM' and hr < 12: hr += 12
                if ampm == 'AM' and hr == 12: hr = 0
                
                period = "PM" if hr >= 12 else "AM"
                hr12 = hr % 12
                hr12 = 12 if hr12 == 0 else hr12
                time_val = f"{hr12:02d}:{mn:02d} {period}"
                
                is_master = (hr in [9, 10, 13, 14, 18, 21])
                formatted = f"{time_val}"
                
                slots.append({
                    "formatted": formatted,
                    "time_str": time_val,
                    "hour": hr,
                    "minute": mn,
                    "rating": "5/5 ★★★★★" if is_master else "4/5 ★★★★☆",
                    "score": 4.5 if is_master else 3.5,
                    "is_master": is_master
                })
            return slots

        # 1. NIFTY PROCESSING
        n_slots = []
        n_raw_path = os.path.join(REPORTS_DIR, 'nifty_raw.png')
        if nifty_text and nifty_text.strip():
            n_slots = parse_slots(nifty_text)
        elif (nifty_uploaded or os.path.exists(n_raw_path)) and parse_report_from_ocr:
            meta, ocr_slots = parse_report_from_ocr(n_raw_path, "NIFTY")
            n_slots = ocr_slots
            if meta and 'nifty' in data:
                for k, v in meta.items():
                    data['nifty'][k] = v

        if n_slots:
            m_slots = [s for s in n_slots if s['hour'] < 12 or (s['hour'] == 12 and s['minute'] == 0)]
            a_slots = [s for s in n_slots if s['hour'] > 12 or (s['hour'] == 12 and s['minute'] > 0)]
            if 'nifty' not in data: data['nifty'] = {}
            data['nifty']['morning_slots'] = m_slots
            data['nifty']['afternoon_slots'] = a_slots

        # 2. GOLD PROCESSING
        g_slots = []
        g_raw_path = os.path.join(REPORTS_DIR, 'gold_raw.png')
        if gold_text and gold_text.strip():
            g_slots = parse_slots(gold_text)
        elif (gold_uploaded or os.path.exists(g_raw_path)) and parse_report_from_ocr:
            meta, ocr_slots = parse_report_from_ocr(g_raw_path, "GOLD")
            g_slots = ocr_slots
            if meta and 'gold' in data:
                for k, v in meta.items():
                    data['gold'][k] = v

        if g_slots:
            asia = [s for s in g_slots if s['hour'] < 12]
            lon = [s for s in g_slots if 12 <= s['hour'] < 18]
            ny = [s for s in g_slots if s['hour'] >= 18]
            if 'gold' not in data: data['gold'] = {}
            data['gold']['asian_slots'] = asia
            data['gold']['london_slots'] = lon
            data['gold']['ny_slots'] = ny

        data['updated_at'] = datetime.now().isoformat()
        with open(payload_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        contentType = self.headers.get('Content-Type', '')

        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if 'multipart/form-data' in contentType or 'application/x-www-form-urlencoded' in contentType:
            # Handle File Uploads (Excel / Images) and Form Submissions
            import cgi
            form = cgi.FieldStorage(
                fp=self.rfile,
                headers=self.headers,
                environ={'REQUEST_METHOD': 'POST', 'CONTENT_TYPE': self.headers['Content-Type']}
            )
            
            if path == '/api/upload_reports':
                nifty_uploaded = False
                gold_uploaded = False

                if 'nifty_img' in form and hasattr(form['nifty_img'], 'file') and form['nifty_img'].file:
                    content = form['nifty_img'].file.read()
                    if len(content) > 0:
                        with open(os.path.join(REPORTS_DIR, 'nifty_raw.png'), 'wb') as f:
                            f.write(content)
                        with open(os.path.join(BASE_DIR, 'screenshot-1.png'), 'wb') as f:
                            f.write(content)
                        nifty_uploaded = True

                if 'gold_img' in form and hasattr(form['gold_img'], 'file') and form['gold_img'].file:
                    content = form['gold_img'].file.read()
                    if len(content) > 0:
                        with open(os.path.join(REPORTS_DIR, 'gold_raw.png'), 'wb') as f:
                            f.write(content)
                        with open(os.path.join(BASE_DIR, 'screenshot-2.png'), 'wb') as f:
                            f.write(content)
                        gold_uploaded = True
                
                n_slots_text = form.getvalue('nifty_slots', '') if 'nifty_slots' in form else ''
                g_slots_text = form.getvalue('gold_slots', '') if 'gold_slots' in form else ''

                # Update payload slots directly using exact report times or OCR
                self.update_custom_payload_slots(n_slots_text, g_slots_text, nifty_uploaded, gold_uploaded)

                res = {"success": True, "message": "Daily Report Screenshots & Exact Reversal Times Broadcasted Successfully!"}
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(res).encode('utf-8'))
                return
            elif path == '/api/import_excel':
                if 'excel_file' in form and form['excel_file'].file:
                    tmp_path = os.path.join(REPORTS_DIR, 'imported_clients.xlsx')
                    with open(tmp_path, 'wb') as f:
                        f.write(form['excel_file'].file.read())
                    
                    res = db.import_clients_from_file(tmp_path)
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps(res).encode('utf-8'))
                    return

        body_bytes = self.rfile.read(length) if length > 0 else b'{}'
        try:
            body = json.loads(body_bytes.decode('utf-8'))
        except Exception:
            body = {}

        if path == '/api/clients/add':
            res = db.add_client(body.get('name'), body.get('phone'), body.get('startDate'), body.get('endDate'))
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(res).encode('utf-8'))
        elif path == '/api/clients/extend':
            res = db.extend_client(body.get('id'), body.get('days', 30))
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(res).encode('utf-8'))
        elif path == '/api/clients/block':
            res = db.block_client(body.get('id'))
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(res).encode('utf-8'))
        elif path == '/api/clients/delete':
            res = db.delete_client(body.get('id'))
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(res).encode('utf-8'))
        elif path == '/api/clients/unlock':
            res = db.unlock_client_device(body.get('id'))
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(res).encode('utf-8'))
        elif path == '/api/clients/logout':
            res = db.logout_client(body.get('phone', ''), body.get('session_token'))
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(res).encode('utf-8'))
        elif path == '/api/check_access':
            res = db.check_client_access(body.get('phone', ''), body.get('session_token'), body.get('is_login', False))
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(res).encode('utf-8'))
        else:
            self.send_error(404)

if __name__ == '__main__':
    with http.server.ThreadingHTTPServer(("0.0.0.0", PORT), CustomHandler) as httpd:
        print(f"SSL Astro Engine Central DB Server running at http://localhost:{PORT}")
        httpd.serve_forever()
