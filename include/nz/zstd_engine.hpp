#pragma once

#include <cstdint>
#include <vector>

namespace nz {

class ZstdEngine {
public:
    static std::vector<std::uint8_t> compress(
        const std::uint8_t* data,
        std::size_t size,
        int level = 3
    );

    static std::vector<std::uint8_t> decompress(
        const std::uint8_t* data,
        std::size_t compressed_size,
        std::size_t original_size
    );
};

} // namespace nz
