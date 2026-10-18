# Polo-6N2-Magneti-Marelli-IAW4LV-M95080-EEPROM-Repair
Step-by-step repair guide and Python EEPROM (ST M95080) patcher for Magneti Marelli IAW 4LV.L (036906034D) ECU immobilizer faults on VW Polo 6N2 1.4 16V.

# Magneti Marelli IAW 4LV.L (036906034D) EEPROM Immobilizer Repair Guide & Patcher

> **Disclaimer & Legal Notice:**  
> This repository is provided strictly for **educational, diagnostic, and Right-to-Repair purposes** to help legal vehicle owners restore engine functionality on aging vehicles (25+ years old) suffering from immobilizer hardware failures.  
> - This repository **DOES NOT** contain or distribute any proprietary Volkswagen or Magneti Marelli binary dumps (`.bin` / `.hex`).  
> - All procedures and scripts operate exclusively on the user's own legally extracted EEPROM backup.

---

## Vehicle & ECU Specifications

This documentation and patching tool were developed and verified on the following hardware configuration:

* **Vehicle:** Volkswagen Polo III (6N2) 1.4i 16V 75HP (1999-2001)
* **Engine Code:** AUA
* **ECU Manufacturer:** Magneti Marelli
* **ECU Hardware Model:** `IAW 4LV.L` (`61600.437.10`)
* **VW/VAG Part Number:** `036 906 034 D` (`036906034D`)
* **Software Version:** `3979`
* **EEPROM IC:** STMicroelectronics **M95080** (SPI EEPROM, SOIC-8 / SOP-8 package, 8 Kbit / 1024 Bytes, 3.3V)
* **External Immobilizer Module:** Valeo `6X0 953 257` (Immobilizer Box located behind the dashboard)

---

## Problem Description & Symptoms

On the VW Polo 6N2 (and similar VAG platforms of this era), the immobilizer system relies on an external Immobilizer Box (`Address 25 - Immobilizer`). The module reads the key transponder via the ignition lock reader coil and authorizes the Engine Control Unit (`Address 01 - Engine`) over a dedicated serial **W-Line**.

### Common Failure Symptoms:
1. **Start-and-Stall Condition:** The engine cranks, fires up normally, and **stalls immediately after 1 to 2 seconds** as the ECU cuts fuel injection due to missing or corrupted immobilizer authorization.
2. **Intermittent Failures:** When inspecting `25 - Immobilizer` Measuring Blocks in VCDS, the system may intermittently report normal values (`Reader Coil Status = 1`, `Key authorized = 1`, `Engine Start permitted = 1`, `Immobilizer Status = 6`), yet randomly fail to authorize the ECU during cranking due to cold solder joints, W-Line signal degradation, or reader coil connector oxidation.
3. **Diagnostic Trouble Code (DTC):** The Engine ECU logs:
   * `17978 / P1570 - Engine Start Blocked by Immobilizer`
4. **Voltage-Drop EEPROM Corruption:** Weak battery voltage during cranking frequently corrupts EEPROM data across the vehicle electronics (for example, causing the TRW instrument cluster `17 - Instruments` EEPROM to suffer a 16-bit integer overflow `0xFFFF`, displaying `655350 km` or `dEF`).

By patching the **M95080** SPI EEPROM inside the Magneti Marelli ECU (Immo Off) and flashing the modified dump onto a fresh EEPROM chip, the engine starts reliably without depending on the aging external immobilizer module.

---

## Compatibility & Universal Usage Notes

### 1. Applicable ECU Families:
The **Magneti Marelli IAW 4LV / IAW 4MV / IAW 4TV** ECU architecture is widely used across VAG 1.4 16V (75HP & 100HP) engines (**AUA, AHW, APE, BBY, AUB, BBZ**) in:
* **Volkswagen:** Polo (6N2, 9N), Lupo, Golf IV, Bora
* **SEAT:** Ibiza (6K2, 6L), Cordoba, Arosa, Leon (1M)
* **Skoda:** Fabia I (6Y), Octavia I (1U)

All of these ECUs store immobilizer and adaptation data inside an external **95080 (1024 Bytes)** SPI EEPROM.

