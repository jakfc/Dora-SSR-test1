# -*- coding: utf-8 -*-
"""跑起来 → 问一次「每个带 tag 的挂点实际画多大」，用来核对素材和人的比例。"""
import io, json, os, subprocess, sys, time
PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DORA = os.environ.get('DORA_EXE', r'C:\Users\jakfc\AppData\Local\Programs\Dora SSR\Dora.exe')
ASSET = os.path.dirname(DORA)
REQ = os.path.join(PROJ, 'tools', '_scale_req.json')
OUT = os.path.join(PROJ, 'docs', '_scale_dump.txt')
def run(a, **kw):
    return subprocess.run([DORA, '--asset', ASSET] + a, cwd=PROJ, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, **kw)
def main():
    code = io.open(os.path.join(PROJ, 'tools', '_probe_scale.lua'), encoding='utf-8').read()
    io.open(REQ, 'w', encoding='utf-8').write(json.dumps({'mode': 'lua', 'code': code, 'timeoutSeconds': 60}))
    p = subprocess.Popen([DORA, '--asset', ASSET, 'cli', 'agent', 'preview', '-p', PROJ, '--entry', 'init_game'],
                         cwd=PROJ, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(7)
    r = run(['cli', 'agent', 'command', '-p', PROJ, '--input', REQ])
    p.wait()
    raw = r.stdout.decode('utf-8', 'replace')
    try:
        data = json.loads(raw[raw.index('{'):])
    except Exception:
        sys.stdout.write(raw[:1500]); return 1
    out = data.get('output', '')
    io.open(OUT, 'w', encoding='utf-8').write(out)
    print('success=%s lines=%d -> %s' % (data.get('success'), len(out.splitlines()), OUT))
    return 0
if __name__ == '__main__':
    sys.exit(main())
