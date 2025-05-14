from typing import List, Tuple, Optional


class Correcteur:
    
    def __init__(self, lexique: List[str]):
        self.lexique = lexique
        self.prefix_tree = Correcteur.build_prefix_tree(lexique)

    def lemmatize(self, 
        word: str,
        levenstein_minimum_length = 2,
        prefix_similarity_threshold: float = 0.6,
        min_prefix_len: int = 3,
        max_overflow: int = None,
    ) -> Optional[str]:
        word = word.lower()
        if word in self.lexique:
            return word
        else:
            matches, prefix_len = Correcteur.search_tree(
                self.prefix_tree, 
                word, 
                min_prefix_len=min_prefix_len, 
                max_overflow=max_overflow,
            )
            
            if len(matches) == 0:
                return None
                
            length_threshold = int(prefix_len / prefix_similarity_threshold * len(word))
            matches = [m for m in matches if len(m) <= length_threshold]  # A justifier dans le rapport (voir formule plus haut)
            
            if len(matches) == 1:
                return matches[0]

            elif len(matches) >= 2:
                
                scores = { match: Correcteur.levenstein(word, match) for match in matches }
                best_match = min(scores.items(), key=lambda x: x[1])
                return best_match[0]
                    
            # None if no matches found or multiple matches and word too short
            return None
    
    def process_sentence(self, 
            sentence: str,
            levenstein_minimum_length = 2,
            prefix_similarity_threshold: float = 0.6,
            min_prefix_len: int = 3,
            max_overflow: int = None,
        ) -> List[str]:
        words = sentence.split()
        lemmatized_words = [
            self.lemmatize(
                word, 
                levenstein_minimum_length=levenstein_minimum_length,
                prefix_similarity_threshold=prefix_similarity_threshold,
                min_prefix_len=min_prefix_len,
                max_overflow=max_overflow,
            ) for word in words
        ]
        return lemmatized_words
    
    @staticmethod
    def search_tree(
        tree: dict, 
        word: Optional[str] = None, 
        partial: bool = True, 
        min_prefix_len: int = 0,
        max_overflow: Optional[int] = None,
        prefix_length: int = 0,
        overflow: int = 0,
    ) -> Tuple[List[str], int]:
        """
        Search for the word in the prefix tree.
        If word is None, return all the words in the tree.
        
        Parameters:
            tree (dict): the prefix tree.
            word (str): the word to search for. If None, return all words in the tree.
            partial (bool): 
                if True, return all the words that share the longest common prefix with the word.
                if False, returned words must have the entire word as a prefix.
            min_prefix_len (int): the minimum length of the prefix to search for.
            max_overflow (int): the maximum number of characters allowed after the prefix.
            prefix_length (int): 
                the current depth in the tree if a word is being matched. 
                Stops counting when word is None or "".
            overflow (int): the number of characters that are not in the prefix.
            
        Returns:
            Tuple[List[str], int]: a list of words that match the search criteria and the length of the shared prefix.
        """
        results = []
        
        # Prefix search recursive loop
        if word:
            # Looking for a specific character
            if word[0] in tree.keys():
                words, prefix_length = Correcteur.search_tree(
                    tree[word[0]], 
                    word[1:], 
                    min_prefix_len=min_prefix_len,
                    max_overflow=max_overflow,
                    prefix_length=prefix_length+1,
                )
                results.extend(words)
                return results, prefix_length
            
            elif not partial:
                return [], prefix_length  # No match found and partial search is not allowed
            
        if overflow == 0 and prefix_length < min_prefix_len:  # Don't browse all the tree if we don't have enough characters in common
            return [], prefix_length

        # Overflow recursive loop (searching for words from a prefix)
        if max_overflow is None or overflow <= max_overflow:
            
            for key in tree.keys():
                if key == "#":
                    results.extend(tree[key])
                else:
                    words, _ = Correcteur.search_tree(
                        tree[key],
                        min_prefix_len=min_prefix_len,
                        max_overflow=max_overflow,
                        overflow=overflow+1, 
                    )
                    results.extend(words)
                
        return results, prefix_length
    
    @staticmethod
    def build_prefix_tree(lexique: List[str]) -> dict:
        """
        A dictionary of character to dictionary of character to dictionary of character to ... to True
        """
        tree = {}
        for word in lexique:
            current_node = tree
            for char in word:
                if char not in current_node:
                    current_node[char] = {}
                current_node = current_node[char]
                
            if "#" not in current_node:
                current_node['#'] = set()
            current_node['#'].add(word)  # Keeping track of the words that end here
        return tree
    
    @staticmethod
    def levenstein(
        word1: str, 
        word2: str, 
        cost_insert: int = 1,
        cost_delete: int = 1,
        cost_substitute: int = 1,
    ) -> int:
        """Compute the Levenshtein distance between two words."""
        previous_row = range(len(word2) + 1)
        for i, chr1 in enumerate(word1):
            current_row = [i + cost_delete]  # = row[0] + 1
            for j, chr2 in enumerate(word2):
                # j refers to previous index (bc counting from 0 = char1 while column 0 is supposed to be empty string)
                insertion = previous_row[j + 1] + cost_insert
                deletion = current_row[j] + cost_delete
                substitution = previous_row[j] + (cost_substitute if chr1 != chr2 else 0)
                current_row.append(min(insertion, deletion, substitution))
            previous_row = current_row
        return previous_row[-1]
    