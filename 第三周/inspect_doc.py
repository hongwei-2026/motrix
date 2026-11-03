import json
import re

d = json.load(open(r"D:\motrix\第三周\_fetch.json", encoding="utf-8-sig"))
md = d["data"]["markdown"]
open(r"D:\motrix\第三周\_fetch_md.md", "w", encoding="utf-8").write(md)

print("images:")
for m in re.finditer(r"<image [^>]+/>", md):
    print(m.group(0)[:140])

marks = ["[[SHOT_OBS]]", "[[SHOT_ACT]]", "[[SHOT_RWD]]", "[[SHOT_TERM]]", "[[SHOT_TRUNC]]"]
print("markers:", {m: (m in md) for m in marks})

i = md.find("三、代码阅读")
print("---SEC3---")
print(md[i:])
