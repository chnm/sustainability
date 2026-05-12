const fs = require('fs');
const path = require('path');
const cheerio = require('cheerio');

const baseDir = __dirname;
const outputFilePath = path.join(baseDir, 'js', 'search-documents.json');

// Load stopwords
const stopwordsFilePath = path.join(baseDir, 'search', 'stopwords.txt');
let stopwords = [];
try {
  const stopwordsContent = fs.readFileSync(stopwordsFilePath, 'utf8');
  stopwords = stopwordsContent.split('\n')
    .filter(word => word.trim() !== '')
    .map(word => word.trim().toLowerCase());
  console.log(`Loaded ${stopwords.length} stopwords`);
} catch (error) {
  console.warn('Could not load stopwords file:', error.message);
}

// Directories/files to skip
const skipPatterns = [
  'node_modules',
  'search.html',       // our own search page
  'robots.txt.html',
  'newsletter.php.html',
  'search.php',        // old search result pages
];

function shouldSkip(filePath) {
  const relative = path.relative(baseDir, filePath);
  return skipPatterns.some(pattern => relative.includes(pattern));
}

function findHtmlFiles(dir, fileList = []) {
  const files = fs.readdirSync(dir);
  files.forEach(file => {
    const filePath = path.join(dir, file);
    const stat = fs.statSync(filePath);
    if (stat.isDirectory() && !file.startsWith('.') && file !== 'node_modules') {
      findHtmlFiles(filePath, fileList);
    } else if (file.endsWith('.html') && !shouldSkip(filePath)) {
      fileList.push(filePath);
    }
  });
  return fileList;
}

function removeStopwords(text) {
  if (stopwords.length === 0) return text;
  const words = text.toLowerCase().split(/\s+/);
  return words.filter(word => {
    const clean = word.replace(/[^\w]/g, '');
    return clean !== '' && !stopwords.includes(clean);
  }).join(' ');
}

// Determine section label from file path
function getSection(relativePath) {
  if (relativePath.startsWith('d/')) return 'Resource';
  if (relativePath.startsWith('browse/manypasts/') || relativePath.startsWith('text/')) return 'Many Pasts';
  if (relativePath.startsWith('browse/makesense/') || relativePath.startsWith('mse/')) return 'Making Sense of Evidence';
  if (relativePath.startsWith('browse/wwwhistory/') || relativePath.startsWith('reviews/')) return 'WWW.History';
  if (relativePath.startsWith('browse/digblack/')) return 'Digital Blackboard';
  if (relativePath.startsWith('browse/refdesk/')) return 'Reference Desk';
  if (relativePath.startsWith('browse/talkhist/') || relativePath.startsWith('talkinghistory/')) return 'Talking History';
  if (relativePath.startsWith('browse/syllabus/') || relativePath.startsWith('syllabi/')) return 'Syllabus Central';
  if (relativePath.startsWith('browse/studhist/')) return 'Students as Historians';
  if (relativePath.startsWith('browse/secrets/')) return 'Secrets of Great History Teachers';
  if (relativePath.startsWith('browse/puzzled/') || relativePath.includes('puzzle')) return 'Puzzled by the Past';
  if (relativePath.startsWith('browse/pmeetsp/')) return 'Past Meets Present';
  if (relativePath.startsWith('blackboard/')) return 'Digital Blackboard';
  return '';
}

function extractContent(filePath) {
  try {
    const html = fs.readFileSync(filePath, 'latin1');
    const $ = cheerio.load(html);

    // Remove non-content elements
    $('script').remove();
    $('style').remove();
    $('.archive-notice').remove();

    // Get title
    let title = $('title').text().trim();
    if (!title) {
      title = $('h1').first().text().trim() || path.basename(filePath, '.html');
    }
    // Clean up common title suffixes
    title = title.replace(/\s*-\s*History Matters.*$/i, '').trim();
    if (!title) title = path.basename(filePath, '.html');

    // Extract body text, cap at 5000 chars to keep index size manageable
    const bodyText = ($('#container').text() || $('body').text() || '')
      .replace(/\s+/g, ' ').trim().slice(0, 5000);
    const content = removeStopwords(bodyText);

    const relativePath = path.relative(baseDir, filePath);
    const section = getSection(relativePath);

    return { title, content, url: relativePath, section };
  } catch (error) {
    console.error(`Error processing ${filePath}:`, error.message);
    return null;
  }
}

function generateSearchIndex() {
  console.log('Finding HTML files...');
  const htmlFiles = findHtmlFiles(baseDir);
  console.log(`Found ${htmlFiles.length} HTML files`);

  const documents = htmlFiles
    .map((filePath, index) => {
      const doc = extractContent(filePath);
      if (doc) return { id: index + 1, ...doc };
      return null;
    })
    .filter(Boolean);

  console.log(`Indexed ${documents.length} documents`);
  fs.writeFileSync(outputFilePath, JSON.stringify(documents));
  console.log(`Search index written to ${outputFilePath}`);
}

generateSearchIndex();
