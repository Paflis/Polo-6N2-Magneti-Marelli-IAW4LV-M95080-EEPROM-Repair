PATCH_RULES = [
    {
        "offset": 0x0095,          # First immobilizer status flag byte
        "expected_orig": 0x01,     # Safety check: expects original stock value 0x01
        "new_value": 0x00,         # Patched value for Immo Off
        "description": "Immobilizer Status Flag 1"
    },
    {
        "offset": 0x0096,          # Second byte / associated checksum offset
        "expected_orig": 0xA9,     # Safety check: expects original stock value 0xA9
        "new_value": 0xAA,         # Patched value
        "description": "Immobilizer Status Flag 2 / Checksum"
    }
]
