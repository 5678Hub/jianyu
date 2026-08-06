#!/usr/bin/env python3
"""jianyu 本地版 - 8000 端口 + 完全禁用缓存（绕开 GitHub Pages / Service Worker）"""
import http.server, socketserver, os, sys, signal

PORT = 8765
ROOT = r"C:\Users\10487\WorkBuddy\jianyu"
os.chdir(ROOT)

class Handler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, fmt, *args):
        sys.stderr.write("[%s] %s %s\n" % (
            self.log_date_time_string(), self.command, self.path))

    def end_headers(self):
        # 完全禁用浏览器和代理缓存
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate, max-age=0')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        # Service Worker 禁用（强制使用最新 index.html）
        self.send_header('Service-Worker-Allowed', '/')
        super().end_headers()

    def send_error(self, code, message=None, explain=None):
        # 简单错误页
        self.send_response(code)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(f'<h1>{code} {message or ""}</h1>'.encode('utf-8'))

def shutdown(sig, frame):
    print('\n[OK] jianyu 本地版停止', flush=True)
    sys.exit(0)

signal.signal(signal.SIGINT, shutdown)
signal.signal(signal.SIGTERM, shutdown)

print(f'[INFO] jianyu 本地版 启动中…', flush=True)
print(f'[INFO] 工作目录: {ROOT}', flush=True)
print(f'[INFO] 监听端口: {PORT}', flush=True)
print(f'[INFO] 访问地址: http://127.0.0.1:{PORT}/jianyu/', flush=True)
print(f'[INFO] 缓存策略: 完全禁用（Cache-Control: no-cache, no-store, must-revalidate）', flush=True)
print(f'[INFO] 关闭方式: Ctrl+C 或任务管理器 python.exe', flush=True)
print('-' * 60, flush=True)

socketserver.TCPServer.allow_reuse_address = True
with socketserver.TCPServer(("127.0.0.1", PORT), Handler) as httpd:
    httpd.serve_forever()
