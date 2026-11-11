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
# Remonoko — 2026-11-06

Built-in imagegen, reference: Remonoko concept card based on Remek's drawing.
Prompt: Create a production 2D game sprite sheet of REMONOKO, matching the boy
character in reference: short brown hair, red suit, huge steel fist on one arm,
futuristic fictional pistol in opposite hand. Retro Little Fighter style,
readable small cartoon fighter. TRANSPARENT BACKGROUND. EXACT 8 columns by 8
rows, 64 equal square cells, square image 1024x1024. No text, no labels, no grid
lines. Each pose centered in its own cell with empty padding, full body, same
character scale and feet baseline. All face right. Rows: 1 eight standing/idle
variations; 2 eight walking/running poses; 3 eight punch/metal fist and kick
attacks; 4 eight hurt/block/jump poses; 5 eight falling and lying poses; 6 eight
rolling and teleport/dash poses; 7 four airborne attacks followed by four stone
mech full-body poses (same boy encased in bulky gray rock armor with red accents
and massive stone fists); 8 first five poses firing futuristic pistol /
transformed huge arm cannon / fire stream, final three cells ONLY separate
effects: orange small energy bullet, huge glowing orange energy projectile,
small red glowing ground trap. Do not draw multiple characters in a cell. No
scenic background, no contact shadow, no card design, no text. Consistent pixel
art animation poses. Stylized fantasy combat without blood.

Actual output is 1254x1254 RGBA, preserved verbatim as `art/r.png`. The requested
1024 resolution was not the tool's final resolution; layout uses measured cuts.

## Dedicated mech and hero FX — 2026-11-07

Generated bitmap originals preserved byte-for-byte: `art/m.png` (1262x1246 RGBA,
8x8 mech poses: idle, walk/run, punches, fire palms, block/hurt, jump/death,
dash/slam/spin, flame effects) and `art/e.png` (1254x1254 RGBA, 8x8: destructible
toilet turrets, orange fire, violet eclipse, cyan lightning, healing, rings,
clone smoke and teleport flashes). Layout uses measured source cuts and
per-picture scales; 1024 requested resolution was not the delivered image size.
Transparent backgrounds; no new voices. `layout.lua` also exposes `f` (mech
fire effects) and `t` (toilet loop) as aliases of these unchanged PNGs.
