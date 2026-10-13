#!/bin/bash
# Real iOS SDK checks that do not need the proprietary engine or fake headers.
set -euo pipefail
cd "$(dirname "$0")/.."
SDK_PATH="$(xcrun --sdk iphoneos --show-sdk-path)"
mkdir -p Build/Audit
failed=0
for source in Source/MetalGraphicsHost.mm Source/MetalRenderer/*.mm; do
  name="$(basename "$source")"
  if xcrun clang++ -fsyntax-only -std=c++20 -fobjc-arc -fblocks \
    -target arm64-apple-ios17.0 -isysroot "$SDK_PATH" -I Source "$source" \
    > "Build/Audit/$name.log" 2>&1; then
    echo "PASS iOS syntax: $source"
  else
    echo "FAIL iOS syntax: $source"
    cat "Build/Audit/$name.log"
    failed=1
  fi
done
if xcrun clang -fsyntax-only -std=c11 -target arm64-apple-ios17.0 -isysroot "$SDK_PATH" \
  -I Vendor/libarchive.xcframework/ios-arm64/Headers App/GameInstaller/GameInstallerShim.c \
  > Build/Audit/installer-shim.log 2>&1; then
  echo 'PASS iOS syntax: archive installer shim'
else
  cat Build/Audit/installer-shim.log
  failed=1
fi
if xcrun swiftc -typecheck -target arm64-apple-ios17.0 -sdk "$SDK_PATH" -swift-version 5 \
  -I Source -I App/GameInstaller -import-objc-header Source/Native-Bridging-Header.h \
  App/*.swift App/GameInstaller/*.swift > Build/Audit/swift-typecheck.log 2>&1; then
  echo 'PASS iOS typecheck: all Swift app sources'
else
  cat Build/Audit/swift-typecheck.log
  failed=1
fi
exit "$failed"
