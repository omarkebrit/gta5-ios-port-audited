# Repository audit and actual status

Audit date: 2026-10-13. Upstream: <https://github.com/kevinerikjs/gta5-ios-port>.
Audited upstream commit: `151495ccc5d3c95ef8a6f9f7f92b0a98e6fabb49`.

**No working, installable IPA has been verified or published.** This is a plausible native host implementation for a particular supplied Wasm engine, rather than a self-contained port of retail GTA V. There is insufficient evidence to label it fraudulent, and insufficient evidence to certify the full game functional. Its runtime dependencies, provenance and performance claims cannot be verified from this source repository alone.

## Public macOS source-check result on 2026-10-14

At the user's request, the repository was made public; GitHub confirmed the visibility change before retrying checks. No proprietary engine/data files, generated game shader library, signing material or embedded credentials were found in the tracked source or reachable history; no input release or IPA artifact existed. The original full IPA workflow's private-repository guard remains intact, and its Windows uploader refuses a public destination.

The public retry, [run 38543383301](https://github.com/omarkebrit/gta5-ios-port-audited/actions/runs/38543383301), **succeeded** at commit `d2b944172445d3fe2281483b7eea4caa718e196a`. Dependency preparation ran on the ARM64 macOS runner, **11 existing tests passed**, **10 existing tests were explicitly blocked**, and **four pipeline regression tests passed**. The native Metal bridge, all three renderer implementation files, archive installer C shim and all Swift app sources passed the current iOS SDK syntax/type checks. The native-runtime test translates the checked-in synthetic WAT probe; it does not execute the actual GTA engine. See [github-public-source-checks-2026-10-14.json](github-public-source-checks-2026-10-14.json).

The job log was obtained through the GitHub connector and confirms these results. The evidence artifact was published by GitHub, but a CLI artifact download followed a redirect that returned HTTP 403; this audit does not claim that ZIP was downloaded locally. The public job ran without changing payments or spending limits; this does not establish that private macOS jobs now work. The earlier private failure below is retained as historical evidence.

The user now reports having `b/8b0b5899ed/game.wasm` on their computer. That file has **not** been supplied or hash-verified, and the shader packs/manifest have not been supplied. No actual engine translation, full app compilation/link, IPA packaging, device installation or gameplay test occurred. A protected input/artifact transport is required before using the proprietary inputs; the existing full-build workflow cannot be dispatched in this public repository.

## Follow-up status on 2026-10-14

The user created `omarkebrit/gta5-ios-port-audited` and changed it from public to private. The connection verified `private: true` and push access, and successfully published the prepared source/workflows at commit `8948c1608cb37d5631341260214cbf5a75257250`. Repository: <https://github.com/omarkebrit/gta5-ios-port-audited>. Source checks: <https://github.com/omarkebrit/gta5-ios-port-audited/actions/workflows/audit.yml>. IPA build: <https://github.com/omarkebrit/gta5-ios-port-audited/actions/workflows/build-ipa.yml>.

The push created run [38542594399](https://github.com/omarkebrit/gta5-ios-port-audited/actions/runs/38542594399). It failed before allocating/executing the macOS job: the job has an empty step list and GitHub's check annotation states “The job was not started because recent account payments have failed or your spending limit needs to be increased. Please check the 'Billing & plans' section in your settings”. A separate notice mentions ARM64 runner capacity, but the billing annotation is the explicit startup failure. No compilation, macOS test or IPA verification executed. Account billing resolution requires the user; no payment/budget changes were made. The proprietary game inputs remain absent. See [github-status-2026-10-14.json](github-status-2026-10-14.json).

Static follow-up review also corrected two check-harness defects: explicitly select Bash so a failing Python test piped through `tee` fails the step, and compile the ARM64 SIMD comparison with `PG_SHARED_SIMD_BYTEWISE` so the reference path uses atomic bytes independently of the direct ARM64 helper. The latter has not executed on ARM64 yet. The original 2026-10-13 evidence below is retained as the historical audit; its repository-publication blocker is now resolved, and its unexecuted-macOS limitation remains.

## Scope and evidence

The repository was cloned with its full Git history. The upstream tree has 173 tracked files, including 140 readable text files (21,781 lines, including vendored headers), Swift app/UI and archive installer code, C engine/thread/file bridges, the Objective-C++ Metal renderer, 21 standalone test programs, Python/shell build and preparation scripts, resource metadata/images, three libarchive static library slices, licenses, README, changelog and the single upstream workflow. There are no submodules. The file inventory and unresolved include scan are in [upstream-inventory.json](upstream-inventory.json).

Review covered the documented/build paths, dependency acquisition, generated imports and pinned engine patches, ARM64/Metal interfaces, local versus network asset loading, archive import, telemetry/log transmission, entitlements and packaging. This was source/static review and local testing, not a forensic certification of binaries. No proprietary engine or runtime archive was downloaded. The open-source shader translator was downloaded and its pinned checksum verified; it was not executed on this Linux host.

The upstream Actions API reported **zero workflow runs**. Its v1.0 through v1.3.1 releases contain no app IPA (v1.0 has a tutorial video); separate releases supply the shader translator and an older Dawn bundle. Community issues describe gameplay/control problems, but these reports and the README video do not replace an independently reproduced build or physical-device test.

## What the native claim actually means

`prepare.py` requires the exact engine SHA-256, translates `game.wasm` into 64 C translation units with a patched WABT `wasm2c`, applies engine-specific function patches, and generates the Xcode project. `project.yml` compiles C/C++/Objective-C/Swift for iOS 17+, links Metal/UIKit and a libarchive XCFramework, and includes generated Metal shader resources. `EngineHost.c` calls the translated engine's constructors and `_main_argc_argv` on native threads. `MRRenderer.mm` consumes the engine's graphics command ring using Metal commands. This architecture would run ARM64 machine code without a Wasm JIT or remote screen streaming if the missing engine and shaders build and work.

`NativeAssets.m` has a direct local file path enabled by `PGSetLocalGameFolder`, and the Swift app passes the selected folder to it. The older server mode streams asset bytes, not video/gameplay execution. The prepared workflow uses `--mirror` with a blank default server, so the intended runtime route is a local iPhone folder.

## Required missing components and limitations

| Finding | Evidence and consequence |
| --- | --- |
| Proprietary engine absent | No `game.wasm` is tracked. Both `check_game_files.py` and `prepare.py` pin one hash. A different build, `GTA5.exe`, retail archives alone, or a placeholder cannot substitute. |
| No retail-to-Wasm conversion | No scripts/source/compiler inputs reconstruct the required engine from an ordinary licensed PC installation. The provenance/authorization of this web build is not demonstrated. The repository's MIT license does not cover it. |
| Shaders and manifest absent | Exact shader index hash and every indexed pack are required. The claimed 85 MB input size/18 packs cannot be measured without them. The runtime list is proprietary input `data/manifest.json`. |
| Generated engine interface absent | `Generated/game.h`, `game_*.c` and runtime tool directories are intentionally generated/downloaded. Their absence is a required input/build dependency, not proof of fake code. |
| Unported imports stop execution | `generate_imports.py` generates `pg_missing_import` traps for unknown imports. It labels `invoke_*` forwarding “EH remains unported”. Actual imported function coverage requires the real generated `Build/import-status.tsv`, which cannot yet be produced. |
| Incomplete host semantics | Several Emscripten mailbox/cleanup hooks are no-ops; stack snapshot/unwind return zero; `emscripten_system` returns unsupported. Their gameplay relevance depends on actual engine paths. |
| Missing content worked around | Engine-specific patches skip unavailable video loading after a timeout and report absent texture dictionaries as loaded. The changelog acknowledges missing videos and mismatched scripts/assets. These are degraded behavior, not complete content restoration. |
| Graphics gaps | Renderer code logs/skips unknown opcodes, unsupported vertex formats, some format copies and readbacks; format mapping has an RGBA8 fallback. These may matter for visual correctness or game paths. No screenshots/performance were generated in this audit. |
| Memory risk | Engine reserves roughly 4,095 MiB of address space with a 3,328 MiB initial logical heap. Default `PG_UNCHECKED_MEMORY=1` disables scalar range/call-depth checks and relies on a finite guard region; this is not equivalent to complete Wasm memory safety. Physical allocation, Jetsam and performance on the iPhone remain untested. |
| Stale tests | Ten existing tests require removed renderer files or the generated engine plus server. They cannot establish coverage of the current Metal renderer. |

The upstream includes Social Club disabling switches (`-noSocialClub`, `-pc:nosocialclub`). They were removed in the prepared version to respect the requested licensing constraint. Their exact role in this unavailable engine is unknown, and this change may expose an additional startup dependency. No login/DRM bypass was added. Game ownership by itself is not proof of authorization for an unofficial web engine.

The repository says it contains no game files/code, but includes themed UI artwork, game-specific memory offsets, function-number patches, and a game file-path warm set. No playable engine/data archives were found. Do not interpret its statement as a legal clearance of every included image or of the missing engine.

## Dependencies and trust

- WABT 1.0.42: versioned macOS ARM64 release; archive checksum obtained from the same release, with two writer sources downloaded at the same version tag. The writer is patched for atomic wait/notify.
- SIMDe v0.8.2: fetched by tag for shared SIMD helpers; BC decoder fetched at commit `80859ed3b7afb1c527a2a99d70c61457bea72d0c` under MIT.
- `pgmsl` shader translator: macOS ARM64 binary pinned to SHA-256 `c80005c5fe22653cc7b2dd10a8276202df8e8fbfcb6d6d1a3e6599c2240105a1`; checksum matched. Archive includes project source, Dawn/Tint and Abseil license notices. Its README does not pin the exact Dawn commit or fully establish binary-to-source reproducibility.
- libarchive XCFramework: vendored ARM64 iOS/device, iOS/simulator and macOS archives; headers identify version 3.8.9, and license notices are provided. No complete in-repository rebuild recipe/provenance was found for these binary slices.
- Xcode/XcodeGen and Metal compiler: macOS-only. GitHub's current runner documentation lists `macos-15` as standard ARM64 for private repositories (3 M1 cores/7 GB RAM). The workflow checks the actual architecture and records Xcode. Runner images can change; their current configuration was not executed here.
- Prepared GitHub actions are pinned to inspected commit IDs. No third-party builder OAuth service is needed for this path.

`LogUploader.swift` uploads the current/previous game logs and device/app information to `https://fivestarport.vercel.app/api/log` after an explicit Send action. Logs may contain paths, server addresses and game output. The optional `--frame-reports` mode sends metrics to the configured asset server and is off by default. Remote archive import and server mode also use URLSession; ATS allows arbitrary loads for custom servers. No automatic credential-harvesting path was found in the reviewed source/network calls, but this is not a malware-free certification of the app or prebuilt dependencies. No logs/messages were sent to the developer in this session.

The local archive importer can punch holes in or delete a source archive when its source-reclaiming option is enabled. Retain your original on Windows and do not assume the phone's archive will be preserved when choosing that option.

## Changes prepared

- Preserved the original workflow in `audit/upstream-build-ipa.yml` and upstream history locally; replaced the active build workflow with a private, minimal-input path.
- Added a Windows-compatible Python uploader: exact engine/index hash checks, shader range validation, one minimal ZIP, temporary private release upload, and workflow dispatch. It does not read/upload the full runtime dataset.
- Added preflight rejection of wrong/missing inputs before macOS allocation, pinned action references, ARM64/Xcode environment checks, ad-hoc signature/IPA checks, private artifacts and input cleanup. Successful input releases are deleted; failed inputs remain private for retries. Finished IPAs must include compiled proprietary engine/shaders, which this architecture cannot avoid.
- Added asset-free macOS checks for the current renderer, installer C and the full Swift app against the actual iOS SDK, plus open-source runtime/SIMD probes. These have **not run** yet.
- Fixed the shader translator's source exit status, independently required complete reflection in Python because the distributed prebuilt translator still returns success after partial failures, and prevented linking after a shader compiler batch failure.
- Cleaned IPA staging before repackaging, made Linux/unsupported-host failure explicit, and kept failure reporting from being interrupted by `pipefail`/`head`.
- Removed Social Club disabling switches; added explicit Windows line ending/executable-mode handling and installation/data-transfer instructions.

## Tests actually executed

| Check | Actual result |
| --- | --- |
| Nine upstream portable test programs compiled and executed with GCC/G++ on Linux | **9 passed, 0 failed** |
| Remaining upstream tests | **12 blocked**: two require Apple Silicon/macOS, nine reference removed renderer code/resources, one needs generated engine/server |
| Four added pipeline regression tests | **4 passed**: incomplete translator output is rejected, a compiler failure cannot link stale AIR, wrong engine is rejected, arbitrary ZIP is rejected as an IPA |
| GitHub workflow lint | **Passed** using actionlint 1.7.12 |
| Python syntax and shell syntax | **Passed** |
| Upstream real-input preflight | **Failed as expected**: missing `b/8b0b5899ed/game.wasm` |
| Actual local build-script invocation | **Blocked before compilation**: host is Linux and lacks Apple Silicon/macOS/Xcode |
| GitHub-hosted macOS compile/typecheck/test workflows | **Not run**: destination repository cannot be created with current integration |
| Device-signed IPA / sideload / GTA gameplay / iPhone performance | **Not tested; no artifact produced** |

See [portable-test-results.json](portable-test-results.json), [pipeline-tests.log](pipeline-tests.log), [local-validation.json](local-validation.json) and [remote-status.json](remote-status.json). The BC decoder test includes 1,372 comparisons with the project's reference decoder; that verifies consistency with its reference rather than proving all texture formats correct for the missing game.

The IPA verifier is only a packaging gate: ZIP CRC, payload/Info.plist, ARM64 Mach-O executable, iOS-device load command, necessary resources and absence of raw Wasm/RPF runtime archives. A successful static check or ad-hoc `codesign --verify` would **not** prove Apple provisioning, installation or gameplay. AltStore/SideStore must re-sign the actual artifact, and a physical iPhone test remains necessary.

## What remains to complete the requested delivery

1. Source publication and public macOS source checks are complete. The full IPA workflow still requires a protected input/output route and currently enforces a private destination; the public source run does not resolve private Actions billing.
2. User supplies the exact WebAssembly engine, indexed shader packs and matching manifest through the Windows uploader, only if authorized to use them. No lawful source/conversion was established by this audit.
3. After the account restriction and game-input requirement are resolved, the assistant can run the real macOS workflows, inspect failures, fix reproducible issues, verify any actual IPA and provide confirmed artifact links. The currently linked run is a startup failure, not a successful build.
4. User completes Apple ID signing on Windows/iPhone and tests real installation/boot on their iPhone 16 Pro Max. No Apple credentials need to be given to the assistant.

Detailed file requirements, Windows commands, AltStore instructions and direct-to-iPhone transfer are in [README-AUDITED.md](../README-AUDITED.md).
