#!/usr/bin/env python3
"""
Fix emoji variant selectors in GitHub markdown TOC anchors.
This script removes invisible U+FE0F characters from anchor links.
"""

import re

# Read README
with open('README.md', 'r', encoding='utf-8') as f:
    content = f.read()

# Count variant selectors before
variant_count_before = content.count('\uFE0F')
print(f"Variant selectors found: {variant_count_before}")

# Remove variant selectors ONLY from anchor links (inside parentheses after #)
# Pattern: (#<emoji with variant selector>-...)
# We want to remove \uFE0F only from anchors, not from display text

def remove_variant_from_anchor(match):
    """Remove variant selector from anchor link."""
    full_match = match.group(0)
    # Remove all U+FE0F from the anchor
    fixed = full_match.replace('\uFE0F', '')
    return fixed

# Pattern to match markdown links with anchors: [text](#anchor)
# We only want to fix the anchor part (inside parentheses)
pattern = r'\(#[^\)]+\)'

# Replace variant selectors in anchors
fixed_content = re.sub(pattern, remove_variant_from_anchor, content)

# Count variant selectors after (should still have some in display text)
variant_count_after = fixed_content.count('\uFE0F')
print(f"Variant selectors after fix: {variant_count_after}")
print(f"Variant selectors removed from anchors: {variant_count_before - variant_count_after}")

# Show specific fixes
print("\n" + "="*80)
print("FIXES APPLIED")
print("="*80)

# Find all TOC links
toc_pattern = r'-\s+\[([^\]]+)\]\((#[^\)]+)\)'
before_matches = re.findall(toc_pattern, content)
after_matches = re.findall(toc_pattern, fixed_content)

for i, (before, after) in enumerate(zip(before_matches, after_matches)):
    text_before, anchor_before = before
    text_after, anchor_after = after
    if anchor_before != anchor_after:
        print(f"\nLine {11 + i}:")
        print(f"  Text: {text_before}")
        print(f"  BEFORE: {anchor_before}")
        print(f"  AFTER:  {anchor_after}")

# Write fixed content
with open('README.md', 'w', encoding='utf-8') as f:
    f.write(fixed_content)

print("\n" + "="*80)
print("✅ README.md updated successfully!")
print("="*80)
