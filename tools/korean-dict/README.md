# Korean dictionary for HeliBoard K

`main_ko.dict` is a Korean main dictionary with word frequencies, made for HeliBoard's
`KoreanDictionary` (words are stored as decomposed standard jamo).
Add it in HeliBoard K: Settings → Dictionaries → Add dictionary from file.

- Source word list: [hermitdave/FrequencyWords](https://github.com/hermitdave/FrequencyWords)
  `content/2018/ko/ko_full.txt` (OpenSubtitles 2018), licensed CC-BY-SA 4.0
- Top 150000 Hangul-only words with count >= 3, frequencies log-scaled to 1..255
- Words containing common swear words are flagged as possibly offensive

Rebuild:

    python makedict.py ko_full.txt main_ko.dict 150000

Check the result (writes `frequency, word, flags` per line):

    python readdict.py main_ko.dict words.tsv
