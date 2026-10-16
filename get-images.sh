#!/usr/bin/env bash
# Copies the photos, logo, floor plans and state certificate from the current
# windsorplaceofwilmington.com into this project, so the new site doesn't depend
# on the old host. Run once from this folder on your Mac:
#
#   chmod +x get-images.sh && ./get-images.sh && python3 build.py
#
set -u
cd "$(dirname "$0")"
CDN="https://irp.cdn-website.com/c472a16b"
IMG="static/img"
DOCS="static/docs"
mkdir -p "$IMG/gallery" "$DOCS"

fetch() { # url dest
  if curl -fsSL "$1" -o "$2"; then echo "  ok   $2"; return 0; else rm -f "$2"; return 1; fi
}

# Try a few size variants, largest first.
photo() { # remote-basename local-name
  local base="$1" name="$2" got=""
  for w in 1920 1600 1200 960 838 699 698 672 419; do
    if fetch "$CDN/dms3rep/multi/opt/${base}-${w}w.jpg" "$IMG/$name.jpg"; then got=1; break; fi
  done
  [ -z "$got" ] && { echo "  MISSING $name ($base)"; return; }
  # Small version for phones
  if command -v sips >/dev/null 2>&1; then
    sips -Z 900 "$IMG/$name.jpg" --out "$IMG/$name-sm.jpg" >/dev/null && echo "  ok   $IMG/$name-sm.jpg (resized)"
  else
    cp "$IMG/$name.jpg" "$IMG/$name-sm.jpg"
  fi
}

echo "Photos"
photo "windsor-cta-1"        entrance
photo "windsor-cta-2"        dining-entry
photo "windsor-cta-3"        family
photo "windsor-cta-4"        patio
photo "1_AssistedLiving"     assisted
photo "2_IndependentLiving"  independent
photo "3_MemoryCare"         memory

echo "Logo"
fetch "$CDN/dms3rep/multi/opt/WPW_Logo2021B-1920w.png" "$IMG/logo.png" || echo "  MISSING logo"

echo "Documents"
fetch "$CDN/files/uploaded/floor-plan1.pdf" "$DOCS/floor-plan-1.pdf" || echo "  MISSING floor plan 1"
fetch "$CDN/files/uploaded/floor-plan2.pdf" "$DOCS/floor-plan-2.pdf" || echo "  MISSING floor plan 2"
fetch "$CDN/files/uploaded/floor-plan3.pdf" "$DOCS/floor-plan-3.pdf" || echo "  MISSING floor plan 3"
fetch "$CDN/files/uploaded/EOAI-Certificate-2026-c438fa38.pdf" "$DOCS/eoai-certificate-2026.pdf" || echo "  MISSING certificate"

echo "Gallery (from the old Photos page)"
page="$(curl -fsSL https://www.windsorplaceofwilmington.com/lifestyle/photos || true)"
urls="$(printf '%s' "$page" | grep -oE 'https://irp\.cdn-website\.com/c472a16b/dms3rep/multi/[^"'"'"' )?]+\.(jpg|jpeg|png|webp)' \
        | grep -viE 'logo|WPW_|windsor-cta|_AssistedLiving|_IndependentLiving|_MemoryCare|download-' \
        | sed -E 's/-[0-9]+w\.(jpg|jpeg|png|webp)$/.\1/' | sort -u)"
n=0
for u in $urls; do
  f="$(basename "$u")"
  stem="${f%.*}"; ext="${f##*.}"
  # Prefer a web-sized variant if the CDN has one
  big="$(dirname "$u")/${stem}-1920w.${ext}"
  fetch "$big" "$IMG/gallery/$f" || fetch "$u" "$IMG/gallery/$f" && n=$((n+1))
done
echo "  $n gallery photos saved to $IMG/gallery/ (rename files to set captions, e.g. the-library.jpg)"

echo
echo "Done. Now run: python3 build.py"
