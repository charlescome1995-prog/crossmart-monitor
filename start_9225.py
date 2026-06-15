import subprocess, time, urllib.request, json, os, sys

exe = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
args = [
    exe,
    "--remote-debugging-port=9225",
    "--remote-allow-origins=*",
    "about:blank",
]
p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
print(f"Started Edge, pid={p.pid}")
time.sleep(12)
rc = p.poll()
print(f"Exit code: {rc}")
if rc is not None:
    stdout = p.stdout.read().decode('utf-8', errors='replace')
    stderr = p.stderr.read().decode('utf-8', errors='replace')
    print(f"STDOUT: {stdout[:500]}")
    print(f"STDERR: {stderr[:500]}")
else:
    try:
        req = urllib.request.urlopen("http://127.0.0.1:9225/json", timeout=5)
        tabs = json.loads(req.read())
        print(f"9225 OK: {len(tabs)} tabs")
    except Exception as e:
        print(f"9225 not ready: {e}")