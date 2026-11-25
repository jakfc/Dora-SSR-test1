import io, json, os, subprocess, sys, time
PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DORA = os.environ.get('DORA_EXE', r'C:\Users\jakfc\AppData\Local\Programs\Dora SSR\Dora.exe')
ASSET = os.path.dirname(DORA)
REQ = os.path.join(PROJ, 'tools', '_anim_req.json')
code = io.open(os.path.join(PROJ, 'tools', '_probe_anim.lua'), encoding='utf-8').read()
io.open(REQ, 'w', encoding='utf-8').write(json.dumps({'mode':'lua','code':code,'timeoutSeconds':30}))
pv = subprocess.Popen([DORA,'--asset',ASSET,'cli','agent','preview','-p',PROJ,'--entry','init_game','--capture-at','4,7,10'],
                      cwd=PROJ, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(6)
raw = ''
for i in range(8):
    r = subprocess.run([DORA,'--asset',ASSET,'cli','agent','command','-p',PROJ,'--input',REQ],
                       cwd=PROJ, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    raw = r.stdout.decode('utf-8','replace')
    if '"output"' in raw:
        break
    time.sleep(1)
pv.wait()
io.open(os.path.join(PROJ,'tools','_anim_out.json'),'w',encoding='utf-8').write(raw)
sys.stdout.write(raw[:6000].encode('ascii','replace').decode('ascii') + '\n')
