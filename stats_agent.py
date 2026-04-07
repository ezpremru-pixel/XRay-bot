import http.server, json, psutil, time
class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200); self.send_header('Content-type','application/json'); self.end_headers()
        d = {"status":"🟢 Онлайн","cpu":f"{psutil.cpu_percent()}%","ram":f"{psutil.virtual_memory().percent}%","uptime":f"{int((time.time()-psutil.boot_time())//86400)} дн."}
        self.wfile.write(json.dumps(d).encode())
http.server.HTTPServer(('0.0.0.0', 80), H).serve_forever()
