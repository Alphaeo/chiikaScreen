# chiikaScreen

Agent local qui voit ton ecran et repond a tes questions, avec un petit
"curseur" a lui qui suit ta souris. `Ctrl+T` ouvre une boite de texte sous
le curseur, tape ta question, l'agent capture l'ecran, l'envoie au modele
vision (Qwen2.5-VL-3B, GGUF quantise, tourne 100% en local sur CPU) et
affiche la reponse.

## Setup

```
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu
```

Le flag `--extra-index-url` est necessaire sur Windows: llama-cpp-python n'a
pas de wheel precompile sur PyPI pour cette plateforme, et compiler depuis
les sources plante a cause de la longueur des chemins Windows.

Le modele (`models/Qwen2.5-VL-3B-Instruct-Q4_K_M.gguf` + `models/mmproj-F16.gguf`,
~3.3 Go) se telecharge via:

```
.venv\Scripts\python -c "from huggingface_hub import hf_hub_download as d; d('unsloth/Qwen2.5-VL-3B-Instruct-GGUF', 'Qwen2.5-VL-3B-Instruct-Q4_K_M.gguf', local_dir='models'); d('unsloth/Qwen2.5-VL-3B-Instruct-GGUF', 'mmproj-F16.gguf', local_dir='models')"
```

## Lancer

```
.venv\Scripts\python main.py
```

Il faut le lancer depuis une session desktop interactive (pas via un shell
sans interface graphique) puisqu'il ouvre des fenetres Tkinter et pose un
hook clavier global.

## Etat actuel (v1)

- Capture ecran + overlay (curseur qui suit la souris) + `Ctrl+T` + reponse
  du modele local. C'est un assistant de vision Q&A sur ton ecran.
- Ce que ca ne fait **pas encore**: prendre le controle de la souris/clavier
  pour agir a ta place. C'est l'etape suivante une fois que la boucle
  perception + reponse tourne correctement.
- `Ctrl+T` est capture globalement (suppress=True), donc il ne declenchera
  plus "nouvel onglet" dans ton navigateur/terminal pendant que l'app tourne.
