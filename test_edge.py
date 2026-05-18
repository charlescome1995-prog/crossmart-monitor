import subprocess, time, urllib.request, json, os

port = 9223
exe = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
EDGE_PROFILE_DIR = os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\User Data")
print("EXE exists:", os.path.exists(exe))
print("Profile dir:", EDGE_PROFILE_DIR)
print("Profile dir exists:", os.path.exists(EDGE_PROFILE_DIR))

args = [
    exe,
    "--user-data-dir=" + EDGE_PROFILE_DIR,
    "--remote-debugging-port=" + str(port),
    "--remote-allow-origins=*",
    "--no-first-run",
    "--no-default-browser-check",
    "--new-window",
    "about:blank",
]
print("Running:", " ".join(args))
proc = subprocess.Popen(args)
print("PID:", proc.pid)
time.sleep(10)

deadline = time.time() + 15
while time.time() < deadline:
    try:
        req = urllib.request.urlopen("http://127.0.0.1:%d/json" % port, timeout=3)
        tabs = json.loads(req.read())
        print("SUCCESS! %d tabs" % len(tabs))
        for t in tabs[:3]:
            print("  ", t.get("title","?")[:60], "|", t.get("url","?")[:80])
        break
    except Exception as e:
        print("  try fail:", e)
        time.sleep(2)
else:
    print("FAILED to connect after timeout")
    # 检查进程
    import psutil
    try:
        p = psutil.Process(proc.pid)
        print("Process status:", p.status())
        print("Process cmdline:", p.cmdline())
    except:
        print("Process not found")
