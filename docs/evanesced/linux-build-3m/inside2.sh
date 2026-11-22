#!/bin/bash
# Second pass, inside debian:13-slim: reuse the runner built in pass 1, check --embed, build the .deb.
set -euo pipefail
t0=$(date +%s); step() { echo "== $(( $(date +%s) - t0 ))s $*"; }
export DEBIAN_FRONTEND=noninteractive
step apt
apt-get update -qq
apt-get install -y -qq --no-install-recommends git ca-certificates libvulkan1 libgomp1 build-essential cmake ninja-build glslc libvulkan-dev spirv-headers \
  python3 python3-venv python3-pil dpkg-dev binutils file gcc libc6-dev pkg-config libgstreamer1.0-dev >/out/apt2.log 2>&1
git config --global --add safe.directory '*'
git clone -q /src /w/lastbook && cd /w/lastbook && git log -1 --oneline
mkdir -p derived/release
if [ -x /out/bin-linux/lastbook-llm ]; then mkdir -p derived/llm/bin-linux && cp -a /out/bin-linux/. derived/llm/bin-linux/
else step runner; bash packaging/llm/build_llm_linux.sh; mkdir -p /out/bin-linux && cp -a derived/llm/bin-linux/. /out/bin-linux/; fi
cp /out/packs-manifest-v1.json derived/release/manifest-v1.json
step embed-check
mkdir -p /w/m && cp /src/derived/models/meaning-red/bge-small-en-v1.5-q8_0.gguf /w/m/
{ printf '%s\n' '{"op":"embed","id":1,"texts":["he is not breathing","how do i boil an egg"],"max_tokens":320}'; sleep 30; } \
  | timeout 60 derived/llm/bin-linux/lastbook-llm --model /w/m/bge-small-en-v1.5-q8_0.gguf --embed --cpu-only --threads 2 > /out/embed.out 2>/out/embed.err || true
python3 - <<'PY'
import json
for line in open('/out/embed.out', encoding='utf-8'):
    try: ev = json.loads(line)
    except ValueError: continue
    if ev.get('ev') in ('ready', 'error'): print(ev.get('ev'), {k: ev[k] for k in ev if k in ('embed', 'desc', 'code', 'msg')})
    if ev.get('ev') == 'embedding':
        v = ev['vectors']; a, b = v
        print('embedding:', len(v), 'vectors of', len(a), 'norm', round(sum(x*x for x in a) ** .5, 4), 'cos', round(sum(x*y for x, y in zip(a, b)), 4))
PY
step app
bash packaging/linux/build_app_linux.sh > /out/app-build.log 2>&1 || { tail -30 /out/app-build.log; exit 1; }
tail -8 /out/app-build.log
cp -L derived/app-build/linux/latest.deb /out/ && ls -la /out/latest.deb
step done
