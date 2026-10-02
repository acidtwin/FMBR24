#!/usr/bin/env python3
"""Regenerate resources/icon.svg from resources/icon-source.png.

The SVG is layered pieces only: no raster, no <text>, no filters, no clipPath.
  * silhouette, top-left bevel band and the FMBR / 24 letters are traced with
    potrace from sub-pixel masks (source upscaled 4x with bicubic, thresholded
    at the mid-level of the two colours meeting at that edge);
  * shutter, recess, window, label plate / rim / panel are rounded rects whose
    box and corner radius were measured from the same masks (RECTS below);
  * every fill is a flat colour or a linear gradient fitted to the source
    pixels that are actually visible for that layer (least-squares direction,
    binned colour curve, Douglas-Peucker reduced to a few stops).

potrace parameters (all runs: -u 10 = 0.1 unit grid on the 4x bitmap, i.e. 0.025 px;
-t = turdsize, specks smaller than N px at 4x are dropped; -a = alphamax, corner
threshold; -O = opttolerance, curve optimisation, in 4x px):
  silhouette / bevel / edge light: -t 20 -a 1.2 -O 5.0 (smooth outline, few nodes)
  letters:                         -t 8  -a 0.6 -O 1.0 (stays crisp at the corners)
The silhouette mask is blurred (sigma 1 px) and closed (r 2 px) first, to drop the
1 px dark specks on the source's right edge.

Known limits: QtSvg ignores clipPath, so shapes that share the silhouette's top edge
(shutter, recess) overlap it in the antialiased edge row; at tiny sizes that edge is
slightly more opaque than the source. Gradient seam of the bevel is hidden with a
stop-opacity ramp (QtSvg and rsvg both honour stop-opacity).

Usage:  python3 scripts/make_icon_svg.py [out.svg]   (needs potrace, Pillow, numpy)
"""
import math
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "resources" / "icon-source.png"
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "resources" / "icon.svg"
N, SS = 1024, 4  # image size, supersampling for traced masks

img = np.array(Image.open(SRC).convert("RGBA")).astype(float)
RGB, ALPHA = img[..., :3], img[..., 3]
R, G, B = RGB[..., 0], RGB[..., 1], RGB[..., 2]

# Measured geometry (px, SVG user space = image px). (x0, y0, x1, y1, r, rounded corners tl,tr,br,bl)
RECTS = dict(
    recess=(270.75, 59.25, 775.95, 367.35, 52.9, (0, 0, 1, 1)),
    shutter_rim=(772.35, 58.5, 779.15, 367.5, 0, (0, 0, 0, 0)),  # light line right of the shutter / recess
    shutter=(307.1, 57.4, 775.65, 353.4, 36.0, (0, 0, 1, 1)),
    shutter_hi=(307.25, 57.4, 775.55, 79.9, 0, (0, 0, 0, 0)),
    win_rim=(577.6, 104.4, 716.0, 319.25, 19, (1, 1, 1, 1)),
    window=(578.75, 105.6, 712.15, 315.35, 15.75, (1, 1, 1, 1)),
    plate=(136.5, 424.3, 885.0, 892.25, 52.5, (1, 1, 1, 1)),
    rim_lip=(144.4, 441.2, 888.8, 897.15, 53.0, (1, 1, 1, 1)),  # light halo right of / under the rim
    rim=(144.4, 439.65, 885.85, 895.55, 51.05, (1, 1, 1, 1)),
    shadow=(148.45, 453.35, 876.0, 882.45, 42.0, (1, 1, 1, 1)),  # dark hairline, bottom-right of panel
    edge=(148.9, 452.35, 873.75, 879.25, 40.35, (1, 1, 1, 1)),    # grey hairline, top-left of panel
    panel=(151.3, 455.75, 874.2, 881.5, 39.45, (1, 1, 1, 1)),
)


# ---------------------------------------------------------------- masks ----
def up(field):
    return np.array(Image.fromarray(field.astype(np.float32), "F").resize((N * SS, N * SS), Image.BICUBIC))


def lores(hi):
    return hi.reshape(N, SS, N, SS).mean(axis=(1, 3))


def rrect_hi(x0, y0, x1, y1, r, corners):
    im = Image.new("L", (N * SS, N * SS), 0)
    ImageDraw.Draw(im).rounded_rectangle((x0 * SS, y0 * SS, x1 * SS - 1, y1 * SS - 1), max(r, 0) * SS, fill=255,
                                         corners=tuple(bool(c) for c in corners))
    return np.array(im) > 127


def erode_px(m, px):
    if px <= 0:
        return m
    return np.array(Image.fromarray(m.astype(np.uint8) * 255).filter(ImageFilter.MinFilter(2 * px + 1))) > 127


