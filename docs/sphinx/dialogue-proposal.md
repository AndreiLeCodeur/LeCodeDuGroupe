# Rencontre avec le sphinx — contrat du dialogue

Ce document décrit ce que le navigateur, le serveur Python, le moteur et le
sphinx échangent pendant la rencontre, et les comportements sur lesquels chacun
peut compter. Il sert de référence commune à S2-03 (classe `Sphinx`) et à S2-04
(règles du moteur).

Il décrit le comportement du transport **fourni** dans `gridworld/web_support.py`,
que personne ne modifie. Les échanges de [examples.json](examples.json) n'ont pas
été écrits à la main : ils ont été enregistrés en faisant tourner ce transport
avec un moteur d'essai qui suit les fragments de S2-04 et un faux sphinx.

| Fichier | Rôle |
| --- | --- |
| `levels/sphinx.json` | Carte de démonstration, avec le marqueur `"sphinx": true`. |
| `docs/sphinx/dialogue-proposal.md` | Ce document. |
| `docs/sphinx/examples.json` | Six scénarios complets : requêtes, codes HTTP, réponses. |
| `docs/sphinx/evaluation-corpus.json` | Cas pour mettre le dialogue à l'épreuve. |

## Map and demonstration

La carte est un couloir de sept cases sur trois. Les coordonnées commencent à
zéro, `x` va vers la droite et `y` vers le bas.

```text
      x = 0 1 2 3 4 5 6
y = 0     # # # # # # #
y = 1     # P . . . S #      P : départ (1, 1)   S : sortie et sphinx (5, 1)
y = 2     # # # # # # #
```

Le sphinx n'a pas de coordonnées à lui : `"sphinx": true` signifie « un sphinx
garde la sortie ». Il est donc toujours sur la case `exit`, et c'est sa présence
qui bloque le passage, pas un nouveau type de mur. N0 n'a pas ce marqueur et
reste inchangé.

Trajet de démonstration :

| Action | Position du joueur | `turn` | `revision` | Ce qui se passe |
| --- | --- | --- | --- | --- |
| départ | (1, 1) | 0 | 0 | — |
| `east` | (2, 1) | 1 | 1 | déplacement |
| `east` | (3, 1) | 2 | 2 | déplacement |
| `east` | (4, 1) | 3 | 3 | déplacement |
| `east` | (4, 1) | 4 | 4 | tentative d'entrer sur la sortie : le joueur ne bouge pas, la question apparaît |
| réponse envoyée | (4, 1) | 4 | 5 | évaluation en cours |
| verdict favorable | (5, 1) | 4 | 6 | le joueur est placé sur la sortie : `Victory!` |

La sortie est inaccessible tant que le sphinx n'a pas accepté une réponse. Une
bonne réponse place directement le joueur sur la sortie : il n'y a pas de
déplacement supplémentaire à faire, la victoire arrive au tour 4. Répondre,
attendre le verdict et annuler ne consomment aucun tour.

Le sphinx ne garde la sortie que si le moteur possède un objet sphinx. Le lanceur
web en fournit un pour une carte marquée ; en mode terminal ou Pygame, et sur N0,
le jeu se comporte comme avant.

## Public and private data

L'état public reste le `JsonState` de `gridworld/contracts.py`, avec ses huit
champs. Le dialogue utilise le champ `interaction` déjà prévu : aucun second
format d'état n'est créé.

**Public** (envoyé au navigateur) :

- l'entité `{"id": "sphinx-1", "kind": "sphinx", "x": 5, "y": 1, "appearance": "sphinx"}`
  dans `entities`, dès le début de la partie ;
- `interaction`, qui vaut `null` hors dialogue, sinon exactement cinq chaînes :

| Champ | Contenu |
| --- | --- |
| `id` | Identifiant de cette rencontre, généré par le serveur. |
| `actor_id` | Toujours `sphinx-1`. |
| `status` | `question`, `pending`, `rejected` ou `error`. |
| `question` | Le texte de l'énigme. |
| `message` | Retour au joueur : vide, un indice, ou le message de panne. |

**Privé** (reste dans le processus Python) :

- l'objet `Sphinx` lui-même, rangé dans `engine.sphinx` ;
- `riddle["expected_answer"]`, la réponse de référence ;
- `history`, la liste des réponses refusées et de leurs indices ;
- la sortie brute du modèle et les prompts ;
- le jeton de tentative du transport, qui distingue deux évaluations d'une même
  interaction.

`Engine.get_state()` ne doit jamais recopier `self.sphinx`, son énigme ou son
historique, et ne doit jamais appeler le LLM. La carte ne contient aucune énigme :
il n'y a donc rien de privé dans `levels/sphinx.json`.

