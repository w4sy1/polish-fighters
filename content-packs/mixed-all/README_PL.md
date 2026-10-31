# Polish Fighters — wspólna pula (eksperymentalna)

Budowanie z istniejących lokalnych importów:

    .build-venv/Scripts/python.exe tools/build_mixed_pack.py

Oryginały nie są modyfikowane. Wygenerowane `assets/` pozostają lokalne.
Pakiet wymaga osobno załadowanych `polish-originals` i bazowego `polish-fighters`.
Przycisk w katalogu menu uruchamia komplet zależności automatycznie.

Nowy katalog ma unikalne ID. Odwołania `opoint.oid`, stany transformacji 3000–3999
i ścieżki zasobów są przepisywane w osobnych kopiach. Brakujące cele otrzymują
odrębne, nieistniejące ID; nie są zastępowane przypadkowym obiektem innego moda.

To pierwszy port wspólnych walk, a nie pełna zgodność wszystkich autorskich silników:
mechaniki EXE, AngelScript, wyspecjalizowane porównania starych ID w silniku LF2,
autorskie AI i kampanie mieszane wymagają dalszej pracy. Kampanie profili źródłowych
pozostają dostępne osobno. W trybie mieszanym używane są standardowe etapy LF2.
Oryginalne pliki i obecne braki Bleach nie zostały odtworzone ani zastąpione.
