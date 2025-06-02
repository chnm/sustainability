// Script to generate a comprehensive search-documents.json file
// This script will scan all HTML files and create entries for the search index

const fs = require('fs');
const path = require('path');
const cheerio = require('cheerio');

// Base directory to start scanning
const baseDir = __dirname;
// Output file path
const outputFilePath = path.join(baseDir, 'js', 'search-documents.json');

// Load stopwords from file
const stopwordsFilePath = path.join(baseDir, 'search', 'stopwords.txt');
let stopwords = [];
try {
  const stopwordsContent = fs.readFileSync(stopwordsFilePath, 'utf8');
  stopwords = stopwordsContent.split('\n')
    .filter(word => word.trim() !== '')
    .map(word => word.trim().toLowerCase());
  console.log(`Loaded ${stopwords.length} stopwords from ${stopwordsFilePath}`);
} catch (error) {
  console.warn('Could not load stopwords file, proceeding without stopwords:', error);
}

// Function to recursively find all HTML files
function findHtmlFiles(dir, fileList = []) {
  const files = fs.readdirSync(dir);
  
  files.forEach(file => {
    const filePath = path.join(dir, file);
    const stat = fs.statSync(filePath);
    
    // Skip the primary-sources/browse/ directory
    if (filePath.includes('primary-sources/browse/')) {
      return;
    }
    // Skip the items/browse/ directory
    if (filePath.includes('items/browse/')) {
      return;
    }
    // If a file contains the string "?output=rss2.html", skip it
    if (filePath.includes('?output=rss2.html')) {
      return;
    }
    
    if (stat.isDirectory() && !file.startsWith('.') && file !== 'node_modules') {
      fileList = findHtmlFiles(filePath, fileList);
    } else if (file.endsWith('.html') && !file.includes('?output=rss2')) {
      // Skip RSS feed HTML files
      fileList.push(filePath);
    }
  });
  
  return fileList;
}

// Function to remove stopwords from text
function removeStopwords(text) {
  if (stopwords.length === 0) {
    return text; // No stopwords to remove
  }
  
  // Convert to lowercase and split into words
  const words = text.toLowerCase().split(/\s+/);
  
  // Filter out stopwords
  const filteredWords = words.filter(word => {
    // Clean word of punctuation for comparison
    const cleanWord = word.replace(/[^\w]/g, '');
    return cleanWord !== '' && !stopwords.includes(cleanWord);
  });
  
  // Join back into a string
  return filteredWords.join(' ');
}

// Function to extract content from HTML files
function extractContentFromHtml(filePath) {
  try {
    const html = fs.readFileSync(filePath, 'utf8');
    const $ = cheerio.load(html);
    
    // Remove scripts, styles, and other non-content elements
    $('script').remove();
    $('style').remove();
    $('nav').remove();
    $('header').remove();
    $('footer').remove();
    
    // Get the title from the title tag or the first h1
    let title = $('title').text().trim();
    if (!title) {
      title = $('h1').first().text().trim() || path.basename(filePath, '.html');
    }
    
    // Look for the first h3 tag in the item-text div and prepend to the title
    const firstH3 = $('#item-text h3').first();
    if (firstH3.length > 0) {
      const h3Text = firstH3.text().trim();
      if (h3Text) {
        title = `${h3Text} - ${title}`;
        console.log(`Added first h3 heading to title for ${path.relative(baseDir, filePath)}`);
      }
    }
    
    // Extract main content from the body
    // This selects either the main element, the primary element, or falls back to the body
    const mainContent = $('#content, #primary, main, article').text() || $('body').text();
    
    // Clean up the content (remove extra whitespace)
    const contentWithStopwords = mainContent.replace(/\s+/g, ' ').trim();
    
    // Remove stopwords from content
    let content = removeStopwords(contentWithStopwords);
    
    // Make the URL relative to the baseDir
    const relativePath = path.relative(baseDir, filePath);

    // Ensure question marks in the URL are properly encoded
    const encodedRelativePath = relativePath.replace(/\?/g, '%3F');
    
    // Determine content type based on file path
    let contentType = 'Other';
    if (relativePath.startsWith('case-studies/')) {
      contentType = 'Case Study';
    } else if (relativePath.startsWith('teaching-modules/')) {
      contentType = 'Teaching Module';
    } else if (relativePath.startsWith('items/')) {
      contentType = 'Primary Source';
    } else if (relativePath.startsWith('primary-sources/')) {
      contentType = 'Primary Source';
    } else if (relativePath.startsWith('website-reviews/')) {
      contentType = 'Website Review';
    }
    
    // Extract tags from the item-tags div
    let tags = [];
    
    // First check for item-tags div with an unordered list
    if ($('#item-tags ul li').length > 0) {
      $('#item-tags ul li').each((index, element) => {
        // Get the text content but remove the trailing comma if present
        const tagText = $(element).text().trim();
        const tag = tagText.replace(/,\s*$/, '').trim();
        if (tag) tags.push(tag);
      });
    } 
    // Then check for meta keywords if no item-tags found
    else if ($('meta[name="keywords"]').attr('content')) {
      tags = $('meta[name="keywords"]').attr('content').split(',').map(tag => tag.trim());
    }
    
    console.log(`Extracted ${tags.length} tags for ${relativePath}`);
    // Log the first few tags for debugging
    if (tags.length > 0) {
      console.log(`Sample tags: ${tags.slice(0, 3).join(', ')}`);
    }
    
    return {
      title,
      content,
      url: encodedRelativePath,
      tags: tags,
      contentType: contentType
    };
  } catch (error) {
    console.error(`Error processing file ${filePath}:`, error);
    return null;
  }
}

// Main function to generate the search index
async function generateSearchIndex() {
  try {
    console.log('Finding HTML files...');
    const htmlFiles = findHtmlFiles(baseDir);
    console.log(`Found ${htmlFiles.length} HTML files.`);
    
    console.log('Extracting content from HTML files...');
    if (stopwords.length > 0) {
      console.log(`Will filter out ${stopwords.length} stopwords from content.`);
    } else {
      console.log('No stopwords loaded, proceeding without stopword filtering.');
    }
    
    const searchDocuments = htmlFiles
      .map((filePath, index) => {
        const documentContent = extractContentFromHtml(filePath);
        if (documentContent) {
          // Log sample of content with stopwords removed (first file only)
          if (index === 0 && stopwords.length > 0) {
            const beforeWords = documentContent.content.split(/\s+/).length;
            const sampleBefore = documentContent.content.split(/\s+/).slice(0, 20).join(' ');
            console.log(`\nSample content after stopword removal (first 20 words): "${sampleBefore}..."`);
            console.log(`Content length after stopword removal: ${beforeWords} words\n`);
          }
          
          return {
            id: index + 1,
            ...documentContent
          };
        }
        return null;
      })
      .filter(Boolean); // Remove any null entries
    
    console.log(`Successfully extracted content from ${searchDocuments.length} files.`);
    
    // Write the search documents to the output file
    fs.writeFileSync(outputFilePath, JSON.stringify(searchDocuments, null, 2));
    console.log(`Search index written to ${outputFilePath}`);
    console.log(`Search index includes stopword filtering: ${stopwords.length > 0 ? 'Yes' : 'No'}`);
  } catch (error) {
    console.error('Error generating search index:', error);
  }
}

// Run the function
generateSearchIndex();