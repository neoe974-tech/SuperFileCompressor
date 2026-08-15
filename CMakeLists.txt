cmake_minimum_required(VERSION 3.20)

project(SuperFileCompressor
    VERSION 0.1.0
    LANGUAGES CXX
)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

find_package(PkgConfig REQUIRED)

pkg_check_modules(ZSTD REQUIRED IMPORTED_TARGET libzstd)
pkg_check_modules(XXHASH REQUIRED IMPORTED_TARGET libxxhash)

add_executable(nzcompress
    src/main.cpp
    src/compression/zstd_engine.cpp
    src/integrity/checksum.cpp
)

target_include_directories(nzcompress
    PRIVATE
        ${CMAKE_CURRENT_SOURCE_DIR}/include
)

target_link_libraries(nzcompress
    PRIVATE
        PkgConfig::ZSTD
        PkgConfig::XXHASH
)

target_compile_options(nzcompress
    PRIVATE
        -Wall
        -Wextra
        -Wpedantic
)

