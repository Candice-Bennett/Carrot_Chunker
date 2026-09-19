# Carrot Chunker

Turns a Chinese `.txt` or `.epub` into a CSV of vocab cards you import
into Anki. It will clean the text, segment it with HanLP,
filter words down to reduce card count, looks the remaining words up in a
dictionary, and writes the result to a CSV. The entry point is
[main.py](main.py), and the pipeline steps live under [src](src).

## Card fields

Cards will include:
- Hanzi,
- Pinyin (based of the most frequent reading in your dict, will not be 100% accurate),
- Definition (from your dictionary),
- Count (# of occurances in the text),
- Rank (When all words in the text ordered by frequency),
- Dict Rank (Frequency from frequency dictionary),
- Example Sentence (First occurance of words in text with word bolded)


## Prerequisites

- **Python** - get it from [python.org/downloads](https://www.python.org/downloads/). On Windows,
  tick "Add python.exe to PATH" during install, then confirm it worked with `python --version`
  in a new terminal.
- **AnkiConnect** (only needed for `dedupe_enabled`) - in Anki go to Tools > Add-ons > Get Add-ons,
  paste in code `2055492159`, and restart Anki. More info at
  [ankiweb.net/shared/info/2055492159](https://ankiweb.net/shared/info/2055492159).
- **Dictionaries** [dictionaries](dictionaries) is empty by default- a good source of Yomitan-format Chinese term and frequency dictionaries is
  [MarvNC/yomitan-dictionaries](https://github.com/MarvNC/yomitan-dictionaries). Drop the `.zip` files
  straight into [dictionaries](dictionaries) / [frequency_dictionaries](frequency_dictionaries).

## Downloading Carrot Chunker

Click the green "Code" button near the top of this page, then "Download ZIP",
and extract it somewhere.

You'll then need a terminal open *in that folder* to run the commands below. On Windows,
open the extracted folder in File Explorer, click the address bar, type `cmd`, and hit Enter.

## Running Carrot Chunker

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

- `start_percent` / `end_percent` = only use the middle chunk of the text, by character count

  i.e if `start_percent = 0.1` and `end_percent = 0.4` only the text from 10% in to 40% in
  is used. Handy for cutting a huge text down before segmenting it. Ignored if `use_chapters` is on.

- `use_chapters` = pick specific chapters instead of a percent range

  Looks for `第...章`/`节`/`回` headings, tells you how many chapters it found, then asks
  which ones you want. You can answer with a single chapter (`5`), a range (`10-100`), a
  list (`4,5,6,9,10`), or mix them (`1-3,5,9-10`). If no headings are found it falls back
  to using the whole text.

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

## Importing into Anki

The chunker writes a CSV (default [output/deck.csv](output/deck.csv)), not Anki cards directly -
you still need to import it:

1. In Anki, go to File > Import, and pick the CSV.
2. Check that the [field mapping](#card-fields) lines up (Hanzi, Pinyin, Definition, Count, Rank, Dict Rank,
   Example - skip any column your note type doesn't have).
3. Tick **"Allow HTML in fields"** - the example sentence wraps the target word in `<b>` tags,
   and without this ticked you'll see the literal `<b>` text instead of bold text.
4. Pick the deck and note type you want the cards added to, then import.

## Config ([config.json](config.json))

### NOTE: All paths in this config, if you are on Windows will need to have all slashes escaped, what that means is if your path is `"C:\Users\Me\Downloads\[西子绪]死亡万花筒.txt"` then you need to put `"C:\\Users\\Me\\Downloads\\[西子绪]死亡万花筒.txt"` in the `config.json`

| Flag | What it does |
|---|---|
| `min_count` / `percentile_cutoff` | bottom frequency cutoff |
| `top_cutoff_rank` | top frequency cutoff, needs a frequency dictionary |
| `start_percent` / `end_percent` | only use this % range of the text (by character count) |
| `use_chapters` | pick specific chapters instead, prompts you at run time |
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

## Troubleshooting

- **HanLP's model download fails partway through**, with an error along the
  lines of `Chunk 1 downloaded size 197 mismatches with expected size ...`
  HanLP is used to identify the words so is essential. If you run into errors try running carrot chunker again, if it keeps failing after a
    handful of retries then you can work around it by fetching the file yourself:
    1. Copy the URL from the `Downloading ...` line above the error.
    2. Download it in your browser and unzip it.
    3. Drop the resulting folder into the matching path under `~/.hanlp/`
       (e.g. `~/.hanlp/tok/coarse_electra_small_20220616_012050/`),
       overwriting anything already there.
    4. Re-run the chunker - it'll see the model's already in place and
       skip downloading it.
