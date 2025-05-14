"""
Produit un ensemble de lemmes associés aux tokens d'entrée.
"""

from typing import List, Tuple

def lemmatize_tokens(
    tokens: List[str],
    lexicon: List[str],
    min_len: int = 3,
    max_diff: int = 4,
    min_proximity: int = 60
) -> List[Tuple[str, str]]:
    """
    Produit un ensemble de lemmes associés aux tokens d'entrée.
    
    Pour chaque token, cherche dans le lexique :
      1. [DIRECT]      : mot en minuscules dans lexique
      2. [PREFIXE]     : un seul candidat par préfixe
      3. [LEV(distance)]: plusieurs candidats → on choisit sur distance de Levenshtein
      4. [NON TROUVÉ]  : aucun candidat
      
    Parameters:
        tokens (List[str]): Liste de tokens à lemmatiser
        lexicon (List[str]): Liste de mots du lexique
        min_len (int): Longueur minimale d'un mot pour être considéré
        max_diff (int): Différence maximale de longueur entre deux mots
        min_proximity (int): Proximité minimale pour considérer un mot comme candidat
        
    Returns:
        List[Tuple[str, str]]: Liste de tuples contenant le token original et sa lemmatisation
    """
    lex = [w.lower() for w in lexicon]

    def prefix_score(a: str, b: str) -> int:
        if len(a) < min_len or len(b) < min_len or abs(len(a) - len(b)) > max_diff:
            return 0
        common = 0
        for ca, cb in zip(a, b):
            if ca == cb:
                common += 1
            else:
                break
        return common * 100 // max(len(a), len(b))

    def levenshtein(a: str, b: str) -> int:
        m, n = len(a), len(b)
        dp = list(range(n + 1))
        for i in range(1, m + 1):
            prev, row = i, [i] + [0] * n
            for j in range(1, n + 1):
                cost = 0 if a[i - 1] == b[j - 1] else 1
                row[j] = min(dp[j] + 1, row[j - 1] + 1, prev + cost)
                prev = dp[j]
            dp = row
        return dp[n]

    resultat: List[Tuple[str, str]] = []
    for tok in tokens:
        w = tok.lower()
        # (1) direct
        if w in lex:
            resultat.append((w, f"{w} [DIRECT]"))
            continue
        # (2) candidats par préfixe
        cands = [(c, prefix_score(w, c)) for c in lex if prefix_score(w, c) >= min_proximity]
        if not cands:
            resultat.append((None, "[NON TROUVÉ]"))
            continue
        # (3a) un seul candidat
        if len(cands) == 1:
            resultat.append((cands[0][0], f"[PREFIXE]"))
            continue
        # (3b) tri par proximité et choix par Levenshtein
        cands.sort(key=lambda x: x[1], reverse=True)
        best, dist = cands[0][0], float("inf")
        for c, _ in cands:
            d = levenshtein(w, c)
            if d < dist:
                best, dist = c, d
        resultat.append((best, f"[LEV({dist})]"))
    return resultat