L'énigme et la rencontre sont deux choses différentes. L'énigme est inventée une
fois par objet `Sphinx`, avant le démarrage du serveur, et ne change plus. L'`id`
d'interaction désigne une rencontre : après une annulation, une nouvelle rencontre
reçoit un nouvel identifiant mais repose la même question.

Limite connue : après un refus, `message` contient un **indice rédigé par le
modèle**. Le prompt fourni lui demande de ne pas nommer la solution, mais rien ne
le garantit. Le transport refuse en revanche tout verdict qui contient un champ en
trop, donc la référence ne peut pas arriver dans l'état par un champ
supplémentaire. Les deux autres messages sont fixes :

| Situation | Texte | Où |
| --- | --- | --- |
| Réponse acceptée | `Victory!` | `state.message` (le dialogue est fermé) |
| Panne de l'évaluateur | `The evaluator is unavailable. Try again.` | `interaction.message` |
| Réponse refusée | indice du modèle | `interaction.message` |

Le sphinx renvoie aussi `Correct!` quand il accepte, mais ce texte n'est pas
affiché : le moteur ferme le dialogue et publie `Victory!`.

## Dialogue transitions

| `status` | Ce que cela signifie pour le joueur |
| --- | --- |
| `question` | La question est affichée ; il peut proposer une réponse. |
| `pending` | Sa réponse est en cours d'évaluation ; il peut seulement annuler. |
| `rejected` | La réponse est refusée, un indice est affiché ; il peut réessayer. |
| `error` | L'évaluation a échoué techniquement ; il peut réessayer. |

Il n'y a pas d'état « accepté » visible : une réponse acceptée ferme le dialogue
et termine la partie dans la même transition. Le rendu fourni sait afficher un
statut `accepted`, utilisé par une ancienne démonstration, mais notre jeu ne le
produit pas.

```text
                 east vers la sortie (tour +1)
  pas de dialogue ───────────────────────────▶ question
        ▲                                         │ POST /api/answer (202)
        │ POST /api/cancel                        ▼
        ├──────────────────────────────────── pending ──────────────┐
        │                                      │      │             │
        │                         correct=false│      │panne        │correct=true
        │                                      ▼      ▼             ▼
        ├──────────────────────────────── rejected   error     victoire :
        │                                      │      │        dialogue fermé,
        │                                      └──┬───┘        status "won"
        │                       POST /api/answer  │
        │                                         ▼
        └──────────────────────────────────── pending …
```

| Depuis | Événement | Vers | `turn` | `revision` |
| --- | --- | --- | --- | --- |
| pas de dialogue | déplacement vers la sortie gardée | `question` | +1 | +1 |
| `question`, `rejected`, `error` | `POST /api/answer` valide | `pending` | — | +1 |
| `pending` | verdict `correct: false` | `rejected` | — | +1 |
| `pending` | panne, délai dépassé, verdict mal formé | `error` | — | +1 |
| `pending` | verdict `correct: true` | pas de dialogue, partie gagnée | — | +1 |
| les quatre statuts | `POST /api/cancel` | pas de dialogue | — | +1 |
| les quatre statuts | action `quit` | pas de dialogue, `running=false` | — | +1 |
| les quatre statuts | déplacement ou `wait` | inchangé | — | — |
| tous | `GET /api/state`, requête refusée, verdict périmé | inchangé | — | — |

`turn` compte les tours du jeu ; `revision` signale chaque changement visible, y
compris ceux du dialogue. C'est pourquoi une rencontre suivie de trois réponses
fait passer `revision` de 4 à 10 alors que `turn` reste à 4.

La question reste identique après un refus, une panne ou une annulation. Après un
refus, la réponse et son indice sont ajoutés à l'historique privé, ce qui permet
au modèle de proposer un indice différent la fois suivante. Une tentative annulée
n'est pas ajoutée à l'historique.

Pendant un dialogue, les déplacements et `wait` sont suspendus : le serveur
répond 200 avec le même état, sans tour ni révision. Seul `quit` reste actif.

## Requests, responses and errors

Toutes les réponses réussies sont un `StateFrame` complet, en JSON, avec
`Cache-Control: no-store` :

```json
{"protocol_version": 1, "session_id": "…", "revision": 5, "running": true, "state": { … }}
```

| Route | Corps JSON exact | Succès |
| --- | --- | --- |
| `GET /api/state` | aucun | 200, état courant, sans rien modifier |
| `POST /api/actions` | `{"action": "east"}` | 200, état après l'action |
| `POST /api/answer` | `{"interaction_id": "…", "answer": "…"}` | 202, état avec `status: "pending"` |
| `POST /api/cancel` | `{"interaction_id": "…"}` | 200, état avec `interaction: null` |

