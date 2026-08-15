#include "nz/checksum.hpp"

#include <xxhash.h>

namespace nz {

std::uint64_t checksum64(
    const void* data,
    std::size_t size
) {
    return XXH64(data, size, 0);
}

} // namespace nz
