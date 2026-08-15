#pragma once

#include <cstdint>
#include <string>

namespace nz {

struct CompressionStats {
    std::uint64_t original_size = 0;
    std::uint64_t compressed_size = 0;
    std::uint64_t chunk_count = 0;
    double compression_ratio = 0.0;
};

CompressionStats compress_file(
    const std::string& input_path,
    const std::string& output_path,
    int compression_level = 3,
    std::uint64_t chunk_size = 64ULL * 1024ULL * 1024ULL
);

void decompress_file(
    const std::string& input_path,
    const std::string& output_path
);

} // namespace nz
