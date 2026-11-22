import os, sys, json
root = sys.argv[1]; out = {}
for d, _, fs in os.walk(root, followlinks=True):
    parts = set(d.replace(os.sep, '/').split('/'))
    if parts & {'cache', 'logs'}:
        continue
    for f in fs:
        p = os.path.join(d, f)
        try:
            st = os.stat(p); out[p] = (st.st_size, st.st_mtime_ns)
        except OSError:
            pass
with open(sys.argv[2], 'w', encoding='utf-8') as fh:
    json.dump(out, fh)
print(len(out))
