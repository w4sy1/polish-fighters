"""Summarize actual test artifacts and synchronize this local portable build."""
import hashlib,json,re,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'validation/remaining-mechanics-2026-10-30'
STAGE=ROOT/'engine/out/PolishFighters-remaining-2026-10-30'
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    lua=(OUT/'lua-tests-final.log').read_text()
    assert 'PASS syntax: 90 files' in lua and len(re.findall(r'^PASS \w+_test\.lua$',lua,re.M))==17
    assert 'Ran 48 tests' in (OUT/'python-tests.log').read_text() and 'OK (skipped=1)' in (OUT/'python-tests.log').read_text()
    assert 'PASS: disconnect and stalled-peer timeout abort' in (OUT/'cpp-tests-final.log').read_text()
    summary=json.loads((OUT/'all-final/native-summary.json').read_text())
    # DBZ was retested after its isolated [MU] handler and explicit base-music fallback.
    latest=json.loads((OUT/'dbz-final/native-summary.json').read_text())
    assert latest['binary_sha256']==summary['binary_sha256']
    tests=[t for t in summary['tests'] if t['pack']!='dbz']+latest['tests'];assert len(tests)==388
    (OUT/'combined-native-results.json').write_text(json.dumps({'scope':'Original full sweep plus all 76 DBZ cases repeated after isolated music changes; 120-frame starts, not complete gameplay.',
        'binary_sha256':summary['binary_sha256'],'sources':['all-final/native-summary.json','dbz-final/native-summary.json'],'tests':tests},indent=2)+'\n')
    assert summary['binary_sha256']==digest(STAGE/'openlf2.exe')
    modes=json.loads((OUT/'dbz-modes/summary.json').read_text())
    assert modes['binary_sha256']==summary['binary_sha256']
    rows=[]
    for pack in dict.fromkeys(t['pack'] for t in tests):
        cases=[t for t in tests if t['pack']==pack]
        maps=[t for t in cases if t['kind']=='map'];stages=[t for t in cases if t['kind']=='stage']
        rows.append({'pack':pack,'maps_passed':sum(t['pass'] for t in maps),'maps':len(maps),
                     'stages_passed':sum(t['pass'] for t in stages),'stages':len(stages)})
    failed=[t for t in tests if not t['pass']]
    report='# Zgodność DBZ / NTSD / One Piece i oględziny arkuszy — 2026-10-30\n\n'
    report+='Własny Windows EXE: `engine/out/PolishFighters-remaining-2026-10-30/openlf2.exe`.\n\nSHA256: `'+summary['binary_sha256']+'`.\n\n'
    report+='## Wyniki natywne\n\n| Pakiet | Mapy | Starty etapów |\n|---|---:|---:|\n'
    for row in rows:report+='| {pack} | {maps_passed}/{maps} | {stages_passed}/{stages} |\n'.format(**row)
    report+='\nKażdy przypadek: 120 klatek headless, odczyt i rysowanie zasobów, własny silnik, aktor QA Deep i autorscy przeciwnicy/sceny. Indeks: combined-native-results.json. Dodatkowo '+str(sum(t['pass'] for t in modes['tests']))+'/'+str(len(modes['tests']))+' wariantów DBZ. To nie są ukończone kampanie, testy wszystkich postaci, potwierdzenie zgodności obrazu ani pełnego odsłuchu.\n\n'
    report+='## Zmienione elementy\n\n'
    report+='- DBZ: klatki 0–998 i do 32 itr; bazowy profil zachowuje 400/16. Autorskie 14 scen i 50 wariantów, geometria, warstwy respond, opoint/arest, 62 powiązania etapów z bg/mode. Dane i źródłowe sumy: content-packs/dbz/scene-modes.json oraz stage-scenes.json.\n'
    report+='- NTSD: 364 literały w 37 DAT przeliczone według własnego programu wywołującego zainstalowany x86 VC80 sscanf. To nie arbitralne przycinanie. Oryginały i nagłówki zachowano; ponowna kontrola CRT, wszystkich pól i sum: ntsd-normalization-verification.json.\n'
    report+='- DBZ muzyka: [MU] obsłużono jako stop/unload na podstawie statycznego przepływu oryginalnego kodu (music-sentinel-proof.json). Brakujący standardowy bgm/stage4.wma otrzymał jawny zamiennik z przypiętego bazowego LF2 (inherited-base-music.json); to nie odzyskane nagranie DBZ.\n'
    report+='- One Piece: dekoder FFmpeg wmalossless; wszystkie sześć oryginalnych plików ASF/WMA ma tag 0x0163. Audio nie transkodowano. Cztery dawne blokady startu usunięte.\n'
    report+='- Obejrzano 11 arkuszy (Bleach6/Kate2/Reinforced3). Szczegóły: VISUAL-REVIEW.md. Nie odtworzono brakujących rysunków.\n\n'
    report+='## Nierozwiązane — zakres nie jest ukończony\n\n'
    report+='- Bleach284/action83 i151/action30: oba ID nieobecne w autorskim katalogu. Audyt wszystkich123 DAT wskazuje18/74 kandydatów z samym numerem akcji; to nie potwierdza tożsamości. weapon3.dat nie zawiera akcji30. Nie dodano zgadywanego celu. Dowód: content-packs/bleach/missing-object-audit.json.\n'
    report+='- Starszy plik2.0 Final jest wymieniony na [stronie autora](https://bleachbankaibr.webnode.page/download/versoes-anteriores/), lecz wskazane 4shared/uploadmirrors nie dostarczyły archiwum. Nie odzyskano z nich danych.\n'
    report+='- DBZ: nieprzeniesione pełna semantyka questów, selektory lustrzanych przeciwników8001–8008, zmiany scen między fazami i AI AngelScript. Start Mirror Match po naprawie muzyki nie dowodzi obecności właściwych lustrzanych przeciwników. Nadal brakuje common/kiball_pink.png, a autorskiego stage4.wma nie odzyskano.\n'
    report+='- Android: zmiany wspólnego kodu są w źródłach; nie wykonano nowego natywnego buildu ARM ani testu na telefonie.\n\n'
    report+='## Testy i pliki\n\nPrzegląd388 przypadków oraz pełne powtórzenie76 przypadków DBZ po zmianie obsługi muzyki. Python:48 testów,47 OK/1 pominięty (symlink Windows). LuaJIT:17 zestawów i składnia90 plików. MSVC:6 zestawów C++; TCP2–8 procesów, rozłączenie i timeout OK. Logi w tym katalogu. Oryginalnych EXE/DLL nie uruchamiano.\n\n'
    report+='Zmiany kodu: engine/conanfile.py, engine/include/openlf2/resources/object_data.hpp, engine/src/resources/object_data.cpp, engine/src/app/application.cpp, content-packs/dbz/*.lua i package.manifest,37 lokalnych DAT NTSD oraz metadane i narzędzia testowe/odzyskiwania. Dokładny diff pozostaje w Git.\n\n'
    report+='Kopia sprzed zmian: ../baseline-remaining-mechanics-2026-10-30/. Starsze paczki pozostają osobno. Nie wykonano commitu, push ani release w tym etapie.\n'
    (OUT/'REPORT.md').write_text(report,encoding='utf-8')
    totals={'binary_sha256':summary['binary_sha256'],'packs':rows,'failed_starts':failed,'dbz_modes_passed':sum(t['pass'] for t in modes['tests'])}
    (OUT/'results.json').write_text(json.dumps(totals,indent=2)+'\n')
    status=ROOT/'PROJECT-STATUS.md';old=status.read_text('utf-8')
    old=re.sub(r'<!-- remaining-mechanics:start -->.*?<!-- remaining-mechanics:end -->\s*','',old,flags=re.S)
    prefix='<!-- remaining-mechanics:start -->\n# Aktualizacja mechanik — 2026-10-30\n\n'
    prefix+=str(sum(r['maps_passed'] for r in rows))+'/'+str(sum(r['maps'] for r in rows))+' map oraz '+str(sum(r['stages_passed'] for r in rows))+'/'+str(sum(r['stages'] for r in rows))+' startów etapów przeszło test120 klatek na nowym Windows EXE. DBZ50/50 wariantów. NTSD25/25 i One Piece25/25 startów.\n\n'
    prefix+='Bleach284/83 i151/30 pozostają nieodzyskane. DBZ: pełne questy, mirror/8001–8008, przejścia scen i AI nadal nieprzeniesione; stage4.wma to jawny zamiennik z bazowego LF2. 11 arkuszy obejrzano; brakujących rysunków nie odtworzono. Pełnej rozgrywki i Android ARM nie potwierdzono.\n\nRaport: validation/remaining-mechanics-2026-10-30/REPORT.md. Nowy build: engine/out/PolishFighters-remaining-2026-10-30/. Testy Python48(47OK/1skip), Lua17/składnia90, C++6/TCP2–8.\n<!-- remaining-mechanics:end -->\n\n'
    status.write_text(prefix+old,encoding='utf-8')
    config=ROOT/'config/project.json';data=json.loads(config.read_text())
    data['last_validation']='2026-10-30';data['source_work']['pack_validation']='validation/remaining-mechanics-2026-10-30/REPORT.md'
    for pack in data['packs']:
        match=next((row for row in rows if row['pack']==pack['id']),None)
        if match:pack['status']='experimental; {maps_passed}/{maps} map and {stages_passed}/{stages} stage-start warmups passed on current Windows engine; full gameplay not verified'.format(**match)
    data['remaining_mechanics']={'report':data['source_work']['pack_validation'],'bleach_missing_targets':['284/action83','151/action30'],'dbz_unported':['quest semantics','mirror selectors8001-8008','between-phase scene transitions','AngelScript AI'],'visual_sheets_reviewed':11,'missing_art_restored':False}
    config.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    # Synchronize only changed pack metadata/Lua. Assets were staged by the build.
    for pack in (ROOT/'content-packs').iterdir():
        if not pack.is_dir():continue
        target=STAGE/'content-packs'/pack.name
        if not target.is_dir():continue
        for source in pack.iterdir():
            if source.is_file():shutil.copy2(source,target/source.name)
    inherited=json.loads((ROOT/'content-packs/dbz/inherited-base-music.json').read_text())
    inherited_target=STAGE/'content-packs/dbz'/inherited['asset']
    inherited_target.parent.mkdir(exist_ok=True,parents=True)
    shutil.copy2(ROOT/'content-packs/dbz'/inherited['asset'],inherited_target)
    assert digest(inherited_target)==inherited['asset_sha256']
    shutil.copy2(status,STAGE/status.name);shutil.copy2(OUT/'REPORT.md',STAGE/'MECHANICS-REPORT.md')
    for entry in json.loads((ROOT/'content-packs/ntsd/vc80-integer-normalization.json').read_text())['files']:
        assert digest(STAGE/'content-packs/ntsd'/entry['asset'])==entry['after_sha256']
    staged=[{'path':p.relative_to(STAGE).as_posix(),'bytes':p.stat().st_size,'sha256':digest(p)} for p in STAGE.rglob('*') if p.is_file() and 'userdata' not in p.relative_to(STAGE).parts]
    (OUT/'portable-files.json').write_text(json.dumps(staged,indent=2)+'\n')
    print(json.dumps(totals,indent=2))
if __name__=='__main__':main()
