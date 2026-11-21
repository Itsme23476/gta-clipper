#!/usr/bin/env python3
"""Windows and Linux stand-in for vision.swift, using OpenCV and Pillow. Same commands, same output:
  vision.py faces IMG...     one line per image: "x y width" of each face (0-1, y from top), clearest first and
                             split by ";", or "null"
  vision.py captions SPEC    draw the transparent caption images listed in a JSON spec, one or more lines each
"""
import json
import math
import sys
from functools import lru_cache
from pathlib import Path

try:
    import cv2
    from PIL import Image, ImageDraw, ImageFilter, ImageFont
except ImportError:
    sys.exit("Missing OpenCV or Pillow. Ask the user before installing them: pip install opencv-python-headless pillow")

# YuNet face detector, MIT licence: https://github.com/opencv/opencv_zoo/tree/main/models/face_detection_yunet
MODEL = Path(__file__).resolve().parent / "face_detection_yunet_2023mar.onnx"
# The styles name macOS fonts. Each maps to the closest font that ships with Windows, then to one on a Mac.
FONTS = {
    "Arial Black": ["ariblk.ttf", "Arial Black.ttf"],
    "Arial-Black": ["ariblk.ttf", "Arial Black.ttf"],
    "HelveticaNeue-Bold": ["arialbd.ttf", "Arial Bold.ttf"],
    "HelveticaNeue-Medium": ["seguisb.ttf", "Arial.ttf"],
    "SnellRoundhand-Bold": ["segoescb.ttf", "SnellRoundhand.ttc"],
    "Didot-Bold": ["georgiab.ttf", "Georgia Bold.ttf"],
    "AvenirNext-Heavy": ["seguibl.ttf", "Arial Black.ttf"],
    "AvenirNext-DemiBold": ["seguisb.ttf", "Arial Bold.ttf"],
    "Charter-Black": ["georgiab.ttf", "Georgia Bold.ttf"],
}
FALLBACK = ["arialbd.ttf", "Arial Bold.ttf", "LiberationSans-Bold.ttf", "DejaVuSans-Bold.ttf"]  # last two: Linux


def faces(paths):
    detector = None
    for p in paths:
        img = cv2.imread(p)
        if img is None:
            print("null")
            continue
        h, w = img.shape[:2]
        img = cv2.resize(img, (w * 2, h * 2))  # a streamer's face can be 25 pixels wide in a 640-wide frame
        if detector is None:
            detector = cv2.FaceDetectorYN.create(str(MODEL), "", (w * 2, h * 2), 0.7)
        detector.setInputSize((w * 2, h * 2))
        found = detector.detect(img)[1]
        if found is None:
            print("null")
            continue
        # most confident first, not largest: a webcam face scores about 0.93, a GTA character under 0.87
        print(";".join(f"{(x + fw / 2) / (w * 2)} {(y + fh / 2) / (h * 2)} {fw / (w * 2)}"
                       for x, y, fw, fh in (f[:4] for f in sorted(found, key=lambda f: -f[-1]))))


@lru_cache(None)
def font(name, size):
    """A font file for a style's font name. A path to a .ttf, .otf or .ttc file also works."""
    own = [name] if name.lower().endswith((".ttf", ".otf", ".ttc")) else []
    for f in own + FONTS.get(name, []) + FALLBACK:
        try:
            return ImageFont.truetype(f, size)
        except OSError:
            pass
    return ImageFont.load_default(size)


def rgba(s, alpha=255):
    v = int(s.lstrip("#") or "0", 16)
    return (v >> 16 & 255, v >> 8 & 255, v & 255, alpha)


def runs(k, words, fit):
    """[(text, font, colour or None while hidden)] for one line. Each space takes the font of the word after it."""
    out = []
    for i, w in enumerate(words):
        size = k["size"] * fit
        if w["hl"]:  # c, f, z: a highlighted word's own colour, font and size multiplier
            z = w["z"] if w.get("z") is not None else k["highlight_scale"]
            f = font(w.get("f") or k["highlight_font"] or k["font"], max(1, round(size * z)))
        else:
            f = font(k["font"], max(1, round(size)))
        colour = rgba(w.get("c") or (k["highlight"] if w["hl"] else k["color"])) if w["on"] else None
        out.append(((" " if i else "") + w["t"], f, colour))
    return out


def width(line):
    return sum(f.getlength(t) for t, f, _ in line)


def captions(path):
    s = json.loads(Path(path).read_text(encoding="utf-8"))
    W, H = s["width"], s["height"]
    max_w = W - 100
    for item in s["items"]:
        k = item["look"]
        img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        # a line too wide for the frame shrinks to fit, instead of wrapping out of the caption strip
        fits = [min(1, max_w / max(width(runs(k, ws, 1)), 1)) for ws in item["lines"]]
        lines = [runs(k, ws, fit) for ws, fit in zip(item["lines"], fits)]
        heights = [max(sum(f.getmetrics()) for _, f, _ in line) for line in lines]
        gap = -0.12 * k["size"] if len(lines) > 1 else 0  # stacked lines sit tight
        top = (H - sum(heights) - gap * (len(lines) - 1)) / 2
        rects = []
        for i, (line, lh) in enumerate(zip(lines, heights)):  # each line centred, then stepped right by `stagger`
            w = math.ceil(width(line)) + 2
            x = 0.12 * W if k["align"] == "left" else (W - w) / 2 + (i - (len(lines) - 1) / 2) * k["stagger"]
            rects.append((min(max(x, 10), W - w - 10), top, w, lh))
            top += lh + gap
        draw = ImageDraw.Draw(img)
        if k["box"] and rects:
            pad_x, pad_y = 0.3 * k["size"], 0.1 * k["size"]
            draw.rectangle((min(r[0] for r in rects) - pad_x, min(r[1] for r in rects) - pad_y,
                            max(r[0] + r[2] for r in rects) + pad_x, max(r[1] + r[3] for r in rects) + pad_y),
                           fill=rgba(k["box"]))

        def paint(canvas, colour=None, offset=0, stroke=False):
            d = ImageDraw.Draw(canvas)
            for line, (x, y, _, _) in zip(lines, rects):
                base = y + max(f.getmetrics()[0] for _, f, _ in line)  # one baseline for big and small words
                for t, f, c in line:
                    if c:
                        sw = round(k["stroke_width"] / 100 * f.size / 2) if stroke else 0  # % of the font size
                        d.text((x, base + offset), t, font=f, fill=colour or c, anchor="ls",
                               stroke_width=sw, stroke_fill=rgba(k["stroke"]) if sw else None)
                    x += f.getlength(t)

        if k["shadow"] > 0:  # a soft drop shadow, drawn twice for a darker halo on light shirts
            layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            paint(layer, (0, 0, 0, 204), offset=k["shadow"] / 4)
            layer = layer.filter(ImageFilter.GaussianBlur(k["shadow"] / 2))
            img.alpha_composite(layer)
            img.alpha_composite(layer)
        paint(img, stroke=k["stroke_width"] > 0)
        img.save(item["path"])


if __name__ == "__main__":
    args = sys.argv[1:]
    if args[:1] == ["faces"]:
        faces(args[1:])
    elif args[:1] == ["captions"] and len(args) == 2:
        captions(args[1])
    else:
        sys.exit("usage: vision.py faces IMG... | vision.py captions SPEC")
