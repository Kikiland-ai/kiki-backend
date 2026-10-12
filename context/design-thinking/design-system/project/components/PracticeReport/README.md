# PracticeReport

The analysis after a written practice set: the score, how many marks were lost to English and how many to concept gaps, each question with its own split, and the weak spots to fix before the exam.

**Consumer provides:** `data` (`{title, time, total, questions: [{n, topic, got, max, english, note}]}`, where `english` is the marks lost only because of English), `onOpen(question)` to open that answer in AnswerOverlay, `onRepair` for "Make my repair map" (pass `false` to hide it).

Concept marks lost are worked out as max − got − english. A question is a weak spot when it lost 2 or more marks to the concept, or any marks to English.

- Do: show the English cost separately every time. It is the core insight for the student.
- Do: open each question's marked-up answer on tap.
- Don't: show a rank or compare with classmates.
