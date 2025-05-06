# index/nlp/interactive_lemmatizer.py
import os
import re
from typing import Dict, List, Tuple, Optional

# --- Configuration ---
# Seuil minimum de longueur pour appliquer la recherche par préfixe
SEUIL_MIN_LEN = 3
# Différence de longueur maximale autorisée entre le mot cherché et le mot du lexique
SEUIL_MAX_DIFF = 4
# Seuil de proximité (en %) pour qu'un mot soit considéré comme candidat par préfixe
SEUIL_PROXIMITE = 60

class InteractiveLemmatizer:
    """
    Analyse une phrase saisie, recherche les mots dans un lexique pré-chargé
    et utilise la recherche par préfixe et la distance de Levenshtein pour
    trouver des correspondances proches si aucune correspondance directe n'est trouvée.
    """

    def __init__(self, lexicon_path: str):
        """
        Initialise l'analyseur en chargeant le lexique.

        Args:
            lexicon_path: Chemin vers le fichier TSV (mot<TAB>lemme).
        """
        self.lexicon: Dict[str, str] = self._load_lexicon(lexicon_path)
        if not self.lexicon:
            print(f"Avertissement: Lexique vide ou non chargé depuis {lexicon_path}")

    @staticmethod
    def _load_lexicon(filepath: str) -> Dict[str, str]:
        """Charge le lexique depuis un fichier TSV (mot<TAB>lemme)."""
        lexicon = {}
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    parts = line.strip().split('\t')
                    if len(parts) == 2:
                        word, lemma = parts[0].strip(), parts[1].strip()
                        if word: # S'assurer que le mot n'est pas vide
                            lexicon[word] = lemma
            print(f"Lexique chargé avec succès depuis {filepath} ({len(lexicon)} entrées).")
        except FileNotFoundError:
            print(f"Erreur: Fichier lexique non trouvé : {filepath}")
        except Exception as e:
            print(f"Erreur lors du chargement du lexique depuis {filepath}: {e}")
        return lexicon

    @staticmethod
    def _calculate_prefix_proximity(word1: str, word2: str) -> int:
        """
        Calcule le score de proximité basé sur le préfixe commun,
        conformément à l'algorithme du cours (Slide 21, Chap 3).

        Args:
            word1: Le mot de la requête (en minuscule).
            word2: Le mot du lexique (en minuscule).

        Returns:
            Score de proximité (0-100) ou 0 si les seuils ne sont pas respectés.
        """
        len1, len2 = len(word1), len(word2)

        # 1. Vérifier seuil minimum
        if len1 < SEUIL_MIN_LEN or len2 < SEUIL_MIN_LEN:
            return 0

        # 2. Vérifier différence de longueur maximale
        if abs(len1 - len2) > SEUIL_MAX_DIFF:
            return 0

        # 3. Calculer le préfixe commun
        common_prefix_len = 0
        for i in range(min(len1, len2)):
            if word1[i] == word2[i]:
                common_prefix_len += 1
            else:
                break

        # Calculer le score de proximité
        # Attention: division par zéro si max(len1, len2) == 0, mais déjà géré par SEUIL_MIN_LEN
        proximity_score = (common_prefix_len * 100) / max(len1, len2)

        return int(proximity_score)

    @staticmethod
    def _calculate_levenshtein(s1: str, s2: str) -> int:
        """
        Calcule la distance de Levenshtein entre deux chaînes.
        Implémentation standard (Wagner-Fischer, Slide 28, Chap 3).
        """
        m, n = len(s1), len(s2)
        # Créer une matrice pour stocker les distances
        dp = [[0] * (n + 1) for _ in range(m + 1)]

        # Initialiser la première ligne et la première colonne
        for i in range(m + 1):
            dp[i][0] = i
        for j in range(n + 1):
            dp[0][j] = j

        # Remplir le reste de la matrice
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                cost = 0 if s1[i - 1] == s2[j - 1] else 1
                dp[i][j] = min(dp[i - 1][j] + 1,        # Suppression
                               dp[i][j - 1] + 1,        # Insertion
                               dp[i - 1][j - 1] + cost) # Substitution ou Identique

        # La distance est dans le coin inférieur droit
        return dp[m][n]

    def find_lemma(self, word: str) -> Tuple[str, str]:
        """
        Trouve le lemme d'un mot en suivant les étapes du TD5.

        Args:
            word: Le mot original extrait de la phrase.

        Returns:
            Tuple[str, str]: (Mot original, Lemme trouvé ou statut).
                             Statut peut être '[DIRECT]', '[PREFIXE]', '[LEVENSHTEIN]', ou '[NON TROUVÉ]'.
        """
        if not self.lexicon:
            return word, "[LEXIQUE VIDE]"

        # (a) Convertir en minuscules
        lower_word = word.lower()

        # (b) Tester si le mot existe directement dans le lexique
        if lower_word in self.lexicon:
            return word, f"{self.lexicon[lower_word]} [DIRECT]"

        # (c) Si non, chercher par préfixe
        candidates: List[Tuple[str, str, int]] = [] # (mot_lexique, lemme, score_proximite)
        for lexicon_word, lemma in self.lexicon.items():
            # Comparer le mot en minuscule avec les mots du lexique (qui sont déjà en clé)
            proximity = self._calculate_prefix_proximity(lower_word, lexicon_word)
            if proximity >= SEUIL_PROXIMITE:
                candidates.append((lexicon_word, lemma, proximity))

        # Si aucun candidat par préfixe
        if not candidates:
            return word, "[NON TROUVÉ]"

        # Si un seul candidat par préfixe
        if len(candidates) == 1:
            lex_word, lemma, _ = candidates[0]
            return word, f"{lemma} [PREFIXE: {lex_word}]"

        # (d) Si plusieurs candidats, utiliser Levenshtein
        # Trier d'abord par score de proximité décroissant (pour favoriser les meilleurs préfixes)
        candidates.sort(key=lambda item: item[2], reverse=True)

        best_match_lemma = None
        best_match_word = None
        min_lev_distance = float('inf')

        for lexicon_word, lemma, _ in candidates:
            distance = self._calculate_levenshtein(lower_word, lexicon_word)
            if distance < min_lev_distance:
                min_lev_distance = distance
                best_match_lemma = lemma
                best_match_word = lexicon_word
            # En cas d'égalité de distance, on garde le premier trouvé
            # (qui a potentiellement un meilleur score de préfixe grâce au tri)

        if best_match_lemma is not None:
             # On indique la distance et le mot trouvé
            return word, f"{best_match_lemma} [LEVENSHTEIN({min_lev_distance}): {best_match_word}]"
        else:
             # Ne devrait pas arriver si on a des candidats, mais par sécurité
            return word, "[NON TROUVÉ après Levenshtein]"


    def process_sentence(self, sentence: str) -> List[Tuple[str, str]]:
        """
        Traite une phrase entière, mot par mot.

        Args:
            sentence: La phrase entrée par l'utilisateur.

        Returns:
            Liste de tuples: [(mot_original1, resultat1), (mot_original2, resultat2), ...]
        """
        # Tokenisation simple (similaire à BaseDocument)
        # Conserve la ponctuation comme token séparé si elle n'est pas collée aux mots
        # Ou utilise \w+ pour ne garder que les "mots"
        tokens = re.findall(r'\w+|[^\w\s]', sentence) # Sépare mots et ponctuation
        # tokens = re.findall(r'\w+', sentence) # Ne garde que les mots

        results = []
        for token in tokens:
            # On ne traite que les "mots" (alphanumériques)
            if re.fullmatch(r'\w+', token):
                results.append(self.find_lemma(token))
            else:
                # Garder la ponctuation/symboles tels quels
                results.append((token, "[SYMBOLE/PONCTUATION]"))

        return results

