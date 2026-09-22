# Sustainability

Flattened, static versions of retired RRCHNM web projects, kept here so repairs, fixes, and deploys stay under version control. Each site directory has its own README describing what was crawled, what was fixed, and what is still outstanding.

## Sites

| Project | Directory | Live site | Source platform | Year |
|---|---|---|---|---|
| 1989 | `1989/` | 1989.rrchnm.org | Omeka | 2025 |
| 20 Years of RRCHNM | `20.rrchnm.org/` | 20th.dev.chnm.gmu.edu (dev) | Omeka | 2026 |
| Amboyna Conspiracy Trial | `amboyna/` | amboyna.org | Drupal | 2023 |
| Children and Youth in History | `cyh/` | cyh.rrchnm.org | Omeka | 2025 |
| Digital Campus | `digitalcampus/` | digitalcampus.tv | WordPress | 2025 |
| DoHistory | `dohistory/` | dohistory.org | Custom | 2025 |
| Eagle Eye Citizen | `eagleeyecitizen/` | eagleeyecitizen.org | Drupal | 2026 |
| For Us the Living | `futl/` | forustheliving.org | Drupal | 2026 |
| Harambee City | `harambeecity/` | harambeecity.rrchnm.org | Omeka | 2024 |
| Hearing the Americas | `hearingtheamericas/` | hearingtheamericas.org | Omeka S | 2026 |
| History Matters | `historymatters.gmu.edu/` | historymatters.gmu.edu | Custom | 2026 |
| Imaging the French Revolution | `imagingthefrenchrevolution/` | imagingthefrenchrevolution.rrchnm.org | Custom | 2026 |
| Islam Perspectives | `islamperspectives/` | islampers.dev.chnm.gmu.edu (dev) | Omeka | 2026 |
| Mall History | `mallhistory/` | mallhistory.org | Omeka | 2026 |
| Maritime Asia | `maritime/` | maritime-asia.org | Drupal | 2023 |
| Material Histories of the Indian Ocean World | `iowmaterialhistorieswebinar.org/` | iowmaterialhistorieswebinar.org | Omeka S | 2026 |
| Objects of History | `objectsofhistory/` | objectofhistory.org | Custom | 2025 |
| Occupy Archive | `occupyarchive/` | occupyarchive.org | Omeka Classic | 2026 |
| Pandemic Religion | `pandemicreligion/` | (pilot: 3 of 7 sites) | Omeka S | 2026 |
| Pilbara Strike | `pilbarastrike/` | pilbarastrike.org | Drupal | 2023 |
| Plaster Cast Collection | `plastercast/` | plastercast.gmu.edu | Omeka | 2026 |
| Resounding the Archives | `resounding/` | resoundingthearchives.org | Drupal | 2026 |
| Thanks, Roy | `thanksroy/` | thanksroy.org | Omeka | 2026 |
| Transatlantic Encounters | `transatlanticencounters/` | transatlaenc.dev.chnm.gmu.edu (dev) | Omeka | 2026 |
| Virginia's Lost AT | `virginiaslostat/` | virginiaslostat.org | Omeka | 2026 |

### Sites in their own repos

Larger Hugo builds that outgrew the monorepo, or never lived here, have their own repositories. Their issues may still be tracked here.

| Project | Repo | Live site |
|---|---|---|
| Papers of the War Department | [chnm/pwd](https://github.com/chnm/pwd) | wardepartmentpapers.org |
| Hurricane Digital Memory Bank | [chnm/hurricanearchive](https://github.com/chnm/hurricanearchive) | hurricanearchive.org |
| 9/11 Digital Archive | [chnm/911digitalarchive](https://github.com/chnm/911digitalarchive) | 911digitalarchive.org |
| Bracero History Archive | [chnm/braceroarchive](https://github.com/chnm/braceroarchive) | braceroarchive.org |

## Tools and guides

| Path | What it is |
|---|---|
| `scripts/` | Site-specific flattening and fix scripts, plus the `crawler/` used for item pages. |
| `utils/alt-text/` | Cross-site alt text generator. See below. |
| `_snippets/` | Shared HTML fragments, such as the sustainability banner. |
| `DEVNOTES.md` | How to add static search (MiniSearch) to a flattened site. |
| `paginationNotes.md` | How to paginate static search results. |

## Deploys

Every site has a workflow in `.github/workflows/` named `<site>--deploy.yml`. It runs when a push touches that site's directory and calls the shared `static--deploy.yml` workflow in `chnm/.github`, which reads the dev and production hostnames set in the site's workflow file.

## Alt text generation

Most crawled sites arrived with empty alt text, or with a filename or URL where a description should be. The tool in `utils/alt-text/` finds those images and writes descriptions with Claude, one site directory at a time. It runs against any site here, flattened HTML or Hugo source.

```
python utils/alt-text/generate-alt-text.py plastercast --list       # scan only, no Claude calls
python utils/alt-text/generate-alt-text.py plastercast --limit 5    # dry-run a few descriptions
python utils/alt-text/generate-alt-text.py plastercast --apply      # write them into the HTML
```

Sites whose item media lives in the object-storage bucket rather than the repo (thanksroy, virginiaslostat) need `--base-url` so the images can be fetched:

```
python utils/alt-text/generate-alt-text.py thanksroy --base-url https://thanksroy.org --apply
```

By default only empty, placeholder, and filename alt is flagged. Add `--strict` to also flag short or duplicated alt, which on a flattened site will include every header logo, so use it deliberately. The same image on many pages is described once and reused. Images the tool cannot locate, such as JavaScript-templated tags, are listed as SKIP for a manual pass. It needs the `claude` CLI installed and signed in. Run `python utils/alt-text/test_generate_alt_text.py` to self-check after editing it.

Work site by site: run `--list`, spot-check with `--limit`, then `--apply` on its own branch and review the diff before merging.

## Project Team

- Jessica Otis (@jmotis)
- Jason Heppler (@hepplerj)
- Tony Trinh (@qtrinh2)
- Savannah Scott (@sscott710)
