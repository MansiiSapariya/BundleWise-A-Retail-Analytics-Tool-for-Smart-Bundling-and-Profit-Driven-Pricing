from collections import defaultdict
import logging # Added for potential debugging if needed inside prefixspan

logger = logging.getLogger(__name__) # Logger for prefixspan.py

class PrefixSpan:
    """
    A robust and corrected implementation of the PrefixSpan algorithm for
    sequential pattern mining.
    """

    def __init__(self, sequences, min_support=0.01, max_len=5):
        """
        Args:
            sequences: A list of sequences. Each sequence is a list of itemsets,
                       and each itemset is a list of items.
                       e.g., [[['a', 'b'], ['c']], [['a'], ['d', 'e']]]
            min_support: The minimum support threshold (a float between 0 and 1).
            max_len: The maximum length of the patterns to be mined.
        """
        self.sequences = sequences
        self.min_support_count = int(min_support * len(sequences))
        self.max_len = max_len

    def frequent(self):
        """
        Mines and returns all frequent sequential patterns.
        Returns:
            A list of tuples, where each tuple contains (support_count, pattern).
            Pattern is a list of itemsets (where each itemset contains clean strings).
        """
        # The core recursive mining function
        def _mine(patterns, current_max_len):
            if current_max_len <= 0:
                return

            item_counts = defaultdict(int)
            for p in patterns:
                for item in p.unique_items:
                    item_counts[item] += p.count
            
            frequent_items = {
                item for item, count in item_counts.items() if count >= self.min_support_count
            }

            for item in frequent_items:
                new_patterns = []
                total_count = 0
                for p in patterns:
                    try:
                        new_p = p.project(item)
                        # The `sum(len(itemset_in_prefix) for itemset_in_prefix in new_p.prefix)`
                        # is an unconventional way to measure length for PrefixSpan.
                        # Usually, `max_len` refers to the number of *elements* in the sequence,
                        # where an element is an itemset or just an item if flattened.
                        # Given `new_prefix = prefix + [item]` in recursive call (not this method)
                        # It counts items. So we stick to simple length here.
                        if len(new_p.prefix) > self.max_len: # Standard PrefixSpan length is number of items
                            continue 
                        
                        new_patterns.append(new_p)
                        total_count += new_p.count
                    except IndexError:
                        pass
                
                if total_count >= self.min_support_count:
                    new_prefix = new_patterns[0].prefix 
                    
                    # Ensure final yielded pattern adheres to max_len
                    if len(new_prefix) <= self.max_len: # Check length of new_prefix (number of items)
                        yield (total_count, new_prefix)
                        _mine(new_patterns, current_max_len - 1)


        initial_patterns = [Pattern(seq) for seq in self.sequences]
        yield from _mine(initial_patterns, self.max_len)


class Pattern:
    """
    Represents a sequence pattern during the mining process.
    It contains the sequence itself and methods for projection.
    """
    def __init__(self, sequence, count=1):
        self.sequence = []
        self.count = count
        self.prefix = [] # Stores the current prefix as a list of items (e.g., ['A', 'B', 'C'])
        
        # --- CRITICAL CHANGE HERE ---
        # Ensure every item is a stripped string before it enters the frozenset
        # This standardizes the item keys for frozenset hashing and later lookup
        for itemset in sequence:
            cleaned_itemset = frozenset(str(item).strip() for item in itemset)
            self.sequence.append(cleaned_itemset)
            
        self.unique_items = set(item for itemset in self.sequence for item in itemset)

    def project(self, new_item):
        """
        Projects the current pattern based on a new item to be added to the prefix.
        Returns a new Pattern object representing the projected database (suffix).
        """
        # Ensure new_item is also a clean string for robust matching
        new_item_clean = str(new_item).strip() # <--- Ensure new_item is also stripped

        found_at_idx = -1
        for i, itemset_in_seq in enumerate(self.sequence):
            if new_item_clean in itemset_in_seq: # <--- Use cleaned new_item
                found_at_idx = i
                break
        
        if found_at_idx == -1:
            raise IndexError("Item not in sequence after current prefix.")

        new_sequence_suffix = self.sequence[found_at_idx:]
        
        # The prefix for the projected pattern includes the new item
        # The prefix is a list of items, so we add the new_item_clean
        new_pattern = Pattern(
            [list(s) for s in new_sequence_suffix], # Convert frozensets back to lists for Pattern.__init__
            self.count
        )
        new_pattern.prefix = self.prefix + [new_item_clean] # <--- Add cleaned new_item to prefix
        
        return new_pattern

