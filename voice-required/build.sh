#!/bin/sh
# Baut VoiceRequired.jar. Die Klassen unter stubs/ bilden nur die benutzten Teile
# der Paper-API nach, damit sich das Plugin ohne Paper-Download kompilieren lässt;
# im Jar landen sie nicht, auf dem Server kommen die echten Klassen von Paper.
set -e
cd "$(dirname "$0")"
rm -rf build && mkdir -p build/stubs build/classes
javac --release 17 -d build/stubs $(find stubs -name '*.java')
javac --release 17 -cp build/stubs -d build/classes $(find src/main/java -name '*.java')
cp src/main/resources/plugin.yml build/classes/
jar --create --file VoiceRequired.jar -C build/classes .
rm -rf build
echo "VoiceRequired.jar gebaut"
