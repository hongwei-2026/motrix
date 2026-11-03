from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

OUT = Path(r"D:\motrix\第三周\截图")
OUT.mkdir(parents=True, exist_ok=True)

candidates = [
    r"C:\Windows\Fonts\consola.ttf",
    r"C:\Windows\Fonts\CascadiaMono.ttf",
    r"C:\Windows\Fonts\cour.ttf",
]
font_path = next((p for p in candidates if Path(p).exists()), None)
font_ui = r"C:\Windows\Fonts\msyh.ttc" if Path(r"C:\Windows\Fonts\msyh.ttc").exists() else font_path

snippets = [
    {
        "name": "01_观测_get_obs",
        "caption": "观测 walk_np.py _init_obs_space + _get_obs",
        "file": r"D:\motrix\MotrixLab\motrix_envs\src\motrix_envs\locomotion\go1\walk_np.py",
        "ranges": [(48, 59), (188, 213)],
    },
    {
        "name": "02_动作_apply_action",
        "caption": "动作 walk_np.py apply_action + _compute_torques",
        "file": r"D:\motrix\MotrixLab\motrix_envs\src\motrix_envs\locomotion\go1\walk_np.py",
        "ranges": [(160, 174)],
    },
    {
        "name": "03_奖励_update_reward",
        "caption": "奖励 walk_np.py update_reward",
        "file": r"D:\motrix\MotrixLab\motrix_envs\src\motrix_envs\locomotion\go1\walk_np.py",
        "ranges": [(249, 264)],
    },
    {
        "name": "04_失败终止_update_terminated",
        "caption": "失败终止 walk_np.py update_terminated",
        "file": r"D:\motrix\MotrixLab\motrix_envs\src\motrix_envs\locomotion\go1\walk_np.py",
        "ranges": [(224, 233)],
    },
    {
        "name": "05_截断与重置_env",
        "caption": "截断+重置 np/env.py truncate + reset + step",
        "file": r"D:\motrix\MotrixLab\motrix_envs\src\motrix_envs\np\env.py",
        "ranges": [(112, 125), (141, 147), (195, 207)],
    },
]

BG = (30, 30, 30)
FG = (212, 212, 212)
LN = (128, 128, 128)
HDR = (40, 40, 40)
ACCENT = (86, 156, 214)
PAD = 24
LH = 22
FS = 15


def load_font(size, path=font_path):
    if path:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            pass
    return ImageFont.load_default()


code_font = load_font(FS)
header_font = load_font(14, font_ui)


def render(snippet):
    src = Path(snippet["file"]).read_text(encoding="utf-8").splitlines()
    lines = []
    rel = Path(snippet["file"]).name
    for a, b in snippet["ranges"]:
        if lines:
            lines.append((None, ""))
        for i in range(a, b + 1):
            lines.append((i, src[i - 1]))

    header = f"{rel}  |  {snippet['caption']}"
    max_code = max((len(t) for _, t in lines), default=0)
    width = max(960, PAD * 2 + 70 + max_code * 9)
    height = PAD * 2 + 40 + LH * (len(lines) + 1)

    img = Image.new("RGB", (width, height), BG)
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 0, width, 36], fill=HDR)
    draw.text((PAD, 10), header, fill=ACCENT, font=header_font)

    y = 48
    for ln, text in lines:
        if ln is None:
            y += LH // 2
            continue
        draw.text((PAD, y), f"{ln:4d}", fill=LN, font=code_font)
        draw.text((PAD + 60, y), text.replace("\t", "    "), fill=FG, font=code_font)
        y += LH

    out = OUT / f"{snippet['name']}.png"
    img.save(out)
    print("wrote", out, img.size)


for s in snippets:
    render(s)
print("DONE")
