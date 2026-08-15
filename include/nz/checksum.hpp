#pragma once

#include <cstdint>
#include <cstddef>

namespace nz {

std::uint64_t checksum64(
    const void* data,
    std::size_t size
);

} // namespace nz
