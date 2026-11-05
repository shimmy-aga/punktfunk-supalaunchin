# punktfunk-supalaunchin

Two Android TV launcher tiles for the Xiaomi MiTV (`192.168.2.5`) that start the
stream directly through the official Punktfunk app.

They use Punktfunk's **host record id**, not the display name, so they work in
the **console UI** and do **not** show the "Open this link?" prompt.

Built and installed 2026-11-05.

> **Public repository.** It contains the TV's local Punktfunk record id, the
> host certificate fingerprint, LAN addresses and the signing keystore. These
> are local-only values; see [Privacy](#privacy).

## Tiles

| Tile label | APK | Package / activity | Host result |
|---|---|---|---|
| **Steam BPM** | `apk/SteamBPM.apk` | `io.unom.punktfunk.shortcuts.steam/.SteamActivity` | Desktop: dedicated gamescope + Steam Big Picture |
| **Gamescope** | `apk/Gamescope.apk` | `io.unom.punktfunk.shortcuts.homelab/.HomelabActivity` | Game Mode: native Managed gamescope; Desktop: KDE |

Each is an invisible `LEANBACK_LAUNCHER` activity that sends one
`ACTION_VIEW` intent to `io.unom.punktfunk`, then finishes. No UI, no
permissions, no settings, no storage, no network.

## Repository contents

```text
apk/SteamBPM.apk        signed, installed build
apk/Gamescope.apk       signed, installed build
steam/                  Steam BPM manifest, Java source, adaptive icons, banner
homelab/                Gamescope manifest, Java source, adaptive icons, banner
assets/steam.svg        source logo (Font Awesome brands / CC BY 4.0)
assets/bazzite.svg      source logo (ublue-os/bazzite / Apache-2.0)
licenses/               icon licence texts
build.sh                builds one APK without Gradle
make_adaptive_icons.py  regenerates icons/banners from assets/
tvbridge.keystore       signing key (alias/password documented below)
README.md
```

## The links

The record id below is local to the TV's Punktfunk install:

```text
record id: f46c67d5-24f1-43b2-8e6c-27ebbb401854
host fp:   2e123935076f66914368051920cea981792edf1f5a40ba4d9d489501d62004e5
host:      192.168.2.14  (default port 9777)
```

Gamescope tile:

```text
punktfunk://connect/f46c67d5-24f1-43b2-8e6c-27ebbb401854?fp=2e123935076f66914368051920cea981792edf1f5a40ba4d9d489501d62004e5&host=192.168.2.14
```

Steam BPM:

```text
punktfunk://connect/f46c67d5-24f1-43b2-8e6c-27ebbb401854?fp=2e123935076f66914368051920cea981792edf1f5a40ba4d9d489501d62004e5&host=192.168.2.14&launch=steam%3Abig-picture
```

`%3A` decodes to `:`; the launch id is `steam:big-picture`.

## Why this works in the console UI

- A link that names the host by **label or address** resolves to `Confirm`; the
  TV console refuses it.
- A link that starts with the **record id** resolves to `Known`; the console
  dials it immediately, with the optional `launch` id, and no prompt.
- The record id is Punktfunk's own stable reference. The prompt itself says:
  "Shortcuts made in Punktfunk name the host's id and connect without asking."

## One-time extraction (already done)

The TV's touch UI exposes **Copy link**; the console does not. The record id
above was obtained once via:

1. `adb shell setprop debug.punktfunk.console_backend none` (transient touch UI)
2. Punktfunk -> host card three-dot menu -> **Copy link**
3. **Add Host** -> focus the Host field -> `adb shell input keyevent 279`
   (paste) -> `adb shell uiautomator dump` -> read the field text
4. `adb shell setprop debug.punktfunk.console_backend ''`

The `Controller-optimized UI` setting was left **on**; the console UI returned
immediately. No permanent UI change.

## When the record id changes

The record id survives Punktfunk updates and re-pairing. It changes if:

- Punktfunk's app data is cleared or the app is reinstalled, or
- the host's certificate/identity is reset (the `fp` would no longer match).

Then repeat the one-time extraction, update `URL` in the two Java files, rebuild
and reinstall. `adb install -r` keeps the home tiles in place.

## Rebuild

### Prerequisites

- JDK 17+ (the original build used JDK 21)
- Android SDK build-tools `35.0.0` and platform `android-35`
- `zip`/`unzip`
- ImageMagick (`magick`), Pillow, and the Liberation Sans fonts, only for icon
  regeneration

`build.sh` reads `ANDROID_HOME` and `JAVA_HOME`. If unset it falls back to the
original `/tmp/opencode/android-sdk` and `/tmp/opencode/jdk21` paths.

```bash
# optional: regenerate adaptive icons / legacy PNG / banners
python3 make_adaptive_icons.py

./build.sh steam      # -> steam/build/steam.apk + apk/SteamBPM.apk
./build.sh homelab    # -> homelab/build/homelab.apk + apk/Gamescope.apk
```

The link step uses `--auto-add-overlay` for `values/colors.xml`.

### Signing

`tvbridge.keystore`, alias `tvbridge`, store/key password `android`.
Installing a build signed with a different key requires uninstalling both
packages first.

## Install / remove

```bash
ADB=${ANDROID_HOME:-/tmp/opencode/android-sdk}/platform-tools/adb
# or simply: ADB=adb

$ADB connect 192.168.2.5:5555
$ADB install -r apk/SteamBPM.apk
$ADB install -r apk/Gamescope.apk

# remove
$ADB uninstall io.unom.punktfunk.shortcuts.steam
$ADB uninstall io.unom.punktfunk.shortcuts.homelab
```

## Notes

- The tiles work in the **console UI**, with no prompt. The touch UI was used
  only for the one-time Copy link.
- **Steam BPM tile in Game Mode** would spawn a separate dedicated gamescope,
  not join the live native session. Use the **Gamescope** tile in Game Mode.
- Desktop + **Gamescope** tile shows the KDE desktop, by design.
- Client settings are untouched: HEVC, 20 Mbps, 1920x1080@60, HDR off, Fit,
  Lowest latency.
- Icons are adaptive (brand background + full-bleed logo + monochrome layer);
  the Plume theme currently renders them monochrome like the other tiles.

## Known UI behaviour: brief console flash

Punktfunk shows its console UI for a moment before the stream starts. The tile
opens the app, and the app's console shell is what handles the deep link; the
host bringup was ~450 ms in the last sessions. The bridge cannot skip or cover
that UI with the stock app.

Low-risk optional polish, not applied: add `FLAG_ACTIVITY_SINGLE_TOP` to the two
bridge intents so a warm Punktfunk receives the link through `onNewIntent`, and
optionally `FLAG_ACTIVITY_NO_ANIMATION` to skip the app-open animation. The
console still appears during the host bringup. A completely dark transition
needs an app-side change (a black "Connecting" surface before the console, or a
dedicated stream activity), not a bridge change.

## Privacy

This repository is public and contains:

- the TV's local Punktfunk record id,
- the host certificate fingerprint (`fp`),
- LAN addresses (`192.168.2.5`, `192.168.2.14`),
- `tvbridge.keystore` and its password.

The record id is meaningful only to the TV's Punktfunk install. The fingerprint
is the host's public certificate. The addresses are LAN-only. The keystore only
signs these shortcut packages; if you fork this for another setup, generate your
own key and use your own record id.

## Icon licences

- `assets/steam.svg` — Font Awesome Free 5 brands (CC BY 4.0), via
  react-icons `FaSteam`; see `licenses/font-awesome-brands.txt`.
- `assets/bazzite.svg` — ublue-os/bazzite (Apache-2.0); see
  `licenses/bazzite.txt`.
- `licenses/simple-icons.txt` is included for completeness.

## Repository

```text
https://github.com/shimmy-aga/punktfunk-supalaunchin
```

Public. Prebuilt signed APKs are in `apk/` and in the `v1.0` release.
