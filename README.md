# SuperFileCompressor

SuperFileCompressor is the native C++ implementation of the **NZ** archive format. The current v0.2 engine uses Zstandard for compression and XXH64 for per-chunk and whole-file integrity verification.

## Current capabilities

- Compress a file into an `.nz` archive.
- Extract an `.nz` archive back to its original file.
- Stream the input in chunks instead of loading the complete file into memory.
- Store original size, compressed size, chunk count, and checksums in the archive header.
- Verify every decompressed chunk before writing it.
- Verify the final reconstructed size and whole-file checksum after extraction.
- Use the included desktop GUI to select files, choose operations, monitor output, and verify results.

## Requirements — Kali Linux / Debian / Ubuntu

Install the compiler, CMake, pkg-config, Zstandard development files, xxHash development files, and Tkinter for the desktop GUI:

```bash
sudo apt update
sudo apt install -y build-essential cmake pkg-config libzstd-dev libxxhash-dev python3-tk
```

The project requires C++20 and CMake 3.20 or newer.

## Build from GitHub

Clone the repository and enter it:

```bash
git clone https://github.com/neoe974-tech/SuperFileCompressor.git
cd SuperFileCompressor
```

Create a clean build directory:

```bash
rm -rf build
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j"$(nproc)"
```

The native executable will be created at:

```text
build/nzcompress
```

Check that it starts:

```bash
./build/nzcompress
```

## Desktop GUI

The repository includes a dependency-light Tkinter GUI at `gui/nzgui.py`. The GUI delegates all archive work to the native C++ engine, so the GUI and CLI use the same NZ implementation.

Start it from the project root:

```bash
python3 gui/nzgui.py
```

The GUI provides:

- Compress → `.nz`
- Extract `.nz`
- File picker for input and output
- Automatic output-name suggestions
- Overwrite confirmation
- Operation log
- Background execution so the window remains responsive
- Output-folder opener
- Basic result verification/information
- Automatic discovery of `build/nzcompress`

If the GUI says the NZ engine cannot be found, build the C++ target first:

```bash
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j"$(nproc)"
```

Then start the GUI again.

## Basic CLI test

Create a test file:

```bash
printf 'SuperFileCompressor NZ test file\n' > test-local.txt
```

Compress it:

```bash
./build/nzcompress compress test-local.txt test-local.nz
```

Expected output is similar to:

```text
NZ compression successful
Original:   34 bytes
Compressed: <size> bytes
Chunks:     1
```

Extract it:

```bash
./build/nzcompress extract test-local.nz restored-local.txt
```

Verify the extracted file is identical to the original:

```bash
cmp test-local.txt restored-local.txt && echo 'ROUND-TRIP OK'
```

You can also compare SHA-256 hashes:

```bash
sha256sum test-local.txt restored-local.txt
```

Both hashes must be identical.

## GUI test

After building:

```bash
python3 gui/nzgui.py
```

1. Select **Compress → .nz**.
2. Choose `test.txt` or another test file.
3. Confirm the suggested `.nz` destination.
4. Click **Start Compression**.
5. Switch to **Extract .nz**.
6. Select the generated archive.
7. Choose a restored-file destination.
8. Click **Start Extraction**.
9. Compare the original and restored files with `cmp` or SHA-256.

## Test the repository sample

The repository contains `test.txt` and sample `.nz` files. To perform a fresh round trip without overwriting the tracked samples:

```bash
./build/nzcompress compress test.txt test-local.nz
./build/nzcompress extract test-local.nz restored-local.txt
cmp test.txt restored-local.txt && echo 'ROUND-TRIP OK'
```

## Large-file test

Generate a larger file locally:

```bash
dd if=/dev/urandom of=large-test.bin bs=1M count=128 status=progress
```

Compress:

```bash
./build/nzcompress compress large-test.bin large-test.nz
```

Extract:

```bash
./build/nzcompress extract large-test.nz large-test-restored.bin
```

Verify:

```bash
cmp large-test.bin large-test-restored.bin && echo 'LARGE FILE ROUND-TRIP OK'
```

Remove temporary test files when finished:

```bash
rm -f test-local.txt test-local.nz restored-local.txt large-test.bin large-test.nz large-test-restored.bin
```

## Command reference

### Compress

```bash
./build/nzcompress compress <input-file> <output.nz>
```

Example:

```bash
./build/nzcompress compress photo.jpg photo.nz
```

### Extract

```bash
./build/nzcompress extract <input.nz> <output-file>
```

Example:

```bash
./build/nzcompress extract photo.nz photo-restored.jpg
```

## NZ v0.2 format

The current engine writes the `NZ02` format with:

- magic: `NZ02`
- format version: `2`
- compression method: Zstandard
- chunk size
- original file size
- compressed payload size
- whole-file XXH64 checksum
- chunk count
- per-chunk compressed size
- per-chunk uncompressed size
- per-chunk XXH64 checksum

The format is intentionally stream-oriented so large files can be processed without reading the entire source file into RAM.

## Troubleshooting

### `Package 'libzstd' ... not found`

```bash
sudo apt install -y libzstd-dev
```

### `Package 'libxxhash' ... not found`

```bash
sudo apt install -y libxxhash-dev
```

### `No module named tkinter`

```bash
sudo apt install -y python3-tk
```

### `cmake: command not found`

```bash
sudo apt install -y cmake
```

### `g++: command not found`

```bash
sudo apt install -y build-essential
```

### Build is using stale files

```bash
rm -rf build
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j"$(nproc)"
```

## Development notes

The archive format and compression engine are still under active development. Do not assume NZ v0.2 archives will remain byte-compatible with future format versions until a stable format specification is published.

For repository security, do not commit credentials, API keys, private keys, or other secrets.
