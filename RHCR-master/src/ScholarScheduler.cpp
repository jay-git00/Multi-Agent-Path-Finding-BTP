#include "ScholarScheduler.h"
#include <iostream>
#include <vector>
#include <unordered_set>

ScholarScheduler::ScholarScheduler(const BasicGraph& G) : G(G) {
}

ScholarScheduler::~ScholarScheduler() {
}

void ScholarScheduler::clear_graph() {
    dependency_graph.clear();
}

int ScholarScheduler::get_agent_at(int location, const std::vector<State>& current_states) const {
    for (size_t i = 0; i < current_states.size(); i++) {
        if (current_states[i].location == location) {
            return i;
        }
    }
    return -1; // No agent at this location
}

bool ScholarScheduler::would_create_cycle(int from_agent, int to_agent) {
    if (from_agent == to_agent) return true; // Self-cycle

    // Simple DFS to check if 'to_agent' can reach 'from_agent' in the dependency graph
    std::unordered_set<int> visited;
    std::vector<int> stack;
    stack.push_back(to_agent);

    while (!stack.empty()) {
        int curr = stack.back();
        stack.pop_back();

        if (curr == from_agent) return true; // Cycle detected!

        if (visited.find(curr) != visited.end()) continue;
        visited.insert(curr);

        if (dependency_graph.find(curr) != dependency_graph.end()) {
            for (int neighbor : dependency_graph[curr].dependencies) {
                stack.push_back(neighbor);
            }
        }
    }
    return false;
}

bool ScholarScheduler::is_safe_move(int agent_id, int current_node, int next_node, 
                                    const std::vector<State>& current_states, 
                                    const std::vector<std::vector<State>>& planned_paths) {
    
    // Check if anyone else is at 'next_node'
    int blocking_agent = get_agent_at(next_node, current_states);

    if (blocking_agent != -1 && blocking_agent != agent_id) {
        // Someone is at our target node.
        // If we move there, we are essentially "waiting for them to leave".
        // This creates a dependency: agent_id -> blocking_agent.
        
        if (would_create_cycle(agent_id, blocking_agent)) {
            // "I wait for Him, but He waits for Me" -> DEADLOCK.
            return false; 
        } else {
            // No cycle yet, so we record this dependency and allow the move attempt 
            // (but in reality, the low-level planner will likely make us wait).
            // For the SCHEDULER, we only block if it's a DEADLOCK.
            dependency_graph[agent_id].agent_id = agent_id;
            dependency_graph[agent_id].dependencies.insert(blocking_agent);
            return true;
        }
    }

    return true; // No immediate block, safe to proceed.
}

bool ScholarScheduler::is_junction(int location) const {
    // A location is a junction if it has more than 2 neighbors (intersection)
    // or is a Dead End (degree 1), exactly as described in the wait-spot logic.
    std::list<int> neighbors = G.get_neighbors(location);
    return neighbors.size() != 2; 
}

int ScholarScheduler::find_wait_spot(int agent_id, int current_node) {
    // BFS to find the nearest node k where is_junction(k) is true
    // This is Algorithm 3 concept.
    std::queue<int> q;
    q.push(current_node);
    
    std::unordered_set<int> visited;
    visited.insert(current_node);
    
    while (!q.empty()) {
        int curr = q.front();
        q.pop();
        
        if (is_junction(curr) && curr != current_node) {
            return curr;
        }
        
        for (int neighbor : G.get_neighbors(curr)) {
            if (visited.find(neighbor) == visited.end()) {
                visited.insert(neighbor);
                q.push(neighbor);
            }
        }
    }
    
    return current_node; // Fallback
}

void ScholarScheduler::print_dependency_graph() const {
    std::cout << "--- Dependency Graph ---" << std::endl;
    for (auto const& [agent, node] : dependency_graph) {
        std::cout << "Agent " << agent << " waits for: ";
        for (int dep : node.dependencies) {
            std::cout << dep << " ";
        }
        std::cout << std::endl;
    }
}
