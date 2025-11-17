from flask import Flask, render_template, jsonify, request, send_file, abort
import os, io, csv, json, time, subprocess, signal

from dotenv import load_dotenv
from db import latest_points, points_between, list_dates

CONFIG_PATH = "config.json"

def default_config():
    return {"temp": True, "dist": True, "light": True, "sample_time": 2.0}

def load_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH) as f:
            return json.load(f)
    return default_config()

def save_config(cfg):
    with open(CONFIG_PATH, "w") as f:
        json.dump(cfg, f, indent=2)

load_dotenv()
app = Flask(__name__)

# --------- Monitor process control ---------
def get_collector_dir():
    default_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "collector"))
    return os.environ.get("COLLECTOR_DIR", default_dir)

def pid_file():
    return os.path.join(get_collector_dir(), "monitor.pid")

def log_file():
    return os.path.join(get_collector_dir(), "monitor.log")

def is_running(pid:int)->bool:
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False

def current_pid():
    try:
        with open(pid_file(), "r") as f:
            pid = int(f.read().strip())
            return pid if is_running(pid) else None
    except Exception:
        return None

def stop_monitor(timeout=5):
    pid = current_pid()
    if not pid:
        return False
    try:
        os.kill(pid, signal.SIGTERM)
    except ProcessLookupError:
        return False
    # wait up to timeout seconds
    t0 = time.time()
    while time.time() - t0 < timeout:
        if not is_running(pid):
            break
        time.sleep(0.2)
    if is_running(pid):
        try:
            os.kill(pid, signal.SIGKILL)
        except Exception:
            pass
    return True

def start_monitor():
    cdir = get_collector_dir()
    os.makedirs(cdir, exist_ok=True)
    # open log file
    lf = open(log_file(), "a+", buffering=1)
    env = os.environ.copy()
    # ensure ENV_CONFIG_PATH points to config.json in project root
    env.setdefault("ENV_CONFIG_PATH", os.path.abspath(CONFIG_PATH))
    # spawn
    p = subprocess.Popen(
        ["python3", "monitor.py"],
        cwd=cdir,
        stdout=lf, stderr=lf,
        env=env,
        start_new_session=True
    )
    with open(pid_file(), "w") as f:
        f.write(str(p.pid))
    return p.pid

@app.route('/')
def index():
    return render_template('index.html', title='Introduction')

@app.route('/operation')
def operation():
    db_path = os.environ.get("ENV_DB_PATH", os.path.abspath("./gpu.sqlite"))
    cfg = load_config()
    mon_status = {"pid": current_pid(), "collector_dir": get_collector_dir(), "log": log_file()}
    return render_template('operation.html', title='Operation', db_path=db_path, cfg=cfg, mon_status=mon_status)

@app.route('/monitor')
def monitor():
    return render_template('monitor.html', title='Monitoring')

@app.route('/history')
def history():
    dates = list_dates()
    return render_template('history.html', title='History', dates=dates)

# ======== Data APIs ========
@app.get('/api/latest')
def api_latest():
    n = int(request.args.get('n', 180))
    data = latest_points(n)
    return jsonify({'data': data})

@app.get('/api/range')
def api_range():
    date = request.args.get('date')
    start = request.args.get('start')
    end = request.args.get('end')
    if date:
        start = f"{date} 00:00:00"
        end   = f"{date} 23:59:59"
    if not (start and end):
        abort(400, 'Missing date/start/end')
    data = points_between(start, end)
    return jsonify({'data': data})

@app.get('/api/export_csv')
def api_export_csv():
    date = request.args.get('date')
    if not date:
        abort(400, 'Missing date')
    start = f"{date} 00:00:00"
    end   = f"{date} 23:59:59"
    rows = points_between(start, end)

    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(['ts','light','temperature','distance'])
    for r in rows:
        w.writerow([r.get('ts'), r.get('light'), r.get('temperature'), r.get('distance')])

    mem = io.BytesIO(out.getvalue().encode('utf-8'))
    return send_file(mem, as_attachment=True, download_name=f"env_{date}.csv", mimetype='text/csv')

# ---- Config APIs ----
@app.get('/api/get_config')
def get_config():
    return jsonify(load_config())

@app.post('/api/update_config')
def update_config():
    data = request.get_json(force=True) or {}
    cfg = load_config()
    cfg['temp']  = bool(data.get('temp', cfg['temp']))
    cfg['dist']  = bool(data.get('dist', cfg['dist']))
    cfg['light'] = bool(data.get('light', cfg['light']))
    try:
        cfg['sample_time'] = float(data.get('sample_time', cfg['sample_time']))
    except Exception:
        pass
    save_config(cfg)
    return jsonify({"status": "ok", "config": cfg})

# ---- Monitor control APIs ----
@app.get('/api/monitor_status')
def api_monitor_status():
    return jsonify({"pid": current_pid(), "collector_dir": get_collector_dir(), "log": log_file()})

@app.post('/api/restart_monitor')
def api_restart_monitor():
    # optional: update COLLECTOR_DIR from body
    body = request.get_json(silent=True) or {}
    if 'collector_dir' in body:
        os.environ['COLLECTOR_DIR'] = body['collector_dir']
    stopped = stop_monitor()
    pid = start_monitor()
    return jsonify({"stopped": stopped, "pid": pid})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
