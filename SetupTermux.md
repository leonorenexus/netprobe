# NETPROBE — Setup Guide untuk Termux

NETPROBE adalah domain-to-IP checker dengan backend real-time yang bisa dijalankan di Termux.

## Apa aja yang dibutuhkan

- **Termux** (download dari F-Droid atau Termux official)
- **Python 3.9+**
- **pip** (package manager Python)
- Internet connection

## Step 1: Setup Termux

Buka Termux dan jalankan:

```bash
pkg update
pkg install python3 python3-pip git curl
```

## Step 2: Install Dependencies Python

```bash
pip install flask flask-cors dnspython requests
```

Ini install:
- **Flask** — web server/API framework
- **flask-cors** — handle CORS untuk cross-origin requests
- **dnspython** — query DNS records
- **requests** — HTTP requests untuk geo lookup & reachability checks

## Step 3: Setup Files

Copy file-file berikut ke Termux:

1. **backend.py** — Server Flask (inti dari aplikasi)
2. **frontend.html** — Web UI (buka di browser)

Tempatin di folder yang mudah, contoh:

```bash
# Buat folder
mkdir -p ~/netprobe
cd ~/netprobe

# Copy backend.py dan frontend.html ke folder ini
# (via ADB, email, atau download langsung)
```

## Step 4: Run Backend

```bash
cd ~/netprobe
python3 backend.py
```

Output bakal terlihat kayak:

```
╔══════════════════════════════════════════════════════════╗
║         NETPROBE Backend — Running                       ║
╠══════════════════════════════════════════════════════════╣
║ 📡 API:      http://localhost:5000/api/probe             ║
║ 🌐 Frontend: http://localhost:5000                       ║
║ 💚 Health:   http://localhost:5000/api/health            ║
╚══════════════════════════════════════════════════════════╝
```

**Backend udah running!** Server jalan di port 5000.

## Step 5: Akses Frontend

### Opsi A: Via Browser di Perangkat yang Sama

Buka browser di HP/computer yang sama dengan Termux:

1. Buka **Chrome/Firefox**
2. Ketik di address bar: `http://localhost:5000`
3. Atau buka file `frontend.html` langsung

### Opsi B: Via File Frontend

Kalau mau buka frontend sebagai file lokal (tanpa browser):

1. Buat folder akses:
```bash
cp frontend.html ~/netprobe/
```

2. Di file manager, buka `~/netprobe/frontend.html` dengan browser

3. Frontend bakal try connect ke `http://localhost:5000` (backend)

**Note:** Di beberapa setup, localhost mungkin perlu diganti dengan IP address Termux.

## Troubleshooting

### 1. "Port 5000 already in use"

Ada proses lain yang pake port 5000. Ganti port di `backend.py` — cari line:

```python
app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
```

Ubah `5000` jadi port lain (misal `8888`), terus update juga di `frontend.html`:

```javascript
const BACKEND_URL = 'http://localhost:8888';
```

### 2. "ModuleNotFoundError: No module named 'flask'"

Dependencies belum install. Jalankan:

```bash
pip install flask flask-cors dnspython requests
```

### 3. "Connection refused" di browser

Pastikan:
- Backend running di Termux
- Browser buka `http://localhost:5000` (bukan HTTPS)
- Firewall/router tidak block port 5000

Kalau masih error, coba setup Termux dengan:

```bash
termux-setup-storage
```

Ini biar Termux akses storage dan network dengan benar.

### 4. DNS Query Gagal

Kalau backend error saat query DNS:

```bash
# Cek internet connection
ping 8.8.8.8

# Cek DNS resolution
nslookup google.com
```

Kalau DNS-nya down, backend bakal report error di live log.

## API Endpoints

### POST /api/probe

Submit domain, dapat semua data (DNS, IP, geolocation, reachability).

**Request:**
```json
{
  "domain": "google.com"
}
```

