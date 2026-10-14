# Audited Windows build preparation

**Status on 2026-10-14: no verified IPA has been produced.** Source and build workflows are now published in the user's [private repository](https://github.com/omarkebrit/gta5-ios-port-audited). GitHub accepted the push and created a [source-check run](https://github.com/omarkebrit/gta5-ios-port-audited/actions/runs/38542594399), but refused to start the macOS job because recent account payments have failed or the spending limit needs to be increased. No macOS test or compilation step executed. The required proprietary WebAssembly engine/shaders/manifest are also absent. See [audit/REPORT.md](audit/REPORT.md) for evidence and limitations.

This project requires a specific pre-existing WebAssembly build. A normal Steam, Epic or Rockstar GTA V installation is insufficient. The repository provides neither the engine nor a conversion from a retail PC executable. Owning the PC game does not establish permission to obtain or use a third-party WebAssembly redistribution. Supply only files you are authorized to use; no game download sources are provided here.

## Required build inputs

The folder supplied to the uploader must contain:

| Relative path | Requirement |
| --- | --- |
| `b/8b0b5899ed/game.wasm` | SHA-256 `11ca8d2c04c5e843d18ff4aea4899d72c86973c6b031df334e67c446b2ae83e0` |
| `b/8b0b5899ed/shaders/index.json` | SHA-256 `11c331895051b30126980ef666bd8935314ab400348b17c56ef8fe8983f50ee0` |
| `b/8b0b5899ed/shaders/<pack filename>` | Every filename in `index.json` → `_packs` → `file`, with every indexed byte range present |
| `data/manifest.json` | The matching build's nonempty file list; not a manifest generated from a different PC installation |

The upstream describes 18 shader packs and about 85 MB total upload. Those counts/sizes cannot be independently confirmed without the actual inputs. The uploader prints the measured ZIP size. You do not need to make `shaders.zip` manually; it packages the same minimal files automatically.

For play on the iPhone, supply **every runtime file named by `data/manifest.json` → `files[][0]` under `data/`, at the listed size**, preserving relative paths. The engine and shaders are compiled into the IPA; the full runtime data stays off GitHub. The exact hashed pack names and runtime file list are determined by your verified index and manifest, which are absent from this repository.

## Current account blocker

