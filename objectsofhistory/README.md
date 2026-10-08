# The Object of History

**Note: This is a flattened version of the project structure.**

## About

The Object of History is a digital history created in collaboration between the Smithsonian's National Museum of American History and George Mason University's Roy Rosenzweig Center for History and New Media intended to provide low-cost access to the museum's collections and curatorial expertise for students and teachers of U.S. History.

## Project Goals

- Improve students' content knowledge of standard topics in U.S. History
- Develop students' ability to understand material culture objects as historical evidence
- Provide smaller museums and historical societies with a model for creating similar materials using their own collections

## Featured Objects

The project centers around six historical objects from the National Museum of American History:

1. **Desk** - A writing desk with historical significance
2. **Gold Nugget** - From the California Gold Rush era
3. **Dress** - A period dress with cultural importance
4. **Voting Machine** - Early American voting technology
5. **Lunch Counter** - Connected to civil rights history
6. **Short-Handled Hoe** - Agricultural tool with labor history connections

## Structure

The website includes several main sections:

- **Guide** - Instructions for doing history with objects
- **Objects** - Detailed exploration of the six featured artifacts
- **Forum** - Expert discussions about the objects
- **Activity** - Interactive virtual exhibit creation (removed in 2026; its backend no longer exists and its pages now show a notice)
- **Teachers** - Educational materials and resources
- **Search** - Site-wide search functionality

## Technical Details

This is a static HTML website built circa 2006 but converted to a flattened site in 2025, featuring:

- CSS-based layout with cross-browser compatibility
- JavaScript enhancements using Prototype.js and Scriptaculous
- Interactive features including drag-and-drop functionality
- Video tutorials for site usage
- Analytics tracking (Matomo and WebTrends)

## Repairs (2026)

- **Media:** QuickTime `<object>`/`<embed>` players were replaced with native `<video>`/`<audio>`. Most media files live only on the server under `content/vault/`. The ones browsers can't decode (Sorenson SVQ3 and MPEG-4 Part 2) were transcoded to H.264 and committed as `content/vault/<name>-h264.mp4`. Audio-only `.mov` files were remuxed to `.m4a`.
- **Item popups:** GreyBox was replaced with a native `<dialog>` (`content/public/j/itemdialog.js`). Links marked `data-dialog` open `objects/show/` pages in it.
- **Accessibility:** a WCAG 2.2 AA pass covered contrast, page titles, alt text, the skip link and landmarks (see chnm/sustainability#116).

### Outstanding

- Video has no captions (WCAG 1.2.2).
- The fixed 780px layout doesn't reflow at narrow widths (WCAG 1.4.10).
- `content/vault/deskfinal_1e2b642090.mp4` on the server is a 48-byte stub; the desk Virtual Object plays a transcode of its Theora fallback instead.
- The teacher lesson plans still refer students to the removed Activity.

## Educational Features

- Multiple tour options (brief, extended) for each object
- Museum-quality curatorial content
- Teacher lesson plans and activity guides
- Standards alignment for classroom use
- Student tutorial videos

## Credits

**Project Management:**
- Roy Rosenzweig Center for History and New Media (CHNM)
- National Museum of American History (NMAH)

**Key Contributors:**
- Roy Rosenzweig (Principal Investigator)
- Sharon Leon (Director of Public Projects, CHNM)
- Judy Gradwohl (Associate Director, NMAH)
- Multiple museum curators and researchers

## Copyright

Copyright © 2006. A collaborative project between the Smithsonian Institution and George Mason University.
