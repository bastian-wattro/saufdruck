#!/usr/bin/env python3
"""
Keep picking PDF files form the current folder without replacement.
Saves the picked files to a history file and uses them as negative weights
when running the script again
"""

import os
import random
from collections import Counter
from copy import deepcopy
from datetime import date
from pprint import pprint
from statistics import median
from typing import Optional

HISTORY_FILE = 'probe_protokoll.md'
HISTORY_FILE = 'setlist.md'
AGAIN_MARKER = '! '

def main():
    all_songs = get_songs()
    all_weights = get_weights(all_songs)
    list_of_choices: list[str] = []
    songs = deepcopy(all_songs)
    weights = deepcopy(all_weights)
    try:
        while True:
            if all([w == 0 for w in weights]):
                next_song = random.choices(songs)[0]
            else:
                next_song = random.choices(songs, weights=weights)[0]
            answer = ''
            while answer.lower() not in ['y', 'n', 's']:
                answer = input(f" < {next_song} > spielen? [Y/n] oder stop [s]?").strip()
                if answer == 'y' or answer == '':
                    os.system('zathura ' + next_song + '.pdf')
                    pop_this(next_song, songs, weights)
                    list_of_choices.append(next_song)
                    break
                elif answer == 'n':
                    break
                elif answer == 's':
                    raise KeyboardInterrupt

            if not songs:
                songs = deepcopy(all_songs)
                weights = deepcopy(all_weights)

    except KeyboardInterrupt:
        pass
    if list_of_choices:
        clean_marked(list_of_choices)
        add_to_history(list_of_choices)

def get_pdfs() -> list[str]:
    return [x for x in os.listdir() if x.endswith('.pdf')]


def get_songs() -> list[str]:
    return [x[:-len('.pdf')] for x in get_pdfs()]


def get_weights(choices: list[str]) -> Optional[list[int]]:
    if not os.path.isfile(HISTORY_FILE):
        return None
    count_old_choices = count_played(choices)

    weights = []

    if count_old_choices:
        max_weight = max(count_old_choices.values())
    else:
        max_weight = 1

    for item in choices:
        new_weight = max_weight - count_old_choices[item]
        weights.append(new_weight)

    med = median(weights)

    for weight, item in zip(weights, choices):
        if weight == 0:
            pprint("-" * 7 + item)
        elif weight < med:
            pprint(f"{weight} ---  {item}")
        elif weight > med:
            pprint(f"{weight} +++  {item}")
        else:
            pprint(f"{weight}" + " " * 6 + f"{item}")

    return weights


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


def add_to_history(list_of_choices):
    today = date.today().isoformat()

    with open(HISTORY_FILE, 'a') as history:
        history.write('\n\n# ' + today + '\n\n')
        for item in list_of_choices:
            history.write(item + '\n')
    return


def clean_marked(list_of_choices):
    lines_to_keep = []
    with open(HISTORY_FILE, 'r') as history:
        for line in history:
            line = line.strip()
            if not line.startswith(AGAIN_MARKER):
                lines_to_keep.append(line)
                continue
            elif line[len(AGAIN_MARKER):] not in list_of_choices:
                pprint(f"skipped marked song {line[len(AGAIN_MARKER):]}, not in {list_of_choices}")
                lines_to_keep.append(line)
                continue
            else:
                pprint(f"dropped {line[len(AGAIN_MARKER):]} from Marked")

    pprint("rewriting history")
    with open(HISTORY_FILE, 'w') as history:
        for l in lines_to_keep:
            print(l, file=history)


def pop_this(item, population, weights):
    i = population.index(item)
    population.pop(i)
    weights.pop(i)




if __name__ == '__main__':
    main()
