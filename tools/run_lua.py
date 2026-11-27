# -*- coding: utf-8 -*-
"""把任意 tools/*.lua 送进正在运行的 Dora 引擎里执行，打印输出。

用法：
    python tools/run_lua.py tools/_probe_hud3.lua

引擎要先跑起来（端口 8866），否则会报连接失败。
"""
import io
import json
import os
import subprocess
import sys

PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DORA = r'C:\Users\jakfc\AppData\Local\Programs\Dora SSR\Dora.exe'
ASSET = r'C:/Users/jakfc/AppData/Local/Programs/Dora SSR'
REQ = os.path.join(PROJ, 'tools', '_run_lua_req.json')


def main():
    if len(sys.argv) < 2:
        print('用法: python tools/run_lua.py tools/xxx.lua')
        return
    lua = sys.argv[1]
    if not os.path.isabs(lua):
        lua = os.path.join(PROJ, lua)
    code = io.open(lua, encoding='utf-8').read()
    io.open(REQ, 'w', encoding='utf-8').write(
        json.dumps({'mode': 'lua', 'code': code, 'timeoutSeconds': 90}))
    p = subprocess.run([DORA, '--asset', ASSET, 'cli', 'agent', 'command',
                        '-p', PROJ, '--input', REQ],
                       capture_output=True)
    out = p.stdout.decode('utf-8', 'replace')
    try:
        data = json.loads(out[out.index('{'):out.rindex('}') + 1])
    except Exception:
        print(out)
        return
    print(data.get('output', data))
    if data.get('message'):
        print('!! %s' % data['message'])


if __name__ == '__main__':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
    main()