def disc_erode_hi(m, rad, outside=False):
    """erosion of a hi-res bool mask by a disc (rad hi-res px), 32-gon approximation"""
    out = m.copy()
    for k in range(32):
        a = 2 * math.pi * k / 32
        dx, dy = int(round(rad * math.cos(a))), int(round(rad * math.sin(a)))
        sh = np.full_like(m, outside)
        sh[max(0, dy):m.shape[0] + min(0, dy), max(0, dx):m.shape[1] + min(0, dx)] = \
            m[max(0, -dy):m.shape[0] - max(0, dy), max(0, -dx):m.shape[1] - max(0, dx)]
        out &= sh
    return out


def dilate_hi(m, rad):
    return ~disc_erode_hi(~m, rad, outside=True)


# --------------------------------------------------------------- potrace ---
def trace(hi, alphamax=1.0, opt=0.4, turd=8):
    """hi-res bool mask -> svg path data in image px (2 decimals)"""
    with tempfile.TemporaryDirectory() as td:
        pbm, svg = Path(td) / "m.pbm", Path(td) / "m.svg"
        Image.fromarray(np.where(hi, 0, 255).astype(np.uint8)).convert("1").save(pbm)
        subprocess.run(["potrace", "-s", "-u", "10", "-t", str(turd), "-a", str(alphamax),
                        "-O", str(opt), "-o", str(svg), str(pbm)], check=True)
        txt = svg.read_text()
    tx, ty, sx, sy = map(float, re.search(r"translate\(([-\d.]+),([-\d.]+)\) scale\(([-\d.]+),([-\d.]+)\)", txt).groups())
    d = " ".join(re.findall(r'<path d="([^"]+)"', txt, re.S))  # one <path> per outer component
    toks = re.findall(r"[MmCcLlZz]|-?\d+(?:\.\d+)?", d)
    fmt = lambda v: ("%.2f" % v).rstrip("0").rstrip(".")
    pt = lambda x, y: "%s %s" % (fmt((tx + sx * x) / SS), fmt((ty + sy * y) / SS))
    out, i, cx, cy, cmd = [], 0, 0.0, 0.0, None
    while i < len(toks):
        if re.match(r"[A-Za-z]", toks[i]):
            cmd = toks[i]
            i += 1
            if cmd in "zZ":
                out.append("Z")
                continue
        rel, c = cmd.islower(), cmd.upper()
        if c in "ML":
            x, y = float(toks[i]), float(toks[i + 1]); i += 2
            if rel:
                x, y = cx + x, cy + y
            cx, cy = x, y
            out.append(c + pt(x, y))
            cmd = "L" if c == "M" else cmd  # implicit lineto after moveto
            cmd = cmd.lower() if rel else cmd
        else:  # C
            v = [float(t) for t in toks[i:i + 6]]; i += 6
            p = [(v[0], v[1]), (v[2], v[3]), (v[4], v[5])]
            if rel:
                p = [(cx + a, cy + b) for a, b in p]
            cx, cy = p[2]
            out.append("C" + " ".join(pt(*q) for q in p))
    return "".join(out)


# ------------------------------------------------------ gradient fitting ---
def _simplify(ts, cols, tol):
    def rec(a, b):
        if b <= a + 1:
            return [a, b]
        best, bi = 0.0, None
        for k in range(a + 1, b):
            w = (ts[k] - ts[a]) / (ts[b] - ts[a])
            e = np.abs(cols[a] * (1 - w) + cols[b] * w - cols[k]).max()
            if e > best:
                best, bi = e, k
        if best <= tol:
            return [a, b]
        return rec(a, bi)[:-1] + rec(bi, b)
    return [(ts[i], cols[i]) for i in rec(0, len(ts) - 1)]


def hexc(c):
    return "#%02x%02x%02x" % tuple(int(round(min(255, max(0, v)))) for v in c)


