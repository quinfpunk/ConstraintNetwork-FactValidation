import qualreas.src.qualreas as qr
import os

# Assume 'allen_algebra.json' is in the same directory as this script.
# This file defines the 13 base relations of Allen's Interval Algebra.
# TODO: define my own or use extended rcc8 with far close etc...
# TODO: also change the code to be adpated to this
ALGEBRA_FILE = "qualreas/Algebras/Linear_Interval_Algebra.json"

def get_rcc_relation(interval1_start, interval1_end, interval2_start, interval2_end):
    """
    Computes the Allen's Interval Algebra relation between two intervals.

    The function returns one of the 13 base relations as a single character string.
    Relations:
        B: precedes
        M: meets
        O: overlaps
        S: starts
        D: during
        F: finishes
        E: equals
        BI: preceded by (inverse of p)
        MI: met by (inverse of m)
        OI: overlapped by (inverse of o)
        SI: started by (inverse of s)
        DI: contains (inverse of d)
        FI: finished by (inverse of f)

    Args:
        interval1_start (int or float): The start time of the first interval.
        interval1_end (int or float): The end time of the first interval.
        interval2_start (int or float): The start time of the second interval.
        interval2_end (int or float): The end time of the second interval.

    Returns:
        str: The character representing the Allen's algebra relation.
    """
    if interval1_end < interval2_start:
        return 'B'  # precedes
    if interval1_end == interval2_start:
        return 'M'  # meets
    if interval1_start < interval2_start and interval1_end > interval2_start and interval1_end < interval2_end:
        return 'O'  # overlaps
    if interval1_start == interval2_start and interval1_end < interval2_end:
        return 'S'  # starts
    if interval1_start > interval2_start and interval1_end < interval2_end:
        return 'D'  # during
    if interval1_end == interval2_end and interval1_start > interval2_start:
        return 'F'  # finishes
    if interval1_start == interval2_start and interval1_end == interval2_end:
        return 'E'  # equals
    # Inverse relations
    if interval1_start > interval2_end:
        return 'BI' # preceded by
    if interval1_start == interval2_end:
        return 'MI' # met by
    if interval2_start < interval1_start and interval2_end > interval1_start and interval2_end < interval1_end:
        return 'OI' # overlapped by
    if interval2_start == interval1_start and interval2_end < interval1_end:
        return 'SI' # started by (inverse of starts)
    if interval2_start > interval1_start and interval2_end < interval1_end:
        return 'DI' # contains (inverse of during)
    if interval2_end == interval1_end and interval2_start < interval1_start:
        return 'FI' # finished by
    
    # This case should ideally not be reached if intervals are well-formed
    return None


# The parameters used to compute the relation should be different it should probably be the networkx graph
def create_cross_sequence_network(sequence_a, sequence_b, algebra_path=ALGEBRA_FILE):
    """
    Creates a qualreas constraint network from two time sequences.

    Each node in the network represents an interval from one of the sequences.
    Edges are Allen's algebra relations computed by comparing each interval
    from sequence A to each interval from sequence B.

    Args:
        sequence_a (list of tuples): The first time sequence, where each tuple
                                     is an interval (start_time, end_time).
        sequence_b (list of tuples): The second time sequence.
        algebra_path (str): Path to the Allen's algebra JSON definition file.

    Returns:
        qualreas.Network: The populated constraint network, or None if the
                          algebra file is not found.
    """
    # Step 1: Check for the algebra file and load it.
    if not os.path.exists(algebra_path):
        print(f"Error: Algebra file not found at '{algebra_path}'")
        print("Please download 'allen_algebra.json' from the qualreas repository.")
        return None
        
    algebra = qr.Algebra(algebra_path)

    # Step 2: Initialize the constraint network with the algebra.
    net = qr.Network(algebra)

    # Step 3: Iterate through all intervals in A and B to build constraints.
    # Nodes will be named 'A_0', 'A_1', ... and 'B_0', 'B_1', ...
    for i, interval_a in enumerate(sequence_a):
        node_a_name = f"A_{i}"
        start_a, end_a = interval_a.start, interval_a.end

        for j, interval_b in enumerate(sequence_b):
            node_b_name = f"B_{j}"
            start_b, end_b = interval_b.start, interval_b.end

            # Step 4: Compute the specific Allen's relation for this pair.
            relation = get_allen_relation(start_a, end_a, start_b, end_b)

            # Step 5: Add the constraint to the network.
            if relation:
                # print(f"Comparing {node_a_name} {interval_a} and {node_b_name} {interval_b}: Relation is '{relation}'")
                net.add_constraint(node_a_name, node_b_name, relation)

    return net

if __name__ == '__main__':
    # --- Example Usage ---

    # Define two time sequences, A and B.
    # Each sequence is a list of events, represented as (start_time, end_time) tuples.
    
    # Sequence A: A morning routine
    # 8:00-8:30 -> Wake Up & Stretch
    # 8:30-9:00 -> Breakfast
    # 9:00-9:15 -> Shower
    sequence_A = [
        (800, 830),
        (830, 900),
        (900, 915)
    ]

    # Sequence B: A overlapping but distinct schedule
    # 8:15-8:45 -> Check Emails
    # 8:45-9:05 -> Team Stand-up
    sequence_B = [
        (815, 845),
        (845, 905)
    ]
    
    print("Building constraint network from Sequence A and Sequence B...\n")
    
    # Create the network.
    constraint_network = create_cross_sequence_network(sequence_A, sequence_B)

    # Check if the network was created successfully before proceeding.
    if constraint_network:
        print("\nNetwork construction complete.")
        
        # The network now contains all the direct relationships.
        # You can view the summary of the network.
        print("\n--- Network Summary ---")
        print(constraint_network)

        # To make the network more useful, you would typically propagate the constraints
        # to infer new relationships and check for consistency.
        # For example:
        #
        # print("\nPropagating constraints...")
        # is_consistent = constraint_network.propagate()
        # if is_consistent:
        #     print("Network is consistent.")
        #     print("\n--- Network Summary After Propagation ---")
        #     print(constraint_network)
        # else:
        #     print("Network is inconsistent!")

