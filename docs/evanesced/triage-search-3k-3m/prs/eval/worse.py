"""Questions that got worse (first_ok lost, useful to 0, wrong sense first gained). argv: before after"""
import json, sys
b = {(r['set'], r['id']): r for r in json.load(open(sys.argv[1], encoding='utf-8'))['rows'] if 'useful' in r}
a = {(r['set'], r['id']): r for r in json.load(open(sys.argv[2], encoding='utf-8'))['rows'] if 'useful' in r}
for k in b:
    x, y = b[k], a.get(k)
    if not y:
        continue
    flags = []
    if x.get('first_ok') and not y.get('first_ok'):
        flags.append('lost first')
    if not x.get('first_ok') and y.get('first_ok'):
        flags.append('GAINED first')
    if x['useful'] > 0 and y['useful'] == 0:
        flags.append('to zero')
    if not x.get('wrong_sense_first') and y.get('wrong_sense_first'):
        flags.append('wrong sense first')
    if flags and k[0] == 'triage':
        print(k, x.get('colour'), x.get('typo'), flags, repr(x['q'])[:60], x['useful'], '->', y['useful'])
        print('   before:', x['titles'][:3])
        print('   after :', y['titles'][:3])
