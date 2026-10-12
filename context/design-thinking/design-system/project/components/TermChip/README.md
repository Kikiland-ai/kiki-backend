# TermChip

An English technical term inside running text, always in the same dotted-underline style; tapping opens a sheet with the Odia meaning, pronunciation and an example.

**Consumer provides:** `term` (the canonical English term, never translated), optional `entry` (`{odia, example}` from the glossary; defaults to the built-in sample glossary), `state` (`new`, `collected`, `owned`), `pulse` (a one-time ring when the paragraph morphs), `onOpen`.

- Do: use one entry per term from the shared glossary so every lesson says the same thing.
- Don't: style English terms any other way, or translate the term itself.
