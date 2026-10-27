#!/usr/bin/env python3
"""kakomon.actabit.net 用の暗号化データを作る。
usage: KAKOMON_PASSWORD='...' [KAKOMON_SALT_HEX=...] python3 -I build_public.py --questions questions.jsonl [--record 臨床心理系入試問題_収集記録.json] --out dist/
出力: dist/data.bin（AES-256-GCM, 鍵 = PBKDF2-SHA256(password, salt, ITER)）, dist/info.json（件数など非機密）
data.bin の形式: b"KKM1" + salt(16) + iter(uint32 BE) + iv(12) + ciphertext(gzip(JSON))+tag
"""
import argparse, gzip, json, os, struct, datetime, collections, hashlib
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
ITER = 310000
KEEP = ['id', 'univ', 'school', 'year', 'held', 'course', 'session', 'subject', 'qno', 'qtype', 'field', 'field2',
        'keywords', 'text', 'official', 'official_type', 'points', 'choices', 'note']
ap = argparse.ArgumentParser(); ap.add_argument('--questions', required=True); ap.add_argument('--record'); ap.add_argument('--out', required=True)
a = ap.parse_args()
pw = os.environ.get('KAKOMON_PASSWORD', '')
assert len(pw) >= 10, 'KAKOMON_PASSWORD (10文字以上) を環境変数で渡してください'
src = {}
if a.record and os.path.exists(a.record):
    rec = json.load(open(a.record, encoding='utf-8'))
    for f in rec.get('files', []):
        ref = (f.get('references') or [{}])[0]
        src[f['drive_file_id']] = {'pdf': f.get('url', ''), 'page': ref.get('source_page', ''), 'label': ref.get('label', '')}
Q = []
for line in open(a.questions, encoding='utf-8'):
    if not line.strip(): continue
    r = json.loads(line)
    o = {k: r.get(k, '') for k in KEEP}
    s = src.get(r.get('file_id'), {})
    o['pdf'] = s.get('pdf', ''); o['page'] = s.get('page', '')
    Q.append(o)
content_sha = hashlib.sha256(json.dumps(Q, ensure_ascii=False, sort_keys=True).encode('utf-8')).hexdigest()[:16]
info = {'updated': datetime.date.today().isoformat(), 'content_sha': content_sha, 'n_records': len(Q), 'n_universities': len({q['univ'] for q in Q}),
        'n_official': sum(1 for q in Q if q['official']), 'n_with_link': sum(1 for q in Q if q['pdf'])}
payload = gzip.compress(json.dumps({'info': info, 'q': Q}, ensure_ascii=False, separators=(',', ':')).encode('utf-8'), 9)
prev = os.path.join(a.out, 'data.bin')
salt = None
if os.path.exists(prev):                      # 同じソルトを使い回し、保存済みログインを月次更新後も有効にする
    with open(prev, 'rb') as f:
        h = f.read(20)
    if h[:4] == b'KKM1': salt = h[4:20]
if os.environ.get('KAKOMON_SALT_HEX'):          # 明示指定があれば最優先（月次更新で同じソルトを使う）
    salt = bytes.fromhex(os.environ['KAKOMON_SALT_HEX'])
salt = salt or os.urandom(16); iv = os.urandom(12)
key = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=ITER).derive(pw.encode('utf-8'))
ct = AESGCM(key).encrypt(iv, payload, b'KKM1')
os.makedirs(a.out, exist_ok=True)
with open(os.path.join(a.out, 'data.bin'), 'wb') as f:
    f.write(b'KKM1' + salt + struct.pack('>I', ITER) + iv + ct)
json.dump(info, open(os.path.join(a.out, 'info.json'), 'w', encoding='utf-8'), ensure_ascii=False)
print(info, 'data.bin', len(ct) + 36, 'bytes')
