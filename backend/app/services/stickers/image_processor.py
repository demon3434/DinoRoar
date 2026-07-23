import colorsys
import collections
import logging
from pathlib import Path
from PIL import Image, ImageFilter

logger = logging.getLogger("DinoRoar.image_processor")

def remove_background_and_shadow(input_path, output_path, tolerance: int = 60):
    """
    抠除纯白背景并保留自然 3D 阴影处理工具函数。
    1. 修正基准色采样，仅连通边缘 BFS 扣除纯白色背景，100% 完整保留恐龙肚皮、皮肤与脚下 3D 立体阴影。
    2. 清理肢体/腿缝间未连通的内部纯白像素。
    3. 平滑 Alpha 通道边缘并保存为 256x256 RGBA PNG 格式。
    """
    try:
        img = Image.open(input_path).convert("RGBA")
        w, h = img.size
        pix = img.load()

        corner_samples = [
            pix[0, 0], pix[w - 1, 0],
            pix[0, h - 1], pix[w - 1, h - 1],
            pix[w // 2, 0], pix[0, h // 2], pix[w - 1, h // 2]
        ]
        valid_samples = [c for c in corner_samples if c[3] > 200]

        if valid_samples:
            bg_r = sum(c[0] for c in valid_samples) // len(valid_samples)
            bg_g = sum(c[1] for c in valid_samples) // len(valid_samples)
            bg_b = sum(c[2] for c in valid_samples) // len(valid_samples)
        else:
            bg_r, bg_g, bg_b = 255, 255, 255

        visited = set()
        queue = collections.deque()

        for x in range(w):
            queue.append((x, 0))
            queue.append((x, h - 1))
        for y in range(h):
            queue.append((0, y))
            queue.append((w - 1, y))

        while queue:
            x, y = queue.popleft()
            if (x, y) in visited:
                continue
            visited.add((x, y))

            r, g, b, a = pix[x, y]
            if a == 0:
                for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < w and 0 <= ny < h and (nx, ny) not in visited:
                        queue.append((nx, ny))
                continue

            diff = abs(r - bg_r) + abs(g - bg_g) + abs(b - bg_b)

            if r > 230 and g > 230 and b > 230 and diff < tolerance:
                pix[x, y] = (r, g, b, 0)
                for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < w and 0 <= ny < h and (nx, ny) not in visited:
                        queue.append((nx, ny))

        for y in range(h):
            for x in range(w):
                if (x, y) not in visited:
                    r, g, b, a = pix[x, y]
                    if a > 0:
                        diff = abs(r - bg_r) + abs(g - bg_g) + abs(b - bg_b)
                        if r > 240 and g > 240 and b > 240 and diff < 30:
                            transparent_neighbors = 0
                            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                                nx, ny = x + dx, y + dy
                                if 0 <= nx < w and 0 <= ny < h and pix[nx, ny][3] == 0:
                                    transparent_neighbors += 1
                            if transparent_neighbors > 0:
                                pix[x, y] = (r, g, b, 0)

        alpha = img.split()[3]
        alpha_blurred = alpha.filter(ImageFilter.GaussianBlur(radius=0.3))
        img.putalpha(alpha_blurred)

        resized_img = img.resize((256, 256), Image.Resampling.LANCZOS)
        output_dir = Path(output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)
        resized_img.save(output_path, "PNG")
        logger.info(f"Successfully processed clean white bg transparent sticker: {output_path}")
        return True
    except Exception as e:
        logger.error(f"Failed processing image background removal for {input_path}: {e}")
        return False
