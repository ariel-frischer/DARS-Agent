import networkx as nx
from collections import deque

class RepoSearcher:
    def __init__(self, graph):
        self.graph = graph

    def one_hop_neighbors(self, query):
        # get one-hop neighbors from networkx graph
        return list(self.graph.neighbors(query))

    def two_hop_neighbors(self, query):
        # get two-hop neighbors from networkx graph
        one_hop = self.one_hop_neighbors(query)
        two_hop = []
        for node in one_hop:
            two_hop.extend(self.one_hop_neighbors(node))
        return list(set(two_hop))

    def dfs(self, query, depth):
        # perform depth-first search on networkx graph
        # Optimized: Use set for O(1) membership test instead of O(n) list search
        visited = set()
        result = []
        stack = [(query, 0)]
        while stack:
            node, level = stack.pop()
            if node not in visited:
                visited.add(node)
                result.append(node)
                if level < depth:
                    stack.extend(
                        [(n, level + 1) for n in self.one_hop_neighbors(node)]
                    )
        return result
    
    def bfs(self, query, depth):
        # perform breadth-first search on networkx graph
        # Optimized: Use deque for O(1) popleft instead of O(n) pop(0)
        # Use set for O(1) membership test instead of O(n) list search
        visited = set()
        queue = deque([(query, 0)])
        result = []
        while queue:
            node, level = queue.popleft()
            if node not in visited:
                visited.add(node)
                result.append(node)
                if level < depth:
                    queue.extend(
                        [(n, level + 1) for n in self.one_hop_neighbors(node)]
                    )
        return result