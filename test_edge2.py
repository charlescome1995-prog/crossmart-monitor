import subprocess, os, time, urllib.request, json

CDP_PORT = 9225
exe = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

# 不指定 --user-data-dir，让Edge自动用默认的
args = [
    exe,
    "--remote-debugging-port=%d" % CDP_PORT,
    "--remote-allow-origins=*",
    "--no-first-run",
    "--no-default-browser-check",
    "--new-window",
    "about:blank",
]
print("Running:", " ".join(a for a in args if not a.startswith("--") or True))
proc = subprocess.Popen(args)
print("PID:", proc.pid)

deadline = time.time() + 20
while time.time() < deadline:
    try:
        r = urllib.request.urlopen("http://127.0.0.1:%d/json" % CDP_PORT, timeout=3)
        tabs = json.loads(r.read())
        print("SUCCESS! %d tabs" % len(tabs))
        for t in tabs[:3]:
            print("  '%s' | %s" % (t.get('title','?')[:60], t.get('url','?')[:80]))
        break
    except Exception as e:
        time.sleep(2)
else:
    print("FAILED")
