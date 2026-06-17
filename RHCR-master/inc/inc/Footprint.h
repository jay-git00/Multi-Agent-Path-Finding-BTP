#pragma once
#include <vector>
#include <utility>

class Footprint {
public:
    // List of relative (dx, dy) offsets from the center
    std::vector<std::pair<int, int>> offsets;

    bool is_sideloader = false;

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
        if (is_sideloader) {
            Footprint rotated;
            rotated.is_sideloader = true;
            rotated.offsets.clear();
            rotated.offsets.push_back({0, 0}); // Center is ALWAYS the strip/fork
            
            // The body is ALWAYS horizontal (3 cells wide, 1 cell tall).
            if (theta == 0) { // Facing East (Travel corridor)
                // Body is around the fork
                rotated.offsets.push_back({0, -1});
                rotated.offsets.push_back({0, 1});
            } else if (theta == 2) { // Facing West (Travel corridor)
                rotated.offsets.push_back({0, -1});
                rotated.offsets.push_back({0, 1});
            } else if (theta == 1) { // Facing South (picking from rack below)
                // Fork is at (0,0). Body must be on the Travel lane (North).
                // So body is at row -1.
                rotated.offsets.push_back({-1, -1});
                rotated.offsets.push_back({-1, 0});
                rotated.offsets.push_back({-1, 1});
            } else if (theta == 3) { // Facing North (picking from rack above)
                // Fork is at (0,0). Body must be on the Travel lane (South).
                // So body is at row +1.
                rotated.offsets.push_back({1, -1});
                rotated.offsets.push_back({1, 0});
                rotated.offsets.push_back({1, 1});
            }
            return rotated;
        }

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

    // SideLoader footprint:
    // Body is ALWAYS horizontal (3x1).
    // Center is the fork mechanism.
    static Footprint SideLoader() {
        Footprint f;
        f.is_sideloader = true;
        f.offsets.clear();
        f.offsets.push_back({0, 0});
        // Base is theta=0 (East). Body wraps around the fork.
        f.offsets.push_back({0, -1});
        f.offsets.push_back({0, 1});
        return f;
    }

    // Forklift footprint: center is the FRONT (strip/fork).
    // Body extends BACKWARD by (length-1) cells.
    // When facing South (toward rack), center touches endpoint,
    // body cells at (-1,0), (-2,0) stay in the corridor behind.
    static Footprint Forklift(int length) {
        Footprint f;
        f.offsets.clear();
        f.offsets.push_back({0, 0}); // front/strip (center)
        for (int i = 1; i < length; ++i) {
            f.offsets.push_back({0, -i}); // body extends backward (negative col = West)
        }
        return f;
    }
};
