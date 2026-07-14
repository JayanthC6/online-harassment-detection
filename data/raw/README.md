# Dataset notes

**Source:** Davidson, T., Warmsley, D., Macy, M., & Weber, I. (2017).
"Automated Hate Speech Detection and the Problem of Offensive Language."
`davidson_hate_speech.csv` — 24,783 labeled tweets, pulled from the authors'
public GitHub repo (t-davidson/hate-speech-and-offensive-language).

## Label mapping decision

The dataset ships with 3 classes: `0 = hate_speech`, `1 = offensive_language`,
`2 = neither`. The project synopsis calls for 4 categories: cyberbullying,
hate speech, threats, offensive language. This dataset does **not** cleanly
separate "threats" or "bullying" from the other categories — that's a real
gap, not an oversight, and worth stating plainly in your report rather than
quietly working around it.

Current mapping used by `train_baseline.py` / `predict.py`:

| Dataset class | Category label | Harassing? |
|---|---|---|
| 0 | hate_speech | yes |
| 1 | offensive_language | yes |
| 2 | none | no |

## Known issue: class imbalance

| class | count | share |
|---|---|---|
| hate_speech | 1,430 | 5.8% |
| offensive_language | 19,190 | 77.4% |
| neither | 4,163 | 16.8% |

hate_speech is the rarest class by far, which is also the most serious
category. The baseline model reflects this: 86% overall accuracy but only
~32% precision on hate_speech specifically. `class_weight="balanced"` is
already applied in training to partially offset this — document the
before/after if you turn this off to compare.

## To add threat/bullying-specific data later

Consider combining with a second dataset that labels threats more explicitly,
e.g. OLID/OffensEval (has a "targeted insult" subtype) or HateXplain (comes
with span-level rationales, useful if you build the explainability module).
Merging label schemes across datasets is nontrivial — map both into your own
4-category schema rather than assuming their categories line up 1:1.
