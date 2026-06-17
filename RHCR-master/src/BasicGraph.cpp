#include "BasicGraph.h"
#include <fstream>
#include <boost/tokenizer.hpp>
#include "StateTimeAStar.h"
#include <sstream>
#include <random>
#include <chrono>
#include <unordered_set>


void BasicGraph::print_map() const
{  
    std::cout << "***type***" << std::endl;
    for (std::string t : types)
        std::cout << t << ",";
    std::cout << std::endl;

    std::cout << "***weights***" << std::endl;
    for (std::vector<double> n : weights)
    {
        for (double w : n)
        {
            std::cout << w << ",";
        }
        std::cout << std::endl;
    }
}


int BasicGraph::get_rotate_degree(int dir1, int dir2) const
{
    if (dir1 == dir2)
        return 0;
    else if (abs(dir1 - dir2) == 1 || abs(dir1 - dir2) == 3)
        return 3; // 90 degree turn takes 3 timesteps
    else
        return 6; // 180 degree turn takes 6 timesteps
}


list<int> BasicGraph::get_neighbors(int v) const
{
    list<int> neighbors;
    if (v < 0)
        return neighbors;

    for (int i = 0; i < 4; i++) // move
        if (weights[v][i] < WEIGHT_MAX - 1)
            neighbors.push_back(v + move[i]);

    return neighbors;
}

// Check if the full rotated footprint at (location, orientation) is free of obstacles.
// Returns true if ALL footprint cells are within bounds and not obstacles.
bool BasicGraph::isFootprintValidAtState(int location, int orientation) const
{
    // If footprint is just the default 1x1 point, skip the expensive check
    if (active_footprint.offsets.size() <= 1)
        return true;

    int center_r = location / cols;
    int center_c = location % cols;
    Footprint rotated_fp = active_footprint.apply_rotation(std::max(0, orientation));
    for (const auto& offset : rotated_fp.offsets)
    {
        int nr = center_r + offset.first;
        int nc = center_c + offset.second;
        if (nr < 0 || nr >= rows || nc < 0 || nc >= cols)
            return false;  // out of bounds
        
        int cell = nr * cols + nc;
        bool is_center = (offset.first == 0 && offset.second == 0);

        if (is_center)
        {
            // Center is allowed anywhere EXCEPT solid obstacles
            if (types[cell] == "Obstacle")
                return false;
        }
        else
        {
            // The tail/body MUST stay strictly on travel corridors, home parking zones, AND endpoints.
            // It cannot sweep over Obstacles (Racks).
            if (types[cell] != "Travel" && types[cell] != "Home" && types[cell] != "Endpoint")
                return false;
        }
    }
    return true;
}

bool BasicGraph::isRotationValid(int location) const
{
    // Point agents don't sweep volume
    if (active_footprint.offsets.size() <= 1)
        return true;

    auto swept = get_rotation_swept_volume(location, active_footprint);
    for (int cell : swept)
    {
        // During a turn, NO part of the swept volume can hit an Obstacle (Rack).
        // It must be entirely within Travel, Home, or Endpoint space.
        if (cell == location)
            continue;
            
        if (types[cell] != "Travel" && types[cell] != "Home" && types[cell] != "Endpoint")
            return false;
    }
    return true;
}

list<State> BasicGraph::get_neighbors(const State& s) const
{
    list<State> neighbors;
    if (s.location < 0)
        return neighbors;
    if (s.orientation >= 0)
    {
        // Wait: footprint doesn't change, always valid if current state is valid
        neighbors.push_back(State(s.location, s.timestep + 1, s.orientation));

        // Move forward: check destination footprint against obstacles
        if (weights[s.location][s.orientation] < WEIGHT_MAX - 1)
        {
            int next_loc = s.location + move[s.orientation];
            if (isFootprintValidAtState(next_loc, s.orientation))
                neighbors.push_back(State(next_loc, s.timestep + 1, s.orientation));
        }

        // Turn left / right: check rotated footprint at same location against obstacles
        int next_orientation1 = s.orientation + 1;
        int next_orientation2 = s.orientation - 1;
        if (next_orientation2 < 0)
            next_orientation2 += 4;
        else if (next_orientation1 > 3)
            next_orientation1 -= 4;

        if (isFootprintValidAtState(s.location, next_orientation1))
            neighbors.push_back(State(s.location, s.timestep + 1, next_orientation1));
        if (isFootprintValidAtState(s.location, next_orientation2))
            neighbors.push_back(State(s.location, s.timestep + 1, next_orientation2));
    }
    else
    {
        neighbors.push_back(State(s.location, s.timestep + 1)); // wait
        for (int i = 0; i < 4; i++) // move
            if (weights[s.location][i] < WEIGHT_MAX - 1)
                neighbors.push_back(State(s.location + move[i], s.timestep + 1));
    }
    return neighbors;
}    

