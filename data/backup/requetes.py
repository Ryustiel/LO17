# traitement_requete.py

import re
from datetime import datetime

# ---- Constantes ----
# mois français → numéro
MONTHS = {
    'janvier':1, 'février':2, 'mars':3, 'avril':4,
    'mai':5, 'juin':6, 'juillet':7, 'août':8,
    'septembre':9, 'octobre':10, 'novembre':11, 'décembre':12
}

# mots‐clés temporels → opérateur
TEMP_OP = {
    'avant'        : '<=',
    'au plus tard' : '<=',
    'jusqu'        : '<=',
    'après'        : '>=',
    'depuis'       : '>=',
    'à partir de'  : '>='
}

# regex plage de dates "entre X et Y"
RANGE_RE = re.compile(
    r'entre\s+'
    r'(\d{1,2})(?:er)?\s+(' + '|'.join(MONTHS) + r')\s+(\d{4})'
    r'\s+et\s+'
    r'(\d{1,2})(?:er)?\s+(' + '|'.join(MONTHS) + r')\s+(\d{4})'
)

# regex date simple avec modificateur optionnel
UNIT_RE = re.compile(
    r'(?:(avant|après|depuis|jusqu|à partir de|au plus tard)\s+)?'
    r'(\d{1,2})(?:er)?\s+(' + '|'.join(MONTHS) + r')\s+(\d{4})'
)

# liste étendue de mots vides (sans et/​ou car on les utilisera pour le booléen)
STOP = {
  'le','la','les','de','du','des','un','une','d','l','en','dans','sur','à','au','aux',
  'pour','par','dont','leur','leurs','ce','ces','cette','ceux','celui','celle',
  'mon','ton','son','notre','votre','nos','vos',
  'je','tu','il','elle','nous','vous','ils','elles',
  'veux','voudrais','souhaite','cherche','recherche','aimerais',
  'donner','afficher','liste','listes',
  'articles','article',
  # verbes fréquents
  'sont','suis','est','serez','étaient','étais','sera','seront','ont','avait','avais','avoir',
  'parle','parlent','parler','traite','traitant','évoquent','évoquant','mentionnent','mentionnant',
  'doivent','devrait','doit','peuvent','peux','peut','être'
}

# ---- Fonctions auxiliaires ----

def parse_bool(s: str):
    """
    Transforme une chaîne de mots+et/or+(parenthèses) en AST de la forme :
      'mot' ou ('et',[...]) ou ('ou',[...]) voire imbriqué.
    On considère 'et' > 'ou' en priorité.
    On remplace d'abord les virgules par des espaces.
    """
    s = s.replace(',', ' ')
    # on arrive à des tokens: parenthèses, mots, 'et','ou'
    toks = re.findall(r'\(|\)|\w+', s)
    prec = {'et': 2, 'ou': 1}
    outq, ops = [], []
    for t in toks:
        if t == '(':
            ops.append(t)
        elif t == ')':
            while ops and ops[-1] != '(':
                outq.append(ops.pop())
            ops.pop()
        elif t in prec:
            # dépile les opérateurs de priorité ≥
            while ops and ops[-1] in prec and prec[ops[-1]] >= prec[t]:
                outq.append(ops.pop())
            ops.append(t)
        else:
            outq.append(t)
    while ops:
        outq.append(ops.pop())
    # construction de l'AST depuis la RPN
    stack = []
    for tok in outq:
        if tok in prec:
            b = stack.pop(); a = stack.pop()
            stack.append((tok, [a, b]))
        else:
            stack.append(tok)
    return stack[0] if stack else None

# ---- Parsing principal ----

def parse_query(q: str, zones: list):
    """
    q     : requête en français
    zones : liste de zones possibles, ex. ["titre","texte","rubrique","caption","image"]
    renvoie dict { 'dates': [ {'op':...,'date':datetime}, … ],
                   'zones': { 'titre': AST_bool, 'texte': AST_bool, … } }
    """
    txt = q.lower()
    # on garde virgules et parenthèses pour parse_bool, on retire le reste de la ponctuation
    txt = re.sub(r"[«»\"'\.\;\:\?\!]", " ", txt)
    txt = re.sub(r'\s+', ' ', txt).strip()

    res = {'dates': [], 'zones': {}}

    # 1) plages "entre X et Y"
    m = RANGE_RE.search(txt)
    if m:
        d1, M1, y1 = int(m.group(1)), MONTHS[m.group(2)], int(m.group(3))
        d2, M2, y2 = int(m.group(4)), MONTHS[m.group(5)], int(m.group(6))
        res['dates'].append({'op': '>=', 'date': datetime(y1, M1, d1)})
        res['dates'].append({'op': '<=', 'date': datetime(y2, M2, d2)})
        # on neutralise la plage dans le texte
        txt = txt[:m.start()] + ' '*(m.end()-m.start()) + txt[m.end():]

    # 2) dates unitaires
    for m in UNIT_RE.finditer(txt):
        key = m.group(1) or ''
        op  = TEMP_OP.get(key, '=')
        d, M, y = int(m.group(2)), MONTHS[m.group(3)], int(m.group(4))
        res['dates'].append({'op': op, 'date': datetime(y, M, d)})
    # on retire toutes les dates simples détectées
    txt = UNIT_RE.sub(' ', txt)

    # 3) extraction des zones par priorité
    for z in zones:
        # on cherche "... TERMS ... dans|sur|en [le|la|les|leur|leurs] Z"
        pat = rf'([\w\s,()]+?)\s+(?:dans|sur|en)\s+(?:le|la|les|leur|leurs)?\s*{z}'
        m = re.search(pat, txt)
        if not m:
            continue
        grp = m.group(1).strip()
        # suppression des stop words _sauf_ "et"/"ou"
        mots = [w for w in re.split(r'[\s,]+', grp) if w and w not in STOP]
        expr = parse_bool(" ".join(mots))
        res['zones'][z] = expr
        # on retire la partie traitée
        txt = txt[:m.start()] + ' '*(m.end()-m.start()) + txt[m.end():]

    # 4) reste → zone "texte" par défaut (si reste non vide)
    reste = [w for w in re.split(r'[\s,]+', txt) if w and w not in STOP]
    if reste:
        res['zones']['texte'] = parse_bool(" ".join(reste))

    return res

# ---- Exemple d'exécution ----
if __name__ == "__main__":
    zones = ["titre", "texte", "rubrique", "caption", "image"]
    q = (
      'montre moi les articles qui parlent de “trouver” ou de “chercher” '
      'dans leur titre et qui ont abricot dans leur texte. '
      'Ils doivent dater d’avant le 12 décembre 2025.'
    )
    from pprint import pprint
    pprint(parse_query(q, zones))
    