class Fills:
    def __init__(self):
        self.defs, self.n = [], 0

    def fit(self, vis, tol=2.2, bins=28, flat_tol=3.0, fade=None):
        """flat colour or userSpaceOnUse linear gradient fitted to pixels of bool mask `vis`"""
        ys, xs = np.nonzero(vis)
        if len(xs) < 40:
            raise ValueError("layer has no visible pixels to fit (%d)" % len(xs))
        px, x, y = RGB[ys, xs], xs + 0.5, ys + 0.5
        if px.std(axis=0).max() < flat_tol:
            return hexc(np.median(px, axis=0))
        gx, gy, _ = np.linalg.lstsq(np.c_[x, y, np.ones_like(x)], px.mean(axis=1), rcond=None)[0]
        nrm = math.hypot(gx, gy)
        if nrm < 1e-6:
            return hexc(np.median(px, axis=0))
        ux, uy = gx / nrm, gy / nrm
        t = x * ux + y * uy
        edges = np.linspace(np.percentile(t, 0.5), np.percentile(t, 99.5), bins + 1)
        which = np.clip(np.digitize(t, edges) - 1, 0, bins - 1)
        ts, cols = [], []
        for b in range(bins):
            m = which == b
            if m.sum() > 12:
                ts.append((edges[b] + edges[b + 1]) / 2)
                cols.append(np.median(px[m], axis=0))
        stops = _simplify(np.array(ts), np.array(cols), tol)
        ta, tb = stops[0][0], stops[-1][0]
        tc = x.mean() * ux + y.mean() * uy
        p0 = (x.mean() + (ta - tc) * ux, y.mean() + (ta - tc) * uy)
        p1 = (x.mean() + (tb - tc) * ux, y.mean() + (tb - tc) * uy)
        gid = "g%d" % self.n
        self.n += 1
        off = lambda s: ("%.3f" % ((s - ta) / (tb - ta))).rstrip("0").rstrip(".") or "0"
        st = "".join('<stop offset="%s" stop-color="%s"/>' % (off(s), hexc(c)) for s, c in stops)
        if fade:  # fade the gradient in between image rows fade[0] .. fade[1] (stop-opacity ramp)
            tt = lambda yy: (x.mean() * ux + yy * uy)
            fa, fb = (min(max((tt(v) - ta) / (tb - ta), 0), 1) for v in fade)
            cs = lambda o: np.array([np.interp(ta + o * (tb - ta), [q[0] for q in stops], [q[1][k] for q in stops]) for k in range(3)])
            pts = sorted({0.0, 1.0, fa, fb} | {(q[0] - ta) / (tb - ta) for q in stops})
            op = lambda o: min(max((o - fa) / ((fb - fa) or 1e-6), 0), 1)
            st = "".join('<stop offset="%s" stop-color="%s"%s/>' % (("%.3f" % o).rstrip("0").rstrip(".") or "0", hexc(cs(o)),
                                                                   "" if op(o) >= 1 else ' stop-opacity="%.2f"' % op(o)) for o in pts)
        self.defs.append('<linearGradient id="%s" gradientUnits="userSpaceOnUse" x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f">%s</linearGradient>'
                         % (gid, p0[0], p0[1], p1[0], p1[1], st))
        return "url(#%s)" % gid


def rrect_svg(name, fill):
    x0, y0, x1, y1, r, c = RECTS[name]
    if r == 0:
        return '<rect x="%g" y="%g" width="%g" height="%g" fill="%s"/>' % (x0, y0, x1 - x0, y1 - y0, fill)
    if all(c):
        return '<rect x="%g" y="%g" width="%g" height="%g" rx="%g" fill="%s"/>' % (x0, y0, x1 - x0, y1 - y0, r, fill)
    assert c == (0, 0, 1, 1)  # square top, round bottom corners
    d = "M%g %gH%gV%ga%g %g 0 0 1-%g %gH%ga%g %g 0 0 1-%g-%gZ" % (
        x0, y0, x1, y1 - r, r, r, r, r, x0 + r, r, r, r, r)
    return '<path d="%s" fill="%s"/>' % (d, fill)


