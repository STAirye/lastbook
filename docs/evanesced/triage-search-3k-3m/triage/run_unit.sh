# usage: run_unit.sh ROOT OUTFILE
cd "$1"
: > "$2"
for f in app/tests/test_*.py; do n=$(basename $f .py); out=$(timeout 900 python -B -X utf8 -m unittest app.tests.$n 2>&1); rc=$?; summ=$(echo "$out" | grep -E '^(Ran |OK|FAILED)' | tr '\n' ' '); echo "$n rc=$rc $summ" >> "$2"; if [ $rc -ne 0 ]; then echo "$out" | grep -E -A6 '^(ERROR|FAIL):' | head -40 >> "$2"; echo "$out" | tail -5 >> "$2"; fi; done
echo DONE >> "$2"
