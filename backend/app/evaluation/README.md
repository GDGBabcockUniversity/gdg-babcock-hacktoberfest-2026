# Grader evaluation harness

This folder checks how closely a grader agrees with a person. It grades 30 made-up answers
that were scored by hand, then prints a report comparing the two sets of marks.

## Run it

From `backend/`, with your virtual environment active:

    python -m app.evaluation.harness

It uses whichever grader `GRADER_MODE` selects, so `mock` by default. To try the Ollama
grader, set the variable first (on Windows: `set GRADER_MODE=ollama`, on macOS and Linux:
`export GRADER_MODE=ollama`). Add `--output report.md` to save the report, and
`--tolerance 0.2` to count a wider gap as agreement.

The mock grader gives written answers a fixed 70% and flags them for review, so its report
is the baseline any real grader should beat.

## Files

- `dataset.json`: the questions, then the cases (an answer plus its hand-picked score).
- `harness.py`: loads the dataset, grades every case, works out the numbers and prints them.

## The dataset

30 cases: 8 objective, 11 short answer, 11 theory. They include full marks, partial marks,
wrong answers, blank answers, correct answers in different words, keyword stuffing and an
attempt to tell the grader what mark to give. Everything is invented, so no real student
data is stored here.

Each case has a `note` saying why it got its score. Written questions have rubric points
whose marks add up to the question's max marks.

## How agreement is measured

Every number compares the grader's score with the hand score. Gaps are measured as a share
of the question's max marks, so a 1 mark gap on a 2 mark question counts more than on a
10 mark question.

- **Agreement:** the share of cases where the grader is within 10% of max marks of the
  hand score. This is the main number.
- **Exact match:** the share of cases with the same score.
- **Mean error:** the average size of the gap, ignoring direction. Lower is better.
- **Bias:** the average gap with direction. Positive means the grader gives too many marks,
  negative means too few.
- **Flagged for review:** the share of cases the grader sent to a person. A wrong grade that
  was flagged is less harmful than one that was not, so the report also says how many of the
  disagreements were flagged.

## Limits of this dataset

- Thirty cases is a small sample. One case moves agreement by about 3 points, so small
  differences between graders mean little.
- The hand scores were given by one person. Nobody checked them, so some are judgment calls.
  Two people might score a few cases differently.
- The answers are short and invented. Real student answers are longer, messier and cover
  more subjects.
- It covers three questions per written type, so a grader could do well here and badly on
  other topics.
- The model answers and rubric points were written by the same person who scored the cases.

## Adding cases

Add a question to `questions` if it is new, then a case to `cases` that points at it. Keep
rubric marks adding up to the max marks and use invented text only. `tests/test_evaluation.py`
checks the file is well formed.