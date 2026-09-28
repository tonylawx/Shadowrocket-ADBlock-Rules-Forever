#!/usr/bin/env python3
from pathlib import Path
import re

START = "# BEGIN CUSTOM APPLE INTELLIGENCE / CHATGPT REGION FIX"
END = "# END CUSTOM APPLE INTELLIGENCE / CHATGPT REGION FIX"

DOMAINS = [
    "gateway.icloud.com",
    "apple-relay.apple.com",
    "apple-relay.fastly-edge.com",
    "apple-relay.cloudflare.com",
    "apple-relay.akamaized.net",
    "apple-relay.mask.apple-dns.net",
    "guzzoni.apple.com",
    "cp4.cloudflare.com",
    "gspe1-ssl.ls.apple.com",
    "smoot.apple.com",
    "apps.mzstatic.com",
    "aapps.mzstatic.com",
]


def rules_block(policy: str) -> str:
    lines = [
        START,
        "# Keep these rules above the generic Apple DIRECT rules.",
        "# They cover Apple Intelligence / Writing Tools / Siri -> ChatGPT region checks.",
    ]
    lines.extend(f"DOMAIN-SUFFIX,{domain},{policy}" for domain in DOMAINS)
    lines.append(END)
    return "\n".join(lines)


def patch(path: str, policy: str, group: bool = False) -> None:
    p = Path(path)
    text = p.read_text(encoding="utf-8")

    marker = re.compile(
        re.escape(START) + r"[\s\S]*?" + re.escape(END) + r"\n*",
        re.MULTILINE,
    )
    text = marker.sub("", text)

    anchor = "# AI\n"
    if anchor not in text:
        raise RuntimeError(f"{path}: '# AI' anchor not found")
    text = text.replace(anchor, anchor + rules_block(policy) + "\n\n", 1)

    if group:
        replacement = (
            "AI = select,美国节点,日本节点,新加坡节点,台湾节点,韩国节点,"
            "PROXY,policy-select-name=美国节点"
        )
        text, count = re.subn(r"^AI = select,.*$", replacement, text, count=1, flags=re.MULTILINE)
        if count != 1:
            raise RuntimeError(f"{path}: AI proxy group not found")

    p.write_text(text, encoding="utf-8")


patch("lazy.conf", "PROXY")
patch("lazy_group.conf", "AI", group=True)