# ================================================================ build ====
def main():
    # ---- layer masks (hi-res bool), painter order bottom -> top
    fills_extra = {}
    L = []  # painter order, bottom -> top: (name, hi-res mask, svg builder(fill) -> str, fit erosion px)

    # alpha upscaled and blurred (sigma ~1 px) before thresholding: smooths the source's JPEG-ish edge noise
    sil_hi = np.array(Image.fromarray((up(ALPHA / 255.0) * 255).clip(0, 255).astype(np.uint8)).filter(
        ImageFilter.GaussianBlur(4))) > 127
    # closing (r = 2 px) removes the 1 px dark specks / notches on the source's right edge
    sil_hi = disc_erode_hi(dilate_hi(sil_hi, 8), 8)
    # bevel: 28 px band along top-left edge (outer edge pulled in 0.5 px to avoid double coverage)
    # inner outline = silhouette intersected with copies shifted right / down / diagonally: 28 px wide on the left
    # and top edges, 33 px (perpendicular) on the 45 degree chamfer, as measured in the source
    inner = sil_hi.copy()
    for dx, dy in ((28 * SS, 0), (0, 28 * SS), (int(23.3 * SS), int(23.3 * SS))):
        sh = np.zeros_like(sil_hi)
        sh[dy:, dx:] = sil_hi[:N * SS - dy, :N * SS - dx]
        inner &= sh
    bev_hi = disc_erode_hi(sil_hi, 2) & ~inner
    bev_hi[:, 272 * SS:] = False
    bev_hi[905 * SS:, :] = False
    L.append(("body", sil_hi, lambda f, p=trace(sil_hi, 1.2, 5.0, 20): '<path d="%s" fill="%s"/>' % (p, f), 3))
    # two pieces (chamfer+top strip / left strip): their gradients run in different directions
    bev_top, bev_left = bev_hi.copy(), bev_hi.copy()
    bev_top[215 * SS:] = False
    bev_left[:170 * SS] = False
    for nm, hi_ in (("bevel_top", bev_top), ("bevel_left", bev_left)):
        L.append((nm, hi_, lambda f, p=trace(hi_, 1.2, 5.0, 20): '<path d="%s" fill="%s"/>' % (p, f), 2))

    def rr(name, erode=2, tag=None):
        x0, y0, x1, y1, r, c = RECTS[name]
        L.append((tag or name, rrect_hi(x0, y0, x1, y1, r, c), lambda f, n=name: rrect_svg(n, f), erode))

    # edge light: 3 px line along the top-right chamfer / top edge right of the shutter
    ring = disc_erode_hi(sil_hi, 2) & ~disc_erode_hi(sil_hi, 12)
    ring[:, :272 * SS] = False
    ring[235 * SS:, :] = False
    L.append(("edge_light", ring, lambda f, p=trace(ring, 1.2, 5.0, 20): '<path d="%s" fill="%s"/>' % (p, f), 0))
    # soft lip: light line just under the recess
    x0, y0, x1, y1, r, c = RECTS["recess"]
    RECTS["lip"] = (x0, y0, x1, y1 + 3.0, r, c)
    for nme in ("lip", "recess", "shutter_rim", "shutter", "shutter_hi", "win_rim", "window", "plate", "rim_lip", "rim",
                "shadow", "edge", "panel"):
        rr(nme, 0 if nme in ("win_rim", "shadow", "edge", "lip", "rim_lip", "shutter_rim") else 2)
        if nme == "window":  # inner shadow along the window's top edge: translucent dark -> clear
            x0, y0, x1, y1, r, c = RECTS["window"]
            fills_extra["win_shade"] = (
                '<linearGradient id="gs" gradientUnits="userSpaceOnUse" x1="0" y1="%g" x2="0" y2="%g">'
                '<stop offset="0" stop-color="#1e0c3c" stop-opacity=".6"/><stop offset=".52" stop-color="#1e0c3c" stop-opacity=".6"/>'
                '<stop offset="1" stop-color="#1e0c3c" stop-opacity="0"/></linearGradient>' % (y0, y0 + 14))
            L.append(("win_shade", rrect_hi(x0, y0, x1, y1, r, c), lambda f, n="window": rrect_svg(n, f), 2))

    # text from colour masks
    white_hi = up(G) > 135
    white_hi[:, 649 * SS:] = False
    white_hi[:500 * SS] = False
    white_hi[:, :150 * SS] = False
    white_hi[760 * SS:] = False
    purple_hi = up(B) > 140
    purple_hi[:, :649 * SS] = False
    purple_hi[:500 * SS] = False
    purple_hi[760 * SS:] = False
    purple_hi[:, 872 * SS:] = False
    L.append(("text24", purple_hi, lambda f, p=trace(purple_hi, 0.6, 1.0, 8): '<path d="%s" fill="%s"/>' % (p, f), 2))
    L.append(("textFMBR", white_hi, lambda f, p=trace(white_hi, 0.6, 1.0, 8): '<path d="%s" fill="%s"/>' % (p, f), 2))

    lo = [lores(m) > 0.5 for _, m, _, _ in L]
    fills, body = Fills(), []
    for i, (name, hi, build, er) in enumerate(L):
        above = np.zeros((N, N), bool)
        for j in range(i + 1, len(L)):
            if L[j][0] != "win_shade":  # translucent overlay does not hide what is below
                above |= lo[j]
        vis = erode_px(lo[i] & ~above, er)
        if vis.sum() < 40:
            vis = lo[i] & ~above  # thin layer: no erosion
        if name == "win_shade":
            f = "url(#gs)"
        else:
            try:
                f = fills.fit(vis, flat_tol=6.0 if name not in ("body",) else 3.0,
                              fade=(190, 215) if name == "bevel_left" else None)
            except ValueError as e:
                raise ValueError("%s: %s" % (name, e))
        body.append("<!-- %s -->\n%s" % (name, build(f)))
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1024 1024" width="1024" height="1024">\n'
           "<!-- FMBR24 icon: generated by scripts/make_icon_svg.py from resources/icon-source.png -->\n"
           "<defs>\n%s\n</defs>\n%s\n</svg>\n" % ("\n".join(fills.defs + list(fills_extra.values())), "\n".join(body)))
    OUT.write_text(svg)
    print("wrote", OUT, len(svg), "bytes")


if __name__ == "__main__":
    main()
