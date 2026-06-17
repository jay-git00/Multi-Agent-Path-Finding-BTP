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

    // Rectangular footprint (e.g., width 1, height 3), center is approximately at origin
    static Footprint Rectangle(int width_x, int height_y) {
        Footprint f;
        f.offsets.clear();
        int start_x = -(width_x / 2);
        int start_y = -(height_y / 2);
        for (int i = 0; i < height_y; ++i) { // row (y)
            for (int j = 0; j < width_x; ++j) { // col (x)
                f.offsets.push_back({start_y + i, start_x + j});
            }
        }
        return f;
    }

    // Rotates the footprint by 90 degrees clockwise 'theta' times.
    // theta=0: No rotation (North)
    // theta=1: 90 deg clockwise (East)
    // theta=2: 180 deg clockwise (South)
    // theta=3: 270 deg clockwise (West)
    Footprint apply_rotation(int theta) const {
        if (theta <= 0) return *this;
        
        Footprint rotated;
        rotated.offsets.clear();
        
        for (const auto& offset : offsets) {
            int r = offset.first;
            int c = offset.second;
            int new_r = r, new_c = c;
            
            // Apply 90-degree clockwise rotation (r, c) -> (c, -r) repeatedly
            for (int k = 0; k < (theta % 4); k++) {
                int temp_r = new_r;
                new_r = new_c;
                new_c = -temp_r;
            }
            rotated.offsets.push_back({new_r, new_c});
        }
        return rotated;
    }


    // Custom footprint from list of offsets
    static Footprint Custom(const std::vector<std::pair<int, int>>& off) {
        Footprint f;
        f.offsets = off;
        return f;
    }
};
