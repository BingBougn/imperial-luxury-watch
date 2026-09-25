#!/usr/bin/env bash
# Replays our edits on top of the live artifact version fetched from claude.ai.
# Everything is byte-oriented: the page is UTF-8 and perl must not decode it.
set -euo pipefail
cd "$(dirname "$0")"

SRC="${1:?usage: patch-live.sh <fetched-artifact.html>}"
OUT=dist/live.html
mkdir -p dist
cp "$SRC" "$OUT"

# 1. Lift the clock block to the top of its sticky stage and cap the dial by
#    viewport height, so the step hanging below it stops being clipped.
# 2. Enlarge the timeline labels.
# 3. Anchor the labels outside the frame instead of straddling its edge.
perl -0777 -i -pe '
  # the site nav is sticky at top:0 and 76px tall, so a stage sticking at 0 too
  # slid its heading underneath it — park the stage just below the bar instead
  s|\Qposition:sticky; top:0; min-height:100vh; min-height:100dvh;\E|position:sticky; top:76px; min-height:calc(100vh - 76px); min-height:calc(100dvh - 76px);|;
  s|\Qjustify-content:center; align-items:center;\E\s*\n\s*\Qpadding:56px 0; overflow:hidden;\E|justify-content:flex-start; align-items:center;\n    padding:20px 0 20px; overflow:hidden;|s;
  s|\Qwidth:min(680px, 92vw); aspect-ratio:1;\E\s*\n\s*\Qmargin:24px auto 0; flex:none;\E|width:min(600px, 44vw, 48vh); aspect-ratio:1;\n    margin:10px auto 0; flex:none;|s;

  s|\Qposition:absolute; width:220px;\E\s*\n\s*\Qtransform:translate(-50%,-50%);\E|position:absolute; width:clamp(200px, 22vw, 300px);\n    --lbl-gap:clamp(16px, 2.4vw, 32px);|s;
  s|\Qfont-size:0.82rem; color:var(--accent-strong)\E|font-size:1.05rem; color:var(--accent-strong)|;
  s|\Q.clock-label h3{ font-size:1.15rem;\E|.clock-label h3{ font-size:1.75rem;|;
  s|\Q.clock-label p{ font-size:0.86rem; line-height:1.5; color:var(--text-dim);\E|.clock-label p{ font-size:1.15rem; line-height:1.6; color:color-mix(in srgb, var(--text) 84%, var(--text-dim));|;

  s|\Q.clock-label[data-pos="1"]{ left:96%; top:16%; text-align:left; }\E|.clock-label[data-pos="1"]{ left:100%; top:16%; transform:translate(0,-50%); margin-left:var(--lbl-gap); text-align:left; }|;
  s|\Q.clock-label[data-pos="2"]{ left:96%; top:84%; text-align:left; }\E|.clock-label[data-pos="2"]{ left:100%; top:84%; transform:translate(0,-50%); margin-left:var(--lbl-gap); text-align:left; }|;
  # the dial stops at 83% of the frame, so the bottom step tucks into the empty
  # band rather than hanging below the frame where the viewport ran out
  s|\Q.clock-label[data-pos="3"]{ left:50%; top:114%; text-align:center; }\E|.clock-label[data-pos="3"]{ left:50%; top:86%; transform:translate(-50%,0); margin-top:10px; text-align:center; }|;
  s|\Q.clock-label[data-pos="4"]{ left:4%; top:84%; text-align:right; }\E|.clock-label[data-pos="4"]{ right:100%; top:84%; transform:translate(0,-50%); margin-right:var(--lbl-gap); text-align:right; }|;
  s|\Q.clock-label[data-pos="5"]{ left:4%; top:16%; text-align:right; }\E|.clock-label[data-pos="5"]{ right:100%; top:16%; transform:translate(0,-50%); margin-right:var(--lbl-gap); text-align:right; }|;

  # Mobile: the labels used to sit in the flow inside a frame with a fixed
  # aspect-ratio, so they spilled past the square and the stage clipped them.
  # Taking them out of the flow lets the frame keep its shape while the active
  # step shows underneath, and every size is capped against viewport height so
  # heading, dial and step all fit on one screen.
  s|\Q.clock-frame{ width:min(280px, 62vw); margin-top:16px; }\E\s*\n\s*\Q.clock-label{\E\s*\n\s*\Qposition:static; transform:none; width:auto; max-width:44ch;\E\s*\n\s*\Qmargin:0 auto; text-align:center !important;\E\s*\n\s*\Qmax-height:0; overflow:hidden;\E\s*\n\s*\Q}\E\s*\n\s*\Q.clock-label.is-active{ max-height:220px; margin-top:26px; }\E|.clock-stage{ height:calc(100dvh - 76px); padding:16px 0 24px; }\n    .clock-stage .section-head h2{ font-size:clamp(1.6rem, 6.4vw, 2.1rem); }\n    .clock-stage .section-head p{ font-size:0.94rem; }\n    .clock-frame{ width:min(260px, 58vw, 32vh); margin-top:12px; }\n    .clock-label{\n      position:absolute; left:50%; right:auto; top:100%;\n      transform:translate(-50%,0);\n      width:min(86vw, 42ch); max-width:none;\n      margin:16px 0 0; text-align:center !important;\n      max-height:none; overflow:visible;\n    }\n    .clock-label[data-pos]{ left:50%; right:auto; top:100%; transform:translate(-50%,0); margin:16px 0 0; }\n    .clock-label.is-active{ max-height:none; margin-top:16px; }\n    .clock-label h3{ font-size:1.45rem; }\n    .clock-label p{ font-size:1.02rem; }|s;

  # a step held at full opacity across a plateau, instead of peaking only at its
  # exact centre point — that peak was why the copy always read as half-faded
  s|\Qconst opacity = Math.max(0, 1 - dist / 0.135);\E|const opacity = dist <= 0.07 ? 1 : Math.max(0, 1 - (dist - 0.07) / 0.055);|;
' "$OUT"

# 4. Append the right-hand jump rail.
perl -0777 -i -pe '
  BEGIN{ local $/; open my $f, "<:raw", "rail-snippet.html" or die "missing rail-snippet.html"; $S = <$f>; }
  s|</body></html>|$S</body></html>|;
' "$OUT"

for marker in "justify-content:flex-start; align-items:center;" "width:min(600px, 44vw, 48vh)" "width:min(260px, 58vw, 32vh)" "clamp(200px, 22vw, 300px)" "dist <= 0.07" "clock-rail" "Étapes de notre histoire" "Spécialiste indépendant"; do
  printf '%-46s %s\n' "$marker" "$(grep -c -- "$marker" "$OUT" || true)"
done
echo "size: $(du -h "$OUT" | cut -f1)"
