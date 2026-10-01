# Prompt for the new AI agent

Skopiuj poniższy tekst do nowego agenta po instalacji systemu:

```text
Pracujemy po polsku nad projektem TV mode z repozytorium
https://github.com/98przem/tv-mode.git. Przeczytaj w całości README.md,
docs/INSTALL.md, docs/STEAMOS.md, handoff/HANDOFF.md i lokalny AGENTS.md,
jeżeli istnieje. Najpierw sprawdź git status oraz ostatnie commity. Nie cofaj
istniejących zmian użytkownika.

Tryb pracy: szybkie iteracje. Ty wykonujesz zmiany, podajesz mi jeden krótki
test na fizycznym padzie, ja testuję w Steam Game Mode i opisuję wynik. Bez
długich tur i bez rozbudowanych automatycznych testów UI.

Najważniejsza zasada: Xbox Cloud ma natywną obsługę pada. Między fizycznym
padem a Xbox Cloud nie może być userscriptu, mapowania klawiszy, wirtualnego
kontrolera ani żadnej translacji. TV mode ma zwolnić SDL przed uruchomieniem
Xbox Cloud, niczego nie przekazywać i wznowić SDL dopiero po zamknięciu Xboxa.
Jeżeli Xbox nie widzi pada, diagnozuj dostęp urządzenia, Steam Input, Flatpak i
procesy. Nie obchodź problemu translacją wejścia.

Steam Input dla skrótu TV mode ma być wyłączony. Nie rób screenshotów przy
logowaniu i nie zapisuj sekretów ani profili przeglądarki. Netflix seeking musi
używać trusted clicks; bez bezpośredniego ustawiania video.currentTime, bo to
powodowało błąd M7375.

Git: identity 98przem <98przem@users.noreply.github.com>, krótkie nazwy commitów
małymi literami, bez Co-authored-by i bez informacji o AI. Bez force-push.
Commit/push dopiero po zaakceptowaniu partii zmian albo na moje polecenie.

Na start uruchom tylko szybkie kontrole składni:
python3 -m py_compile tv_mode.py steam_shortcut.py configure_services.py
bash -n install.sh uninstall.sh launch
node --check scripts/netflix-focus.js
node --check scripts/browser-focus.js

Potem podsumuj stan w kilku zdaniach i poproś mnie o test natywnego pada w
Xbox Cloud oraz powrotu do dashboardu przez Steam > Stop Game.
```
