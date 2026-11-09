#!/bin/sh
# Downloads the public collusion.wiki export and verifies the published checksums.
set -e
cd "$(dirname "$0")/.."
mkdir -p raw && cd raw
for f in pages.jsonl revisions.jsonl events.jsonl labels.jsonl; do curl -sfL -O "https://collusion.wiki/explorer/download/$f.gz"; done
curl -sfL -O https://collusion.wiki/explorer/download/manifest.json.gz
gunzip -kf ./*.gz
cat > SHA256SUMS <<'SUMS'
92b296170b496b836cdf5ef783bed9465d2d75db7e1a0becec1c36c8b7c42cfd  pages.jsonl
60df4a515178230aa952d9f64f6215aea4bd95ab2f05e31e484cf9b887e3f793  revisions.jsonl
588584295f1c4a7c3d90b04075ab151504f165ff069534d935cda08853ec28b1  events.jsonl
d94aecd84baecda46344f5b8726a95a9c81e7e41a1c0969fc89a90c8906f0388  labels.jsonl
b6d53e16b5d9a6a0a98d4577238835ee7a574d7d10a8f1312330b4e626c6ba2b  manifest.json
SUMS
shasum -a 256 -c SHA256SUMS
