#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Magneti Marelli IAW 4LV.L (ST M95080 EEPROM) Binary Patcher
Reference Vehicle: VW Polo 6N2 1.4 16V 75HP (ECU: 036906034D / SW: 3979)

Description:
Educational and Right-to-Repair utility to patch specific memory offsets
in a 1024-byte M95080 SPI EEPROM dump for immobilizer fault recovery.
"""

import sys
import os
import shutil
import zlib
import hashlib
import argparse

# ==============================================================================
# PATCH CONFIGURATION
# ==============================================================================
EXPECTED_FILE_SIZE = 1024
EMPTY_DUMP_CRC32 = 0xB83AFFF4

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
# ==============================================================================


def calculate_hashes(data: bytes) -> tuple[str, str]:
    """Calculates CRC32 and SHA-256."""
    crc32_val = zlib.crc32(data) & 0xFFFFFFFF
    sha256_val = hashlib.sha256(data).hexdigest()
    return f"0x{crc32_val:08X}", sha256_val


def validate_dump(data: bytes) -> bool:
    """Validates that the input binary is a proper 1024-byte M95080 EEPROM read."""
    if len(data) != EXPECTED_FILE_SIZE:
        print(f"[ERROR] Invalid file size: {len(data)} bytes.")
        print(f"        ST M95080 EEPROM dump must be exactly {EXPECTED_FILE_SIZE} bytes (1 KB).")
        return False

    crc32_val = zlib.crc32(data) & 0xFFFFFFFF
    if crc32_val == EMPTY_DUMP_CRC32 or all(b == 0xFF for b in data):
        print("[ERROR] Input file contains only 0xFF bytes! Bad SOP8 clip contact.")
        return False

    if all(b == 0x00 for b in data):
        print("[ERROR] Input file contains only 0x00 bytes! Invalid EEPROM dump.")
        return False

    return True


def patch_eeprom(input_path: str, output_path: str, force: bool = False) -> None:
    if not os.path.isfile(input_path):
        print(f"[ERROR] Input file '{input_path}' not found.")
        sys.exit(1)

    with open(input_path, "rb") as f:
        raw_data = f.read()

    print("=" * 72)
    print(" Magneti Marelli IAW 4LV.L (036906034D) - M95080 EEPROM Patcher")
    print("=" * 72)

    if not validate_dump(raw_data):
        sys.exit(1)

    orig_crc, orig_sha = calculate_hashes(raw_data)
    print(f"[*] Input File     : {input_path} ({len(raw_data)} bytes)")
    print(f"[*] Original CRC32 : {orig_crc}")
    print(f"[*] Original SHA256: {orig_sha[:32]}...")
    print("-" * 72)

    backup_path = input_path + ".bak"
    if not os.path.exists(backup_path):
        shutil.copy2(input_path, backup_path)
        print(f"[+] Created automatic safety backup: {backup_path}")

    buffer = bytearray(raw_data)

    print("\n[*] Applying EEPROM patch rules:")
    for rule in PATCH_RULES:
        offset = rule["offset"]
        expected = rule["expected_orig"]
        new_val = rule["new_value"]
        desc = rule["description"]

        if not (0 <= offset < EXPECTED_FILE_SIZE):
            print(f"[ERROR] Offset 0x{offset:04X} is out of range.")
            sys.exit(1)

        current_val = buffer[offset]
        print(f"    -> Offset 0x{offset:04X} ({desc}): Current = 0x{current_val:02X}", end="")

        if expected is not None and current_val != expected:
            print(f" [WARNING: Expected 0x{expected:02X}!]")
            if not force:
                print("\n[!] Aborting patch. Run with --force if needed.")
                sys.exit(1)
        else:
            print(f" -> New = 0x{new_val:02X}")

        buffer[offset] = new_val

    with open(output_path, "wb") as f:
        f.write(buffer)

    new_crc, new_sha = calculate_hashes(bytes(buffer))
    print("-" * 72)
    print(f"[+] Successfully wrote patched EEPROM dump: {output_path}")
    print(f"[*] Patched CRC32  : {new_crc} (Verify this hash in NeoProgrammer)")
    print(f"[*] Patched SHA256 : {new_sha[:32]}...")
    print("=" * 72)


def main():
    parser = argparse.ArgumentParser(
        description="M95080 (1KB) EEPROM Binary Patcher for Magneti Marelli IAW 4LV ECUs."
    )
    parser.add_argument("input", help="Path to original EEPROM dump (e.g., original.bin)")
    parser.add_argument("output", help="Path to save modified EEPROM dump (e.g., immo_off.bin)")
    parser.add_argument("--force", action="store_true", help="Bypass expected original byte validation")

    args = parser.parse_args()
    patch_eeprom(args.input, args.output, args.force)


if __name__ == "__main__":
    main()
