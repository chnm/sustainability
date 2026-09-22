# alt-text

Cross-site alt text tool. Site-specific fix scripts live in `scripts/` or under each site.

## generate-alt-text.py

Finds images with missing or weak alt text in a site directory and writes replacements
with Claude via the `claude` CLI. Works on flattened HTML sites and Hugo sources.

```
python utils/alt-text/generate-alt-text.py plastercast --list       # scan only, no Claude calls
python utils/alt-text/generate-alt-text.py plastercast --limit 5    # dry-run a few
python utils/alt-text/generate-alt-text.py plastercast --apply      # patch files in place
python utils/alt-text/generate-alt-text.py plastercast --strict     # also flag short/duplicate alt
python utils/alt-text/generate-alt-text.py thanksroy --base-url https://thanksroy.org   # media lives in a bucket
python utils/alt-text/test_generate_alt_text.py                     # self-check
```

Flags alt that is empty, a placeholder, or a filename/URL. The same image on many
pages is described once and reused. Images it cannot find on disk are fetched from
`--base-url` if given, otherwise listed as SKIP for a manual pass. Originally written for [chnm/crdh](https://github.com/chnm/crdh/tree/main/utils).
