#!/usr/bin/env python3
import csv, json, hashlib
from datetime import datetime, timezone
from pathlib import Path
from collections import Counter

ROOT = Path('.')
DATA = ROOT / 'data'
TS = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
OUT_CSV = DATA / f'geohazard_news_v2_candidate_{TS}.csv'
OUT_META = DATA / f'geohazard_news_v2_candidate_{TS}_meta.json'
OUT_REVIEW = DATA / f'geohazard_news_v2_candidate_{TS}_perlu_review.csv'
OUT_DIFF = DATA / f'geohazard_news_v2_candidate_{TS}_diff.csv'
OUT_VAL = DATA / f'geohazard_news_v2_candidate_{TS}_validation.md'

SRC = DATA / 'geohazard_news.csv'
SRC_LOC = DATA / 'geohazard_news_located.csv'
EXISTING_V2 = DATA / 'geohazard_news_v2.csv'

for p in [OUT_CSV, OUT_META, OUT_REVIEW, OUT_DIFF, OUT_VAL]:
    if p.exists():
        raise SystemExit('CONFLICT')

def sha256(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()

h_src_before = sha256(SRC)
h_srcloc_before = sha256(SRC_LOC)

with open(SRC, encoding='utf-8-sig', newline='') as f:
    rows = list(csv.DictReader(f))

OLD = rows
NEW = []
for r in OLD:
    nr = dict(r)
    nr['record_id'] = 'GHV2-' + hashlib.sha256((r.get('url','')+r.get('judul','')+r.get('published_time','')).encode('utf-8')).hexdigest()[:16]
    nr['event_id'] = ''
    src = (r.get('sumber') or '').strip()
    url = r.get('url') or ''
    if src == 'BMKG':
        if '/alerts/' in url:
            nr['data_type'] = ''
            nr['data_type_status'] = 'perlu_review'
            nr['source_type'] = 'resmi_indonesia'
            nr['source_id'] = 'bmkg_nowcast_id'
        elif 'Gempa' in (r.get('judul') or '') or (r.get('kategori') or '').startswith('Gempa'):
            nr['data_type'] = 'official_event_report'
            nr['data_type_status'] = 'terverifikasi'
            nr['source_type'] = 'resmi_indonesia'
            nr['source_id'] = 'bmkg_gempa_dirasakan'
        else:
            nr['data_type'] = 'official_event_report'
            nr['data_type_status'] = 'terverifikasi'
            nr['source_type'] = 'resmi_indonesia'
            nr['source_id'] = 'bmkg_unknown'
    elif src == 'USGS':
        nr['data_type'] = 'official_event_report'
        nr['data_type_status'] = 'terverifikasi'
        nr['source_type'] = 'internasional_pendukung'
        nr['source_id'] = 'usgs_m45'
    elif src == 'GDACS':
        nr['data_type'] = 'official_event_report'
        nr['data_type_status'] = 'terverifikasi'
        nr['source_type'] = 'internasional_pendukung'
        nr['source_id'] = 'gdacs_all'
    else:
        nr['data_type'] = 'news_article'
        nr['data_type_status'] = 'terverifikasi'
        nr['source_type'] = 'berita'
        nr['source_id'] = src.lower().replace(' ', '_')
    kat_old = r.get('kategori','')
    katv = kat_old
    nr['kategori_v2'] = katv
    nr['kategori_utama'] = ''
    if katv == 'Kebakaran Hutan dan Lahan':
        nr['dalam_cakupan'] = 'tidak'
        nr['alasan_cakupan'] = 'di luar 8 kategori: Kebakaran Hutan dan Lahan'
    elif katv == 'Cuaca Ekstrem':
        nr['dalam_cakupan'] = 'tidak'
        nr['alasan_cakupan'] = 'di luar 8 kategori: Cuaca Ekstrem'
    elif katv == 'Lainnya':
        nr['dalam_cakupan'] = 'tidak'
        nr['alasan_cakupan'] = 'di luar 8 kategori: Lainnya'
    else:
        nr['dalam_cakupan'] = 'ya'
        nr['alasan_cakupan'] = 'dalam cakupan 8 kategori'
        nr['kategori_utama'] = katv
    nr['kategori_berubah'] = 'ya' if katv != kat_old else 'tidak'
    nr['event_time'] = ''
    nr['event_time_status'] = 'kosong'
    nr['event_time_sumber'] = ''
    nr['event_time_raw'] = ''
    nr['event_date'] = ''
    nr['published_time_asal'] = r.get('published_time','')
    nr['event_time_asal'] = r.get('event_time','')
    nr['published_time_status'] = 'terverifikasi' if r.get('published_time') else 'tidak_tersedia'
    nr['published_time_sumber'] = 'RSS/Feed'
    nr['collected_at'] = ''
    nr['collected_at_status'] = 'tidak_tersedia'
    nr['latitude'] = ''
    nr['longitude'] = ''
    nr['koordinat_status'] = 'tidak_ada'
    nr['koordinat_sumber'] = ''
    nr['location_status'] = 'tidak_ada'
    nr['location_confidence'] = 'none'
    nr['location_catatan'] = ''
    nr['location_sumber'] = ''
    if src == 'USGS':
        nr['filter_indonesia'] = 'perlu_review'
        nr['filter_indonesia_alasan'] = 'perlu hitung bbox'
    elif src == 'GDACS':
        nr['filter_indonesia'] = 'tidak_diterapkan'
        nr['filter_indonesia_alasan'] = ''
    else:
        nr['filter_indonesia'] = 'tidak_diterapkan'
        nr['filter_indonesia_alasan'] = ''
    nr['duplikat_judul'] = 'tidak'
    nr['duplikat_url'] = 'tidak'
    nr['duplikat_dengan'] = ''
    if '/alerts/' in url:
        nr['status_akses_sumber'] = 'dilarang_robots'
    else:
        nr['status_akses_sumber'] = 'diizinkan'
    alasan = []
    if nr['data_type'] == '':
        alasan.append('data_type_belum_pasti')
    if '/alerts/' in url:
        alasan.append('sumber_dilarang_robots')
    if nr['event_time'] == '':
        alasan.append('event_time_tidak_terverifikasi')
    nr['perlu_review'] = 'ya' if alasan else 'tidak'
    nr['alasan_review'] = ';'.join(alasan)
    nr['catatan_proses'] = ''
    NEW.append(nr)

cols = list(OLD[0].keys()) + ['record_id','event_id','data_type','data_type_status','source_type','source_id','kategori_v2','kategori_utama','dalam_cakupan','alasan_cakupan','kategori_berubah','event_time_status','event_time_sumber','event_time_raw','event_date','published_time_status','published_time_sumber','published_time_asal','event_time_asal','collected_at','collected_at_status','latitude','longitude','koordinat_status','koordinat_sumber','location_status','location_confidence','location_catatan','location_sumber','filter_indonesia','filter_indonesia_alasan','duplikat_judul','duplikat_url','duplikat_dengan','status_akses_sumber','perlu_review','alasan_review','catatan_proses']

with open(OUT_CSV, 'w', encoding='utf-8-sig', newline='') as f:
    w = csv.DictWriter(f, fieldnames=cols)
    w.writeheader()
    for n in NEW:
        w.writerow({k: n.get(k, '') for k in cols})

h_src_after = sha256(SRC)
h_srcloc_after = sha256(SRC_LOC)

with open(OUT_REVIEW, 'w', encoding='utf-8-sig', newline='') as f:
    w = csv.DictWriter(f, fieldnames=cols)
    w.writeheader()
    for n in NEW:
        if n.get('perlu_review') == 'ya':
            w.writerow({k: n.get(k, '') for k in cols})

diff_cols = ['url','judul','sumber','kategori','kategori_v2','kategori_berubah','dalam_cakupan','alasan_cakupan','event_time','event_time_status','published_time','location_status','location_confidence','data_type','source_type','filter_indonesia','perlu_review','alasan_review']
with open(OUT_DIFF, 'w', encoding='utf-8-sig', newline='') as f:
    w = csv.DictWriter(f, fieldnames=diff_cols)
    w.writeheader()
    for n in NEW:
        w.writerow({k: n.get(k, '') for k in diff_cols})

meta = {
    'fase': 'Fase 1 - kandidat non-destruktif',
    'timestamp_utc': TS,
    'source': str(SRC),
    'source_loc': str(SRC_LOC),
    'existing_v2': str(EXISTING_V2),
    'hash_source_before': h_src_before,
    'hash_source_loc_before': h_srcloc_before,
    'hash_source_after': h_src_after,
    'hash_source_loc_after': h_srcloc_after,
    'source_unchanged': h_src_before == h_src_after and h_srcloc_before == h_srcloc_after,
    'input_rows': len(OLD),
    'output_rows': len(NEW),
    'output_csv': str(OUT_CSV),
    'output_review': str(OUT_REVIEW),
    'output_diff': str(OUT_DIFF)
}
with open(OUT_META, 'w', encoding='utf-8') as f:
    json.dump(meta, f, indent=2)

def cnt(col):
    return dict(Counter((x.get(col) or '') for x in NEW))

val = []
val.append('# Validasi Fase 1')
val.append(f'- Timestamp: {TS}')
val.append(f'- Input: {len(OLD)} rows')
val.append(f'- Output: {len(NEW)} rows')
val.append(f'- Sumber tidak berubah: {meta["source_unchanged"]}')
val.append(f'- Hash sumber sebelum: {h_src_before}')
val.append(f'- Hash sumber sesudah: {h_src_after}')
val.append('')
val.append('## Per kategori lama'); val.append(json.dumps(cnt('kategori'), indent=2))
val.append('## Per kategori_v2'); val.append(json.dumps(cnt('kategori_v2'), indent=2))
val.append('## Dalam cakupan'); val.append(json.dumps(cnt('dalam_cakupan'), indent=2))
val.append('## Alasan cakupan'); val.append(json.dumps(cnt('alasan_cakupan'), indent=2))
val.append('## data_type'); val.append(json.dumps(cnt('data_type'), indent=2))
val.append('## perlu_review'); val.append(json.dumps(cnt('perlu_review'), indent=2))
val.append('## alasan_review'); val.append(json.dumps(cnt('alasan_review'), indent=2))
val.append('## filter_indonesia'); val.append(json.dumps(cnt('filter_indonesia'), indent=2))
val.append('## lokasi'); val.append(json.dumps(cnt('location_status'), indent=2))
val.append('## duplikasi'); val.append(json.dumps(cnt('duplikat_judul'), indent=2))
with open(OUT_VAL, 'w', encoding='utf-8') as f:
    f.write('\n'.join(val))

print('done')
print(OUT_CSV)