The repository is now private and writable through the connection; source publication is complete. The prepared workflows are [Asset-free source checks](https://github.com/omarkebrit/gta5-ios-port-audited/actions/workflows/audit.yml) and [Build my IPA](https://github.com/omarkebrit/gta5-ios-port-audited/actions/workflows/build-ipa.yml).

GitHub's exact job annotation is: “The job was not started because recent account payments have failed or your spending limit needs to be increased. Please check the 'Billing & plans' section in your settings”. Inspect [your account billing settings](https://github.com/settings/billing). This message does not identify which condition applies; no credit card, charge, spending increase or payment change was made by the assistant. Account payment/budget resolution requires the account owner. After resolving the account restriction, the assistant can retry the source checks; actual IPA compilation still requires the game inputs. Earlier repository-creation/visibility permission errors have been superseded by the user creating and making the repository private.

## Windows fallback if connection permissions remain insufficient

Source publication is already complete; do not run the empty-repository publisher again. The following publisher instructions are retained for a fresh destination if needed. For uploading your own authorized game inputs, clone the published private repository or use the supplied source ZIP, keeping your game data outside that source folder. Install Git, GitHub CLI and Python 3.11; these Windows commands are one route:

```powershell
winget install --id Git.Git --exact
winget install --id GitHub.cli --exact
winget install --id Python.Python.3.11 --exact
```

Open a new PowerShell window in the extracted source folder and sign in to GitHub:

```powershell
gh auth login
py -3.11 tools/publish_repository.py --repo omarkebrit/gta5-ios-port-audited
```

Select your own GitHub account and authorize repository/workflow writes. The publisher refuses a public, unwritable or nonempty repository and never force-pushes. It imports only the source roots, preserves the license, fixes the build script's executable mode after Windows ZIP extraction, and pushes `main`. The **Asset-free source checks** workflow then runs automatically on `macos-15`.

Once you have the authorized files above, run:

```powershell
py -3.11 tools/build_from_windows.py --game-folder "D:\YourAuthorizedWebBuild" --repo omarkebrit/gta5-ios-port-audited
```

The helper validates the engine/index hashes and shader ranges, creates one minimal ZIP, uploads it as a temporary **private release asset**, and dispatches **Build my IPA**. Proprietary inputs never enter Git history. Only add `--paid` if you will sign with a paid Apple developer team supporting the memory entitlements.

The workflow validates inputs on Ubuntu before allocating macOS, compiles on an Apple Silicon `macos-15` runner, checks the ad-hoc signature and IPA structure, and saves `GTA5Port-ipa` for three days. Download it from the successful run's **Artifacts**, then extract `GTA5Port.ipa` from the downloaded ZIP. No IPA is uploaded when compilation or verification fails. Successful input releases are deleted automatically; failed inputs remain private so builds can be retried without another upload. Delete a retained input release after debugging using its exact tag:

```powershell
gh release delete build-inputs-REPLACE_WITH_YOUR_EXACT_TAG --repo omarkebrit/gta5-ios-port-audited --yes --cleanup-tag
```

The resulting IPA necessarily contains the proprietary engine as ARM64 machine code, compiled shaders and the manifest. That cannot be omitted while preserving this architecture. It does not contain the 21 GB runtime data directory. CI credentials do not require your Apple ID or Apple signing certificate. Private Actions usage is subject to your account's current minutes, billing and runner availability; neither a duration nor a successful build is promised.

## Install on Windows with AltStore Classic

These steps apply only **after** a real IPA is built; installation and gameplay have not been verified in this session.

1. Follow the official [AltStore Classic Windows installation guide](https://faq.altstore.io/altstore-classic/how-to-install-altstore-windows). Install AltServer on Windows and the Apple dependencies it currently specifies. The traditional guide uses Apple-distributed iTunes/iCloud; follow the current guide's version instructions rather than mixing installers. The guide could not be fetched in this session (HTTP 403), so current installer details were not independently verified.
2. Connect the iPhone by USB, unlock it, and accept **Trust This Computer**. Use AltServer's **Install AltStore** command and sign in with your Apple ID yourself. Keep Apple credentials on your own device/PC.
3. On the iPhone, trust the developer entry under **Settings → General → VPN & Device Management**. Enable **Settings → Privacy & Security → Developer Mode** if iOS requests it, including the required restart/confirmation.
4. Transfer the downloaded IPA to the iPhone through a Files-accessible route such as your own SMB share or iCloud Drive. Using iCloud for the small IPA is fine. In AltStore, open **My Apps → +**, select `GTA5Port.ipa`, and let AltStore re-sign/install it.
5. With a free Apple ID, refresh the app within seven days while AltServer is running and reachable; USB is a dependable refresh route. Free-account app/App ID limits also apply. A private Actions artifact's ad-hoc signature alone does not authorize installation on a normal iPhone.

If SideStore is already configured, use its **My Apps → +** to import the IPA. Otherwise follow [SideStore's official installation instructions](https://docs.sidestore.io/docs/installation/install/), including its current Windows pairing and on-device VPN setup; those details could not be fetched here and can change. AltStore Classic is the simpler fallback described above. Do not assume extra-memory entitlements work with a free account; this kit defaults to the empty free entitlements and does not use GetMoreRam or TrollStore.

## Move game data directly from Windows to the iPhone

Use a USB cable and the **Apple Devices** Windows app once the IPA has been installed. Unlock/trust the phone, select it, then **Files → GTA V Port**. Transfer your local game folder containing `data/`; preserve `data/common/...` and `data/x64/...`. The app's `UIFileSharingEnabled` and `LSSupportsOpeningDocumentsInPlace` settings expose its Documents folder as **Files → On My iPhone → GTA V Port**. Launch the app once to create that folder if needed. Choose the folder in **Game files → Choose a folder…** if automatic discovery does not find it.

Apple's [Windows file-sharing guide](https://support.apple.com/guide/devices-windows/transfer-files-to-and-from-your-apple-device-mchl4bd77d3a/windows) documents dragging files into a sharing app; it does not explicitly guarantee dragging directory trees in every version. If folder transfer is unavailable, make a ZIP on the PC containing `data/` and its complete contents, transfer that ZIP as one file into GTA V Port, then select it in the app's archive importer. Keep the original PC copy. Local unpacking may need space for both ZIP and extracted data: the app has an optional source-reclaiming mode, but APFS hole punching is not guaranteed, and that mode modifies/deletes the phone's source archive. The conservative fallback is to allow enough space for both. Direct folder transfer avoids that extra temporary storage.

You may also use an SMB share on your own Windows PC through the iPhone Files app, copying into **On My iPhone → GTA V Port**, then play from that local copy. No GitHub upload or gameplay streaming is involved. Avoid iCloud Drive for the runtime data. The upstream recommends about 30 GB free for its claimed 21 GB dataset; measure your actual dataset and leave room for the app, saves and temporary files.

After selecting the local folder, the app checks presence and file size against the bundled manifest. That check is **not** a cryptographic integrity check. Actual native boot, rendering, missions, stability and offline play on your iPhone 16 Pro Max still require a physical-device test. Start with conservative graphics and 30 FPS; the repository's claimed frame rates are not verified measurements for your phone.
