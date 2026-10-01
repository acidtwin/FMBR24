"""Cut a generated icon sheet (3 columns x 2 rows of 512 px cells on one flat dark background) into transparent PNGs.

Usage: python3 scripts/cut_icon_sheet.py SHEET.png OUT_DIR name1 name2 name3 name4 name5 name6 [--cols 3] [--rows 2]

Background removal is a colour un-mix, not a threshold: each pixel is modelled as bg + a * (fg - bg) with fg one of the
sheet's two ink colours (off-white or the purple accent, estimated from the sheet itself), so anti-aliased edges keep
their true colour and get a smooth alpha (no dark halo when the icon is drawn on another background).
"""
import argparse
import os

import numpy as np
from PIL import Image


def estimate(rgb):
    h, w, _ = rgb.shape
    border = np.concatenate([rgb[:12].reshape(-1, 3), rgb[-12:].reshape(-1, 3)])
    bg = np.median(border, axis=0)
    px = rgb.reshape(-1, 3).astype(float)
    white = np.median(px[px.min(axis=1) > 200], axis=0)
    purple_mask = (px[:, 2] - px[:, 1] > 90) & (px[:, 2] > 200)
    purple = np.median(px[purple_mask], axis=0) if purple_mask.any() else white
    return bg, white, purple


def unmix(rgb, bg, inks):
    p = rgb.astype(float) - bg
    best_a = None
    best_err = None
    best_ink = None
    for ink in inks:
        d = ink - bg
        a = np.clip((p @ d) / (d @ d), 0.0, 1.0)
        err = ((p - a[..., None] * d) ** 2).sum(axis=-1)
        if best_err is None:
            best_a, best_err, best_ink = a, err, np.broadcast_to(ink, rgb.shape).copy()
        else:
            m = err < best_err
            best_a = np.where(m, a, best_a)
            best_err = np.where(m, err, best_err)
            best_ink[m] = ink
    best_a[best_a < 0.04] = 0.0           # kill sensor-level noise in the flat background
    out = np.dstack([np.clip(best_ink, 0, 255), best_a * 255.0]).round().astype(np.uint8)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('sheet')
    ap.add_argument('out_dir')
    ap.add_argument('names', nargs='+')
    ap.add_argument('--cols', type=int, default=3)
    ap.add_argument('--rows', type=int, default=2)
    ap.add_argument('--size', type=int, default=512, help='cell size in the sheet (px)')
    a = ap.parse_args()
    im = Image.open(a.sheet).convert('RGB')
    if im.size != (a.cols * a.size, a.rows * a.size):
        im = im.resize((a.cols * a.size, a.rows * a.size), Image.LANCZOS)
        print('resized sheet to', im.size)
    rgb = np.array(im)
    bg, white, purple = estimate(rgb)
    print('bg', bg, 'white', white, 'purple', purple)
    os.makedirs(a.out_dir, exist_ok=True)
    for i, name in enumerate(a.names):
        r, c = divmod(i, a.cols)
        cell = rgb[r * a.size:(r + 1) * a.size, c * a.size:(c + 1) * a.size]
        rgba = unmix(cell, bg, [white, purple])
        Image.fromarray(rgba, 'RGBA').save(os.path.join(a.out_dir, name + '.png'))
        print('wrote', name)


if __name__ == '__main__':
    main()
