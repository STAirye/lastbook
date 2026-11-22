#!/bin/bash
# PR 6 check, inside debian:13-slim: build lastbook-llm from PR 6's tree, run --embed, compare with the fork's earlier build.
set -euo pipefail
t0=$(date +%s); step() { echo "== $(( $(date +%s) - t0 ))s $*"; }
export DEBIAN_FRONTEND=noninteractive
step apt
apt-get update -qq
apt-get install -y -qq --no-install-recommends git ca-certificates build-essential cmake ninja-build glslc libvulkan-dev spirv-headers \
  libvulkan1 libgomp1 python3 binutils >/out/apt3.log 2>&1
step build
mkdir -p /w/pr6 && tar -xf /out/pr6.tar -C /w/pr6 && cd /w/pr6
find . -name '*.sh' -exec sed -i 's/$//' {} +
bash packaging/llm/build_llm_linux.sh > /out/build-pr6.log 2>&1 || { tail -40 /out/build-pr6.log; exit 1; }
tail -5 /out/build-pr6.log
mkdir -p /w/m && cp /out/model/bge-small-en-v1.5-q8_0.gguf /w/m/
REQ='{"op":"embed","id":1,"texts":["he is not breathing","how do i boil an egg","my toddler drank bleach and is throwing up"],"max_tokens":320}'
run() {  # $1 runner, $2 output
  { printf '%s\n' "$REQ"; sleep 8; printf '%s\n' '{"op":"quit"}'; } | timeout 60 "$1" --model /w/m/bge-small-en-v1.5-q8_0.gguf --embed --cpu-only --threads 2 > "$2" 2>"$2.err" || echo "exit $?"
}
step run-pr6;  run derived/llm/bin-linux/lastbook-llm /out/embed-pr6.out
step run-fork; mkdir -p /w/fork && cp -a /out/bin-linux/. /w/fork/ && run /w/fork/lastbook-llm /out/embed-fork.out
step done
