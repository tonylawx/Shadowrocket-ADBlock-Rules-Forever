#!/usr/bin/env python3
from pathlib import Path
import re

RULE_START = "# BEGIN CUSTOM APPLE INTELLIGENCE / CHATGPT REGION FIX"
RULE_END = "# END CUSTOM APPLE INTELLIGENCE / CHATGPT REGION FIX"
GROUP_START = "# BEGIN CUSTOM APPLE INTELLIGENCE PROXY GROUP"
GROUP_END = "# END CUSTOM APPLE INTELLIGENCE PROXY GROUP"

APPLE_RULES = [
    "DOMAIN-SUFFIX,gateway.icloud.com,{policy}",
    "DOMAIN,apple-relay.apple.com,{policy}",
    "DOMAIN,apple-relay.fastly-edge.com,{policy}",
    "DOMAIN,apple-relay.cloudflare.com,{policy}",
    "DOMAIN,apple-relay.akamaized.net,{policy}",
    "DOMAIN,apple-relay.mask.apple-dns.net,{policy}",
    "DOMAIN,guzzoni.apple.com,{policy}",
    "DOMAIN,cp4.cloudflare.com,{policy}",
    "DOMAIN,gspe1-ssl.ls.apple.com,{policy}",
    "DOMAIN-SUFFIX,smoot.apple.com,{policy}",
    "DOMAIN-SUFFIX,apps.mzstatic.com,{policy}",
    "DOMAIN-SUFFIX,aapps.mzstatic.com,{policy}",
    "DOMAIN-WILDCARD,*mask*.apple-dns.net,{policy}",
    "DOMAIN-WILDCARD,*mask*.icloud.com,{policy}",
    "DOMAIN-WILDCARD,*siri*.apple.com,{policy}",
]

OPENAI_RULES = [
    "DOMAIN-SUFFIX,chat.com,{policy}",
    "DOMAIN-SUFFIX,chatgpt.com,{policy}",
    "DOMAIN-SUFFIX,openai.com,{policy}",
    "DOMAIN-SUFFIX,oaistatic.com,{policy}",
    "DOMAIN-SUFFIX,oaiusercontent.com,{policy}",
    "DOMAIN-SUFFIX,livekit.cloud,{policy}",
    "DOMAIN-SUFFIX,sora.com,{policy}",
    "DOMAIN,api.statsig.com,{policy}",
    "DOMAIN,api-iam.intercom.io,{policy}",
    "DOMAIN,o33249.ingest.sentry.io,{policy}",
    "DOMAIN,openaiapi-site.azureedge.net,{policy}",
    "DOMAIN-KEYWORD,openaiapi,{policy}",
    "DOMAIN-KEYWORD,openaicom,{policy}",
]


def rules_block(policy: str) -> str:
    lines = [
        RULE_START,
        "# Apple Intelligence / Writing Tools / Siri -> ChatGPT.",
        "# Keep this block above the generic AI and Apple DIRECT rules.",
    ]
    for rule in APPLE_RULES + OPENAI_RULES:
        lines.append(rule.format(policy=policy))
    lines.append(RULE_END)
    return "\n".join(lines)


def strip_block(text: str, start: str, end: str) -> str:
    return re.sub(
        re.escape(start) + r"[\s\S]*?" + re.escape(end) + r"\n*",
        "",
        text,
        flags=re.MULTILINE,
    )


def patch_rules(path: str, policy: str) -> None:
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    text = strip_block(text, RULE_START, RULE_END)

    anchor = "# AI\n"
    if anchor not in text:
        raise RuntimeError(f"{path}: '# AI' anchor not found")

    text = text.replace(anchor, anchor + rules_block(policy) + "\n\n", 1)
    p.write_text(text, encoding="utf-8")


def patch_group(path: str) -> None:
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    text = strip_block(text, GROUP_START, GROUP_END)

    # Restore the upstream generic AI group if an older version of this patch changed it.
    text = re.sub(
        r"^AI = select,.*$",
        "AI = select,PROXY,香港节点,台湾节点,日本节点,新加坡节点,韩国节点,美国节点,policy-select-name=PROXY",
        text,
        count=1,
        flags=re.MULTILINE,
    )

    ai_line = re.search(r"^AI = select,.*$", text, flags=re.MULTILINE)
    if not ai_line:
        raise RuntimeError(f"{path}: AI proxy group not found")

    group = "\n".join([
        GROUP_START,
        "# Dedicated Apple Intelligence / ChatGPT egress.",
        "# Intentionally pinned to the US node group for region-sensitive capability checks.",
        "Apple Intelligence = select,美国节点,policy-select-name=美国节点",
        GROUP_END,
        "",
    ])
    text = text[:ai_line.start()] + group + text[ai_line.start():]
    p.write_text(text, encoding="utf-8")


patch_rules("lazy.conf", "PROXY")
patch_rules("lazy_group.conf", "Apple Intelligence")
patch_group("lazy_group.conf")
