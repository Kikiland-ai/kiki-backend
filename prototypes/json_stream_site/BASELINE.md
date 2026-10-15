# Hosted baseline snapshot

This is the portable source snapshot of the working private screen-reader Site at `4e1d0c3d132ff2778216e5d7e4d987d3e04d7145`. Read [the end-to-end baseline](../../docs/baselines/screen-reader-v1.md) first: the original README retains historical stages superseded by later changes.

The original project identity is excluded. Do not deploy an experiment to the baseline Site. With Node 22, local build/tests are:

```sh
cd prototypes/hosted_screen_reader
cp .openai/hosting.example.json .openai/hosting.json
node scripts/build.mjs
node --test scripts/test-*.mjs
```

The local example has no project ID; it is not a deployment configuration. Configure a separate project through supported hosting before any future experimental publication. Provider keys are unnecessary for offline tests and must never be written to this source. The private Site remains Worker/D1; its optional Python edge proxy has not been enabled.
