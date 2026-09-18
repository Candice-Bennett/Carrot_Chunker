from __future__ import annotations

import re
from collections import Counter

import hanlp

from models import WordCandidate
from progress import tqdm

HAS_HANZI = re.compile(r"[一-鿿]")


def hanzi_count(s: str) -> int:
    return len(HAS_HANZI.findall(s))


class WordAnalysisService:
    def __init__(
        self,
        chengyu: set[str] | None = None,
        example_min_hanzi: int = 6,
        example_max_hanzi: int = 25,
        segment_batch_size: int = 32,
    ):
        self.chengyu = chengyu or set()
        self.example_min_hanzi = example_min_hanzi
        self.example_max_hanzi = example_max_hanzi
        self.segment_batch_size = segment_batch_size
        self.tokenizer = hanlp.load(hanlp.pretrained.tok.COARSE_ELECTRA_SMALL_ZH)
        if self.chengyu:
            self.tokenizer.dict_force = self.chengyu

    def analyse(self, text: str) -> list[WordCandidate]:
        sentences = [s.strip() for s in hanlp.utils.rules.split_sentence(text) if s.strip()]

        counts: Counter = Counter()
        examples: dict[str, str] = {}

        batches = range(0, len(sentences), self.segment_batch_size)
        for start in tqdm(batches, desc="segmenting", unit="batch"):
            batch = sentences[start : start + self.segment_batch_size]
            for sentence, words in zip(batch, self.tokenizer(batch)):
                sentence_hanzi_count: int | None = None
                for word in words:
                    if not HAS_HANZI.search(word):
                        continue
                    counts[word] += 1

                    if word not in examples:
                        if sentence_hanzi_count is None:
                            sentence_hanzi_count = hanzi_count(sentence)
                        if self.example_min_hanzi < sentence_hanzi_count < self.example_max_hanzi:
                            examples[word] = sentence

        return [
            WordCandidate(text=w, count=c, example_sentence=examples.get(w))
            for w, c in counts.items()
        ]
