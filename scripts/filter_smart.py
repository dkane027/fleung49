#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
过滤 M3U 播放列表中的成人分类/频道。

用法: python3 filter_smart.py [文件路径]   (默认 SMART)

规则:
  1. group-title 命中敏感词的整个分组全部删除
  2. 频道名命中硬核关键词的单条频道删除(即使所在分组名正常)
  3. 其余内容(包括 #EXTM3U 头、其他 # 开头行、普通注释)原样保留
"""
import re
import sys

# ---- 分组名/频道名都会检查的关键词(分组级整组删除) ----
GROUP_PATTERNS = [
    r"成年人",
    r"成人",
    r"\badult\b",
    r"18\+",
    r"\bxxx\b",
    r"porn",
    r"erotic",
]

# ---- 只对频道名额外检查的硬核关键词(避免误伤正常频道名) ----
NAME_PATTERNS = [
    r"\bxxx\b",
    r"\bporn\b",
    r"playboy",
    r"brazzers",
    r"hustler",
    r"penthouse",
    r"\bersotic\b",
    r"色情",
    r"裸聊",
    r"成年人",
]

GROUP_RE = re.compile("|".join(GROUP_PATTERNS), re.IGNORECASE)
NAME_RE = re.compile("|".join(NAME_PATTERNS), re.IGNORECASE)


def is_blocked(extinf_line: str) -> bool:
    m = re.search(r'group-title="([^"]*)"', extinf_line)
    group = m.group(1) if m else ""
    # #EXTINF:-1 attrs,频道名  -> 取最后一个逗号之后的部分
    name = extinf_line.rsplit(",", 1)[-1].strip()
    if GROUP_RE.search(group):
        return True
    if NAME_RE.search(name):
        return True
    return False


def filter_file(path: str) -> tuple[int, int]:
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        lines = f.read().splitlines()

    out = []
    removed = 0
    pending_extinf = None  # 等待配对 URL 行的 #EXTINF

    for line in lines:
        if line.startswith("#EXTINF"):
            pending_extinf = line
        elif pending_extinf is not None:
            # 当前这条是 URL 行(可能为空行,同样跟随 EXTINF)
            if line.strip() and not line.startswith("#"):
                if is_blocked(pending_extinf):
                    removed += 1
                else:
                    out.append(pending_extinf)
                    out.append(line)
            else:
                # EXTINF 后跟的不是 URL,原样吐回
                out.append(pending_extinf)
                out.append(line)
            pending_extinf = None
        else:
            out.append(line)

    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(out) + "\n")

    total = sum(1 for l in out if l.startswith("#EXTINF"))
    return removed, total


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "SMART"
    removed, kept = filter_file(path)
    print(f"[filter] {path}: 删除成人频道 {removed} 条, 保留 {kept} 条")
