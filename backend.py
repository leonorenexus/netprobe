#!/usr/bin/env python3
"""
NETPROBE Backend — DNS checker, IP geolocation, reachability tests
Bisa run di Termux atau server biasa. Install: pip install flask dnspython requests geoip2

Usage:
    python3 backend.py
    # Akses: http://localhost:5000

API Endpoints:
    POST /api/probe
        body: {"domain": "https://leonorenexus.github.io/netprobe/"}
        returns: {records: {...}, ips: [...], geolocation: {...}, reachability: {...}}
"""

from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import dns.resolver
import dns.rdatatype
import socket
import requests
import json
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import re
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# ===== DNS RESOLVER =====
def query_dns(domain, record_type):
    """Query DNS records menggunakan dnspython"""
    try:
        answers = dns.resolver.resolve(domain, record_type, lifetime=8.0)
        results = []
        for rdata in answers:
            results.append({
                'type': record_type,
                'data': str(rdata),
                'ttl': answers.rrset.ttl if hasattr(answers.rrset, 'ttl') else 300
            })
        return results
    except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.exception.DNSException) as e:
        logger.warning(f"DNS query error for {domain} {record_type}: {e}")
        return []

def resolve_domain(domain):
    """Resolve domain ke semua record types penting"""
    record_types = ['A', 'AAAA', 'CNAME', 'MX', 'NS', 'TXT', 'SOA']
    records = {}
    all_ips = set()
    
    for rtype in record_types:
        results = query_dns(domain, rtype)
        records[rtype] = results
        
        # Extract IPs dari A dan AAAA records
        if rtype in ['A', 'AAAA']:
            for r in results:
                try:
                    # Validasi format IP
                    socket.inet_pton(socket.AF_INET if rtype == 'A' else socket.AF_INET6, r['data'])
                    all_ips.add(r['data'])
                except:
                    pass
    
    return records, list(all_ips)

# ===== GEOLOCATION =====
def geolocate_ip(ip):
    """Get geolocation data untuk IP"""
    try:
        # Coba ipwho.is first
        res = requests.get(f'https://ipwho.is/{ip}', timeout=5)
        if res.status_code == 200:
            data = res.json()
            if data.get('success') is not False:
                return {
                    'ip': ip,
                    'country': data.get('country'),
                    'country_code': data.get('country_code'),
                    'city': data.get('city'),
                    'region': data.get('region'),
                    'latitude': data.get('latitude'),
                    'longitude': data.get('longitude'),
                    'isp': data.get('connection', {}).get('isp'),
                    'org': data.get('connection', {}).get('org'),
                    'timezone': data.get('timezone', {}).get('id') if data.get('timezone') else None,
                }
        
        # Fallback ke ip-api.com
        res = requests.get(f'http://ip-api.com/json/{ip}?fields=country,city,isp,org,timezone,lat,lon', timeout=5)
        if res.status_code == 200:
            data = res.json()
            if data.get('status') == 'success':
                return {
                    'ip': ip,
                    'country': data.get('country'),
                    'city': data.get('city'),
                    'isp': data.get('isp'),
                    'org': data.get('org'),
                    'timezone': data.get('timezone'),
                    'latitude': data.get('lat'),
                    'longitude': data.get('lon'),
                }
    except Exception as e:
        logger.warning(f"Geolocation error for {ip}: {e}")
    
    return {'ip': ip, 'error': 'Geolocation unavailable'}

def batch_geolocate(ips):
    """Geolocate multiple IPs dengan concurrent requests"""
    results = {}
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(geolocate_ip, ip): ip for ip in ips}
        for future in as_completed(futures):
            ip = futures[future]
            try:
                results[ip] = future.result()
            except Exception as e:
                logger.error(f"Geo fetch error for {ip}: {e}")
                results[ip] = {'ip': ip, 'error': str(e)}
    
    return results

# ===== REACHABILITY =====
def check_reachability_single(domain, scheme):
    """Check koneksi ke domain via HTTP/HTTPS"""
    url = f"{scheme}://{domain}"
    start = time.time()
    try:
        res = requests.head(url, timeout=6, allow_redirects=False)
        elapsed = int((time.time() - start) * 1000)
        return {
            'scheme': scheme.upper(),
            'url': url,
            'up': True,
            'status_code': res.status_code,
            'ms': elapsed
        }
    except requests.exceptions.Timeout:
        return {'scheme': scheme.upper(), 'url': url, 'up': False, 'error': 'Timeout'}
    except requests.exceptions.ConnectionError:
        return {'scheme': scheme.upper(), 'url': url, 'up': False, 'error': 'Connection refused'}
    except Exception as e:
        return {'scheme': scheme.upper(), 'url': url, 'up': False, 'error': str(e)[:50]}

def check_reachability(domain):
    """Check reachability via HTTP dan HTTPS"""
    results = []
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [
            executor.submit(check_reachability_single, domain, 'https'),
            executor.submit(check_reachability_single, domain, 'http'),
        ]
        for future in as_completed(futures):
            try:
                results.append(future.result())
            except Exception as e:
                logger.error(f"Reachability check error: {e}")
    
    return sorted(results, key=lambda x: x['scheme'])