**Répondre.** Le 202 signifie « l'évaluation a démarré », pas « la réponse est
correcte ». Le verdict n'est jamais dans la réponse au POST : le navigateur le
découvre en relisant `GET /api/state`, qui reste disponible pendant toute
l'évaluation parce que l'appel au modèle se fait hors du verrou de la partie.
Les espaces aux extrémités de `answer` sont retirés, puis la longueur doit être
comprise entre 1 et 500 caractères.

**Annuler.** L'annulation est possible dans les quatre statuts, y compris
`pending`. Le passage reste fermé et l'évaluation en cours devient périmée. Elle
n'est pas forcément interrompue côté modèle : son résultat est simplement ignoré
à l'arrivée, même si une nouvelle rencontre a commencé entre-temps. Un résultat
n'est publié que si la partie tourne encore, que l'identifiant d'interaction est
le même et que le jeton de tentative est toujours le jeton courant.

**Quitter.** `quit` passe par `POST /api/actions`. Il met `running` à `false`,
retire le dialogue et invalide l'évaluation en cours, sans consommer de tour. Le
serveur reste lisible par GET ; aucune autre requête ne peut plus modifier la
partie.

### Requêtes refusées

Le format d'erreur est toujours
`{"error": {"code": "stale_interaction", "message": "…"}}`. Une requête refusée
ne modifie rien et ne déclenche aucune évaluation. Les vérifications se font dans
cet ordre : d'abord la forme de la requête, ensuite l'état de la partie.

| Ordre | HTTP | `code` | Situation |
| --- | --- | --- | --- |
| 1 | 415 | `unsupported_media_type` | `Content-Type` absent ou différent de `application/json`. |
| 2 | 400 | `invalid_json` | Le corps n'est pas du JSON lisible. |
| 3 | 422 | `invalid_request` | Pas un objet, champ manquant ou en trop, valeur qui n'est pas une chaîne. |
| 4 | 422 | `invalid_request` | `answer` vide ou de plus de 500 caractères après retrait des espaces. |
| 5 | 409 | `game_closed` | Requête valide après `quit`. |
| 6 | 409 | `stale_interaction` | Aucun dialogue actif ne porte cet identifiant. |
| 7 | 409 | `evaluation_pending` | Une réponse est déjà en cours d'évaluation. |
| — | 500 | `internal_error` | Erreur interne ; le détail reste dans le terminal Python. |

Après une victoire le dialogue n'existe plus : une réponse tardive reçoit donc
`stale_interaction`. Le transport connaît aussi un code `interaction_complete`,
prévu pour le statut `accepted` ; il ne peut pas se produire dans notre jeu.

### Pannes de l'évaluateur

Une panne survient après le 202, quand le POST est déjà terminé : elle ne peut
plus être une réponse HTTP. Elle devient l'état de dialogue `error`, visible par
GET. Trois situations y mènent :

- le modèle met plus longtemps que le délai maximal (180 secondes dans
  `llm_support.py`) ;
- Ollama est arrêté ou injoignable ;
- la réponse n'est pas exactement `{"correct": <booléen>, "message": <chaîne>}`.

Les chaînes `"true"` et `"false"` ne sont pas des booléens : `{"correct": "false"}`
donne `error`, pas `rejected`, et `{"correct": "true"}` n'ouvre jamais le
passage. Seul le booléen `false` produit un refus.

Une panne n'est pas une mauvaise réponse du joueur : rien n'est ajouté à
l'historique, la question reste la même et une nouvelle tentative est acceptée.

### Les six scénarios de examples.json

Chaque scénario part d'un serveur qui vient de démarrer et se lit seul. Pour
chaque échange, `name`, `precondition` et `why` sont de la documentation ;
`request`, `status` et `response` sont l'échange HTTP. Les identifiants
aléatoires sont remplacés par `example-server-session` et
`example-interaction-N`.

| Scénario | Ce qu'il montre |
| --- | --- |
| `accepted-answer` | Rencontre, 202, lecture pendant l'attente, victoire. |
| `rejected-then-retry` | Deux refus avec deux indices différents, un déplacement ignoré, puis la victoire. |
| `failure-then-retry` | Une panne, puis la même réponse acceptée. |
| `cancel-then-late-verdict` | Double envoi refusé, annulation, verdict tardif ignoré, nouvelle rencontre avec un nouvel identifiant. |
| `quit-while-pending` | `quit` pendant l'attente, verdict tardif ignoré, partie fermée. |
| `refused-requests` | Les requêtes refusées, puis une lecture qui prouve que rien n'a changé. |

Les scénarios alternatifs sont séparés exprès : dans une même chronologie, un
verdict ne peut pas être à la fois accepté et annulé.

## Corpus d'évaluation

