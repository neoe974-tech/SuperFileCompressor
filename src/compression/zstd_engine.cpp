#include "nz/zstd_engine.hpp"

#include <zstd.h>
#include <stdexcept>

namespace nz {

std::vector<std::uint8_t> ZstdEngine::compress(
    const std::uint8_t* data,
    std::size_t size,
    int level
) {
    const std::size_t bound = ZSTD_compressBound(size);

    std::vector<std::uint8_t> output(bound);

    const std::size_t result =
        ZSTD_compress(
            output.data(),
            output.size(),
            data,
            size,
            level
        );

    if (ZSTD_isError(result)) {
        throw std::runtime_error(
            ZSTD_getErrorName(result)
        );
    }

    output.resize(result);

    return output;
}

std::vector<std::uint8_t> ZstdEngine::decompress(
    const std::uint8_t* data,
    std::size_t compressed_size,
    std::size_t original_size
) {
    std::vector<std::uint8_t> output(original_size);

    const std::size_t result =
        ZSTD_decompress(
            output.data(),
            output.size(),
            data,
            compressed_size
        );

    if (ZSTD_isError(result)) {
        throw std::runtime_error(
            ZSTD_getErrorName(result)
        );
    }

    if (result != original_size) {
        throw std::runtime_error(
            "NZ decompression size mismatch"
        );
    }

    return output;
}

} // namespace nz
