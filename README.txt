═══════════════════════════════════════════════
  AMONG US MOBILE AUTOMATION SUITE
  ADB-Based — Controls Android From Your PC
═══════════════════════════════════════════════

REQUIREMENTS
─────────────
1. Python 3.8+       → https://python.org
2. ADB (Platform Tools) → https://developer.android.com/studio/releases/platform-tools
   Add ADB to your system PATH after installing.

ANDROID SETUP (one-time)
──────────────────────────
1. On your Android phone:
   Settings → About Phone → tap "Build Number" 7 times
   (this unlocks Developer Options)

2. Settings → Developer Options → turn ON "USB Debugging"

3. Connect phone to PC via USB cable

4. On the phone — tap "Allow" on the USB debugging popup

5. Verify: open a terminal and type:  adb devices
   You should see your device listed as "authorized"

LAUNCH
───────
Windows : double-click  launch_windows.bat
Mac/Linux: run  bash launch_mac_linux.sh

Or directly: python3 among_us_auto.py

MODES
──────
Crewmate — Task Bot
  Wanders the map, presses USE when tasks are visible,
  handles meetings by skipping vote.

Impostor — Kill + Vent + Sabotage
  Kills when cooldown is expired, vents immediately
  after kill, triggers random sabotages.

Anti-AFK Only
  Sends micro-movements every 20-38s to prevent
  the idle kick.

TUNING
───────
• Kill Cooldown — match your in-game setting exactly
• Scan Speed — faster = more CPU, better reaction time
• If USE/Kill detection misses: the HSV color ranges in
  among_us_auto.py (COLOR_USE_BTN, COLOR_IMPOSTER) may
  need tuning for your device's screen. Screenshot the
  button and sample its color with any color picker tool.

WIFI ADB (optional — no cable)
────────────────────────────────
1. Connect phone via USB first and run:
   adb tcpip 5555
2. Find phone's IP in Settings → WiFi → tap your network
3. Run:  adb connect <phone-ip>:5555
4. Unplug cable — it still works over WiFi
