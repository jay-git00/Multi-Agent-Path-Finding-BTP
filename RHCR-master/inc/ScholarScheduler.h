#pragma once

#include "KivaGraph.h"
#include "States.h"
#include <vector>
#include <list>
#include <unordered_map>
#include <unordered_set>

// Algorithm 2: Deadlock Detection
// Algorithm 3: Deadlock Resolution (Wait Spots)
class ScholarScheduler {
public:
    ScholarScheduler(const BasicGraph& G);
    ~ScholarScheduler();

    // The main hook: Checks if assigning 'next_node' to 'agent_id' creates a deadlock
    bool is_safe_move(int agent_id, int current_node, int next_node, 
                      const std::vector<State>& current_states, 
                      const std::vector<std::vector<State>>& planned_paths);

    // Algorithm 3: Find a wait spot (junction) for a set of agents
    int find_wait_spot(int agent_id, int current_node);

    // Reset the dependency graph (calling this at the start of each timestep)
    void clear_graph();

    // Debugging
    void print_dependency_graph() const;

private:
    const BasicGraph& G;

    // Dependency Graph Structure
    // Edge (A -> B) means Robot A is waiting for Robot B to move
    struct DependencyNode {
        int agent_id;
        std::unordered_set<int> dependencies; // List of agent_ids this agent waits for
    };

    // Current State of the Dependency Graph
    std::unordered_map<int, DependencyNode> dependency_graph;

    // Helper: Algorithm 2 (Deadlock Detection)
    // Returns true if adding edge (from -> to) creates a cycle
    bool would_create_cycle(int from_agent, int to_agent);

    // Helper: Check if a node is a Junction (Wait Spot Candidate)
    bool is_junction(int location) const;

    // Helper: Identify which agent is currently occupying/blocking a location
    int get_agent_at(int location, const std::vector<State>& current_states) const;
};
