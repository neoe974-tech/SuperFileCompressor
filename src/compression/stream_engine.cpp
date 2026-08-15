#include "nz/stream_engine.hpp"

#include <zstd.h>
#include <xxhash.h>

#include <array>
#include <fstream>
#include <stdexcept>
#include <vector>

namespace nz {

namespace {

constexpr char MAGIC[4] = {'N', 'Z', '0', '2'};
constexpr std::uint16_t VERSION = 2;

struct Header {
    char magic[4];
    std::uint16_t version;
    std::uint8_t method;
    std::uint8_t reserved;

    std::uint32_t chunk_size;

    std::uint64_t original_size;
    std::uint64_t compressed_size;

    std::uint64_t checksum;
    std::uint64_t chunk_count;
};

struct ChunkHeader {
    std::uint32_t compressed_size;
    std::uint32_t uncompressed_size;
    std::uint64_t checksum;
};

void write_exact(
    std::ofstream& out,
    const void* data,
    std::size_t size
) {
    out.write(
        static_cast<const char*>(data),
        static_cast<std::streamsize>(size)
    );

    if (!out) {
        throw std::runtime_error("Failed writing NZ archive");
    }
}

void read_exact(
    std::ifstream& in,
    void* data,
    std::size_t size
) {
    in.read(
        static_cast<char*>(data),
        static_cast<std::streamsize>(size)
    );

    if (!in) {
        throw std::runtime_error("Unexpected end of NZ archive");
    }
}

} // namespace

CompressionStats compress_file(
    const std::string& input_path,
    const std::string& output_path,
    int compression_level,
    std::uint64_t chunk_size
) {
    if (chunk_size == 0) {
        throw std::invalid_argument("Chunk size cannot be zero");
    }

    std::ifstream input(
        input_path,
        std::ios::binary
    );

    if (!input) {
        throw std::runtime_error("Cannot open input file");
    }

    std::ofstream output(
        output_path,
        std::ios::binary
    );

    if (!output) {
        throw std::runtime_error("Cannot create output file");
    }

    Header header{};

    std::copy(
        std::begin(MAGIC),
        std::end(MAGIC),
        std::begin(header.magic)
    );

    header.version = VERSION;
    header.method = 1;
    header.chunk_size =
        static_cast<std::uint32_t>(chunk_size);

    write_exact(
        output,
        &header,
        sizeof(header)
    );

    std::vector<std::uint8_t> input_buffer(
        static_cast<std::size_t>(chunk_size)
    );

    const std::size_t max_compressed =
        ZSTD_compressBound(
            static_cast<std::size_t>(chunk_size)
        );

    std::vector<std::uint8_t> compressed_buffer(
        max_compressed
    );

    XXH64_state_t* hash_state = XXH64_createState();

    if (!hash_state) {
        throw std::runtime_error(
            "Failed to create checksum state"
        );
    }

    XXH64_reset(hash_state, 0);

    CompressionStats stats;

    while (input) {

        input.read(
            reinterpret_cast<char*>(input_buffer.data()),
            static_cast<std::streamsize>(chunk_size)
        );

        const std::streamsize bytes_read =
            input.gcount();

        if (bytes_read <= 0) {
            break;
        }

        const std::size_t actual_size =
            static_cast<std::size_t>(bytes_read);

        XXH64_update(
            hash_state,
            input_buffer.data(),
            actual_size
        );

        const std::size_t compressed_size =
            ZSTD_compress(
                compressed_buffer.data(),
                compressed_buffer.size(),
                input_buffer.data(),
                actual_size,
                compression_level
            );

        if (ZSTD_isError(compressed_size)) {

            XXH64_freeState(hash_state);

            throw std::runtime_error(
                ZSTD_getErrorName(compressed_size)
            );
        }

        ChunkHeader chunk{};

        chunk.compressed_size =
            static_cast<std::uint32_t>(compressed_size);

        chunk.uncompressed_size =
            static_cast<std::uint32_t>(actual_size);

        chunk.checksum =
            XXH64(
                input_buffer.data(),
                actual_size,
                0
            );

        write_exact(
            output,
            &chunk,
            sizeof(chunk)
        );

        write_exact(
            output,
            compressed_buffer.data(),
            compressed_size
        );

        stats.original_size += actual_size;
        stats.compressed_size += compressed_size;
        stats.chunk_count++;
    }

    header.original_size = stats.original_size;
    header.compressed_size = stats.compressed_size;
    header.chunk_count = stats.chunk_count;
    header.checksum = XXH64_digest(hash_state);

    XXH64_freeState(hash_state);

    /*
     * Return to the beginning and update the header.
     */
    output.seekp(0);

    write_exact(
        output,
        &header,
        sizeof(header)
    );

    output.close();

    if (stats.original_size > 0) {
        stats.compression_ratio =
            static_cast<double>(
                stats.compressed_size
            ) /
            static_cast<double>(
                stats.original_size
            );
    }

    return stats;
}

void decompress_file(
    const std::string& input_path,
    const std::string& output_path
) {
    std::ifstream input(
        input_path,
        std::ios::binary
    );

    if (!input) {
        throw std::runtime_error(
            "Cannot open NZ archive"
        );
    }

    Header header{};

    read_exact(
        input,
        &header,
        sizeof(header)
    );

    if (!std::equal(
            std::begin(MAGIC),
            std::end(MAGIC),
            std::begin(header.magic))) {

        throw std::runtime_error(
            "Invalid NZ magic"
        );
    }

    if (header.version != VERSION) {
        throw std::runtime_error(
            "Unsupported NZ version"
        );
    }

    if (header.method != 1) {
        throw std::runtime_error(
            "Unsupported compression method"
        );
    }

    std::ofstream output(
        output_path,
        std::ios::binary
    );

    if (!output) {
        throw std::runtime_error(
            "Cannot create output file"
        );
    }

    std::vector<std::uint8_t> compressed;
    std::vector<std::uint8_t> decompressed;

    XXH64_state_t* hash_state = XXH64_createState();

    if (!hash_state) {
        throw std::runtime_error(
            "Failed to create checksum state"
        );
    }

    XXH64_reset(hash_state, 0);

    std::uint64_t total_output = 0;

    for (
        std::uint64_t i = 0;
        i < header.chunk_count;
        ++i
    ) {
        ChunkHeader chunk{};

        read_exact(
            input,
            &chunk,
            sizeof(chunk)
        );

        compressed.resize(chunk.compressed_size);
        decompressed.resize(chunk.uncompressed_size);

        read_exact(
            input,
            compressed.data(),
            compressed.size()
        );

        const std::size_t result =
            ZSTD_decompress(
                decompressed.data(),
                decompressed.size(),
                compressed.data(),
                compressed.size()
            );

        if (ZSTD_isError(result)) {

            XXH64_freeState(hash_state);

            throw std::runtime_error(
                ZSTD_getErrorName(result)
            );
        }

        if (result != chunk.uncompressed_size) {

            XXH64_freeState(hash_state);

            throw std::runtime_error(
                "NZ chunk size mismatch"
            );
        }

        const std::uint64_t checksum =
            XXH64(
                decompressed.data(),
                decompressed.size(),
                0
            );

        if (checksum != chunk.checksum) {

            XXH64_freeState(hash_state);

            throw std::runtime_error(
                "NZ chunk checksum mismatch"
            );
        }

        XXH64_update(
            hash_state,
            decompressed.data(),
            decompressed.size()
        );

        write_exact(
            output,
            decompressed.data(),
            decompressed.size()
        );

        total_output += decompressed.size();
    }

    const std::uint64_t final_checksum =
        XXH64_digest(hash_state);

    XXH64_freeState(hash_state);

    if (total_output != header.original_size) {
        throw std::runtime_error(
            "NZ archive size verification failed"
        );
    }

    if (final_checksum != header.checksum) {
        throw std::runtime_error(
            "NZ archive checksum verification failed"
        );
    }
}

} // namespace nz