### 2. Does the Python Script Require Modification for Other ECUs?
* **Identical ECU (`036906034D` / SW `3979`):** The memory offsets defined in `iaw4lv_patcher.py` match directly.
* **Other `IAW 4LV` Variants:** Most `IAW 4LV` dumps share the same EEPROM memory layout, but you **must always inspect your `original.bin` in a Hex Editor** to verify that the target offsets contain the expected stock values before patching.
* **Newer `IAW 4MV` ECUs (e.g., Polo 9N / Golf IV BBY with Immo 3):** In `IAW 4MV` units, immobilizer status bytes are often mirrored in two separate memory rows, and the corresponding 16-byte page checksum must be recalculated. Modifying bytes on an `IAW 4MV` without updating the page checksum may trigger DTC `16985 / P0601 - Internal Control Module Memory Check Sum Error`. Users adapting this script for `4MV` ECUs should update the `PATCH_RULES` dictionary accordingly.

---

## Required Hardware & Software

1. **Programmer:** CH341A Black Edition USB Programmer with a **150mil SOP8-to-DIP8 ZIF adapter**.
2. **Replacement EEPROM IC (Recommended):** A brand-new **ST M95080W** (SOIC-8). Flashing onto a new IC allows you to keep the factory chip untouched as a physical hardware backup.
3. **Software:**
   * **NeoProgrammer** (v2.2.0.10 or newer)
   * **WCH CH341PAR Driver** (Parallel/SPI/I2C mode driver — *do not* use the CH341SER serial COM port driver).
   * **Python 3.x** (to run `iaw4lv_patcher.py`).
4. **Soldering Equipment:** Hot air rework station or fine-tip soldering iron, flux, solder, isopropyl alcohol (IPA), and RTV silicone gasket maker (for resealing the ECU housing).

---

## Step-by-Step Procedure

### Step 1: ECU Removal & EEPROM Desoldering
1. Disconnect the negative battery terminal.
2. Remove the ECU from the plenum chamber (under the windshield wiper cowl).
3. Carefully open the aluminum ECU casing.
4. Locate the **95080** SOIC-8 chip on the PCB.
5. **Take a clear photo of the PCB** to record the **Pin 1 orientation** (indicated by the dimple/dot or beveled edge on the IC body).
6. Desolder the chip and clean all 8 legs thoroughly with isopropyl alcohol so they make solid contact inside the SOP8 adapter.

### Step 2: CH341A Hardware Setup (Critical Pitfalls)
> **Hardware Troubleshooting Note:** Cheap CH341A clones frequently suffer from defective 3.3V regulators, cold solder joints, or tripping USB polyfuses, resulting in random `IC not responding / Disconnected` errors. Always plug the CH341A directly into a rear motherboard USB port (avoid USB hubs). If random disconnections persist, test with a known-good CH341A unit.

1. **Mode Jumper:** Ensure the jumper next to the USB connector bridges **Pins 1-2** (Programmer / SPI-I2C mode).
2. **ZIF Socket Zone (`25XX`):** Insert the SOP8 adapter into the **25XX** 8-pin zone of the ZIF socket, strictly following the PCB silkscreen diagram on your programmer.
3. **Pin 1 Alignment:** Align Pin 1 of the M95080 chip (dot/dimple) with Pin 1 of the SOP8 adapter and Pin 1 of the CH341A `25XX` socket.

### Step 3: Reading the Original EEPROM Dump
1. Launch **NeoProgrammer** and confirm `Current programmer: CH341 Black` is displayed at the bottom.
2. **DO NOT press the auto `Detect (?)` button:** Auto-detection frequently misidentifies the chip as an older `ST95P08`, which uses incompatible instructions and causes communication errors.
3. Manually select the chip via **`IC` -> `Search`**, type `95080`, and select **`ST -> M95080W [3.3V]`** (8 Kbits, 1 KByte).
4. Click **Read IC**.
5. **Verify the Read Dump:**
   * Inspect the hex buffer to confirm it contains actual data (including your vehicle identification strings) and **not** all `FF` bytes.
   * **Warning:** A `CRC32 = 0xB83AFFF4` indicates 1024 bytes of `0xFF` (empty read caused by poor pin contact in the adapter).
   * Click **Read IC** 3 times consecutively and confirm the `CRC32` checksum remains 100% identical on every read.
6. Save the verified dump (`File -> Save`) as `original.bin`.

### Step 4: Patching the Dump via Python
Run the included patcher script against your backup file:

```bash
python iaw4lv_patcher.py original.bin immo_off.bin
