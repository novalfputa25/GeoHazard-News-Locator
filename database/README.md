# Database

Folder ini hanya menyertakan skema database publik:

- `schema.sql` — skema SQLite untuk seluruh tabel provenance dan dashboard.

Database operasional `geohazard.db` dan folder `backups/` **tidak disertakan** di repository publik karena berisi snapshot data kerja, alasan lisensi/redistribusi sumber belum diverifikasi, dan untuk mencegah publikasi data operasional secara tidak sengaja.

## Membuat database lokal

Dashboard membaca database SQLite secara read-only dan memakai path default:

```text
database/geohazard.db
```

Untuk membangun database lokal dari pipeline:

```powershell
.\.venv\Scripts\python.exe run_pipeline.py
.\.venv\Scripts\python.exe import_database.py --no-baseline
```

Jika memiliki baseline CSV yang sah dan sudah diperiksa lisensinya, baseline dapat diimpor tanpa `--no-baseline`.

Path database alternatif dapat diberikan saat menjalankan dashboard:

```powershell
.\.venv\Scripts\python.exe run_dashboard.py --port 8000 --db path\ke\database.db
```

Jangan commit database hasil generate, backup, atau data mentah ke repository.
