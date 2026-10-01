# Start po czystej instalacji SteamOS

## Najprostsza metoda: GitHub

1. Zainstaluj SteamOS i wykonaj wszystkie aktualizacje systemu.
2. Przejdź do Desktop Mode.
3. Ustaw hasło użytkownika poleceniem `passwd`, jeżeli system jeszcze go nie ma.
4. Zainstaluj Google Chrome z Discover.
5. Opcjonalnie zainstaluj VacuumTube z Discover.
6. Otwórz Konsole.
7. Sklonuj i zainstaluj TV mode:

   ```bash
   git clone https://github.com/98przem/tv-mode.git ~/tv-mode
   cd ~/tv-mode
   ./install.sh
   ```

8. W instalatorze wybierz potrzebne usługi.
9. Uruchom ponownie Steam.
10. Otwórz właściwości skrótu `TV mode`.
11. Ustaw `Kontroler` → `Wyłącz Steam Input`.
12. Uruchom TV mode i zaloguj się oddzielnie do każdej usługi.

## Gdy brakuje zależności

Najpierw uruchom instalator. Nie zmieniaj bazowego systemu, jeżeli wszystko
działa. Jeśli zgłosi brak Python GTK, SDL albo `websockets`, użyj:

```bash
sudo steamos-readonly disable
sudo pacman -S --needed python python-gobject gtk4 python-websockets sdl2-compat xdotool git flatpak
sudo steamos-readonly enable
```

Aktualizacja SteamOS może usunąć pakiety dodane do systemu bazowego. W takim
przypadku powtórz wyłącznie instalację brakujących pakietów.

## Metoda offline

Skopiuj `tv-mode-handoff-2026-10-01.tar.gz` do katalogu domowego i sprawdź sumę
SHA-256 podaną przy przekazaniu paczki. Następnie uruchom:

```bash
cd ~
tar -xzf tv-mode-handoff-2026-10-01.tar.gz
cd ~/Applications/tv-mode
./install.sh
```

## Pierwszy test

1. Sprawdź nawigację dashboardu.
2. Sprawdź Netflix.
3. Sprawdź Apple TV+ i Canal+.
4. Uruchom Xbox Cloud i potwierdź natywne wykrycie pada.
5. Wyjdź z Xbox Cloud przez menu Steam → `Stop Game`.
6. Potwierdź, że pad ponownie działa w dashboardzie.

W Xbox Cloud TV mode nie może przechwytywać ani tłumaczyć żadnego wejścia.

## Przekazanie pracy agentowi

Otwórz `handoff/AI_PROMPT.md` i wklej zawarty tam prompt do nowego agenta.
Poproś go także o przeczytanie `handoff/HANDOFF.md`, `handoff/WORK_HISTORY.md`
oraz dokumentów w `docs/`.

## Usuwanie

Standardowe usunięcie zachowujące konfigurację i loginy:

```bash
~/.local/share/tv-mode/uninstall.sh
```

Pełne usunięcie wraz z konfiguracją i profilami przeglądarki:

```bash
~/.local/share/tv-mode/uninstall.sh --purge-all
```
