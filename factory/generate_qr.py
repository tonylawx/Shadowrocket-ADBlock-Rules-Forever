# -*- coding: utf-8 -*-

"""
为每个 .conf 订阅规则生成二维码 PNG，并把 README 里的上游硬编码 URL
替换为当前仓库（fork 者自己）的地址。

设计要点：
- 白名单驱动：只处理与 README 段落一一对应的 13 个 conf，避免误覆盖
  figure/guide.png（规则选择指南大图，不是二维码）。
- owner/repo/branch 全部由环境变量注入，fork 者无需改任何代码即可让
  二维码和 README 链接指向自己的仓库。

环境变量：
    OWNER   仓库所有者（github.repository_owner）
    REPO    仓库名   （github.event.repository.name）
    BRANCH  分支名   （github.ref_name，一般为 build）
"""

import os
import sys

import qrcode

# 与 README 现有「规则地址 + 二维码」段落一一对应的 conf 列表。
# 不含 sr_adb（README 无对应段落），不含 guide（指南图非二维码）。
CONFS = [
    'sr_top500_banlist_ad',
    'sr_top500_banlist',
    'sr_top500_whitelist_ad',
    'sr_top500_whitelist',
    'sr_direct_banad',
    'sr_proxy_banad',
    'sr_cnip',
    'sr_cnip_ad',
    'sr_backcn',
    'sr_backcn_ad',
    'sr_ad_only',
    'lazy',
    'lazy_group',
]

# README 里待替换的上游 URL 前缀（原作者的 GitHub Pages 地址）。
UPSTREAM_PREFIX = 'https://johnshall.github.io/Shadowrocket-ADBlock-Rules-Forever'

# 脚本位于 factory/，仓库根在上一级。
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    owner = os.environ.get('OWNER', '').strip()
    repo = os.environ.get('REPO', '').strip()
    branch = os.environ.get('BRANCH', '').strip()

    if not (owner and repo and branch):
        print('ERROR: 环境变量 OWNER / REPO / BRANCH 必须全部设置', file=sys.stderr)
        sys.exit(1)

    owner_prefix = 'https://%s.github.io/%s' % (owner, repo)

    # ---------- 1. 生成二维码 ----------
    figure_dir = os.path.join(ROOT, 'figure')
    os.makedirs(figure_dir, exist_ok=True)

    for name in CONFS:
        url = 'https://raw.githubusercontent.com/%s/%s/%s/%s.conf' % (
            owner, repo, branch, name)
        out = os.path.join(figure_dir, name + '.png')

        qr = qrcode.QRCode(
            version=None,                # 自动选择最小容得下的版本
            error_correction=qrcode.constants.ERROR_CORRECT_H,  # 30% 容错
            box_size=8,
            border=2,
        )
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color='black', back_color='white')
        img.save(out)
        print('QR  -> %s  (%s)' % (os.path.relpath(out, ROOT), url))

    # ---------- 2. 替换 README 里的上游 URL ----------
    # 仓库里追踪的文件名是 readme.md（git ls-files 实证）。APFS 大小写不敏感，
    # 这里同时兼容 README.md / readme.md。
    readme = None
    for candidate in ('readme.md', 'README.md'):
        p = os.path.join(ROOT, candidate)
        if os.path.isfile(p):
            readme = p
            break
    if readme is None:
        print('WARN: 未找到 readme.md，跳过 URL 替换', file=sys.stderr)
    else:
        with open(readme, 'r', encoding='utf-8') as f:
            content = f.read()

        new_content = content.replace(UPSTREAM_PREFIX, owner_prefix)
        # 二维码图片链接改用相对路径，GitHub 渲染 md 时更稳。
        new_content = new_content.replace(
            '%s/figure/' % owner_prefix, 'figure/')

        if new_content != content:
            with open(readme, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print('README URL 已替换 -> %s' % owner_prefix)
        else:
            print('README 无 %s 字样，无需替换' % UPSTREAM_PREFIX)


if __name__ == '__main__':
    main()
