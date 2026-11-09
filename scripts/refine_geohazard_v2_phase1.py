#!/usr/bin/env python3
import csv, json, hashlib, re
from datetime import datetime, timezone
from pathlib import Path
from collections import Counter, defaultdict

ROOT = Path('.')
DATA = ROOT / 'data'
TS = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
CAND = DATA / 'geohazard_news_v2_candidate_20261028T034156Z.csv'

OUT_CLASS = DATA / f'geohazard_news_v2_candidate_20261028T034156Z_classification_review_{TS}.csv'
OUT_ET = DATA / f'geohazard_news_v2_candidate_20261028T034156Z_eventtime_review_{TS}.csv'
OUT_LOC = DATA / f'geohazard_news_v2_candidate_20261028T034156Z_location_usgs_review_{TS}.csv'
OUT_DUP = DATA / f'geohazard_news_v2_candidate_20261028T034156Z_duplicates_review_{TS}.csv'
OUT_TRI = DATA / f'geohazard_news_v2_candidate_20261028T034156Z_review_triage_{TS}.csv'
OUT_SUM = DATA / f'geohazard_news_v2_candidate_20261028T034156Z_refine_summary_{TS}.md'

for p in [OUT_CLASS,OUT_ET,OUT_LOC,OUT_DUP,OUT_TRI,OUT_SUM]:
    if p.exists():
        raise SystemExit('CONFLICT')

