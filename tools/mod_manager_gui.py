"""Desktop companion for the Mod Manager; no package code or installers are run."""
import json
import queue as messages
import threading
import tkinter as tk
import uuid
import webbrowser
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog, ttk
from mod_downloads import Queue
from mod_http import validate_url
from mod_manager import ROOT, catalog
from mod_sources import discover, sources
from mod_library import Library


class Manager:
    def __init__(self, root):
        self.root = root; self.events = messages.Queue(); self.busy = set()
        self.home = ROOT / 'userdata/mod-manager'
        self.home.mkdir(parents=True, exist_ok=True)
        self.downloads = self.home / 'downloads'
        self.queue = Queue(self.downloads)
        self.library = Library(self.home); self.game_exe = None
        root.title('Polish Little Fighters — Mod Manager (etap 2)'); root.geometry('960x700')
        tabs = ttk.Notebook(root); tabs.pack(fill='both', expand=True, padx=12, pady=10)
        library = ttk.Frame(tabs); network = ttk.Frame(tabs); downloads = ttk.Frame(tabs); installed = ttk.Frame(tabs)
        tabs.add(library, text='Katalog i import'); tabs.add(network, text='Źródła internetowe'); tabs.add(downloads, text='Pobieranie i historia')
        tabs.add(installed, text='Zainstalowane i profile')
        self.query = tk.StringVar(); ttk.Entry(library, textvariable=self.query).pack(fill='x', pady=6)
        self.query.trace_add('write', lambda *_: self.filter())
        self.mods = self.tree(library, ('name','category','author'), ('Nazwa','Kategoria','Autor'))
        self.mods.bind('<<TreeviewSelect>>', self.details)
        self.detail = tk.StringVar(value='Wybierz mod. Obecność w katalogu nie potwierdza zgodności ani dostępności.')
        ttk.Label(library, textvariable=self.detail, wraplength=900).pack(fill='x', pady=8)
        actions = ttk.Frame(library); actions.pack(fill='x')
        ttk.Button(actions, text='Strona wybranego moda', command=self.open_mod).pack(side='left', padx=3)
        ttk.Button(actions, text='Import własnego ZIP', command=self.import_file).pack(side='left', padx=3)
        ttk.Label(library, text='Import tworzy oddzielny pakiet lokalny. Włączysz go w zakładce Zainstalowane i profile. Zgodność pozostaje nieprzetestowana.', wraplength=900).pack(pady=8)
        self.source_list = sources(); self.source = tk.StringVar(value=self.source_list[0]['name'])
        ttk.Combobox(network, textvariable=self.source, values=[s['name'] for s in self.source_list], state='readonly').pack(fill='x', pady=6)
        ttk.Button(network, text='Odśwież wybrane źródło (maks. 2 strony)', command=self.refresh_source).pack(anchor='w')
        self.candidates = self.tree(network, ('name','kind'), ('Nazwa','Typ odnośnika'))
        self.found = []
        buttons = ttk.Frame(network); buttons.pack(fill='x')
        ttk.Button(buttons, text='Otwórz zaznaczoną stronę', command=self.open_candidate).pack(side='left', padx=3)
        ttk.Button(buttons, text='Dodaj zaznaczony link pliku do kolejki', command=self.enqueue_candidate).pack(side='left', padx=3)
        ttk.Label(network, text='Pośrednicy i skrócone URL wymagają ręcznego otwarcia. Nie obchodzimy CAPTCHA. Wyniki nie zmieniają automatycznie rejestru.', wraplength=900).pack(pady=8)
        direct = ttk.Frame(downloads); direct.pack(fill='x', pady=6)
        self.url = tk.StringVar(); ttk.Entry(direct, textvariable=self.url).pack(side='left', fill='x', expand=True)
        ttk.Button(direct, text='Dodaj bezpośredni HTTPS', command=self.enqueue).pack(side='right')
        self.jobs = self.tree(downloads, ('status','progress','mod'), ('Stan','Pobrano','Mod / identyfikator'))
        self.jobs.bind('<<TreeviewSelect>>', self.job_details)
        self.progress = ttk.Progressbar(downloads, maximum=100); self.progress.pack(fill='x', pady=5)
        self.problem = tk.StringVar(); ttk.Label(downloads, textvariable=self.problem, wraplength=900).pack(fill='x')
        buttons = ttk.Frame(downloads); buttons.pack(fill='x', pady=8)
        for title, action in [('Pobierz kolejkę', self.run_queue), ('Pauza', lambda: self.control('pause')), ('Wznów', lambda: self.control('resume')), ('Anuluj', lambda: self.control('cancel')), ('Import pobranego ZIP', self.import_download)]:
            ttk.Button(buttons, text=title, command=action).pack(side='left', padx=3)
        profile_row = ttk.Frame(installed); profile_row.pack(fill='x', pady=6)
        self.profile_id = tk.StringVar()
        self.profile_box = ttk.Combobox(profile_row, textvariable=self.profile_id, state='readonly', width=30)
        self.profile_box.pack(side='left', padx=3)
        ttk.Button(profile_row, text='Wybierz profil', command=self.select_profile).pack(side='left', padx=3)
        ttk.Button(profile_row, text='Nowy profil', command=self.new_profile).pack(side='left', padx=3)
        self.profile_name = tk.StringVar(); ttk.Label(installed, textvariable=self.profile_name).pack(anchor='w')
        self.packages = self.tree(installed, ('name','active','compatibility'), ('Pakiet','Włączony w profilu','Zgodność'))
        actions = ttk.Frame(installed); actions.pack(fill='x', pady=6)
        for title, action in [('Włącz', lambda: self.package_action('enable')), ('Wyłącz', lambda: self.package_action('disable')), ('Aktualizuj z ZIP', self.update_package), ('Eksportuj na Androida', self.export_android), ('Usuń z kopią', lambda: self.package_action('remove')), ('Przywróć wersję', self.restore_package)]:
            ttk.Button(actions, text=title, command=action).pack(side='left', padx=3)
        self.backup_id = tk.StringVar()
        self.backup_box = ttk.Combobox(installed, textvariable=self.backup_id, state='readonly')
        self.backup_box.pack(fill='x', pady=4)
        actions = ttk.Frame(installed); actions.pack(fill='x', pady=6)
        ttk.Button(actions, text='Pokaż plan uruchomienia', command=lambda: self.start_game(False)).pack(side='left', padx=3)
        ttk.Button(actions, text='Graj wybranym profilem', command=lambda: self.start_game(True)).pack(side='left', padx=3)
        ttk.Button(actions, text='Przywróć wybór modów z kopii', command=self.restore_profile).pack(side='left', padx=3)
        ttk.Label(installed, text='Dwie pełne konwersje LF2 mają konflikt katalogów. Usunięcie zachowuje lokalną kopię. Gra używa oddzielnych ustawień profilu.', wraplength=900).pack(pady=6)
        self.notice = tk.StringVar(value='Etap roboczy — bez testów. Pobieranie następuje wyłącznie na żądanie.')
        ttk.Label(root, textvariable=self.notice, wraplength=920).pack(fill='x', padx=12, pady=6)
        self.filter(); self.poll(); root.protocol('WM_DELETE_WINDOW', self.close)

    def tree(self, parent, columns, headings):
        area = ttk.Frame(parent); area.pack(fill='both', expand=True)
        tree = ttk.Treeview(area, columns=columns, show='headings', selectmode='browse')
        for column, heading in zip(columns, headings): tree.heading(column, text=heading); tree.column(column, width=220)
        scrollbar = ttk.Scrollbar(area, command=tree.yview); tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side='left', fill='both', expand=True); scrollbar.pack(side='right', fill='y')
        return tree

    def background(self, name, task):
        if name in self.busy: return
        self.busy.add(name); self.notice.set('W toku: ' + name)
        def work():
            try: self.events.put((name, task(), None))
            except Exception as error: self.events.put((name, None, str(error)))
        threading.Thread(target=work, name='mods-' + name, daemon=False).start()

    def filter(self):
        self.mods.delete(*self.mods.get_children())
        for row in catalog(self.query.get()): self.mods.insert('', 'end', iid=row['id'], values=(row['name'], row['category'], row['author'] or 'Niepotwierdzony'))

    def selected_mod(self):
        ids = self.mods.selection()
        return next((row for row in catalog() if ids and row['id'] == ids[0]), None)

    def details(self, *_):
        row = self.selected_mod()
        if row: self.detail.set(row['name'] + ' | wersja: ' + (row['version'] or '?') + ' | źródło: ' + (row['source'] or '?') + '\nZgodność: nieprzetestowana. Licencja: ' + (row['license'] or 'niepotwierdzona') + '\n' + (row.get('page_url') or 'Brak zweryfikowanej strony.'))

    def open_link(self, url):
        if not url: self.notice.set('Brak potwierdzonego adresu. Użyj zakładki źródeł.'); return
        self.background('otwieranie strony', lambda: webbrowser.open(validate_url(url)))

    def open_mod(self):
        row = self.selected_mod()
        if row: self.open_link(row.get('download_page_url') or row.get('page_url'))

    def refresh_source(self):
        source = next(s for s in self.source_list if s['name'] == self.source.get())
        self.background('źródła', lambda: discover(source['id']))

    def candidate(self):
        selected = self.candidates.selection()
        return self.found[int(selected[0])] if selected else None

    def open_candidate(self):
        row = self.candidate()
        if row: self.open_link(row['page_url'])

    def enqueue_candidate(self):
        row = self.candidate()
        if not row: return
        if row['kind'] != 'download_candidate':
            self.notice.set('To strona lub odnośnik pośredni. Otwórz ją i wybierz plik ręcznie.'); return
        self.url.set(row['page_url']); self.enqueue()

    def enqueue(self):
        url = self.url.get().strip()
        def task():
            queue = Queue(self.downloads)
            try: return queue.add(url)
            finally: queue.close()
        self.background('dodawanie do kolejki', task)

    def run_queue(self):
        def task():
            queue = Queue(self.downloads)
            try: queue.run(lambda event: None)
            finally: queue.close()
        self.background('pobieranie', task)

    def control(self, action):
        selected = self.jobs.selection()
        if not selected: return
        try:
            self.queue.control(selected[0], action)
            self.notice.set('Zapisano: ' + action + '. Wznowioną kolejkę uruchom przyciskiem Pobierz kolejkę.')
        except Exception as error: self.notice.set(str(error))

    def job_details(self, *_):
        selected = self.jobs.selection()
        if not selected: return
        row = self.queue.job(selected[0])
        self.problem.set(row['error'] or row['result_path'] or '')
        self.progress['value'] = row['received'] * 100 / row['total'] if row['total'] else 0

    def import_file(self):
        path = filedialog.askopenfilename(title='Wybierz paczkę zasobów LF2', filetypes=[('Archiwum ZIP','*.zip')])
        if path: self.import_path(path)

    def import_download(self):
        selected = self.jobs.selection()
        if not selected: return
        row = self.queue.job(selected[0])
        if row['status'] != 'completed' or not row['result_path']:
            self.notice.set('Najpierw zakończ pobieranie.'); return
        self.import_path(row['result_path'])

    def import_path(self, path):
        if Path(path).suffix.lower() != '.zip': self.notice.set('Importer obsługuje obecnie tylko ZIP; RAR i 7z pozostają pobrane.'); return
        row = self.selected_mod()
        self.request_import_preview(path, row['name'] if row else None, row['id'] if row else None)

    def request_import_preview(self, path, name=None, catalog_id=None, update_id=None):
        path = Path(path).resolve()
        def preview():
            info = path.stat()
            return {'path': str(path), 'size': info.st_size, 'mtime': info.st_mtime_ns,
                    'preview': self.library.preview(path), 'name': name, 'catalog_id': catalog_id, 'update_id': update_id}
        self.background('podgląd importu', preview)

    def show_import_preview(self, result):
        report = result['preview']
        window = tk.Toplevel(self.root); window.title('Podgląd danych przed instalacją'); window.geometry('820x560')
        view = tk.Text(window, wrap='word'); view.pack(fill='both', expand=True)
        lines = ['Plik: ' + result['path'], 'Plików danych: ' + str(len(report['files'])),
                 'Rozmiar danych: ' + str(report['total_bytes']) + ' B',
                 'Katalogi LF2: ' + ', '.join(report['legacy_roots']),
                 'Pliki pomijane (nie będą wypakowane): ' + str(len(report['excluded'])),
                 'Zgodność: NIEPRZETESTOWANA. Nie uruchamiamy kodu z archiwum.',
                 'Wpis katalogu (wybór użytkownika, nie dowód pochodzenia): ' + (result['name'] or 'bez przypisania'), '', 'Dane (pierwsze 100):']
        lines += [item['name'] + ' (' + str(item['bytes']) + ' B)' for item in report['files'][:100]]
        lines += ['', 'Pomijane (pierwsze 30):'] + [item['name'] for item in report['excluded'][:30]]
        view.insert('1.0', '\n'.join(lines)); view.configure(state='disabled')
        def install():
            info = Path(result['path']).stat()
            if info.st_size != result['size'] or info.st_mtime_ns != result['mtime']:
                self.notice.set('Plik zmienił się od podglądu. Wybierz go ponownie.'); window.destroy(); return
            window.destroy()
            self.background('import', lambda: self.library.install(result['path'], result['name'], result['catalog_id'], result['update_id']))
        controls = ttk.Frame(window); controls.pack(fill='x', pady=5)
        ttk.Button(controls, text='Anuluj', command=window.destroy).pack(side='right', padx=6)
        if len(report['legacy_roots']) == 1:
            ttk.Button(controls, text='Aktualizuj dane z kopią' if result['update_id'] else 'Importuj tylko dane', command=install).pack(side='right', padx=6)

    def select_profile(self):
        profile = self.profile_id.get()
        if profile: self.background('profil', lambda: self.library.profile(profile, select=True))

    def new_profile(self):
        name = simpledialog.askstring('Nowy profil', 'Nazwa profilu:', parent=self.root)
        if name:
            profile_id = 'profile-' + uuid.uuid4().hex[:10]
            self.background('profil', lambda: self.library.profile(profile_id, name, [], select=True))

    def package_action(self, action):
        selected = self.packages.selection()
        if not selected: return
        pack_id = selected[0]; profile_id = self.library.read()['selected_profile']
        if action == 'remove':
            if not messagebox.askyesno('Usuń pakiet', 'Usunąć pakiet ze wszystkich profili i zachować go w kopii do przywrócenia?'): return
            task = lambda: self.library.remove(pack_id)
        else: task = lambda: self.library.toggle(pack_id, action == 'enable', profile_id)
        self.background('pakiety', task)

    def update_package(self):
        selected = self.packages.selection()
        if not selected: return
        path = filedialog.askopenfilename(title='Nowa wersja pakietu (ZIP)', filetypes=[('Archiwum ZIP','*.zip')])
        if path:
            record = self.library.read()['installed'][selected[0]]
            self.request_import_preview(path, record['name'], record.get('catalog_id'), selected[0])

    def export_android(self):
        selected=self.packages.selection()
        if not selected:return
        pack_id=selected[0]
        path=filedialog.asksaveasfilename(title='Zapisz zweryfikowaną paczkę transferową (bez potwierdzenia zgodności)',
            defaultextension='.lfmod.zip',initialfile=pack_id+'.lfmod.zip',filetypes=[('Paczka Androida','*.lfmod.zip')])
        if path:self.background('eksport Android',lambda:self.library.export_android(pack_id,path))

    def restore_package(self):
        token = self.backup_id.get().split(' | ', 1)[0]
        if token: self.background('pakiety', lambda: self.library.restore(token))

    def restore_profile(self):
        snapshots = sorted((self.home / 'history').glob('snapshot-*.json'), key=lambda item: item.stat().st_mtime, reverse=True)
        if not snapshots: self.notice.set('Brak kopii ustawień profili.'); return
        window = tk.Toplevel(self.root); window.title('Przywróć profile'); window.geometry('700x360')
        choices = tk.Listbox(window); choices.pack(fill='both', expand=True)
        for path in snapshots:
            data = json.loads(path.read_text(encoding='utf-8'))
            choices.insert('end', str(data.get('snapshot_time','')) + ' | ' + str(data.get('snapshot_operation','')))
        def restore():
            selected = choices.curselection()
            if selected:
                token = snapshots[selected[0]].stem; window.destroy()
                self.background('profil', lambda: self.library.snapshot_restore(token))
        ttk.Button(window, text='Przywróć zaznaczoną kopię', command=restore).pack(pady=5)

    def start_game(self, launch):
        if not self.game_exe or not Path(self.game_exe).is_file():
            self.game_exe = filedialog.askopenfilename(title='Wybierz LittleFighters.exe z zaufanej paczki gry (nie instalator)', filetypes=[('Gra Windows','*.exe')])
        if not self.game_exe: return
        profile = self.library.read()['selected_profile']
        if launch:
            self.background('uruchamianie gry', lambda: self.library.launch(self.game_exe, ROOT / 'engine/scripts', profile))
        else:
            try:
                plan = self.library.launch_plan(self.game_exe, ROOT / 'engine/scripts', profile)
                messagebox.showinfo('Plan — bez uruchamiania', json.dumps(plan, ensure_ascii=False, indent=2))
            except Exception as error: self.notice.set(str(error))

    def refresh_library(self):
        data = self.library.read(); active = data['selected_profile']
        self.profile_box['values'] = list(data['profiles'])
        if self.profile_id.get() not in data['profiles']: self.profile_id.set(active)
        self.profile_name.set('Aktywny profil: ' + data['profiles'][active]['name'])
        ids = set(data['installed'])
        for pack_id in self.packages.get_children():
            if pack_id not in ids: self.packages.delete(pack_id)
        for pack_id, row in data['installed'].items():
            values = (row['name'], 'TAK' if pack_id in data['profiles'][active]['mods'] else 'NIE', 'Nieprzetestowany')
            if self.packages.exists(pack_id): self.packages.item(pack_id, values=values)
            else: self.packages.insert('', 'end', iid=pack_id, values=values)
        backups = [token + ' | ' + row['record']['name'] + ' | ' + row['reason'] for token, row in data['archived'].items()]
        self.backup_box['values'] = backups
        if self.backup_id.get() not in backups: self.backup_id.set(backups[-1] if backups else '')

    def poll(self):
        while True:
            try: name, result, error = self.events.get_nowait()
            except messages.Empty: break
            self.busy.discard(name)
            self.notice.set(str(error) if error else 'Zakończono: ' + name)
            if name == 'profil' and not error: self.profile_id.set(self.library.read()['selected_profile'])
            if name == 'podgląd importu' and result and not error: self.show_import_preview(result)
            if name == 'źródła' and result:
                self.found = result['projects']; self.candidates.delete(*self.candidates.get_children())
                for index, row in enumerate(self.found): self.candidates.insert('', 'end', iid=str(index), values=(row['name'], row['kind']))
                report = self.home / ('source-' + result['source'] + '.json')
                report.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
                self.notice.set('Odnośników: ' + str(len(self.found)) + (' | ' + '; '.join(e['message'] for e in result['errors']) if result['errors'] else ''))
        for row in self.queue.jobs():
            values = (row['status'], f"{row['received'] / 1048576:.1f} / {row['total'] / 1048576:.1f} MiB" if row['total'] else f"{row['received'] / 1048576:.1f} MiB", row['mod_id'] or row['id'])
            if self.jobs.exists(row['id']): self.jobs.item(row['id'], values=values)
            else: self.jobs.insert('', 'end', iid=row['id'], values=values)
        self.job_details()
        try: self.refresh_library()
        except Exception as error: self.notice.set('Biblioteka: ' + str(error))
        self.root.after(1000, self.poll)

    def close(self):
        for row in self.queue.jobs():
            if row['status'] == 'downloading': self.queue.control(row['id'], 'pause')
        self.queue.close(); self.root.destroy()


if __name__ == '__main__':
    window = tk.Tk(); Manager(window); window.mainloop()
