import io, json, os, subprocess, sys, time
PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DORA = os.environ.get('DORA_EXE', r'C:\Users\jakfc\AppData\Local\Programs\Dora SSR\Dora.exe')
ASSET = os.path.dirname(DORA)
code = io.open(os.path.join(PROJ, 'tools', '_probe_anim2.lua'), encoding='utf-8').read()
REQ = os.path.join(PROJ, 'tools', '_anim2_req.json')
io.open(REQ, 'w', encoding='utf-8').write(json.dumps({'mode':'lua','code':code,'timeoutSeconds':60}))
pv = subprocess.Popen([DORA,'--asset',ASSET,'cli','agent','preview','-p',PROJ,'--entry','init_game','--capture-at','5,9,10'],
                      cwd=PROJ, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(7)
for k in range(4):
    r = subprocess.run([DORA,'--asset',ASSET,'cli','agent','command','-p',PROJ,'--input',REQ],
                       cwd=PROJ, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    raw = r.stdout.decode('utf-8','replace')
    try:
        print('SAMPLE', k, ':', json.loads(raw).get('output','').strip()[:400])
    except Exception:
        print('SAMPLE', k, ':', raw[:300])
    time.sleep(1.1)
pv.wait()
