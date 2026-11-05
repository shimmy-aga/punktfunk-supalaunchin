#!/usr/bin/env bash
# Build one Punktfunk TV shortcut APK without Gradle.
# usage: ./build.sh steam|homelab
set -euo pipefail

NAME=${1:?usage: build.sh steam|homelab}
case "$NAME" in
    steam)   ARTIFACT=SteamBPM.apk ;;
    homelab) ARTIFACT=Gamescope.apk ;;
    *) echo "usage: build.sh steam|homelab" >&2; exit 2 ;;
esac

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
SDK=${ANDROID_HOME:-/tmp/opencode/android-sdk}
BT=$SDK/build-tools/35.0.0
PLATFORM=$SDK/platforms/android-35/android.jar
JAVA_HOME=${JAVA_HOME:-/tmp/opencode/jdk21}
export JAVA_HOME
export PATH="$JAVA_HOME/bin:$PATH"

[ -x "$BT/aapt2" ] || {
    echo "Android build-tools 35.0.0 not found at $BT" >&2
    echo "Set ANDROID_HOME to an SDK with build-tools;35.0.0 and platforms;android-35." >&2
    exit 1
}
[ -f "$PLATFORM" ] || {
    echo "Android platform 35 not found under $SDK" >&2
    echo "Set ANDROID_HOME to an SDK with platforms;android-35." >&2
    exit 1
}
[ -x "$JAVA_HOME/bin/javac" ] || {
    echo "JDK not found at $JAVA_HOME" >&2
    echo "Set JAVA_HOME to a JDK 17+ (21 used for the original build)." >&2
    exit 1
}

PROJ=$ROOT/$NAME
OUT=$PROJ/build

rm -rf "$OUT"
mkdir -p "$OUT/classes" "$OUT/dex"

echo "== aapt2 compile/link =="
"$BT/aapt2" compile --dir "$PROJ/res" -o "$OUT/resources.zip"
"$BT/aapt2" link \
    -o "$OUT/unsigned.apk" \
    -I "$PLATFORM" \
    --manifest "$PROJ/AndroidManifest.xml" \
    -R "$OUT/resources.zip" \
    --auto-add-overlay \
    --min-sdk-version 23 \
    --target-sdk-version 35 \
    --version-code 1 \
    --version-name 1.0

echo "== javac =="
find "$PROJ/src" -name '*.java' > "$OUT/sources.txt"
"$JAVA_HOME/bin/javac" -source 8 -target 8 -Xlint:-options \
    -bootclasspath "$PLATFORM" -d "$OUT/classes" @"$OUT/sources.txt"

echo "== d8 =="
find "$OUT/classes" -name '*.class' > "$OUT/classes.txt"
"$BT/d8" --release --lib "$PLATFORM" --min-api 23 \
    --output "$OUT/dex" @"$OUT/classes.txt"

(cd "$OUT/dex" && zip -q "$OUT/unsigned.apk" classes.dex)

echo "== align/sign =="
KEYSTORE=$ROOT/tvbridge.keystore
if [ ! -f "$KEYSTORE" ]; then
    "$JAVA_HOME/bin/keytool" -genkeypair -keystore "$KEYSTORE" \
        -alias tvbridge -keyalg RSA -keysize 2048 -validity 10000 \
        -storepass android -keypass android \
        -dname "CN=Punktfunk TV Shortcuts, O=Local, C=US"
fi
"$BT/zipalign" -f 4 "$OUT/unsigned.apk" "$OUT/aligned.apk"
"$BT/apksigner" sign --ks "$KEYSTORE" \
    --ks-pass pass:android --key-pass pass:android \
    --ks-key-alias tvbridge \
    --out "$OUT/$NAME.apk" "$OUT/aligned.apk"
"$BT/apksigner" verify --verbose "$OUT/$NAME.apk" | head -6

mkdir -p "$ROOT/apk"
cp "$OUT/$NAME.apk" "$ROOT/apk/$ARTIFACT"
ls -lh "$OUT/$NAME.apk" "$ROOT/apk/$ARTIFACT"
