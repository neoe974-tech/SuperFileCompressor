#include "nz/zstd_engine.hpp"
#include "nz/checksum.hpp"

#include <fstream>
#include <iostream>
#include <vector>
#include <string>

int main(int argc, char* argv[]) {

    if (argc != 3) {
        std::cerr
            << "Usage: nzcompress <input> <output.nz>\n";

        return 1;
    }

    const std::string input_path = argv[1];
    const std::string output_path = argv[2];

    std::ifstream input(
        input_path,
        std::ios::binary
    );

    if (!input) {
        std::cerr << "Cannot open input file.\n";
        return 1;
    }

    input.seekg(0, std::ios::end);

    const std::streamsize size = input.tellg();

    input.seekg(0, std::ios::beg);

    if (size < 0) {
        std::cerr << "Invalid input size.\n";
        return 1;
    }

    std::vector<std::uint8_t> data(
        static_cast<std::size_t>(size)
    );

    input.read(
        reinterpret_cast<char*>(data.data()),
        size
    );

    if (!input) {
        std::cerr << "Failed to read input file.\n";
        return 1;
    }

    try {

        const auto compressed =
            nz::ZstdEngine::compress(
                data.data(),
                data.size(),
                3
            );

        const auto checksum =
            nz::checksum64(
                data.data(),
                data.size()
            );

        std::ofstream output(
            output_path,
            std::ios::binary
        );

        if (!output) {
            std::cerr << "Cannot create output file.\n";
            return 1;
        }

        const char magic[4] = {'N', 'Z', '0', '1'};

        std::uint64_t original_size = data.size();
        std::uint64_t compressed_size = compressed.size();

        output.write(magic, 4);

        output.write(
            reinterpret_cast<const char*>(&original_size),
            sizeof(original_size)
        );

        output.write(
            reinterpret_cast<const char*>(&compressed_size),
            sizeof(compressed_size)
        );

        output.write(
            reinterpret_cast<const char*>(&checksum),
            sizeof(checksum)
        );

        output.write(
            reinterpret_cast<const char*>(compressed.data()),
            compressed.size()
        );

        output.close();

        std::cout
            << "NZ compression successful\n"
            << "Original:   "
            << original_size
            << " bytes\n"
            << "Compressed: "
            << compressed_size
            << " bytes\n";

        return 0;

    } catch (const std::exception& e) {

        std::cerr
            << "Compression error: "
            << e.what()
            << '\n';

        return 1;
    }
}
