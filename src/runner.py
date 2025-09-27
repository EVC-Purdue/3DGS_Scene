import os
from concurrent.futures import ThreadPoolExecutor
import subprocess
from sys import stdout

os.chdir('/workspace/3DGS_scene/src')

def get_video_frames():
    def process_video(args):
        i, v = args
        print(f"Processing Video {i}: {v}")
        os.mkdir(f'./video_frames/{v}')
        subprocess.run(
            f"ffmpeg -hide_banner -loglevel error -i ./videos/{v} ./video_frames/{v}/image_%06d.JPEG",
            shell=True, check=True
        )

    videos = os.listdir('./videos')
    with ThreadPoolExecutor(max_workers=8) as executor:
        executor.map(process_video, enumerate(videos))


# Masks
import os, cv2, numpy as np

IMG_EXTS = {".jpg", ".jpeg", ".png", ".JPG", ".JPEG", ".PNG"}


def is_image(p): return os.path.splitext(p)[1] in IMG_EXTS


def make_sky_mask(img):
    h, w = img.shape[:2]
    small = cv2.resize(img, (w // 2, h // 2), interpolation=cv2.INTER_AREA) if max(h, w) > 2000 else img
    scale = img.shape[1] / small.shape[1]

    hsv = cv2.cvtColor(small, cv2.COLOR_BGR2HSV)
    H, S, V = cv2.split(hsv)

    # Sky candidates: bright & desaturated OR bluish hues
    cand1 = (S < 60) & (V > 160)
    cand2 = ((H > 90) & (H < 140)) & (S > 30) & (V > 80)  # tweak if sky is grey
    sky_cand = (cand1 | cand2).astype(np.uint8) * 255

    # Edge barrier to avoid flooding into ground/structures
    edges = cv2.Canny(cv2.GaussianBlur(cv2.cvtColor(small, cv2.COLOR_BGR2GRAY), (5, 5), 0), 80, 160)
    barrier = cv2.dilate(edges, np.ones((3, 3), np.uint8), iterations=1)

    # Flood-fill from the top border using sky candidates as a guide
    ff_mask = np.zeros((small.shape[0] + 2, small.shape[1] + 2), np.uint8)
    flood_src = sky_cand.copy()
    flood_src[barrier > 0] = 0
    # seed along top row
    for x in range(0, small.shape[1], max(1, small.shape[1] // 64)):
        if flood_src[0, x] > 0:
            cv2.floodFill(flood_src, ff_mask, (x, 0), 255, flags=8)
    sky = (flood_src == 255).astype(np.uint8) * 255

    # Cleanup and upscale
    sky = cv2.morphologyEx(sky, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8), iterations=1)
    if scale != 1.0:
        sky = cv2.resize(sky, (w, h), interpolation=cv2.INTER_NEAREST)

    # COLMAP expects black=ignored, white=used. We want to ignore sky.
    mask = np.ones((h, w), np.uint8) * 255
    mask[sky == 255] = 0
    return mask


def process_tree(image_root, mask_root):
    for root, _, files in os.walk(image_root):
        for fn in files:
            if not is_image(fn): continue
            img_path = os.path.join(root, fn)
            rel = os.path.relpath(img_path, image_root)
            out_dir = os.path.join(mask_root, os.path.dirname(rel))
            os.makedirs(out_dir, exist_ok=True)
            # COLMAP rule: mask filename = original filename + ".png"
            out_path = os.path.join(out_dir, fn + ".png")

            img = cv2.imread(img_path, cv2.IMREAD_COLOR)
            mask = make_sky_mask(img)
            cv2.imwrite(out_path, mask)


def get_masks(args):
    i, v = args
    print(f"Processing {i}: {v}")

with ThreadPoolExecutor(max_workers=8) as executor:
    executor.map(get_masks, enumerate(os.listdir('./videos')))


subprocess.run('process.sh', stdout=stdout, stderr=stdout)