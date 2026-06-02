# Visual Line Safety Fix - 2026-06-02

## Scope

This update keeps `NhapMonAI` aligned with the English-facing engineering portfolio while removing dash-line motion from SVG visuals.

## Changes

- Cleaned `assets/portfolio-motion.svg` so SVG motion no longer uses moving dashed or dotted line effects.
- Adjusted portfolio-card title sizing so long English project names fit without clipping.
- Preserved ASCII-safe English SVG text and existing non-line motion such as pulse, shimmer, float or scan effects.
- Kept repository claims evidence-first and bounded to the source tree, reports, releases and visual assets.

## Review Context

The latest release points to the commit containing this visual cleanup, so GitHub README embeds and release assets can be reviewed from a stable tag.
