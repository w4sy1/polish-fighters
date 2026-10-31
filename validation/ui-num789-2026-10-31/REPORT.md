# Interfejs i sterowanie — 2026-10-31

Wersja do uruchomienia: engine/out/LittleFighters-ui-num789-2026-10-31/LittleFighters.exe.
Poprzedni folder i ZIP zachowano. Nie wykonano commita, push ani publikacji GitHub.

## Zmiany

- Domyślne klawisze LF2 pozostają oryginalne we wszystkich profilach bez zapisanych ustawień.
- Dodano opcjonalny preset WASD + Num7 (atak), Num8 (skok), Num9 (blok).
- Zachowano pozostałe presety i zapisane ustawienia. Konflikty z innymi graczami wymagają jawnego rozwiązania w panelu.
- Poprawiono polskie znaki i nazwy menu, panelu sterowania oraz etykiety Num.
- Polski jest domyślnym językiem nowej konfiguracji; zapisany wybór języka ma pierwszeństwo.
- Uzupełniono tłumaczenia wyboru postaci i usunięto dodatkowe chińskie linie dołączania w języku polskim.
- Menu otrzymało ciemne panele, czerwone akcenty i pasek wskazówek; poprawiono położenie instrukcji sterowania.
- Przechwytywanie obrazu w testach przekazuje rzeczywistą dostępność tekstu TTF, a dekoder usuwa tę informację z akcji graczy.

## Pliki źródłowe i testy

engine/scripts/polish-fighters/{hub.lua,hub_launch.lua,input_settings.lua};
engine/scripts/base/game/options.lua; engine/scripts/base/i18n/polish.lua;
engine/scripts/base/ui/controls.lua; engine/src/app/application.cpp;
tests/{hub_input_test.lua,ui_locale_test.lua}; tools/probe_ui_num789.py.
PROJECT-STATUS.md zawiera bieżący stan etapu.

## Weryfikacja

- Build Windows Release: PASS.
- Składnia 106 plików Lua i 20 zestawów testowych: PASS.
- Natywny test menu, zapis kodów 103/104/105, ponowny odczyt, profil Polish Fighters i wybór postaci: PASS.
- Rzeczywiste zrzuty SDL: main/frame.bmp, controls/frame.bmp, selection/frame.bmp — obejrzane.
- Test oryginalnego sterowania, anulowania edycji, zachowania zapisanego języka oraz izolacji znacznika TTF: PASS.
- git diff --check: PASS. Repozytorium zawiera też wcześniejsze zmiany innych etapów.

## Granice i pozostałe prace

Nie wykonano fizycznego testu pada, ręcznej rozgrywki, testu Androida ani pełnych kampanii.
Interfejs poprawiono częściowo: nie jest to jeszcze kompletny redesign wszystkich ekranów ani audyt wszystkich tłumaczeń.
Pozostają wspólna pula postaci modów, pobieranie/aktualizacja pakietów z GitHuba,
pełne animacje i balans własnych postaci, pozostałe braki Bleach/DBZ oraz testy całych przygód,
Android, internetowe pokoje i Bluetooth. Ta lista kontynuuje poprzedni stan projektu;
te funkcje nie zostały w tym etapie ponownie poddane pełnemu audytowi.
Zakres bieżącego etapu odpowiada prośbie o Num7/8/9, poprawki polskiego interfejsu i jego wyglądu;
cały projekt pozostaje w rozwoju.
