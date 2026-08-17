# Gemini Proxy Rules Design

## Goal

Force Gemini web, Google AI Studio, and the Gemini API through the repository's existing `Proxy` policy without proxying unrelated Google services.

## Scope

Add the following domain suffixes to `factory/manual_proxy.txt`:

- `gemini.google.com`
- `aistudio.google.com`
- `generativelanguage.googleapis.com`

Do not add wildcard rules for `google.com`, `googleapis.com`, or other Google product domains.

## Integration

`factory/build_confs.py` already converts every entry in `factory/manual_proxy.txt` into a `DOMAIN-SUFFIX,<domain>,Proxy` rule. Existing nightly builds will propagate the change into generated Shadowrocket configurations.

## Expected Result

Requests for Gemini web, AI Studio, and Gemini API endpoints match the explicit proxy rules before broader routing rules. Other Google services keep their current routing behaviour.

## Verification

1. Confirm the three domains appear once in `factory/manual_proxy.txt`.
2. Confirm the generated rule form is `DOMAIN-SUFFIX,<domain>,Proxy`.
3. Confirm no broad `google.com` or `googleapis.com` rule is introduced.
