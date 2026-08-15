# SuperFileCompressor

SuperFileCompressor is the native C++ implementation of the **NZ** archive format. The current v0.2 engine uses Zstandard for compression and XXH64 for per-chunk and whole-file integrity verification.

## Current capabilities

- Compress a file into an `.nz` archive.
- Extract an `.nz` archive back to its original file.
- Stream the input in chunks instead of loading the complete file into memory.
- Store original size, compressed size, chunk count, and checksums in the archive header.
- Verify every decompressed chunk before writing it.
- Verify the final reconstructed size and whole-file checksum after extraction.

## Requirements — Kali Linux / Debian / Ubuntu

Install the compiler, CMake, pkg-config, Zstandard development files, and xxHash development files:

```bash
sudo apt update
sudo apt install -y build-essential cmake pkg-config libzstd-dev libxxhash-dev
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

The executable will be created at:

```text
build/nzcompress
```

Check that it starts:

```bash
./build/nzcompress
```

## Basic test

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

## Test the repository sample

The repository already contains `test.txt` and sample `.nz` files. To perform a fresh round trip without overwriting the tracked samples:

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

Install the Zstandard development package:

```bash
sudo apt install -y libzstd-dev
```

### `Package 'libxxhash' ... not found`

Install the xxHash development package:

```bash
sudo apt install -y libxxhash-dev
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

Do a clean configure/build:

```bash
rm -rf build
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j"$(nproc)"
```

## Development notes

The archive format and compression engine are still under active development. Do not assume NZ v0.2 archives will remain byte-compatible with future format versions until a stable format specification is published.

For repository security, do not commit credentials, API keys, private keys, or other secrets. GitHub recommends using repository security features such as secret scanning and push protection where available.
