# NETPROBE — Domain to IP Checker

Real-time DNS resolver, IP geolocation, dan reachability checker dengan backend Python Flask.

## Files

- **backend.py** — Flask server (API, DNS queries, geolocation, reachability)
- **frontend.html** — Web UI (buka di browser)
- **requirements.txt** — Python dependencies
- **install.sh** — Auto-installer untuk Termux
- **SETUP_TERMUX.md** — Detailed setup guide

## Quick Start

### Option 1: Via Install Script (Recommended)

```bash
bash install.sh
cd ~/netprobe
python3 backend.py
```

Terus buka browser: `http://localhost:5000`

### Option 2: Manual Setup

```bash
# Install dependencies
pkg update && pkg install python3 python3-pip

# Install Python packages
pip install flask flask-cors dnspython requests

# Run backend
python3 backend.py
```

Buka browser: `http://localhost:5000`

## Fitur

✓ **Real-time DNS Query** — A, AAAA, CNAME, MX, NS, TXT, SOA records
✓ **IP Geolocation** — Country, city, ISP, timezone (via ipwho.is & ip-api.com)
✓ **Reachability Tests** — HTTP & HTTPS concurrent checks
✓ **Live Log** — See probe progress real-time
✓ **Concurrent Processing** — Multiple DNS queries & geo lookups in parallel

## How to Use

1. Start backend:
   ```bash
   python3 backend.py
   ```

2. Open browser:
   ```
   http://localhost:5000
   ```

3. Enter domain (e.g., `google.com`)

4. Click **RUN CHECK**

5. See results: DNS records, IPs, geolocation, reachability status

## API

### POST /api/probe

```bash
curl -X POST http://localhost:5000/api/probe \
  -H "Content-Type: application/json" \
  -d '{"domain": "google.com"}'
```

### GET /api/health

```bash
curl http://localhost:5000/api/health
```

## Network Access

Backend run di port 5000, accessible dari:
- **Local**: `http://localhost:5000`
- **Network**: `http://<your-ip>:5000` (ubah ke IP address device)

## Troubleshooting

**Port already in use?**
```bash
# Change port in backend.py line ~220
# app.run(host='0.0.0.0', port=8888, ...)
```

**Can't import modules?**
```bash
pip install flask flask-cors dnspython requests
```

**Backend offline?**
```bash
# Check if service running
ps aux | grep python

# Kill old process
pkill -f backend.py

# Restart
python3 backend.py
```

## Performance

- DNS queries: ~100-500ms (concurrent all record types)
- Geolocation: ~2-5s per IP (parallel requests, max 4 workers)
- Reachability: ~3-10s (HTTP & HTTPS concurrent)
- Total probe time: ~5-15s (depends on network & target)

## Notes

- **No data storage** — Results calculated on-the-fly, nothing saved
- **CORS enabled** — Frontend can access from any origin
- **Public endpoints** — Anyone on network can call API (add authentication if needed)
- **Single location** — Checks from this server only (unlike check-host.net which tests from multiple locations)

## Advanced

See `SETUP_TERMUX.md` untuk:
- Custom port configuration
- Custom nameservers
- Background execution
- Network exposure
- Security hardening

---

**Made for Termux, works anywhere Python runs. 🚀**
