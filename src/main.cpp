#include "nz/stream_engine.hpp"

#include <iostream>
#include <string>

int main(int argc, char* argv[]) {

    if (argc < 2) {
        std::cerr
            << "Super File Compressor - NZ v0.2\n\n"
            << "Usage:\n"
            << "  nzcompress <input> <output.nz>\n"
            << "  nzextract  <input.nz> <output>\n";

        return 1;
    }

    const std::string command = argv[1];

    try {

        if (command == "compress") {

            if (argc != 4) {
                std::cerr
                    << "Usage: nzcompress compress "
                    << "<input> <output.nz>\n";

                return 1;
            }

            const auto stats =
                nz::compress_file(
                    argv[2],
                    argv[3]
                );

            std::cout
                << "NZ compression successful\n"
                << "Original:   "
                << stats.original_size
                << " bytes\n"
                << "Compressed: "
                << stats.compressed_size
                << " bytes\n"
                << "Chunks:     "
                << stats.chunk_count
                << '\n';

            return 0;
        }

        if (command == "extract") {

            if (argc != 4) {
                std::cerr
                    << "Usage: nzcompress extract "
                    << "<input.nz> <output>\n";

                return 1;
            }

            nz::decompress_file(
                argv[2],
                argv[3]
            );

            std::cout
                << "NZ extraction successful\n";

            return 0;
        }

        std::cerr
            << "Unknown command: "
            << command
            << '\n';

        return 1;

    } catch (const std::exception& error) {

        std::cerr
            << "ERROR: "
            << error.what()
            << '\n';

        return 1;
    }
}
