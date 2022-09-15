#!/usr/bin/env python3
"""
Keep picking Saufdruck songs.
Saves the picked files to a history file and uses them as negative weights
when running the script again.
"""

import os
import random
from collections import Counter
from datetime import date
from pprint import pprint
from typing import Optional

import termcolor
from simple_term_menu import TerminalMenu

HISTORY_FILE = 'probe.md'
AGAIN_MARKER = '! '
DIR_BLACK_LIST: list[str] = ["deleted", "ablage"]


def main():
    song_weights, songs_to_play = setup()
    list_of_choices = rocknroll(song_weights, songs_to_play)
    finalize(list_of_choices)
    raise SystemExit(f"{len(list_of_choices)} Hits gerockt.")


def setup():
    songs_to_play = get_songs()
    if not songs_to_play:
        raise SystemExit("Keine Lieder gefunden.")
    song_weights = get_weights(songs_to_play)
    return song_weights, songs_to_play


def rocknroll(song_weights, songs_to_play):
    list_of_choices: list[str] = []
    try:
        while True:
            if not songs_to_play:
                raise KeyboardInterrupt("Alle Lieder gespielt.")
            song = pick_and_pop_song(songs_to_play, song_weights)
            if song is not None:
                list_of_choices.append(song)
    except KeyboardInterrupt:
        pass
    return list_of_choices


def finalize(list_of_choices: list[str]) -> None:
    if len(list_of_choices) == 0:
        return
    options = ["[s] speichern", "[z] zusammenfassen und verwerfen"]
    action = TerminalMenu(options, title="Was soll mit der Session passieren?").show()
    if action == 0:  # speichern
        clean_marked(list_of_choices)
        with open(HISTORY_FILE, 'a') as history:
            print_history(list_of_choices, file=history)
        return
    if action == 1:  # zusammenfassen
        print_history(list_of_choices)
        return


# ## GET SONGS
def get_songs() -> list[str]:
    selected_books = get_song_books()
    pdfs = set()
    for book in selected_books:
        pdfs.update(set([f"{book}/{x}" for x in os.listdir(book) if x.endswith('.pdf')]))
    return [x[:-len('.pdf')] for x in pdfs]


def get_song_books() -> list[str]:
    all_song_books = [dir_name for dir_name in os.listdir()
                      if (os.path.isdir(dir_name) and
                          not is_blacklisted_dir(dir_name))]
    all_song_books.sort(reverse=True)
    options = ["alle"] + all_song_books
    book_menu = TerminalMenu(options,
                             title=("Aus welchen Ordnern soll gewählt werden?"
                                    "  Leertaste zum An/Abwählen,"
                                    "  Enter zum Bestätigen (wählt aktuellen Punkt aus)"),
                             multi_select=True)
    selected_books = book_menu.show()
    if 0 in selected_books:
        return all_song_books
    return [options[i] for i in selected_books]


def is_blacklisted_dir(dir_name: str) -> bool:
    return (dir_name.startswith(".") or
            dir_name in DIR_BLACK_LIST
            )


# ## GET WEIGHTS
def get_weights(song_list: list[str]) -> list[int]:
    if not os.path.isfile(HISTORY_FILE):
        return [0 for _ in song_list]
    count_old_choices = count_played(song_list)

    if not count_old_choices:
        return [0 for _ in song_list]
    max_weight = max(count_old_choices.values())

    return [max_weight - count_old_choices[song] for song in song_list]


def count_played(choices: list[str]) -> Counter:
    count_old_choices = Counter()
    with open(HISTORY_FILE, 'r') as history:
        for line in history:
            line = line.strip()
            count = 1
            if line.startswith(AGAIN_MARKER):
                line = line[2:]
                count = -10
            if line not in choices:
                continue
            count_old_choices[line] += count
    return count_old_choices


# ## MODIFY SONG LIST
def pop_song(item, population, weights):
    i = population.index(item)
    population.pop(i)
    weights.pop(i)


def format_song_name(next_song: str) -> str:
    def highlight(song_name: str) -> str:
        return termcolor.colored(song_name, color="cyan", attrs=['bold'])

    if '/' not in next_song:
        return highlight(next_song)
    songbook, song = next_song.split('/')
    return f"{highlight(song)} ({songbook})"


def pick_and_pop_song(songs, weights) -> Optional[str]:
    if all([w == 0 for w in weights]):
        next_song = random.choice(songs)
    else:
        next_song = random.choices(songs, weights=weights, k=1).pop()

    options = ["[j] ja", "[n] nein", "[x] heute nicht mehr fragen", "[s] stop"]
    print("")
    decide_menu = TerminalMenu(options, title=f"\t{format_song_name(next_song)} spielen?")
    res = decide_menu.show()
    if res == 0:  # ja
        print(f"\t {termcolor.colored('✓', color='cyan')}")
        os.system('zathura ' + next_song + '.pdf')
        pop_song(next_song, songs, weights)
        return next_song
    if res == 1:  # nein
        print(f"\t {termcolor.colored('✗', color='red')}")
        return None
    if res == 2:  # heute nicht
        print(f"\t {termcolor.colored('✗✗✗', color='red')}")
        pop_song(next_song, songs, weights)
        return None
    raise KeyboardInterrupt


# ## LOG
def print_history(list_of_choices, file=None):
    print(f"\n# {date.today().isoformat()}", file=file)
    for song in list_of_choices:
        print(song, file=file)


def clean_marked(list_of_choices):
    lines_to_keep = []
    if not os.path.isfile(HISTORY_FILE):
        return
    with open(HISTORY_FILE, 'r') as history:
        for line in history:
            line = line.strip()
            if not line:
                continue
            if not line.startswith(AGAIN_MARKER):
                lines_to_keep.append(line)
                continue
            if line[len(AGAIN_MARKER):] in list_of_choices:
                pprint(f"{line[len(AGAIN_MARKER):]} aus {HISTORY_FILE} entfernt.")
            else:
                pprint(f"{line[len(AGAIN_MARKER):]} bleibt markiert.")
                lines_to_keep.append(line)
                continue

    pprint(f"{HISTORY_FILE} wird angepasst.")
    with open(HISTORY_FILE, 'w') as history:
        for line in lines_to_keep:
            print(line, file=history)


if __name__ == '__main__':
    main()
