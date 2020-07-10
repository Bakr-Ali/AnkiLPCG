import re
from typing import Any, Dict, List

from anki.notes import Note

from . import model_data as lpcg_models

class PoemLine:
    def populate_note(self, note: Note, title: str, tags: List[str],
                      context_lines: int, deck_id: int) -> None:
        """
        Fill the _note_ with content testing on the current line.
        """
        note.model()['did'] = deck_id
        note.tags = tags
        note['Title'] = title
        note['Sequence'] = str(self.seq)
        note['Context'] = self._format_context(context_lines)
        note['Line'] = self.text

    def _format_context(self, context_lines: int):
        context_without_self = self._get_context(context_lines)[:-1]
        return ''.join("<p>%s</p>" % i for i in context_without_self)

    def _get_context(self, _lines: int) -> List[str]:
        """
        Return a list of context lines, including the current line and
        (lines - 1) of its predecessors.
        """
        raise NotImplementedError


class Beginning(PoemLine):
    def __init__(self):
        self.seq = 0
        self.text = "[Beginning]"

    def _get_context(self, _lines: int) -> List[str]:
        return [self.text]


class SingleLine(PoemLine):
    def __init__(self, text: str, predecessor: 'PoemLine') -> None:
        self.text = text
        self.predecessor = predecessor
        self.seq = self.predecessor.seq + 1

    def _get_context(self, lines: int) -> List[str]:
        if lines == 0:
            return [self.text]
        else:
            return self.predecessor._get_context(lines - 1) + [self.text]


class GroupedLine(PoemLine):
    def __init__(self, text: List[str], predecessor: 'PoemLine') -> None:
        self.text_lines = text
        self.predecessor = predecessor
        self.seq = self.predecessor.seq + 1

    def _get_context(self, lines: int) -> List[str]:
        if lines == 0:
            return [self.text]
        else:
            return self.predecessor._get_context(lines - 1) + self.text_lines


def poemlines_from_textlines(text_lines: List[str]) -> List[PoemLine]:
    """
    Given a list of cleansed text lines, create a list of PoemLine objects
    from it. These are each capable of constructing a correct note testing
    themselves when the to_note() method is called on them.
    """
    beginning = Beginning()
    lines = []  # does not include beginning, as it's not actually a line
    pred = beginning
    for text_line in text_lines:
        poem_line = SingleLine(text_line, pred)
        lines.append(poem_line)
        pred = poem_line
    return lines


def process_text(string: str, config: Dict[str, Any]) -> List[str]:
    """
    Munge raw text from the poem editor into a list of lines that can be
    directly made into notes.
    """
    def _normalize_blank_lines(text_lines):
        # remove consecutive lone newlines
        new_text = []
        last_line = ""
        for i in text_lines:
            if last_line.strip() or i.strip():
                new_text.append(i)
            last_line = i
        # remove lone newlines at beginning and end
        for i in (0, -1):
            if not new_text[i].strip():
                del new_text[i]
        return new_text

    text = string.splitlines()
    # record a level of indentation if appropriate
    text = [re.sub(r'^[ \t]+', r'<indent>', i) for i in text]
    # remove comments and normalize blank lines
    text = [i.strip() for i in text if not i.startswith("#")]
    text = [re.sub(r'\#.*$', '', i) for i in text]
    text = _normalize_blank_lines(text)
    # add end-of-stanza/poem markers where appropriate
    for i in range(len(text)):
        if i == len(text) - 1:
            text[i] += config['endOfTextMarker']
        elif not text[i+1].strip():
            text[i] += config['endOfStanzaMarker']
    # entirely remove all blank lines
    text = [i for i in text if i.strip()]
    # replace <indent>s with valid CSS
    text = [re.sub(r'^<indent>(.*)$', r'<span class="indent">\1</span>', i)
            for i in text]
    return text


def add_notes(col: Any, title: str, tags: List[str], text: List[str], deck_id: int,
              lines_of_context: int = 2):
    """
    Generate notes from the given title, tags, poem text, and number of
    lines of context. Return the number of notes added.

    Return the number of notes added.

    Raises KeyError if the note type is missing fields, which I've seen
    happen a couple times when users accidentally edited the note type. The
    caller should offer an appropriate error message in this case.
    """
    added = 0
    for line in poemlines_from_textlines(text):
        n = Note(col, col.models.byName(lpcg_models.NAME))
        line.populate_note(n, title, tags, lines_of_context, deck_id)
        col.addNote(n)
        added += 1
    return added
