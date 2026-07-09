#!/usr/bin/env python3
"""Phase 4: Convert anchor PNG renders -> lossless WebP for the app.

Source PNGs (Blender, high-res) live OUTSIDE the repo, one folder per sky/exposure:
  <SRC>/Overcast_AnchorRenders/Exp090/Overcast_090NNNN.png    (NNNN = 0001..0202)
  <SRC>/ClearSky_AnchorRenders/Exp075/ClearSky_Exp075NNNN.png (NNNN = 0001..0202)

Mapping: Blender frame N -> per-config cid = N (1-based; frame N = cid N).
Output: App_Data/Anchor_Renders/{Overcast,PartlyClear}/anchor_<cid>.webp
        cid zero-padded to >=2 digits (1->"01", 5->"05", 202->"202").

Two skies ship in the app: Overcast (default) + Partly Clear. The "Partly Clear"
render is the ClearSky Exp075 batch; the app shows the display label "Partly Clear"
but the on-disk folder is space-free ("PartlyClear") to keep the URL paths clean.

Lossless only (lossy visibly degrades glass). Verifies pixel-identical after save.
"""
import sys
from pathlib import Path
from PIL import Image, ImageChops

SRC = Path(r"C:\Users\14084\Documents\Blender_Renderings\IGUConfigurator_RenderingModel\AnchorRenders")
DST = Path(__file__).resolve().parents[2] / "App_Data" / "Anchor_Renders"

# (source subfolder, source filename builder from frame, destination folder name)
SKIES = [
    ("Overcast_AnchorRenders/Exp090",  lambda f: f"Overcast_090{f:04d}.png",    "Overcast"),
    ("ClearSky_AnchorRenders/Exp075",  lambda f: f"ClearSky_Exp075{f:04d}.png", "PartlyClear"),
]
N_FRAMES = 202  # frames 0001..0202 -> cid 1..202 (1-based; frame N = cid N)


def main():
    total, failures = 0, []
    for sub, namefn, dstname in SKIES:
        srcdir = SRC / sub
        dstdir = DST / dstname
        dstdir.mkdir(parents=True, exist_ok=True)
        if not srcdir.is_dir():
            sys.exit(f"ERROR: missing source folder {srcdir}")
        for frame in range(1, N_FRAMES + 1):
            cid = frame  # 1-based: frame N = cid N
            png = srcdir / namefn(frame)
            webp = dstdir / f"anchor_{cid:02d}.webp"
            if not png.is_file():
                sys.exit(f"ERROR: missing {png}")
            with Image.open(png) as im:
                im = im.convert("RGB")
                im.save(webp, "WEBP", lossless=True, method=6)
                # verify pixel-identical
                with Image.open(webp) as out:
                    diff = ImageChops.difference(im, out.convert("RGB")).getbbox()
                    if diff is not None:
                        failures.append(str(webp))
            total += 1
            if total % 40 == 0:
                print(f"  ...{total}/{N_FRAMES*len(SKIES)}")
        print(f"[{dstname}] {N_FRAMES} files -> {dstdir}")
    print(f"\nDone: {total} WebP written.")
    if failures:
        sys.exit(f"PIXEL MISMATCH in {len(failures)} files:\n" + "\n".join(failures))
    print("All files verified pixel-identical to source PNG.")


if __name__ == "__main__":
    main()
