# Cron Monitor — Akun 71 & 72

Dashboard dokumentasi cron **dayparting** Meta Ads untuk akun iklan **71 (Evepro)** dan **72 (Tiny Storie)** yang dijalankan dari **VPS DagangPro** (`srv1641968`, `/root/automation/`).

Tiap pagi script meng-`ACTIVE`-kan campaign, tiap malam meng-`PAUSED`-kan — supaya iklan cuma jalan di jam produktif dan hemat budget di jam sepi.

## Isi
- `index.html` — dashboard 1-file (HTML/CSS/JS, tanpa build). Buka langsung di browser atau via GitHub Pages.
- `sync_status.py` — generator status live (jalan **di VPS**, baca token server-side, 1 batch call/akun, tulis `data/*.json` tanpa token).
- `data/a71.json`, `data/a72.json` — snapshot status ON/OFF campaign (non-rahasia).
- Tab **Akun 71**, **Akun 72**, dan **Info**.

## Status live Meta (anti spam API)
Tiap akun nampilin status **ON/OFF live** per campaign + ringkasan (berapa ON / OFF) + penjelasan gampang. Caranya: `sync_status.py` di VPS baca status ke Meta **1× batch per akun**, tulis JSON ke repo; browser cuma baca JSON, **nggak pernah manggil Meta langsung** → nggak ada spam API.

## Kontrol ON/OFF cron
Halaman statis nggak boleh pegang token (bocor di browser). Kontrol cron lewat **MASBOI di Telegram**: `on/off cron a71`, `on/off cron a72` → MASBOI komen/uncomment baris crontab di VPS + readback. Opsi tombol di dashboard butuh SSH key sebagai GitHub Secret (nunggu keputusan).

## Yang dipantau
| Akun | Script | Jadwal (WIB) | Fungsi | Status |
|------|--------|--------------|--------|--------|
| 71 | `a71_videos_6_26_toggle.py` | ON 06:00 / OFF 21:00 (26 Jun) | 3 campaign video batch | one-shot, dorman |
| 71 | `a71_batch_6_26_toggle.py` | ON 06:00 / OFF 21:00 (26 Jun) | 16 campaign screenshot | one-shot, dorman |
| 72 | `a72_statue_toggle.py` | ON 05:30 / OFF 22:00 (harian) | 6 campaign STATUE/Bestie | **aktif harian** |

## Catatan
- Snapshot dokumentasi (bukan live-poll). Update bila jadwal/script di VPS berubah.
- Crontab VPS pakai UTC; di dashboard sudah diterjemahkan ke WIB.
- **Tidak ada credential/token** di repo ini (token tetap server-side di `.env` VPS).
- Mac Mini tidak punya cron khusus a71/a72 — semuanya di VPS.
