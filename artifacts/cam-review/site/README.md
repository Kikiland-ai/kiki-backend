# Kiki Concept Canvas Studio

Private review library for all ten C-AM concepts: 40 authored placards, 22 Odia–English recordings, editable analytic SVG models, source-language switch and manual navigation. Scientific, native-Odia and pronunciation review is pending. No sentence-alignment or production-app integration is claimed.

The root page lists all ten concepts. Each `/concepts/C-AM-XX/` page provides native audio playback, parameters and reset. The earlier VCO demonstration is preserved at `/vco/`.

To refresh from prepared backend packets:

```sh
python build-review-library.py /absolute/path/to/prepared/packets
```

Hosting: existing `kiki-canvas-studio` identity and audience are retained. No Firestore or private production object-storage writes are part of this preview.
