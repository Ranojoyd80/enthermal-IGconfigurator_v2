#!/usr/bin/env python3
"""Pre-commit guard: keep the anchor-render cache-buster in sync with the files.

Render batches replace .webp files under identical names, so any browser that
cached an earlier batch keeps showing the old pixels (JS-assigned img.src
requests hit the HTTP cache even after a hard refresh). The app therefore
versions every render URL with a `?v=<token>` query.

This script makes the token automatic and mistake-proof:

  1. Fingerprints the STAGED content of App_Data/Anchor_Renders/ (git blob
     hashes -> sha1 -> first 8 hex chars). Same files => same token; any
     changed/added/removed render => new token.
  2. Rewrites the token in enthermal-configurator.html — the RENDER_V constant
     plus every literal Anchor_Renders/...webp URL — and re-stages the file.
  3. Fails the commit if any Anchor_Renders URL in the HTML somehow lacks a
     version (safety net for future edits).

Runs from .githooks/pre-commit (git config core.hooksPath .githooks).
"""
import hashlib
import re
import subprocess
import sys

HTML = 'enthermal-configurator.html'
RENDER_DIR = 'App_Data/Anchor_Renders'


def run(*args):
    return subprocess.run(args, capture_output=True, text=True, check=True).stdout


def staged_render_fingerprint():
    # `ls-files -s` reads the index (staged state), not the working tree.
    listing = run('git', 'ls-files', '-s', '--', RENDER_DIR)
    if not listing.strip():
        print('sync_render_version: no files under %s in the index — refusing to commit '
              'without renders.' % RENDER_DIR, file=sys.stderr)
        sys.exit(1)
    return hashlib.sha1(listing.encode()).hexdigest()[:8]


def main():
    ver = staged_render_fingerprint()

    with open(HTML, encoding='utf-8', newline='') as f:
        html = f.read()

    # Literal render URLs in markup: ensure/refresh ?v=<token>
    url_re = re.compile(r'(Anchor_Renders/[^"\'\s?]+\.webp)(\?v=[0-9A-Za-z]+)?')
    new_html = url_re.sub(lambda m: m.group(1) + '?v=' + ver, html)

    # The runtime constant used by setAnchorImages()
    const_re = re.compile(r"(RENDER_V\s*=\s*')\?v=[0-9A-Za-z]+(')")
    new_html, n_const = const_re.subn(r'\g<1>?v=' + ver + r'\g<2>', new_html)
    if n_const != 1:
        print('sync_render_version: expected exactly one RENDER_V constant in %s, found %d. '
              'Fix the constant (var RENDER_V=\'?v=...\') and retry.' % (HTML, n_const),
              file=sys.stderr)
        sys.exit(1)

    # Safety net: every literal render URL must now carry a version.
    bare = [m.group(0) for m in re.finditer(r'Anchor_Renders/[^"\'\s?]+\.webp(?!\?v=)', new_html)
            if "'+" not in m.group(0)]
    if bare:
        print('sync_render_version: unversioned render URL(s) left in %s: %s'
              % (HTML, ', '.join(bare[:5])), file=sys.stderr)
        sys.exit(1)

    if new_html != html:
        with open(HTML, 'w', encoding='utf-8', newline='') as f:
            f.write(new_html)
        subprocess.run(['git', 'add', HTML], check=True)
        print('sync_render_version: render cache-buster set to ?v=%s (re-staged %s)' % (ver, HTML))

    sys.exit(0)


if __name__ == '__main__':
    main()