# --- Point d'entrée pour l'exécution interactive ---
if __name__ == "__main__":
    # **ÉTAPE 1 : TEST AVEC LEXIQUE MANUEL (comme demandé dans l'énoncé)**
    manual_lexicon_data = {
        "cherche": "chercher",
        "manger": "manger",
        "pomme": "pomme",
        "grandes": "grand",
        "larges": "large",
        "beau": "beau",
        "belle": "beau", # Exemple de lemme partagé
        "informations": "information",
        "information": "information",
        "données": "donnée",
        "ordinateur": "ordinateur",
        "programmation": "programmation",
        "système": "système",
        "analyse": "analyse",
        "rapide": "rapide",
    }
    # Crée un fichier temporaire pour le test
    TEST_LEXICON_FILE = "temp_test_lexicon.tsv"
    try:
        with open(TEST_LEXICON_FILE, 'w', encoding='utf-8') as f_test:
            for word, lemma in manual_lexicon_data.items():
                f_test.write(f"{word}\t{lemma}\n")
        print("--- Utilisation du lexique de test ---")
        lemmatizer = InteractiveLemmatizer(TEST_LEXICON_FILE)
    finally:
        # Nettoie le fichier temporaire
        if os.path.exists(TEST_LEXICON_FILE):
            os.remove(TEST_LEXICON_FILE)

    # **ÉTAPE 2 : UTILISATION DU LEXIQUE COMPLET (après tests)**
    # Décommenter ces lignes pour utiliser le lexique généré au TD4
    LEXICON_PATH_TD4 = "output/lemma_comparison/lemma_comparison_spacy.tsv" # ou _snowball.tsv
    print(f"\n--- Utilisation du lexique complet ({LEXICON_PATH_TD4}) ---")
    if os.path.exists(LEXICON_PATH_TD4):
         lemmatizer = InteractiveLemmatizer(LEXICON_PATH_TD4)
    else:
         print(f"Erreur: Le fichier lexique {LEXICON_PATH_TD4} n'a pas été trouvé.")
         print("Assurez-vous d'avoir exécuté le TD4 et que le chemin est correct.")
         # L'exécution continue avec le lemmatiseur de test si le fichier complet n'est pas trouvé

    print("\nEntrez une phrase à analyser (ou 'quit' pour quitter).")
    while True:
        try:
            input_sentence = input("> ")
            if not input_sentence or input_sentence.lower() in ['quit', 'exit']:
                break

            results = lemmatizer.process_sentence(input_sentence)

            print("Résultats de l'analyse :")
            for original, result in results:
                print(f"  - {original:<15} -> {result}")
            print("-" * 20)

        except EOFError: # Gère Ctrl+D
            break
        except KeyboardInterrupt: # Gère Ctrl+C
            break

    print("\nFin du programme.")