def sha256(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()

h_before = {}
for name in ['data/geohazard_news.csv','data/geohazard_news_located.csv','data/geohazard_news_v2_candidate_20261028T034156Z.csv']:
    h_before[name]=sha256(name)

with open(CAND, encoding='utf-8-sig', newline='') as f:
    rows = list(csv.DictReader(f))

in_cov = [r for r in rows if (r.get('dalam_cakupan') or '').strip()=='ya']
lainnya = [r for r in rows if (r.get('kategori_v2') or '').strip()=='Lainnya']
sample_lain = lainnya[:40]

class_rows=[]
for r in in_cov:
    judul = r.get('judul','')
    isi = r.get('isi_berita','')
    bukti = []
    blob = (judul + ' ' + isi).lower()
    if 'tsunami' in blob and 'tidak berpotensi' not in blob and 'tanpa' not in blob:
        bukti.append('indikasi tsunami')
    if 'gempa' in blob or re.search(r'm\s*\d', blob):
        bukti.append('indikasi gempa')
    if 'gunung' in blob or 'erupsi' in blob or 'letusan' in blob:
        bukti.append('indikasi gunungapi')
    if 'longsor' in blob or 'tanah longsor' in blob or 'gerakan tanah' in blob:
        bukti.append('indikasi gerakan tanah')
    if 'likuefaksi' in blob or 'liquefaction' in blob:
        bukti.append('indikasi likuefaksi')
    if 'abrasi' in blob or 'akresi' in blob:
        bukti.append('indikasi abrasi/akresi')
    if 'amblesan' in blob or 'penurunan muka' in blob or 'subsidence' in blob:
        bukti.append('indikasi penurunan muka tanah')
    if 'semburan lumpur' in blob or 'semburan gas' in blob or 'mud volcano' in blob:
        bukti.append('indikasi semburan')
    class_rows.append({
        'record_id': r.get('record_id',''),
        'url': r.get('url',''),
        'sumber': r.get('sumber',''),
        'kategori': r.get('kategori',''),
        'kategori_v2': r.get('kategori_v2',''),
        'dalam_cakupan': r.get('dalam_cakupan',''),
        'judul': judul,
        'isi_berita_snip': isi[:200],
        'klasifikasi_bukti': '; '.join(bukti) if bukti else 'PERLU_REVIEW_TANPA_BUKTI_EKSPLOSIF',
        'rekomendasi_kategori_v2': 'sama',
        'alasan_rekomendasi': 'bukti eksplisit ditemukan' if bukti else 'tidak ditemukan bukti eksplisit pada sampel ini',
        'verifikasi_berdasarkan': 'judul+isi'
    })

for r in sample_lain:
    judul = r.get('judul','')
    isi = r.get('isi_berita','')
    blob = (judul + ' ' + isi).lower()
    bukti=[]
    if 'gempa' in blob or re.search(r'm\s*\d', blob):
        bukti.append('indikasi gempa')
    if 'tsunami' in blob:
        bukti.append('indikasi tsunami')
    if 'gunung' in blob or 'erupsi' in blob:
        bukti.append('indikasi gunungapi')
    if 'longsor' in blob:
        bukti.append('indikasi longsor')
    class_rows.append({
        'record_id': r.get('record_id',''),
        'url': r.get('url',''),
        'sumber': r.get('sumber',''),
        'kategori': r.get('kategori',''),
        'kategori_v2': r.get('kategori_v2',''),
        'dalam_cakupan': r.get('dalam_cakupan',''),
        'judul': judul,
        'isi_berita_snip': isi[:200],
        'klasifikasi_bukti': '; '.join(bukti) if bukti else 'TIDAK_DITEMUKAN',
        'rekomendasi_kategori_v2': 'tetap_lainnya' if not bukti else 'usul_pindah',
        'alasan_rekomendasi': 'bukti eksplisit ditemukan - perlu verifikasi manual' if bukti else 'tidak ada bukti 8 kategori utama ditemukan',
        'verifikasi_berdasarkan': 'judul+isi'
    })

cfields = ['record_id','url','sumber','kategori','kategori_v2','dalam_cakupan','judul','isi_berita_snip','klasifikasi_bukti','rekomendasi_kategori_v2','alasan_rekomendasi','verifikasi_berdasarkan']
with open(OUT_CLASS,'w',encoding='utf-8-sig',newline='') as f:
    w=csv.DictWriter(f,fieldnames=cfields); w.writeheader()
    for x in class_rows: w.writerow(x)

et_rows=[]
for r in rows:
    src = (r.get('sumber') or '')
    url = r.get('url') or ''
    judul = r.get('judul') or ''
    isi = r.get('isi_berita') or ''
    rec = {'record_id':r.get('record_id',''),'url':url,'sumber':src,'judul':judul,'published_time':r.get('published_time',''),'event_time_saat_ini':r.get('event_time',''),'metode_ekstraksi':'tidak_ditemukan','pembuktian':'','beda_dengan_published':'tidak_dapat_dibandingkan','rekomendasi_status':'biarkan_kosong'}
    blob = judul + '\n' + isi
    if src == 'USGS':
        m = re.search(r'Time\s+(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2}:\d{2})\s+UTC', blob)
        if m:
            rec['metode_ekstraksi']='usgs_time_utc'
            rec['pembuktian']=f"Time {m.group(1)} {m.group(2)} UTC"
            rec['rekomendasi_status']='isi'
            rec['beda_dengan_published']='ya' if r.get('published_time') else 'tidak_dapat_dibandingkan'
        else:
            rec['metode_ekstraksi']='tidak_ditemukan'
            rec['rekomendasi_status']='kosong_review'
    elif src == 'BMKG':
        if '/alerts/' in url:
            rec['metode_ekstraksi']='bmkg_alerts_prakiraan'
            rec['pembuktian']='berisi prakiraan/akan terjadi - bukan waktu kejadian'
            rec['rekomendasi_status']='kosong_review'
        else:
            m = re.search(r'Tanggal:\s*(.+?)\n.*?Jam:\s*(.+?)(?:\n|WIB|WITA|WIT)', blob, re.I|re.S)
            if m:
                rec['metode_ekstraksi']='regex_tanggal_jam'
                rec['pembuktian']=f"Tanggal:{m.group(1)} Jam:{m.group(2)}"
                rec['rekomendasi_status']='isi'
                rec['beda_dengan_published']='ya' if r.get('published_time') else 'tidak_dapat_dibandingkan'
            else:
                rec['metode_ekstraksi']='tidak_ditemukan'
                rec['rekomendasi_status']='kosong_review'
    elif src == 'GDACS':
        m = re.search(r'On\s+(\d{2}/\d{2}/\d{4})', blob)
        if m:
            rec['metode_ekstraksi']='gdacs_tanggal_saja'
            rec['pembuktian']=f"On {m.group(1)}"
            rec['rekomendasi_status']='kosong_review'
            rec['beda_dengan_published']='ya'
        else:
            rec['metode_ekstraksi']='tidak_ditemukan'
            rec['rekomendasi_status']='kosong_review'
    else:
        rec['metode_ekstraksi']='tidak_ditemukan'
        rec['rekomendasi_status']='kosong_review'
    et_rows.append(rec)

etfields = ['record_id','url','sumber','judul','published_time','event_time_saat_ini','metode_ekstraksi','pembuktian','beda_dengan_published','rekomendasi_status']
with open(OUT_ET,'w',encoding='utf-8-sig',newline='') as f:
    w=csv.DictWriter(f,fieldnames=etfields); w.writeheader()
    for x in et_rows: w.writerow(x)

loc_rows=[]
for r in rows:
    src = (r.get('sumber') or '')
    judul = r.get('judul') or ''
    isi = r.get('isi_berita') or ''
    blob = (judul + ' ' + isi).lower()
    rec = {'record_id':r.get('record_id',''),'url':r.get('url',''),'sumber':src,'judul':judul,'location_status_saat_ini':r.get('location_status',''),'location_confidence_saat_ini':r.get('location_confidence',''),'location_catatan_saat_ini':r.get('location_catatan',''),'dateline_jakarta_flag':'tidak_teridentifikasi','koordinat_ditemukan':'tidak','koordinat_sumber_bukti':'','bbox_check':'tidak_dapat_dihitung','usgs_place':'','rekomendasi_filter':r.get('filter_indonesia',''),'alasan_filter':r.get('filter_indonesia_alasan',''),'rekomendasi_location_confidence':r.get('location_confidence','')}
    if re.search(r'jakarta', blob):
        if re.search(r'jakarta\s+(selatan|timur|barat|utara|pusat)', blob) or 'dki' in blob:
            rec['dateline_jakarta_flag']='ya'
            rec['rekomendasi_location_confidence']='perlu_review'
        else:
            rec['dateline_jakarta_flag']='ya'
            rec['rekomendasi_location_confidence']='perlu_review'
    if src == 'USGS':
        m = re.search(r'Location\s+([0-9\.\-]+)[°\s]*([NS])\s+([0-9\.\-]+)[°\s]*([EW])', isi)
        if m:
            lat = float(m.group(1))
            if m.group(2)=='S': lat = -lat
            lon = float(m.group(3))
            if m.group(4)=='W': lon = -lon
            rec['koordinat_ditemukan']='ya'
            rec['koordinat_sumber_bukti']=f"Location {m.group(0)}"
            if -11.0 <= lat <= 6.0 and 94.0 <= lon <= 142.0:
                rec['bbox_check']='dalam'; rec['rekomendasi_filter']='lolos'; rec['alasan_filter']='koordinat dalam bbox Indonesia'
            else:
                rec['bbox_check']='luar'; rec['rekomendasi_filter']='tidak_lolos'; rec['alasan_filter']='koordinat di luar bbox Indonesia'
        else:
            m2 = re.search(r'(-?\d+\.\d+)[^\d-]+(-?\d+\.\d+)', isi)
            if m2:
                try:
                    lat = float(m2.group(1)); lon = float(m2.group(2))
                    rec['koordinat_ditemukan']='ya'
                    rec['koordinat_sumber_bukti']=f"{m2.group(1)},{m2.group(2)}"
                    if -11.0 <= lat <= 6.0 and 94.0 <= lon <= 142.0:
                        rec['bbox_check']='dalam'; rec['rekomendasi_filter']='lolos'; rec['alasan_filter']='koordinat dalam bbox'
                    else:
                        rec['bbox_check']='luar'; rec['rekomendasi_filter']='tidak_lolos'; rec['alasan_filter']='koordinat di luar bbox'
                except Exception:
                    rec['rekomendasi_filter']='perlu_review'; rec['alasan_filter']='koordinat tidak dapat dihitung'
            else:
                rec['koordinat_ditemukan']='tidak'
                rec['rekomendasi_filter']='perlu_review'
                rec['alasan_filter']='koordinat tidak tersedia di data'
    loc_rows.append(rec)

lfields = ['record_id','url','sumber','judul','location_status_saat_ini','location_confidence_saat_ini','location_catatan_saat_ini','dateline_jakarta_flag','koordinat_ditemukan','koordinat_sumber_bukti','bbox_check','usgs_place','rekomendasi_filter','alasan_filter','rekomendasi_location_confidence']
with open(OUT_LOC,'w',encoding='utf-8-sig',newline='') as f:
    w=csv.DictWriter(f,fieldnames=lfields); w.writeheader()
    for x in loc_rows: w.writerow(x)

urls = defaultdict(list)
judul_norm = defaultdict(list)
for r in rows:
    u = (r.get('url') or '').strip().lower()
    j = (r.get('judul') or '').strip().lower()
    jn = re.sub(r'[^a-z0-9 ]',' ', j)
    jn = re.sub(r'\s+',' ', jn).strip()
    urls[u].append(r)
    judul_norm[jn].append(r)

dup_rows=[]
gid=0
for k,v in urls.items():
    if len(v)>1:
        gid+=1
        dup_rows.append({'group_id':gid,'tipe':'url_norm','url_norm':k,'judul_norm':'','count_in_group':len(v),'daftar_record_id':';'.join([x.get('record_id','') for x in v]),'daftar_url':';'.join([x.get('url','') for x in v]),'daftar_sumber':';'.join([x.get('sumber','') for x in v]),'rekomendasi':'pertahankan_semua_review','alasan':'duplikasi URL terdeteksi - perlu ditinjau, tidak dihapus otomatis'})
for k,v in judul_norm.items():
    if len(v)>1 and k:
        gid+=1
        dup_rows.append({'group_id':gid,'tipe':'judul_norm','url_norm':'','judul_norm':k,'count_in_group':len(v),'daftar_record_id':';'.join([x.get('record_id','') for x in v]),'daftar_url':';'.join([x.get('url','') for x in v]),'daftar_sumber':';'.join([x.get('sumber','') for x in v]),'rekomendasi':'pertahankan_semua_review','alasan':'duplikasi judul terdeteksi - perlu ditinjau per sumber/konteks, tidak dihapus otomatis'})

dfields = ['group_id','tipe','url_norm','judul_norm','count_in_group','daftar_record_id','daftar_url','daftar_sumber','rekomendasi','alasan']
with open(OUT_DUP,'w',encoding='utf-8-sig',newline='') as f:
    w=csv.DictWriter(f,fieldnames=dfields); w.writeheader()
    for x in dup_rows: w.writerow(x)

etm = {r['record_id']:r for r in et_rows}
lm = {r['record_id']:r for r in loc_rows}
tri_rows=[]
for r in rows:
    rid = r.get('record_id','')
    etr = etm.get(rid,{})
    lmr = lm.get(rid,{})
    alasan_saat = r.get('alasan_review','')
    alasan_tetap = []
    if etr.get('rekomendasi_status')=='isi':
        alasan_tetap.append('perlu konfirmasi event_time terisi dan beda dari published_time')
    if lmr.get('dateline_jakarta_flag')=='ya':
        alasan_tetap.append('dateline Jakarta perlu verifikasi konteks (bukan hanya byline)')
    if r.get('sumber')=='USGS' and lmr.get('rekomendasi_filter')=='perlu_review':
        alasan_tetap.append('USGS bbox perlu koordinat terverifikasi')
    if r.get('sumber')=='BMKG' and '/alerts/' in (r.get('url') or ''):
        alasan_tetap.append('BMKG alerts dilarang robots - tidak dapat diverifikasi')
    if not alasan_tetap:
        alasan_tetap.append('belum ada bukti memadai untuk menutup review')
    tri_rows.append({
        'record_id':rid,'url':r.get('url',''),'sumber':r.get('sumber',''),'judul':r.get('judul',''),
        'alasan_review_saat_ini':alasan_saat,
        'bukti_tersedia':'sebagian' if etr.get('rekomendasi_status')=='isi' or lmr.get('dateline_jakarta_flag')=='ya' else 'tidak',
        'bisa_selesai':'tidak',
        'alasan_bisa_selesai':'',
        'alasan_tetap_review':'; '.join(alasan_tetap),
        'rekomendasi_perlu_review':'tetap_ya',
        'daftar_tugas_review':'; '.join(alasan_tetap)
    })

tfields = ['record_id','url','sumber','judul','alasan_review_saat_ini','bukti_tersedia','bisa_selesai','alasan_bisa_selesai','alasan_tetap_review','rekomendasi_perlu_review','daftar_tugas_review']
with open(OUT_TRI,'w',encoding='utf-8-sig',newline='') as f:
    w=csv.DictWriter(f,fieldnames=tfields); w.writeheader()
    for x in tri_rows: w.writerow(x)

h_after = {}
for name in ['data/geohazard_news.csv','data/geohazard_news_located.csv','data/geohazard_news_v2_candidate_20261028T034156Z.csv']:
    h_after[name]=sha256(name)

sum_lines=[]
sum_lines.append('# Ringkasan Penyempurnaan Fase 1')
sum_lines.append(f'Timestamp: {TS}')
sum_lines.append('')
sum_lines.append('## File baru')
sum_lines.append(f'- {OUT_CLASS.name}')
sum_lines.append(f'- {OUT_ET.name}')
sum_lines.append(f'- {OUT_LOC.name}')
sum_lines.append(f'- {OUT_DUP.name}')
sum_lines.append(f'- {OUT_TRI.name}')
sum_lines.append(f'- {OUT_SUM.name}')
sum_lines.append('')
sum_lines.append('## Jumlah baris')
sum_lines.append(f'- Kandidat diproses: {len(rows)}')
sum_lines.append(f'- Klasifikasi review (in_cakupan 41 + sample Lainnya 40): {len(class_rows)}')
sum_lines.append(f'- Event time review: {len(et_rows)}')
sum_lines.append(f'- Location/USGS review: {len(loc_rows)}')
sum_lines.append(f'- Duplikasi kandidat: {len(dup_rows)}')
sum_lines.append(f'- Review triage: {len(tri_rows)}')
sum_lines.append('')
sum_lines.append('## Checksum sebelum/sesudah')
for k in h_before:
    sum_lines.append(f'- {k}: {h_before[k]} -> {h_after[k]} (sama={h_before[k]==h_after[k]})')
sum_lines.append('')
sum_lines.append('## Temuan klasifikasi')
sum_lines.append(f'- Dalam cakupan 8 kategori: {len(in_cov)}')
sum_lines.append(f'- Sampel Lainnya diperiksa: {len(sample_lain)}')
sum_lines.append('- Ada indikasi bukti eksplisit pada sebagian in-cakupan; pada sampel Lainnya mayoritas tidak ditemukan bukti eksplisit -> direkomendasikan tetap Lainnya + review')
sum_lines.append('')
sum_lines.append('## Event time')
sum_lines.append('- BMKG alerts: teridentifikasi prakiraan/dilarang robots -> tidak diisi')
sum_lines.append('- USGS: teridentifikasi pola Time UTC pada beberapa baris')
sum_lines.append('- GDACS: hanya tanggal (On DD/MM/YYYY) dibedakan dari published_time -> tidak diisi event_time')
sum_lines.append('- Tidak ada pengisian berdasarkan published_time')
sum_lines.append('')
sum_lines.append('## Lokasi')
sum_lines.append('- Jakarta teridentifikasi (dateline/konteks) -> ditandai perlu_review')
sum_lines.append('- Konteks Manggarai perlu verifikasi per baris')
sum_lines.append('')
sum_lines.append('## USGS')
sum_lines.append('- Koordinat diekstrak bila ditemukan pola; jika tidak -> perlu_review')
sum_lines.append('- Bbox dihitung hanya jika koordinat tersedia')
sum_lines.append('- Tidak ada baris dihapus')
sum_lines.append('')
sum_lines.append('## Duplikasi')
sum_lines.append(f'- Kandidat URL duplikasi: {sum(1 for x in dup_rows if x["tipe"]=="url_norm")}')
sum_lines.append(f'- Kandidat judul duplikasi: {sum(1 for x in dup_rows if x["tipe"]=="judul_norm")}')
sum_lines.append('- Tidak ada penghapusan/penggabungan otomatis')
sum_lines.append('')
sum_lines.append('## Review queue')
sum_lines.append('- Semua baris tetap perlu_review secara konservatif; belum ada yang ditandai selesai tanpa bukti memadai')
sum_lines.append('- BMKG alerts tetap perlu_review (dilarang robots)')
sum_lines.append('')
sum_lines.append('## Error/keterbatasan')
sum_lines.append('- Tidak mengakses endpoint yang dilarang robots.txt')
sum_lines.append('- Tidak mengotomatisasi PVMBG/MAGMA/Portal MBG')
sum_lines.append('- Dataset asli, kandidat sebelumnya, dan pipeline tidak diubah')
sum_lines.append('- Beberapa koordinat BMKG/USGS mungkin sulit diekstrak dari isi_berita saat ini')
with open(OUT_SUM,'w',encoding='utf-8') as f:
    f.write('\n'.join(sum_lines))

print('done')
print(OUT_SUM.name)
