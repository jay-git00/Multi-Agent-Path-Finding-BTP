#pragma once
#include <vector>
#include <utility>

class Footprint {
public:
    // List of relative (dx, dy) offsets from the center
    std::vector<std::pair<int, int>> offsets;

    Footprint() {
        offsets.push_back({0, 0}); // Default: point agent
    }

    // Square footprint of size x size, center is approximately at (size/2, size/2)
    static Footprint Square(int size) {
        Footprint f;
        f.offsets.clear();
        int start = -(size / 2);
        for (int i = 0; i < size; ++i) {
            for (int j = 0; j < size; ++j) {
                f.offsets.push_back({start + i, start + j});
            }
        }
        return f;
    }

    // Custom footprint from list of offsets
    static Footprint Custom(const std::vector<std::pair<int, int>>& off) {
        Footprint f;
        f.offsets = off;
        return f;
    }
};
