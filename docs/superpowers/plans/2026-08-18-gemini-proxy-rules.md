# Gemini Proxy Rules Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Force Gemini web, Google AI Studio, and the Gemini API through the existing `Proxy` policy.

**Architecture:** Add three explicit domain suffixes to the existing manual proxy source. Let the repository's established build script generate `DOMAIN-SUFFIX,<domain>,Proxy` entries in all relevant Shadowrocket configurations.

**Tech Stack:** Plain-text Shadowrocket rules, Python build scripts, GitHub Actions.

## Global Constraints

- Add only `gemini.google.com`, `aistudio.google.com`, and `generativelanguage.googleapis.com`.
- Do not add broad `google.com` or `googleapis.com` wildcard rules.
- Modify the source file `factory/manual_proxy.txt`, not generated files manually.

---

### Task 1: Add Gemini proxy domains and build

**Files:**
- Modify: `factory/manual_proxy.txt`
- Verify generated: `sr_proxy_banad.conf`

**Interfaces:**
- Consumes: `factory/build_confs.py` conversion of manual entries to `DOMAIN-SUFFIX,<domain>,Proxy`.
- Produces: Three explicit proxy rules in generated configuration files.

- [ ] **Step 1: Verify the domains are absent from the source**

Search `factory/manual_proxy.txt` for each exact domain and confirm zero matches.

- [ ] **Step 2: Add the minimal rule block**

Append:

```text
# ==================== Gemini / Google AI 强制代理 ====================
gemini.google.com
aistudio.google.com
generativelanguage.googleapis.com
```

- [ ] **Step 3: Commit to `build`**

Use commit message:

```text
feat: force Gemini services through proxy
```

- [ ] **Step 4: Verify the GitHub Actions build**

Confirm the `Build Shadowrocket Rules` workflow finishes successfully.

- [ ] **Step 5: Verify generated rules**

Confirm these exact lines exist once in a generated configuration:

```text
DOMAIN-SUFFIX,gemini.google.com,Proxy
DOMAIN-SUFFIX,aistudio.google.com,Proxy
DOMAIN-SUFFIX,generativelanguage.googleapis.com,Proxy
```

Confirm no broad `DOMAIN-SUFFIX,google.com,Proxy` or `DOMAIN-SUFFIX,googleapis.com,Proxy` rule was introduced by this change.
