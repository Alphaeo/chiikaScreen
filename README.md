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

Le modele (`models/Qwen2.5-VL-3B-Instruct-Q4_K_M.gguf` + `models/mmproj-Qwen2.5-VL-3B-Instruct-Q8_0.gguf`,
~2.8 Go) se telecharge via:

```
.venv\Scripts\python -c "from huggingface_hub import hf_hub_download as d; d('unsloth/Qwen2.5-VL-3B-Instruct-GGUF', 'Qwen2.5-VL-3B-Instruct-Q4_K_M.gguf', local_dir='models'); d('ggml-org/Qwen2.5-VL-3B-Instruct-GGUF', 'mmproj-Qwen2.5-VL-3B-Instruct-Q8_0.gguf', local_dir='models')"
```

**Espace disque libre requis:** garde au moins ~10-15 Go libres sur le disque
pendant que ca tourne. Sur une machine avec peu de RAM (8 Go ici), llama.cpp
mmap les poids depuis le disque et Windows s'appuie sur le pagefile pour le
reste; avec le disque presque plein, l'encodage de l'image plantait de facon
quasi systematique (`access violation reading 0x0`, pas juste un `bad_alloc`
propre) meme avec un modele/contexte/resolution reduits. Liberer le disque a
resolu le probleme completement (4/4 requetes OK ensuite), donc si ca replante,
regarde l'espace disque avant de re-tuner le modele.

## Lancer

```
.venv\Scripts\python main.py
```

Il faut le lancer depuis une session desktop interactive (pas via un shell
sans interface graphique) puisqu'il ouvre des fenetres Tkinter et pose un
hook clavier global.

## Etat actuel (v1)

- Capture ecran + overlay (curseur qui suit la souris) + `Ctrl+T` + reponse
  du modele local. C'est un assistant de vision Q&A sur ton ecran. Teste et
  fonctionnel: reponses correctes, ~2.5-3.5 min chacune sur un i5-8265U (4
  coeurs, pas de GPU dedie).
- Ce que ca ne fait **pas encore**: prendre le controle de la souris/clavier
  pour agir a ta place. C'est l'etape suivante une fois que la boucle
  perception + reponse tourne correctement.
- `Ctrl+T` est capture globalement (suppress=True), donc il ne declenchera
  plus "nouvel onglet" dans ton navigateur/terminal pendant que l'app tourne.
- `chiikascreen/model.py` retente une fois avec une image plus petite si
  l'encodage plante (defense en profondeur), mais la vraie cause du plantage
  qu'on a vu etait le disque presque plein, pas la resolution de l'image.
