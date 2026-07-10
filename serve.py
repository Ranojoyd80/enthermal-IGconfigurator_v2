#!/usr/bin/env python3
"""Dev server for the Enthermal configurator.

Identical to `python -m http.server`, except every response carries
`Cache-Control: no-store`. Without that header the browser heuristically
caches the HTML (which contains ALL the app's JS/CSS), so after an edit a
normal reload can silently serve the old app. With it, a plain F5 always
loads the latest files — no Ctrl+Shift+R needed.

Usage:  python serve.py [port]     (default 8000)
"""
import sys
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler


class NoCacheHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Cache-Control', 'no-store')
        super().end_headers()


if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    print(f'Serving http://localhost:{port}/enthermal-configurator.html  (caching disabled — Ctrl+C to stop)')
    ThreadingHTTPServer(('', port), NoCacheHandler).serve_forever()
