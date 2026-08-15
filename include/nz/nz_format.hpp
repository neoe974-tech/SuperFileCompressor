#pragma once

#include <cstdint>

namespace nz {

constexpr char MAGIC[4] = {'N', 'Z', '0', '1'};
constexpr std::uint16_t VERSION = 1;

enum class CompressionMethod : std::uint8_t {
    Zstd = 1
};

struct ArchiveHeader {
    char magic[4];
    std::uint16_t version;
    std::uint8_t compression_method;
    std::uint8_t flags;

    std::uint32_t chunk_size;

    std::uint64_t original_size;
    std::uint64_t compressed_size;

    std::uint64_t original_checksum;

    std::uint32_t chunk_count;
};

struct ChunkHeader {
    std::uint32_t compressed_size;
    std::uint32_t uncompressed_size;
    std::uint32_t checksum;
};

} // namespace nz
