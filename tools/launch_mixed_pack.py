"""Select installed content packs, build a temporary mixed profile and launch Windows."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import subprocess
import tempfile
import tkinter as tk
from tkinter import ttk

from build_mixed_pack import PACKS, build_selection


def play(installation, installer, packs):
    with tempfile.TemporaryDirectory(prefix='polish-fighters-mix-') as directory:
        output = Path(directory) / 'package'
        content = installation / 'content-packs'
        build_selection(packs, content, output)
        subprocess.run(
            [
                str(installation / 'openlf2.exe'), '--installer', str(installer),
                '--scripts', str(installation / 'scripts'), '--mod',
                str(content / 'polish-originals'), '--mod', str(output),
            ],
            cwd=installation,
            check=True,
        )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('installation', type=Path, help='directory containing openlf2.exe')
    parser.add_argument('--installer', type=Path, required=True, help='original LF2 v2.0a installer')
    args = parser.parse_args()
    installation, installer = args.installation.resolve(), args.installer.resolve()
    content = installation / 'content-packs'
    for needed in (
        installation / 'openlf2.exe',
        installation / 'scripts/base/package.manifest',
        content / 'polish-originals/package.manifest',
        installer,
    ):
        if not needed.is_file():
            parser.error(f'Brak pliku: {needed}')

    installed = [pack for pack in PACKS if (content / pack / 'package.manifest').is_file()]
    window = tk.Tk()
    window.title('Polish Fighters – połącz paczki')
    window.minsize(420, 260)
    panel = ttk.Frame(window, padding=20)
    panel.pack(fill='both', expand=True)
    ttk.Label(panel, text='Zainstalowane paczki obsługiwane przez mixer').pack(anchor='w', pady=(0, 8))
    selection = {pack: tk.BooleanVar() for pack in installed}
    checks = []
    names = {
        'lf4-turbo': 'LF4 Turbo', 'dbz': 'Dragon Ball Z', 'one-piece': 'One Piece',
        'kate': 'Kate', 'reinforced': 'Reinforced', 'ntsd': 'NTSD / Naruto', 'bleach': 'Bleach',
    }
    for pack, value in selection.items():
        check = ttk.Checkbutton(panel, text=names[pack], variable=value)
        check.pack(anchor='w', pady=2)
        checks.append(check)
    message = tk.StringVar(value=(
        'Baza zestawu: LF2 Classic i Polish Originals.' if installed
        else 'Brak zainstalowanych paczek obsługiwanych przez mixer.'
    ))
    ttk.Label(panel, textvariable=message, wraplength=380).pack(anchor='w', pady=(12, 8))

    with ThreadPoolExecutor(max_workers=1) as worker:
        future = None

        def update():
            nonlocal future
            if not future.done():
                window.after(150, update)
                return
            try:
                future.result()
                message.set('Gra została zamknięta. Możesz wybrać następny zestaw.')
            except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as error:
                message.set(str(error))
            finally:
                future = None
                for check in checks:
                    check.state(['!disabled'])
                start.state(['!disabled'])

        def launch():
            nonlocal future
            packs = [pack for pack, value in selection.items() if value.get()]
            if not packs:
                message.set('Zaznacz przynajmniej jedną paczkę.')
                return
            for check in checks:
                check.state(['disabled'])
            start.state(['disabled'])
            message.set('Przygotowuję zestaw. Pliki tymczasowe zostaną usunięte po zamknięciu gry.')
            future = worker.submit(play, installation, installer, packs)
            window.after(150, update)

        def close():
            if future is None:
                window.destroy()
            else:
                message.set('Zamknij grę po zakończeniu, aby usunąć pakiet tymczasowy.')

        start = ttk.Button(panel, text='ZŁÓŻ I URUCHOM', command=launch)
        start.pack(anchor='w')
        if not installed:
            start.state(['disabled'])
        window.protocol('WM_DELETE_WINDOW', close)
        window.mainloop()


if __name__ == '__main__':
    main()
