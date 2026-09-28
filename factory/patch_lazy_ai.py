#!/usr/bin/env python3
from pathlib import Path
import re

RULE_START = "# BEGIN CUSTOM APPLE INTELLIGENCE / CHATGPT REGION FIX"
RULE_END = "# END CUSTOM APPLE INTELLIGENCE / CHATGPT REGION FIX"
GROUP_START = "# BEGIN CUSTOM APPLE INTELLIGENCE PROXY GROUP"
GROUP_END = "# END CUSTOM APPLE INTELLIGENCE PROXY GROUP"

# Keep this list intentionally focused on Apple Intelligence / Siri / ChatGPT.
# Sources cross-checked against current community Apple Intelligence and OpenAI rule sets.
APPLE_RULES = [
    "DOMAIN-SUFFIX,gateway.icloud.com,{policy}",
    "DOMAIN,guzzoni.apple.com,{policy}",
    "DOMAIN,identity.apple.com,{policy}",
    "DOMAIN,appleid.cdn-apple.com,{policy}",
    "DOMAIN,gsa.apple.com,{policy}",
    "DOMAIN,setup.icloud.com,{policy}",
    "DOMAIN-SUFFIX,acsegateway.icloud.com,{policy}",

    # Apple Intelligence / Private Cloud Compute / relay path
    "DOMAIN,mask-api.fe.apple-dns.net,{policy}",
    "DOMAIN,mask-api.icloud.com,{policy}",
    "DOMAIN,mask-t.apple-dns.net,{policy}",
    "DOMAIN,mask.apple-dns.net,{policy}",
    "DOMAIN-SUFFIX,mask-h2.icloud.com,{policy}",
    "DOMAIN-SUFFIX,mask.icloud.com,{policy}",
    "DOMAIN-SUFFIX,apple-relay.apple.com,{policy}",
    "DOMAIN-SUFFIX,apple-relay.fastly-edge.com,{policy}",
    "DOMAIN-SUFFIX,apple-relay.cloudflare.com,{policy}",
    "DOMAIN-SUFFIX,apple-relay.akamaized.net,{policy}",
    "DOMAIN-SUFFIX,apple-relay.mask.apple-dns.net,{policy}",
    "DOMAIN-KEYWORD,apple-relay,{policy}",

    # Siri / location capability checks used before ChatGPT hand-off
    "DOMAIN-SUFFIX,cp4.cloudflare.com,{policy}",
    "DOMAIN-SUFFIX,gspe1-ssl.ls.apple.com,{policy}",
    "DOMAIN-SUFFIX,ls.apple.com,{policy}",
    "DOMAIN-SUFFIX,smoot.apple.com,{policy}",
    "DOMAIN-KEYWORD,siri,{policy}",

    # Apple Intelligence resources / CloudKit
    "DOMAIN-SUFFIX,apple-cloudkit.com,{policy}",
    "DOMAIN-SUFFIX,apps.mzstatic.com,{policy}",
    "DOMAIN-SUFFIX,aapps.mzstatic.com,{policy}",

    # Catch Apple Intelligence traffic that arrives as raw Apple IPs on Wi-Fi.
    "IP-CIDR,17.0.0.0/8,{policy},no-resolve",
    "IP-CIDR6,2403:300:a42::/48,{policy},no-resolve",
    "IP-CIDR6,2403:300:a51::/48,{policy},no-resolve",
    "IP-CIDR6,2620:149:a44::/48,{policy},no-resolve",
    "IP-CIDR6,2a01:b740:a42::/48,{policy},no-resolve",
]

OPENAI_RULES = [
    # Core OpenAI / ChatGPT
    "DOMAIN-SUFFIX,chat.com,{policy}",
    "DOMAIN-SUFFIX,chatgpt.com,{policy}",
    "DOMAIN-SUFFIX,chatgpt.site,{policy}",
    "DOMAIN-SUFFIX,openai.com,{policy}",
    "DOMAIN-SUFFIX,oaistatic.com,{policy}",
    "DOMAIN-SUFFIX,oaiusercontent.com,{policy}",
    "DOMAIN-SUFFIX,oaistatsig.com,{policy}",
    "DOMAIN-SUFFIX,livekit.cloud,{policy}",
    "DOMAIN-SUFFIX,sora.com,{policy}",

    # Feature flags / auth / CDN / realtime endpoints that do not end in openai.com
    "DOMAIN,api.statsig.com,{policy}",
    "DOMAIN,api-iam.intercom.io,{policy}",
    "DOMAIN,o33249.ingest.sentry.io,{policy}",
    "DOMAIN,o33249.ingest.us.sentry.io,{policy}",
    "DOMAIN,openai.com.cdn.cloudflare.net,{policy}",
    "DOMAIN,openai-api.arkoselabs.com,{policy}",
    "DOMAIN,openaiapi-site.azureedge.net,{policy}",
    "DOMAIN,openaiassets.blob.core.windows.net,{policy}",
    "DOMAIN,openaicom.imgix.net,{policy}",
    "DOMAIN,openaicomproductionae4b.blob.core.windows.net,{policy}",
    "DOMAIN,production-openaicom-storage.azureedge.net,{policy}",

    # Dynamic Azure WebPubSub / Azure Front Door hostnames
    "AND,((DOMAIN-KEYWORD,chatgpt-async-webps-prod-),(DOMAIN-SUFFIX,webpubsub.azure.com)),{policy}",
    "AND,((DOMAIN-KEYWORD,openaicom-api-),(DOMAIN-SUFFIX,azurefd.net)),{policy}",

    # Catch future OpenAI-owned dynamic hostnames without proxying all Azure/CDN traffic.
    "DOMAIN-KEYWORD,openaiapi,{policy}",
    "DOMAIN-KEYWORD,openaicom,{policy}",
]


def rules_block(policy: str) -> str:
    lines = [
        RULE_START,
        "# Apple Intelligence / Writing Tools / Siri -> ChatGPT.",
        "# Keep this block above generic AI and Apple DIRECT rules.",
        "# Expanded for iOS 27 region/capability checks and dynamic OpenAI backends.",
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


def patch_network_path(path: str) -> None:
    """Avoid Wi-Fi IPv6/system-DNS paths bypassing the region-sensitive proxy rules."""
    p = Path(path)
    text = p.read_text(encoding="utf-8")

    # Force IPv4 while troubleshooting Apple Intelligence on mainland Wi-Fi.
    text, count = re.subn(r"^ipv6\s*=\s*true\s*$", "ipv6 = false", text, count=1, flags=re.MULTILINE)
    if count == 0 and "ipv6 = false" not in text:
        raise RuntimeError(f"{path}: ipv6 setting not found")

    # Do not force Apple/iCloud names back to the local ISP resolver.
    text = re.sub(r"^\*\.apple\.com\s*=\s*server:system\s*\n?", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\*\.icloud\.com\s*=\s*server:system\s*\n?", "", text, flags=re.MULTILINE)

    p.write_text(text, encoding="utf-8")


def patch_group(path: str) -> None:
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    text = strip_block(text, GROUP_START, GROUP_END)

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
        "# Pinned to the US node group for region-sensitive capability checks.",
        "Apple Intelligence = select,美国节点,policy-select-name=美国节点",
        GROUP_END,
        "",
    ])
    text = text[:ai_line.start()] + group + text[ai_line.start():]
    p.write_text(text, encoding="utf-8")


patch_rules("lazy.conf", "PROXY")
patch_rules("lazy_group.conf", "Apple Intelligence")
patch_network_path("lazy.conf")
patch_network_path("lazy_group.conf")
patch_group("lazy_group.conf")
