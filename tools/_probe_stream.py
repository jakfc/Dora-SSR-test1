import io, json, os, subprocess, sys, time
PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DORA = os.environ.get('DORA_EXE', r'C:\Users\jakfc\AppData\Local\Programs\Dora SSR\Dora.exe')
ASSET = os.path.dirname(DORA)
REQ = os.path.join(PROJ, 'tools', '_stream_req.json')
code = io.open(os.path.join(PROJ, 'tools', '_probe_stream.lua'), encoding='utf-8').read()
io.open(REQ, 'w', encoding='utf-8').write(json.dumps({'mode': 'lua', 'code': code, 'timeoutSeconds': 60}))
pv = subprocess.Popen([DORA, '--asset', ASSET, 'cli', 'agent', 'preview', '-p', PROJ,
                       '--entry', 'init_game', '--capture-at', '4,7,9'],
                      cwd=PROJ, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(8)
r = subprocess.run([DORA, '--asset', ASSET, 'cli', 'agent', 'command', '-p', PROJ, '--input', REQ],
                   cwd=PROJ, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=180)
pv.wait()
sys.stdout.write(r.stdout.decode('utf-8', 'replace')[:4000])
