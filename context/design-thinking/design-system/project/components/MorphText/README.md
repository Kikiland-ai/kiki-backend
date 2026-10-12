# MorphText

The lesson paragraph that re-renders at the student's dial level while the English term chips stay the same.

**Consumer provides:** `level` (1 to 5, from LanguageDial), `levels` (five arrays of segments: strings, or `{term}` objects for chips), optional `glossary`, `termStates` (`{term: state}`), `onTermOpen`. Odia runs are detected automatically and set 12% larger with a looser line height.

- Do: generate all five levels for a card at once and cache them, so the morph is instant.
- Don't: change which terms appear between levels: the chips are the anchors.
