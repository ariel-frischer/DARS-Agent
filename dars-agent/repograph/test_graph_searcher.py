from __future__ import annotations

import pytest
import networkx as nx
from repograph.graph_searcher import RepoSearcher


class TestRepoSearcher:
    """Test suite for RepoSearcher class"""

    @pytest.fixture
    def simple_graph(self):
        """Create a simple directed graph for testing"""
        G = nx.DiGraph()
        G.add_edges_from([
            ('A', 'B'),
            ('A', 'C'),
            ('B', 'D'),
            ('C', 'D'),
            ('D', 'E'),
        ])
        return G

    @pytest.fixture
    def complex_graph(self):
        """Create a more complex graph with cycles"""
        G = nx.DiGraph()
        G.add_edges_from([
            ('A', 'B'),
            ('A', 'C'),
            ('B', 'D'),
            ('C', 'D'),
            ('D', 'E'),
            ('E', 'F'),
            ('F', 'G'),
            ('B', 'C'),  # additional connection
            ('D', 'A'),  # creates a cycle
        ])
        return G

    @pytest.fixture
    def empty_graph(self):
        """Create an empty graph"""
        return nx.DiGraph()

    @pytest.fixture
    def single_node_graph(self):
        """Create a graph with a single node"""
        G = nx.DiGraph()
        G.add_node('A')
        return G

    # Tests for one_hop_neighbors
    def test_one_hop_neighbors_basic(self, simple_graph):
        """Test one hop neighbors returns direct neighbors"""
        searcher = RepoSearcher(simple_graph)
        neighbors = searcher.one_hop_neighbors('A')
        assert set(neighbors) == {'B', 'C'}

    def test_one_hop_neighbors_leaf_node(self, simple_graph):
        """Test one hop neighbors for a leaf node returns empty list"""
        searcher = RepoSearcher(simple_graph)
        neighbors = searcher.one_hop_neighbors('E')
        assert neighbors == []

    def test_one_hop_neighbors_middle_node(self, simple_graph):
        """Test one hop neighbors for a middle node"""
        searcher = RepoSearcher(simple_graph)
        neighbors = searcher.one_hop_neighbors('B')
        assert set(neighbors) == {'D'}

    def test_one_hop_neighbors_nonexistent_node(self, simple_graph):
        """Test one hop neighbors for a node not in the graph"""
        searcher = RepoSearcher(simple_graph)
        with pytest.raises(nx.NetworkXError):
            searcher.one_hop_neighbors('Z')

    def test_one_hop_neighbors_empty_graph(self, single_node_graph):
        """Test one hop neighbors on a single node graph"""
        searcher = RepoSearcher(single_node_graph)
        neighbors = searcher.one_hop_neighbors('A')
        assert neighbors == []

    # Tests for two_hop_neighbors
    def test_two_hop_neighbors_basic(self, simple_graph):
        """Test two hop neighbors returns nodes two steps away"""
        searcher = RepoSearcher(simple_graph)
        neighbors = searcher.two_hop_neighbors('A')
        # A -> B -> D, A -> C -> D
        assert 'D' in neighbors

    def test_two_hop_neighbors_includes_all(self, simple_graph):
        """Test two hop neighbors includes all reachable nodes"""
        searcher = RepoSearcher(simple_graph)
        neighbors = searcher.two_hop_neighbors('A')
        # Should include D (from B and C) and may include duplicates removed by set
        assert 'D' in neighbors

    def test_two_hop_neighbors_leaf_node(self, simple_graph):
        """Test two hop neighbors for a leaf node returns empty list"""
        searcher = RepoSearcher(simple_graph)
        neighbors = searcher.two_hop_neighbors('E')
        assert neighbors == []

    def test_two_hop_neighbors_deduplication(self, simple_graph):
        """Test that two hop neighbors removes duplicates"""
        searcher = RepoSearcher(simple_graph)
        neighbors = searcher.two_hop_neighbors('A')
        # D is reachable via B and C, should appear once
        assert neighbors.count('D') == 1

    def test_two_hop_neighbors_empty_graph(self, single_node_graph):
        """Test two hop neighbors on a single node graph"""
        searcher = RepoSearcher(single_node_graph)
        neighbors = searcher.two_hop_neighbors('A')
        assert neighbors == []

    # Tests for DFS
    def test_dfs_depth_zero(self, simple_graph):
        """Test DFS with depth 0 returns only the query node"""
        searcher = RepoSearcher(simple_graph)
        result = searcher.dfs('A', 0)
        assert result == ['A']

    def test_dfs_depth_one(self, simple_graph):
        """Test DFS with depth 1 returns query node and direct neighbors"""
        searcher = RepoSearcher(simple_graph)
        result = searcher.dfs('A', 1)
        assert 'A' in result
        assert 'B' in result or 'C' in result  # At least one neighbor should be present
        assert len(result) <= 3  # A and up to 2 neighbors

    def test_dfs_depth_two(self, simple_graph):
        """Test DFS with depth 2"""
        searcher = RepoSearcher(simple_graph)
        result = searcher.dfs('A', 2)
        assert 'A' in result
        assert 'D' in result  # Should reach D at depth 2

    def test_dfs_full_traversal(self, simple_graph):
        """Test DFS with large depth traverses entire graph"""
        searcher = RepoSearcher(simple_graph)
        result = searcher.dfs('A', 10)
        # Should visit all nodes reachable from A
        assert 'A' in result
        assert 'B' in result
        assert 'C' in result
        assert 'D' in result
        assert 'E' in result

    def test_dfs_handles_cycles(self, complex_graph):
        """Test DFS handles cycles without infinite loop"""
        searcher = RepoSearcher(complex_graph)
        result = searcher.dfs('A', 5)
        # Should visit each node only once despite the cycle
        assert len(result) == len(set(result))

    def test_dfs_leaf_node(self, simple_graph):
        """Test DFS starting from a leaf node"""
        searcher = RepoSearcher(simple_graph)
        result = searcher.dfs('E', 3)
        assert result == ['E']

    def test_dfs_single_node(self, single_node_graph):
        """Test DFS on a single node graph"""
        searcher = RepoSearcher(single_node_graph)
        result = searcher.dfs('A', 5)
        assert result == ['A']

    def test_dfs_negative_depth(self, simple_graph):
        """Test DFS with negative depth behaves correctly"""
        searcher = RepoSearcher(simple_graph)
        result = searcher.dfs('A', -1)
        assert result == ['A']

    # Tests for BFS
    def test_bfs_depth_zero(self, simple_graph):
        """Test BFS with depth 0 returns only the query node"""
        searcher = RepoSearcher(simple_graph)
        result = searcher.bfs('A', 0)
        assert result == ['A']

    def test_bfs_depth_one(self, simple_graph):
        """Test BFS with depth 1 returns query node and direct neighbors"""
        searcher = RepoSearcher(simple_graph)
        result = searcher.bfs('A', 1)
        assert 'A' in result
        assert 'B' in result
        assert 'C' in result
        assert len(result) == 3

    def test_bfs_depth_two(self, simple_graph):
        """Test BFS with depth 2"""
        searcher = RepoSearcher(simple_graph)
        result = searcher.bfs('A', 2)
        assert 'A' in result
        assert 'B' in result
        assert 'C' in result
        assert 'D' in result  # Should reach D at depth 2

    def test_bfs_full_traversal(self, simple_graph):
        """Test BFS with large depth traverses entire graph"""
        searcher = RepoSearcher(simple_graph)
        result = searcher.bfs('A', 10)
        # Should visit all nodes reachable from A
        assert 'A' in result
        assert 'B' in result
        assert 'C' in result
        assert 'D' in result
        assert 'E' in result

    def test_bfs_handles_cycles(self, complex_graph):
        """Test BFS handles cycles without infinite loop"""
        searcher = RepoSearcher(complex_graph)
        result = searcher.bfs('A', 5)
        # Should visit each node only once despite the cycle
        assert len(result) == len(set(result))

    def test_bfs_leaf_node(self, simple_graph):
        """Test BFS starting from a leaf node"""
        searcher = RepoSearcher(simple_graph)
        result = searcher.bfs('E', 3)
        assert result == ['E']

    def test_bfs_single_node(self, single_node_graph):
        """Test BFS on a single node graph"""
        searcher = RepoSearcher(single_node_graph)
        result = searcher.bfs('A', 5)
        assert result == ['A']

    def test_bfs_order_is_breadth_first(self, simple_graph):
        """Test BFS visits nodes in breadth-first order"""
        searcher = RepoSearcher(simple_graph)
        result = searcher.bfs('A', 2)
        # First should be A, then B and C (depth 1), then D (depth 2)
        assert result[0] == 'A'
        assert result.index('B') < result.index('D')
        assert result.index('C') < result.index('D')

    def test_bfs_negative_depth(self, simple_graph):
        """Test BFS with negative depth behaves correctly"""
        searcher = RepoSearcher(simple_graph)
        result = searcher.bfs('A', -1)
        assert result == ['A']

    # Edge case tests
    def test_graph_with_self_loop(self):
        """Test behavior with self-loop in graph"""
        G = nx.DiGraph()
        G.add_edges_from([('A', 'A'), ('A', 'B')])
        searcher = RepoSearcher(G)

        # One hop should include self and B
        neighbors = searcher.one_hop_neighbors('A')
        assert 'A' in neighbors
        assert 'B' in neighbors

    def test_disconnected_graph(self):
        """Test behavior with disconnected components"""
        G = nx.DiGraph()
        G.add_edges_from([('A', 'B'), ('C', 'D')])
        searcher = RepoSearcher(G)

        # Starting from A should not reach C or D
        result = searcher.bfs('A', 10)
        assert 'A' in result
        assert 'B' in result
        assert 'C' not in result
        assert 'D' not in result

    def test_initialization_with_none(self):
        """Test initialization with None raises appropriate error"""
        with pytest.raises((TypeError, AttributeError)):
            searcher = RepoSearcher(None)
            searcher.one_hop_neighbors('A')

    def test_dfs_vs_bfs_visit_same_nodes(self, simple_graph):
        """Test that DFS and BFS visit the same nodes (order may differ)"""
        searcher = RepoSearcher(simple_graph)
        dfs_result = searcher.dfs('A', 10)
        bfs_result = searcher.bfs('A', 10)
        assert set(dfs_result) == set(bfs_result)