[evaluation-corpus.json](evaluation-corpus.json) rassemble les saisies et les
incidents à examiner. `riddle_id` est à la racine et `cases` est une liste. Le
corpus utilise l'énigme de l'écho du faux LLM fourni, parce que l'énigme du vrai
modèle change d'une partie à l'autre.

| Clé d'un cas | Signification |
| --- | --- |
| `id`, `family` | Nom du cas et famille : `meaning`, `input`, `ambiguity`, `technical`, `cancellation`. |
| `answer` | Texte saisi par le joueur. |
| `answer_recipe` | Fabrique une longue saisie : `{"repeat": "x", "count": 501}` vaut 501 fois `x`. `surround_with_spaces` ajoute ce nombre d'espaces de chaque côté. |
| `expected` | `accepted` ou `rejected` : le verdict qu'un bon juge doit rendre. |
| `ambiguous` | `true` si le résultat attendu n'est pas encore fixé par le groupe. |
| `service_failure` | Incident à simuler : `timeout` ou `unavailable`. |
| `service_reply` | Réponse brute de l'évaluateur à simuler. |
| `cancel_before_verdict` | `true` si l'on annule pendant `pending`. |
| `expected_http` | Code HTTP et code d'erreur du POST quand il est refusé. |
| `expected_status` | Statut du dialogue lu par GET une fois l'évaluation terminée. |
| `observe` | Comment constater le résultat. |

Ce sont des conventions du corpus. Aucune de ces clés n'est un champ à ajouter
aux requêtes HTTP.

Trois résultats ne se mélangent pas dans un même score :

- **Jugement** : les cas `accepted` / `rejected`. C'est la seule mesure de qualité
  du modèle ; elle concerne S2-03 et demande le vrai modèle pour les
  reformulations.
- **Saisie** : les requêtes refusées en 422. Elles n'atteignent jamais
  l'évaluateur et se vérifient sur l'API, côté S2-04.
- **Technique** : pannes et annulations. Elles se vérifient avec un faux sphinx,
  côté S2-04. Une panne simulée n'est jamais comptée comme un mauvais jugement.

Les cas `ambiguous` restent hors du score binaire tant que le groupe n'a pas
discuté et fixé leur résultat attendu. Les tentatives d'imposer le verdict
(`forced-verdict-json`, `forced-verdict-instruction`) doivent être refusées : le
texte du joueur est une donnée à juger, pas une instruction pour l'évaluateur.

## Interfaces à relire avec S2-03 et S2-04

**S2-03 — `gridworld/sphinx.py`**

- `get_question() -> str` : génère l'énigme au premier appel, la mémorise et ne
  renvoie que la question.
- `answer(player_text) -> {"correct": bool, "message": str}` : exactement ces deux
  champs. En cas de problème technique, la méthode lève une exception ; elle ne
  renvoie pas un verdict inventé.
- Le transport évalue sur une **copie** du sphinx (`deepcopy`) et ne la conserve
  que si la tentative est toujours courante. L'objet doit donc rester copiable :
  pas de connexion ouverte ni de verrou gardé en attribut.

**S2-04 — `gridworld/engine.py`**

- `self.sphinx` et `self.interaction` existent dès le constructeur.
- Rencontre : `start_sphinx_dialogue()` range `new_interaction(self.sphinx)` dans
  `self.interaction` ; le tour est consommé, le joueur ne bouge pas.
- `apply_sphinx_verdict(verdict)` : refus → `status="rejected"` et `message` reçoit
  l'indice ; acceptation → joueur sur la case du sphinx, `interaction=None`,
  `status="won"`, `message="Victory!"`.
- `get_state()` publie `self.interaction` et garde l'entité sphinx de S2-02.

**Points à trancher ensemble**

- `state.message` au moment de la rencontre n'est fixé par aucun énoncé. Dans les
  exemples il garde la valeur du dernier déplacement (`You moved.`).
- Après `quit`, notre moteur met `status` à `lost` et `message` à
  `You quit the game.` : c'est le comportement actuel du groupe, repris tel quel
  dans le scénario `quit-while-pending`.
- S2-03 fournit un fichier `tests/test_sphinx.py`. Les tests de la carte de S2-02
  sont donc dans `tests/test_sphinx_map.py` pour ne pas entrer en conflit.

## Vérifier les fichiers

```sh
uv run python -m json.tool levels/sphinx.json
uv run python -m json.tool docs/sphinx/examples.json
uv run python -m json.tool docs/sphinx/evaluation-corpus.json
```

Ces commandes vérifient la syntaxe, pas la justesse du contrat. Pour voir le
dialogue dans le panneau fourni une fois S2-04 intégré :

```sh
uv run python -m gridworld.api_render --level levels/sphinx.json --fake-sphinx rejected
```
