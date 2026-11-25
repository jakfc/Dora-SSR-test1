# -*- coding: utf-8 -*-
"""把 _probe_bottom.lua 送进运行中的引擎，列出地平线以下的节点。"""
import io, json, os, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DORA = r'C:\Users\jakfc\AppData\Local\Programs\Dora SSR\Dora.exe'
ASSET = r'C:/Users/jakfc/AppData/Local/Programs/Dora SSR'
REQ = os.path.join(ROOT, 'tools', '_bottom_req.json')

code = io.open(os.path.join(ROOT, 'tools', '_probe_bottom.lua'), encoding='utf-8').read()
json.dump({'mode': 'lua', 'code': code, 'timeoutSeconds': 60},
          io.open(REQ, 'w', encoding='utf-8'))
r = subprocess.run([DORA, '--asset', ASSET, 'cli', 'agent', 'command',
                    '-p', ROOT, '--input', REQ],
                   capture_output=True, text=True, encoding='utf-8', errors='replace')
raw = (r.stdout or '') + (r.stderr or '')
out = io.open(os.path.join(ROOT, 'docs', '_bottom_dump.txt'), 'w', encoding='utf-8')
try:
    data = json.loads(raw[raw.index('{'):])
    txt = data.get('result') or data.get('output') or json.dumps(data)
except Exception:
    txt = raw
lines = [l for l in str(txt).split('\n') if 'LOW' in l]
out.write('\n'.join(lines))
out.close()
print('lines=%d' % len(lines))
for l in lines[:60]:
    print(l)
