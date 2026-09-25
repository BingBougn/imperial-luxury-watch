#!/usr/bin/env bash
# Inline the videos (and the scroll-world engine) into publishable single-file pages.
set -euo pipefail
cd "$(dirname "$0")"

ENGINE=.claude/skills/scroll-world/references/scrub-engine.js
mkdir -p dist .build

base64 -w 0 assets/vid/hero-1.mp4 > .build/v1.b64
base64 -w 0 assets/vid/hero-2.mp4 > .build/v2.b64

# The engine source is full of $ and \ that a regex replacement would mangle,
# so it is spliced in by line instead of substituted.
inline_engine() {
  local src="$1" dst="$2" line
  if grep -q '__ENGINE__' "$src"; then
    line=$(grep -n '__ENGINE__' "$src" | head -1 | cut -d: -f1)
    head -n $((line - 1)) "$src" > "$dst"
    printf '<script>\n' >> "$dst"
    cat "$ENGINE" >> "$dst"
    printf '</script>\n' >> "$dst"
    tail -n +$((line + 1)) "$src" >> "$dst"
  else
    cp "$src" "$dst"
  fi
}

inline_videos() {
  perl -i -pe '
    BEGIN {
      open my $f1, "<", ".build/v1.b64" or die; my $b1 = <$f1>; chomp $b1;
      open my $f2, "<", ".build/v2.b64" or die; my $b2 = <$f2>; chomp $b2;
      $V1 = "data:video/mp4;base64," . $b1;
      $V2 = "data:video/mp4;base64," . $b2;
    }
    s{__VIDEO_1__}{$V1}g;
    s{__VIDEO_2__}{$V2}g;
  ' "$1"
}

for name in index.html immersif.html; do
  inline_engine "$name" "dist/$name"
  inline_videos "dist/$name"
  echo "$name -> dist/$name ($(du -h "dist/$name" | cut -f1))"
done