# ===== VALIDATION =====
def is_valid_domain(domain):
    """Validasi format domain"""
    pattern = r'^(?!-)[A-Za-z0-9-]{1,63}(?<!-)(\.(?!-)[A-Za-z0-9-]{1,63}(?<!-))*$'
    return re.match(pattern, domain.lower()) is not None

# ===== API ENDPOINTS =====
@app.route('/api/probe', methods=['POST'])
def probe():
    """Main endpoint: submit domain, get semua data (DNS, geo, reachability)"""
    try:
        data = request.get_json()
        domain = (data.get('domain') or '').strip().lower()
        domain = domain.replace('https://', '').replace('http://', '').rstrip('/')
        
        if not domain:
            return jsonify({'error': 'Domain tidak boleh kosong'}), 400
        
        if not is_valid_domain(domain):
            return jsonify({'error': f'Format domain "{domain}" tidak valid'}), 400
        
        logger.info(f"Probe started: {domain}")
        
        # DNS resolve
        records, ips = resolve_domain(domain)
        
        # Geolocation untuk semua IPs
        geolocation = {}
        if ips:
            geolocation = batch_geolocate(ips)
        
        # Reachability checks
        reachability = check_reachability(domain)
        
        result = {
            'domain': domain,
            'records': records,
            'ips': ips,
            'geolocation': geolocation,
            'reachability': reachability,
            'timestamp': time.time()
        }
        
        logger.info(f"Probe completed: {domain} — {len(ips)} IPs found")
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Probe error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({'status': 'ok', 'service': 'netprobe-backend'})

# ===== SIMPLE FRONTEND (optional, untuk testing) =====
FRONTEND_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NETPROBE Backend</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            background: #0a0e13;
            color: #e7edf3;
            font-family: 'IBM Plex Mono', monospace;
            padding: 20px;
        }
        .container { max-width: 1000px; margin: 0 auto; }
        h1 { margin-bottom: 20px; font-size: 24px; }
        .status { padding: 10px; background: #10161d; border: 1px solid #1f2934; border-radius: 6px; margin-bottom: 20px; }
        .input-group { display: flex; gap: 10px; margin-bottom: 20px; }
        input { flex: 1; padding: 10px; background: #10161d; border: 1px solid #1f2934; color: #e7edf3; border-radius: 6px; font-family: inherit; }
        button { padding: 10px 20px; background: #5fe0b7; color: #06110d; border: none; border-radius: 6px; cursor: pointer; font-weight: 600; }
        button:hover { background: #7cf0cc; }
        button:disabled { opacity: 0.5; cursor: not-allowed; }
        .output { background: #10161d; border: 1px solid #1f2934; border-radius: 6px; padding: 15px; margin-top: 20px; max-height: 500px; overflow-y: auto; }
        pre { font-size: 12px; line-height: 1.6; }
        .error { color: #ef5b5b; }
        .success { color: #5fe0b7; }
    </style>
</head>
<body>
    <div class="container">
        <h1>NETPROBE Backend API</h1>
        <div class="status">
            <span id="status-text">Backend running — siap terima request</span>
        </div>
        
        <div class="input-group">
            <input id="domain-input" type="text" placeholder="Domain (contoh: google.com)" autocomplete="off">
            <button id="check-btn" onclick="runProbe()">RUN PROBE</button>
        </div>
        
        <div class="output" id="output">
            <pre id="output-text">Output bakal muncul di sini...</pre>
        </div>
    </div>
    
    <script>
        async function runProbe() {
            const domain = document.getElementById('domain-input').value.trim();
            if (!domain) { alert('Masukin domain!'); return; }
            
            const btn = document.getElementById('check-btn');
            btn.disabled = true;
            btn.textContent = 'CHECKING...';
            
            const output = document.getElementById('output-text');
            output.textContent = 'Loading...';
            
            try {
                const res = await fetch('/api/probe', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ domain })
                });
                
                const data = await res.json();
                output.textContent = JSON.stringify(data, null, 2);
                if (res.ok) {
                    output.innerHTML = '<span class="success">✓ Probe berhasil!</span>\n\n' + output.textContent;
                } else {
                    output.innerHTML = '<span class="error">✗ Error: ' + data.error + '</span>\n\n' + output.textContent;
                }
            } catch (err) {
                output.innerHTML = '<span class="error">✗ Network error: ' + err.message + '</span>';
            } finally {
                btn.disabled = false;
                btn.textContent = 'RUN PROBE';
            }
        }
        
        document.getElementById('domain-input').addEventListener('keypress', e => {
            if (e.key === 'Enter') runProbe();
        });
    </script>
</body>
</html>
"""

@app.route('/')
def frontend():
    """Simple frontend untuk testing API"""
    return render_template_string(FRONTEND_HTML)

# ===== MAIN =====
if __name__ == '__main__':
    print("""
╔══════════════════════════════════════════════════════════╗
║         NETPROBE Backend — Running                       ║
╠══════════════════════════════════════════════════════════╣
║ 📡 API:      http://localhost:5000/api/probe             ║
║ 🌐 Frontend: http://localhost:5000                       ║
║ 💚 Health:   http://localhost:5000/api/health            ║
╚══════════════════════════════════════════════════════════╝
    """)
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
