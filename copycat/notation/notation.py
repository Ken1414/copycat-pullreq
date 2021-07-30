import re
from bisect import bisect_left
from collections import defaultdict
from dataclasses import dataclass
from functools import reduce
from typing import Dict, List, Type, Tuple

from global_types import Clef

OCTAVES = {
    "C2": "C,",
    "D2": "D,",
    "E2": "E,",
    "F2": "F,",
    "G2": "G,",
    "A3": "A,",
    "B3": "B,",
    "C3": "C",
    "D3": "D",
    "E3": "E",
    "F3": "F",
    "G3": "G",
    "A4": "A",
    "B4": "B",
    "C4": "c",
    "D4": "d",
    "E4": "e",
    "F4": "f",
    "G4": "g",
    "A5": "a",
    "B5": "b",
    "C5": "c'",
    "D5": "d'",
    "E5": "e'",
    "F5": "f'",
    "G5": "g'",
    "A6": "a'",
    "B6": "b'",
}

LENGTHS = {
    0.0625: "/8",  # 64ths
    0.125: "/4",  # 32nds
    0.25: "/2",  # sixteenth
    0.5: "1",  # eight
    1: "2",  # quarter
    1.5: "3",  # quarter with dot
    2: "4",  # half
    2.5: "5",
    3: "6",
    3.5: "7",
    4: "8",  # whole
}


class Notation:
    def __init__(self, fps: float, tempo: int, octave_offset: int, min_note_speed: int):
        self.fps = round(fps)
        self.tempo = tempo
        self.octave_offset = octave_offset
        self.min_note_speed = min_note_speed

        self.notation_string: str = ""

        self.treble_notes: Dict[str, NoteState] = defaultdict(NoteState)
        self.bass_notes: Dict[str, NoteState] = defaultdict(NoteState)
        self.iteration = 0

    def push_note(self, note: str, clef: Clef = Clef.TREBLE):
        if clef == Clef.TREBLE:
            note_state = self.treble_notes[note]
        else:
            note_state = self.bass_notes[note]

        note_state.frame_count += 1
        note_state.iteration = self.iteration

    def apply_frame(self):
        if len(self.treble_notes) == 0 or (self.treble_notes.get("0") is not None and len(self.treble_notes) == 1):
            self.treble_notes["0"].iteration = self.iteration
            self.treble_notes["0"].frame_count += 1

        section = "["
        for note, state in list(self.treble_notes.items()):
            if state.iteration == self.iteration:
                continue

            if note == "0":
                length, index = length_parser(state.frame_count / self.fps, self.tempo)
                if index >= 3:
                    self.notation_string += f"z{length} "
                self.treble_notes.pop("0")
                continue

            parsed_note = sharp_parser(note)
            parsed_note = octave_parser(parsed_note, self.octave_offset)
            length = length_parser(state.frame_count / self.fps, self.tempo, min_length_index=self.min_note_speed)[0]
            section += f"{parsed_note}{length}"

            self.treble_notes.pop(note)
        section += "] "

        if section != "[] ":
            self.notation_string += section

        self.iteration += 1

    def get_abc_notation(self, title="", composer=""):
        a = self.notation_string.split()
        ret = ''
        for i in range(0, len(a), 10):
            ret += ' '.join(a[i:i + 10]) + '\n'

        return f"T: {title}\nC: {composer}\nQ: {self.tempo}\n{ret}"


def octave_parser(note: str, offset: int = 0) -> str:
    letter = reduce(lambda a, b: a if 65 <= ord(a) <= 90 else b, note)
    octave = int(note[-1]) + offset

    note_with_octave = OCTAVES[f"{letter}{octave}"]

    note = note.replace(letter, note_with_octave)
    return note.replace(str(octave - offset), "")


def sharp_parser(note: str) -> str:
    if "#" in note:
        return f"^{note.replace('#', '')}"
    return note


def length_parser(seconds: float, tempo: int, min_length_index=0) -> Tuple[str, int]:
    crotchet = 60 / tempo
    press_seconds = [x * crotchet for x in LENGTHS.keys()]
    note_index = take_closest(press_seconds, seconds)

    return list(LENGTHS.values())[max(note_index, min_length_index)], note_index


T = Type["T"]


def take_closest(thing_list: List[T], thing: T):
    """
    Assumes thing_list is sorted. Returns the index of the closest value to thing.

    If two numbers are equally close, return the largest number index.

    Based on:
        https://stackoverflow.com/questions/12141150/from-list-of-integers-get-number-closest-to-a-given-value
    """
    pos = bisect_left(thing_list, thing)
    if pos == 0:
        return 0
    if pos == len(thing_list):
        return len(thing_list) - 1
    before = thing_list[pos - 1]
    after = thing_list[pos]
    if after - thing <= thing - before:
        return pos
    else:
        return pos - 1


@dataclass
class NoteState:
    frame_count: int = 0
    iteration: int = 0
