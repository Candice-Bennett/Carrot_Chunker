# Carrot Chunker

Turns a Chinese `.txt` or `.epub` into a CSV of vocab cards you import
into Anki. It will clean the text, segment it with HanLP,
filter words down to reduce card count, looks the remaining words up in a
dictionary, and writes the result to a CSV. The entry point is
[main.py](main.py), and the pipeline steps live under [src](src).

Cards will include:
- Hanzi,
- Pinyin,
- Definition,
- Count (# of occurances in the text),
- Rank (When all words in the text ordered by frequency),
- Dict Rank (Frequency from frequency dictionary),
- Example Sentence (First occurance of words in text with word bolded)

## Running it

You will need python to be installed.

Drop in your dictionaries, frequency dictionaries and text (as a .txt or as a .epub) to the relevant folders
([dictionaries](dictionaries), [frequency_dictionaries](frequency_dictionaries)
and [data](data) respectively) or set the location of these files in
[config.json](config.json).

Set your frequency cut offs in [config.json](config.json). Here's what they do:

- `min_count` = the minimum number of times a word can show up to be made into a card

  i.e if this is set to 10, a word must be present in the text 10 times to be made into a card

- `percentile_cutoff` = remove the bottom this % of words

  i.e if this is set to 0.25 then the 25% least frequent words won't be made into a card

- `top_cutoff_rank` = removes all notes with a frequency rank in the frequency dictionaries below this

  i.e if the chunker finds a 的 and is not removed elsewhere but you have
  `top_cutoff_rank = 1000`
  then the 1000 most common words (as per your freq dicts) will be removed 
  which will remove 的 due to it's high frequency.
  note: this uses frequency in the *language* i.e your text may only have
  的 once but since 的 is used a lot in the chinese *language* it will be removed

- `dedupe_enabled` = removes all words already present in your Anki collection (requires the
  AnkiConnect addon, since that's how the chunker talks to Anki)

  For each `{note_type, field_name}` pair in `dedupe_fields`, it looks up every note of that
  note_type in Anki and compares the words the chunker found against what's in that field,
  removing any matches.

  i.e if you have `note_type = "Hanzi_note"` and `field_name = "Hanzi"` and a Hanzi_note in anki with the
  Hanzi field set to 我, if the chunker finds 我 in in the text and it is not removed from the above filters
  *this* will remove it so you don't have duplicate anki cards.

Then install the dependencies from [requirements.txt](requirements.txt) and run it, passing
the filename to chunk (it's read from the [data](data) folder):
```
pip install -r requirements.txt
python main.py [name of your text]
```
or, if you've set `input_path` in [config.json](config.json) so it already knows which file
to use:
```
pip install -r requirements.txt
python main.py
```

NOTE:
First run downloads the HanLP model (network required, cached after in
`~/.hanlp`).

## Config ([config.json](config.json))

| Flag | What it does |
|---|---|
| `min_count` / `percentile_cutoff` | bottom frequency cutoff |
| `top_cutoff_rank` | top frequency cutoff, needs a frequency dictionary |
| `dedupe_enabled` / `dedupe_fields` | `{note_type, field_name}` pairs to check via AnkiConnect |
| `input_path` | `.txt` or `.epub` to read - `""` uses the command-line filename from [data](data) instead |
| `output_path` | where the CSV is written - `""` uses [output/deck.csv](output/deck.csv) |
| `dictionaries_dir` | definition dictionaries folder - `""` uses [dictionaries](dictionaries) |
| `frequency_dictionaries_dir` | frequency dictionaries folder - `""` uses [frequency_dictionaries](frequency_dictionaries) |
| `segment_batch_size` | sentences per HanLP call |
| `clean_text` | strip downloader noise (default `true`) |
| `keep_unranked_words` | keep words missing from every frequency dictionary |
| `debug` | keep cards with no definition found |
| `example_sentence_min_hanzi` / `example_sentence_max_hanzi` | example sentence length range |
| `ankiconnect_url` | default `http://127.0.0.1:8765` |

`input_path`, `output_path`, `dictionaries_dir`, and
`frequency_dictionaries_dir` are overrides - leave them as `""` to use
the default shown above, or set a path (relative or absolute) to point
elsewhere.

## Notes

- Drop any number of `.zip` files (CC-CEDICT or Yomitan format) into
  `dictionaries_dir` / `frequency_dictionaries_dir` (i.e. the
  [dictionaries](dictionaries) / [frequency_dictionaries](frequency_dictionaries)
  folders by default) - they're all loaded and then applied alphabetically
  (use numeric-prefix filenames to control priority, hence why I have named
  the default ones ZZ - yours should take priority).
- Dedupe matching is exact: a word only counts as a duplicate if the
  field's value (after stripping HTML) equals it exactly.
- Frequency dictionary rank assumes lower number = more common (rank 1
  = most frequent word).
- The file cleaning (in [src/text_cleaning.py](src/text_cleaning.py)) is based
  on my copy of 死亡玩花间 which had some noise from jjwxc (such as donation
  thanks) and the Novel Downloader I used. It may not clean perfectly.
