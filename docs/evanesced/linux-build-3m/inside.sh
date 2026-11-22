#!/bin/bash
# Runs inside debian:13-slim: builds lastbook-llm and the .deb from a clean clone of the fork's committed HEAD.
set -euo pipefail
t0=$(date +%s); step() { echo "== $(( $(date +%s) - t0 ))s $*"; }
export DEBIAN_FRONTEND=noninteractive
step apt
apt-get update -qq
apt-get install -y -qq --no-install-recommends git ca-certificates build-essential cmake ninja-build glslc libvulkan-dev spirv-headers \
  python3 python3-venv python3-pil dpkg-dev binutils file gcc pkg-config libgstreamer1.0-dev >/out/apt.log 2>&1
git config --global --add safe.directory '*'
step clone
git clone -q /src /w/lastbook && cd /w/lastbook && git log -1 --oneline
step runner
bash packaging/llm/build_llm_linux.sh
ls -la derived/llm/bin-linux
cp derived/llm/cmake-linux.log derived/llm/build-linux.log /out/ 2>/dev/null || true
step embed-check
mkdir -p /w/m && cp /src/derived/models/meaning-red/bge-small-en-v1.5-q8_0.gguf /w/m/
printf '%s\n' '{"op":"embed","id":1,"texts":["he is not breathing","how do i boil an egg"],"max_tokens":320}' \
  | timeout 120 derived/llm/bin-linux/lastbook-llm --model /w/m/bge-small-en-v1.5-q8_0.gguf --embed --cpu-only --threads 2 > /out/embed.out 2>/out/embed.err || true
python3 - <<'PY'
import json
for line in open('/out/embed.out', encoding='utf-8'):
    try: ev = json.loads(line)
    except ValueError: continue
    if ev.get('ev') == 'ready': print('ready:', {k: ev[k] for k in ev if k in ('ev', 'embed', 'desc', 'n_ctx')})
    if ev.get('ev') == 'embedding':
        v = ev['vectors']; print('embedding:', len(v), 'vectors of', len(v[0]), 'norm', round(sum(x*x for x in v[0]) ** .5, 4))
PY
step app
bash packaging/linux/build_app_linux.sh 2>&1 | tail -40
step copy
mkdir -p /out/bin-linux && cp -a derived/llm/bin-linux/. /out/bin-linux/
cp -L derived/app-build/linux/latest.deb /out/ && ls -la /out/*.deb
step done
