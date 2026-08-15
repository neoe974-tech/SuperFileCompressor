# SuperFileCompressor

SuperFileCompressor is the native C++ implementation of the **NZ** archive format. The stable engine currently writes NZ02 archives using Zstandard compression and XXH64 integrity verification. **NZ v3** adds a desktop GUI, File menu, toolbar, Help/About dialogs, verification, and a password-key preparation panel.

## NZ v3 desktop features

- Compress files to `.nz`.
- Extract `.nz` archives.
- File menu and toolbar.
- Browse input/output paths.
- Output-folder launcher.
- Operation log and verification.
- Password + confirmation fields.
- Deterministic v3 password-key fingerprint generation.
- Passwords are not written to logs or saved to disk.
- Windows x64 PyInstaller release workflow.

### Password protection status

The current NZ02 archive format is **not encrypted**. The v3 password panel derives a key fingerprint for the planned authenticated-encryption format; it does not pretend that a normal NZ02 archive is password protected. The next archive-format generation should use a per-archive random salt and authenticated encryption rather than a universal static salt or plain password hash.

## Linux requirements

```bash
sudo apt update
sudo apt install -y build-essential cmake pkg-config libzstd-dev libxxhash-dev python3-tk
```

## Build the native engine

```bash
git clone https://github.com/neoe974-tech/SuperFileCompressor.git
cd SuperFileCompressor
rm -rf build
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j"$(nproc)"
```

## Run NZ v3 GUI

```bash
python3 gui/nzgui.py
```

The GUI automatically looks for `build/nzcompress`.

## CLI

```bash
./build/nzcompress compress <input-file> <output.nz>
./build/nzcompress extract <input.nz> <output-file>
```

## Round-trip test

```bash
printf 'SuperFileCompressor NZ v3 test\n' > test-local.txt
./build/nzcompress compress test-local.txt test-local.nz
./build/nzcompress extract test-local.nz restored-local.txt
cmp test-local.txt restored-local.txt && echo 'ROUND-TRIP OK'
sha256sum test-local.txt restored-local.txt
```

## Windows x64 build

The `v3-gui` branch contains `.github/workflows/windows-x64.yml`. It uses a Windows x64 GitHub Actions runner, MSYS2 UCRT64, CMake/Ninja, Zstandard, xxHash, Python x64, and PyInstaller.

To build manually from GitHub Actions, open the **Actions** tab and run **Build Windows x64** with `workflow_dispatch`.

The release artifact is:

```text
SuperFileCompressor-v3-windows-x64.zip
```

It contains the Windows x64 GUI executable. The native NZ engine is bundled into the PyInstaller executable.

## NZ02 format

The current engine stores:

- `NZ02` magic/version information
- chunk size
- original size
- compressed payload information
- whole-file XXH64 checksum
- chunk count
- per-chunk compressed/uncompressed sizes
- per-chunk XXH64 checksums

The stream engine processes data in chunks rather than loading the entire source file into RAM.

## Development roadmap

1. NZ02 compression/extraction — implemented.
2. Desktop GUI — implemented on the v3 branch.
3. Windows x64 packaging — implemented as GitHub Actions workflow.
4. NZ04 password-protected authenticated archive format — next engine milestone.
5. Multi-file archives and directory support.
6. Progress/cancellation and archive information panels.
7. Signed releases and installer.

Do not assume NZ02 archives will remain byte-compatible with future format versions until the archive specification is frozen.
