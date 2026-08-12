// Minimal static server WITH HTTP Range support.
// PMTiles reads its archive with range requests and needs 206 responses;
// `python3 -m http.server` ignores Range and returns the whole file, so the
// basemap cannot be tested against it.
const http = require('http'), fs = require('fs'), path = require('path'), url = require('url');
const ROOT = process.argv[2], PORT = +(process.argv[3] || 8765);
const TYPES = {
  '.html': 'text/html; charset=utf-8', '.css': 'text/css', '.js': 'text/javascript',
  '.json': 'application/json', '.png': 'image/png', '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg', '.gif': 'image/gif', '.svg': 'image/svg+xml',
  '.pmtiles': 'application/octet-stream', '.woff2': 'font/woff2', '.pdf': 'application/pdf',
  '.kml': 'application/vnd.google-earth.kml+xml',
};
http.createServer((req, res) => {
  let p = decodeURIComponent(url.parse(req.url).pathname);
  if (p.endsWith('/')) p += 'index.html';
  const f = path.join(ROOT, p);
  fs.stat(f, (e, st) => {
    if (e || !st.isFile()) { res.writeHead(404); return res.end('not found'); }
    const type = TYPES[path.extname(f).toLowerCase()] || 'application/octet-stream';
    const range = req.headers.range;
    if (range) {
      const m = /bytes=(\d*)-(\d*)/.exec(range);
      const start = m[1] ? +m[1] : 0;
      const end = m[2] ? +m[2] : st.size - 1;
      if (start >= st.size) {
        res.writeHead(416, { 'Content-Range': `bytes */${st.size}` });
        return res.end();
      }
      res.writeHead(206, {
        'Content-Type': type, 'Content-Length': end - start + 1,
        'Content-Range': `bytes ${start}-${end}/${st.size}`, 'Accept-Ranges': 'bytes',
      });
      return fs.createReadStream(f, { start, end }).pipe(res);
    }
    res.writeHead(200, { 'Content-Type': type, 'Content-Length': st.size, 'Accept-Ranges': 'bytes' });
    fs.createReadStream(f).pipe(res);
  });
}).listen(PORT, () => console.log(`serving ${ROOT} on :${PORT} (Range supported)`));
