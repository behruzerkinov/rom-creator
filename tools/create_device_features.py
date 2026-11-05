#!/usr/bin/env python3
"""
create_device_features.py - Create device feature definitions for sweet and sweetin.
"""

import os
import re

STAR_XML = os.path.abspath("workspace/target/product/product/etc/device_features/star.xml")
SWEET_XML = os.path.abspath("workspace/target/product/product/etc/device_features/sweet.xml")
SWEETIN_XML = os.path.abspath("workspace/target/product/product/etc/device_features/sweetin.xml")

with open(STAR_XML, 'r', encoding='utf-8') as f:
    text = f.read()

# Apply modifications for sweet / sweetin
text_sweet = text.replace('<bool name="is_xiaomi">true</bool>', '<bool name="is_xiaomi">false</bool>')
text_sweet = text_sweet.replace('<bool name="is_hongmi">false</bool>', '<bool name="is_hongmi">true</bool>')
text_sweet = text_sweet.replace('<bool name="support_main_misubscreen">true</bool>', '<bool name="support_main_misubscreen">false</bool>')
text_sweet = text_sweet.replace('<integer name="defaultFps">60</integer>', '<integer name="defaultFps">120</integer>')

# fpsList
text_sweet = re.sub(
    r'<integer-array name="fpsList">.*?</integer-array>',
    '<integer-array name="fpsList">\n        <item>60</item>\n        <item>120</item>\n    </integer-array>',
    text_sweet,
    flags=re.DOTALL
)

with open(SWEET_XML, 'w', encoding='utf-8') as f:
    f.write(text_sweet)

with open(SWEETIN_XML, 'w', encoding='utf-8') as f:
    f.write(text_sweet)

print(f"[+] Successfully generated {SWEET_XML} and {SWEETIN_XML}")

