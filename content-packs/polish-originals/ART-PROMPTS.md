# Grafika czterech postaci — ImageGen

Narzędzie: wbudowane `image_gen.imagegen`, transparent_background=true, edycja na podstawie właściwej karty koncepcyjnej. Poniżej zapis specyfikacji generacji; nie jest to gwarancja, że model dotrzymał geometrii.

Wspólna specyfikacja: production 2D game sprite atlas, transparent RGBA, 1024×1024, eight columns and eight rows of 128×128 cells, no gaps, text, grid, floor or panels; side view facing RIGHT; consistent center x64, feet y116, body about74px (boss90px). Eight poses per row: ready/breathing/walking; run/jump; basic/heavy attacks; four hurt and four block; four fall and four lying; four get-up and four cast/summon; four dash and four aerial attacks; five ultimate/cast and three isolated effect sprites. Distinct complete poses with enough transparent padding. Preserve the reference character's identity.

## Wasyl

Reference: „Polish Fighters_ Wasyl kontra Skibidi Sigma Tata.png”. Adult man, short dark cropped hair, small beard, black tracksuit with white triple stripes, white sneakers. Fast boxing/kickboxing punches, elbow strikes, spinning kicks, aerial attacks, flash step, blue clone/summon and blue finishing-combo effects. Last three effect sprites: blue projectile, blue crescent, small blue burst. Generated original: `exec-44d61b07-ca38-496a-8ad3-911a70e64984.png` → `art/w.png`.

## Szymonoko / SZ

Reference: „Szymonoko_ Mroczny bohater retro bijatyki.png”. Friendly stylized round pale drawn face, red hooded tracksuit, white spikes/ears around the hood, two black toy-like pistols. Walking/running, dual gun attack/burst, roll, hurt/block/fall/get-up, clone summon, teleport and dual finishing attacks. Last three isolated effects: red bullet, red burst, clone glow. Generated original: `exec-91c13bf6-efb3-4455-9c98-481162061832.png` → `art/s.png`.

## Mega Ninja Jaś

Reference: „Karta umiejętności Mega Ninja Jasia.png”. Young blond boy with tousled hair, royal blue long sleeve shirt with a white motorcycle motif, navy pants, blue shoes and glowing white/blue toy katana. Sword cuts, sheathe-draw dash, eight-sword throwing, green slime casting, sword surfing in air and eight-sword hurricane. Last three isolated effects: blue-white sword, green slime puddle, cyan crescent. Generated original: `exec-5ef26c42-9a56-47a9-88ce-f901aa6854d9.png` → `art/j.png`.

## Skibidi Sigma Tata

Reference: „Polish Fighters_ Wasyl kontra Skibidi Sigma Tata.png”. Adult dad with sunglasses, gold crown and chain, black tracksuit, red royal cape with white trim, white cartoon toilet throne and flaming sceptre. Throne movement, fire/orb casting, jump/stomp, fire wave, cartoon worm, tiny toilet-helper summon, orb rain and phase-two fire aura. Last three isolated effects: orange fireball, brown cartoon worm, tiny toilet helper. Generated original: `exec-ef12b3e9-92fe-4e61-b049-fb8d83e70ea8.png` → `art/b.png`.

## Rzeczywisty wynik i integracja

Wszystkie cztery wyniki mają 1254×1254 RGBA. Model nie zachował sztywnej siatki, szczególnie w dolnych rzędach Wasyla. Ustalono rzeczywiste przedziały rzędów i ręczne wyjątki w generatorze metadanych. PNG nie przycinano, nie skalowano i nie przemalowywano. Skalowanie i odbicie wykonuje renderer silnika przy rysowaniu. Diagnostyczny `render.bmp` powstał przez produkcyjny adapter SDL; nie zastępuje atlasów gry.