std::list<State> BasicGraph::get_reverse_neighbors(const State& s) const
{
    std::list<State> rneighbors;
    // no wait actions
    if (s.orientation >= 0)
    {
        if (s.location - move[s.orientation] >= 0 && s.location - move[s.orientation] < this->size() &&
            weights[s.location - move[s.orientation]][s.orientation] < WEIGHT_MAX - 1)
            rneighbors.push_back(State(s.location - move[s.orientation], -1, s.orientation)); // move
        int next_orientation1 = s.orientation + 1;
        int next_orientation2 = s.orientation - 1;
        if (next_orientation2 < 0)
            next_orientation2 += 4;
        else if (next_orientation1 > 3)
            next_orientation1 -= 4;
        rneighbors.push_back(State(s.location, -1, next_orientation1)); // turn right
        rneighbors.push_back(State(s.location, -1, next_orientation2)); // turn left
    }
    else
    {
        for (int i = 0; i < 4; i++) // move
            if (s.location - move[i] >= 0 && s.location - move[i] < this->size() &&
                    weights[s.location - move[i]][i] < WEIGHT_MAX - 1)
                rneighbors.push_back(State(s.location - move[i]));
    }
    return rneighbors;
}


double BasicGraph::get_weight(int from, int to) const
{
    if (from == to) // wait or rotate
        return weights[from][4];
    int dir = get_direction(from, to);
    if (dir >= 0)
        return weights[from][dir];
    else
        return WEIGHT_MAX;
}


int BasicGraph::get_direction(int from, int to) const
{
    for (int i = 0; i < 4; i++)
    {
        if (move[i] == to - from)
            return i;
    }
    if (from == to)
        return 4;
    return -1;
}



bool BasicGraph::load_heuristics_table(std::ifstream& myfile)
{
    boost::char_separator<char> sep(",");
    boost::tokenizer< boost::char_separator<char> >::iterator beg;
    std::string line;
    
    getline(myfile, line); //skip "table_size"
    getline(myfile, line);
    boost::tokenizer< boost::char_separator<char> > tok(line, sep);
    beg = tok.begin();
	int N = atoi ( (*beg).c_str() ); // read number of cols
	beg++;
	int M = atoi ( (*beg).c_str() ); // read number of rows
	if (M != this->size())
	    return false;
	for (int i = 0; i < N; i++)
	{
		getline (myfile, line);
        int loc = atoi(line.c_str());
        getline (myfile, line);        
        boost::tokenizer< boost::char_separator<char> > tok(line, sep);
	    beg = tok.begin();
        std::vector<double> h_table(this->size());
        for (int j = 0; j < this->size(); j++)
        {
            h_table[j] = atof((*beg).c_str());
            if (h_table[j] >= INT_MAX && types[j] != "Obstacle")
                types[j] = "Obstacle";
            beg++;
        }
        heuristics[loc] = h_table;
    }
	return true;
}


void BasicGraph::save_heuristics_table(std::string fname)
{
    std::ofstream myfile;
	myfile.open (fname);
	myfile << "table_size" << std::endl << 
        heuristics.size() << "," << this->size() << std::endl;
	for (auto h_values: heuristics) 
	{
        myfile << h_values.first << std::endl;
		for (double h : h_values.second) 
		{
            myfile << h << ",";
		}
		myfile << std::endl;
	}
	myfile.close();
}

