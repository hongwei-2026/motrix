import json
import re

d = json.load(open(r"D:\motrix\第三周\_fetch.json", encoding="utf-8-sig"))
md = d["data"]["markdown"]
open(r"D:\motrix\第三周\_fetch_md.md", "w", encoding="utf-8").write(md)
i = md.find("三、代码阅读")
sec = md[i:]
print("len sec", len(sec))
print("images", len(re.findall(r"<image ", sec)))
for m in re.finditer(r"<image token=\"([^\"]+)\"[^/]*/>", sec):
    start = max(0, m.start() - 150)
    print("BEFORE:", repr(sec[start : m.start()][-120:]))
    print("IMG", m.group(1))
    print("---")