**Response:**
```json
{
  "domain": "google.com",
  "records": {
    "A": [
      { "type": "A", "data": "142.250.185.46", "ttl": 300 },
      ...
    ],
    "AAAA": [...],
    "CNAME": [...],
    "MX": [...],
    "NS": [...],
    "TXT": [...],
    "SOA": [...]
  },
  "ips": ["142.250.185.46", ...],
  "geolocation": {
    "142.250.185.46": {
      "ip": "142.250.185.46",
      "country": "United States",
      "city": "Mountain View",
      "isp": "Google LLC",
      "timezone": "America/Los_Angeles"
    }
  },
  "reachability": [
    { "scheme": "HTTPS", "url": "https://google.com", "up": true, "status_code": 200, "ms": 145 },
    { "scheme": "HTTP", "url": "http://google.com", "up": true, "status_code": 301, "ms": 142 }
  ],
  "timestamp": 1719934200.5
}
```

### GET /api/health

Health check — backend status.

**Response:**
```json
{
  "status": "ok",
  "service": "netprobe-backend"
}
```

## Cara Pake

1. **Start backend**:
   ```bash
   cd ~/netprobe
   python3 backend.py
   ```

2. **Buka browser**, akses:
   ```
   http://localhost:5000
   ```
   atau buka `frontend.html` dan pastikan backend URL di script sesuai.

3. **Masukin domain** (contoh: `google.com`, `anthropic.com`)

4. **Tekan "RUN CHECK"**

5. **Tunggu hasil** — live log bakal show progress:
   - Query A/AAAA/CNAME/MX/NS/TXT records
   - Geolocation IPs yang ditemukan
   - Reachability tests (HTTPS & HTTP)

## Customization

### Port Custom

Edit `backend.py`:
```python
app.run(host='0.0.0.0', port=8888, debug=False, threaded=True)
```

Update `frontend.html`:
```javascript
const BACKEND_URL = 'http://localhost:8888';
```

### Custom Nameserver

Edit `backend.py`, cari function `query_dns()`:

```python
def query_dns(domain, record_type):
    try:
        resolver = dns.resolver.Resolver()
        resolver.nameservers = ['8.8.8.8', '8.8.4.4']  # Custom DNS server
        answers = resolver.resolve(domain, record_type, lifetime=8.0)
        ...
```

### Hide Internal Endpoints

Kalau mau hide `/api/health` atau `/` (frontend), hapus routes:

```python
@app.route('/')
def frontend():
    return render_template_string(FRONTEND_HTML)
```

Ganti dengan bikin redirect atau remove aja.

## Advanced: Run di Background

Jalanin backend tanpa block terminal:

```bash
python3 backend.py &
disown
```

Atau pake `nohup`:

```bash
nohup python3 backend.py > backend.log 2>&1 &
```

Terus cek log:

```bash
tail -f backend.log
```

## Advanced: Expose ke Network Lain

Kalau mau akses backend dari device lain di network (bukan localhost):

1. Cari IP address Termux:
   ```bash
   ifconfig | grep "inet "
   ```

2. Edit `backend.py`, ubah:
   ```python
   app.run(host='0.0.0.0', port=5000, ...)
   ```
   (already set ke `0.0.0.0` jadi accessible dari network)

3. Di frontend atau device lain, pakai IP address Termux:
   ```javascript
   const BACKEND_URL = 'http://192.168.1.100:5000'; // Sesuaikan IP
   ```

## Performance Notes

- **Concurrent DNS queries**: Backend query semua record types parallel, jadi cepat
- **Geolocation berjalan async**: Multiple IP lookups concurrent (max 4 worker threads)
- **Reachability checks parallel**: HTTPS & HTTP di-test bersamaan
- **Timeout handling**: Semua request punya timeout (DNS: 8s, HTTP: 6s) biar nggak hang

## Security Notes

- **No data logging**: Backend nggak simpan query history (unless manually di-log)
- **CORS enabled**: Frontend bisa akses dari domain manapun (sesuaikan `CORS(app)` jika perlu restrict)
- **No authentication**: Endpoint publik, siapa aja bisa akses (run di network yang trusted)

Kalau mau restrict akses:
```python
from flask_cors import CORS

# Restrict to specific origin
CORS(app, origins=['http://localhost:3000'])
```

## Next Steps

- Bikin script auto-start saat boot Termux
- Integrate dengan ngrok/tunneling untuk akses remote
- Add custom DNS server support
- Build mobile app wrapper (Flutter/React Native)

---

**Happy probing! 🚀**

Kalau ada error atau pertanyaan, cek terminal output backend untuk debug logs.