std::vector<double> BasicGraph::compute_heuristics(int root_location)
{
    std::vector<double> res(this->size(), DBL_MAX);
	fibonacci_heap< StateTimeAStarNode*, compare<StateTimeAStarNode::compare_node> > heap;
    unordered_set< StateTimeAStarNode*, StateTimeAStarNode::Hasher, StateTimeAStarNode::EqNode> nodes;

    State root_state(root_location);
    if(consider_rotation)
    {
        for (auto neighbor : get_reverse_neighbors(root_state))
        {
            StateTimeAStarNode* root = new StateTimeAStarNode(State(root_location, -1,
                    get_direction(neighbor.location, root_state.location)), 0, 0, nullptr, 0);
            root->open_handle = heap.push(root);  // add root to heap
            nodes.insert(root);       // add root to hash_table (nodes)
        }
    }
    else
    {
        StateTimeAStarNode* root = new StateTimeAStarNode(root_state, 0, 0, nullptr, 0);
        root->open_handle = heap.push(root);  // add root to heap
        nodes.insert(root);       // add root to hash_table (nodes)
    }

	while (!heap.empty()) 
    {
        StateTimeAStarNode* curr = heap.top();
		heap.pop();
		for (auto next_state : get_reverse_neighbors(curr->state))
		{
			double next_g_val = curr->g_val + get_weight(next_state.location, curr->state.location);
            StateTimeAStarNode* next = new StateTimeAStarNode(next_state, next_g_val, 0, nullptr, 0);
			auto it = nodes.find(next);
			if (it == nodes.end()) 
			{  // add the newly generated node to heap and hash table
				next->open_handle = heap.push(next);
				nodes.insert(next);
			}
			else 
			{  // update existing node's g_val if needed (only in the heap)
				delete(next);  // not needed anymore -- we already generated it before
                StateTimeAStarNode* existing_next = *it;
				if (existing_next->g_val > next_g_val) 
				{
					existing_next->g_val = next_g_val;
					heap.increase(existing_next->open_handle);
				}
			}
		}
	}
	// iterate over all nodes and populate the distances
	for (auto it = nodes.begin(); it != nodes.end(); it++)
	{
        StateTimeAStarNode* s = *it;
		res[s->state.location] = std::min(s->g_val, res[s->state.location]);
		delete (s);
	}
	nodes.clear();
	heap.clear();
    return res;cd C:\Users\DILEEP\MATLAB\Projects\untitled\BTP\MAPF-with-multi-level-architecture\RHCR-master
    
}


int BasicGraph::get_Manhattan_distance(int loc1, int loc2) const
{
    return abs(loc1 / cols - loc2 / cols) + abs(loc1 % cols - loc2 % cols);
}

std::vector<int> BasicGraph::get_footprint_locations(int center_loc, const Footprint& footprint, int theta) const
{
    std::vector<int> locations;
    int r = center_loc / cols;
    int c = center_loc % cols;
    Footprint rotated_fp = footprint.apply_rotation(theta);
    for (auto offset : rotated_fp.offsets)
    {
        int next_r = r + offset.first;
        int next_c = c + offset.second;
        if (next_r >= 0 && next_r < rows && next_c >= 0 && next_c < cols)
        {
            locations.push_back(next_r * cols + next_c);
        }
    }
    return locations;
}

std::vector<int> BasicGraph::get_rotation_swept_volume(int center_loc, const Footprint& footprint) const
{
    std::unordered_set<int> swept_cells;
    int r = center_loc / cols;
    int c = center_loc % cols;
    
    // Simplest robust swept volume: circle swept by the furthest point.
    double max_radius_sq = 0;
    for (auto offset : footprint.offsets) {
        double dist_sq = offset.first * offset.first + offset.second * offset.second;
        if (dist_sq > max_radius_sq) max_radius_sq = dist_sq;
    }
    double max_radius = sqrt(max_radius_sq) + 0.5; // +0.5 to account for cell bounds
    
    int rad_ceil = ceil(max_radius);
    for (int dr = -rad_ceil; dr <= rad_ceil; ++dr) {
        for (int dc = -rad_ceil; dc <= rad_ceil; ++dc) {
            if (dr * dr + dc * dc <= max_radius * max_radius) {
                int next_r = r + dr;
                int next_c = c + dc;
                if (next_r >= 0 && next_r < rows && next_c >= 0 && next_c < cols) {
                    swept_cells.insert(next_r * cols + next_c);
                }
            }
        }
    }
    return std::vector<int>(swept_cells.begin(), swept_cells.end());
}



void BasicGraph::copy(const BasicGraph& copy)
{
    rows = copy.get_rows();
    cols = copy.get_cols();
    weights = copy.get_weights();
}