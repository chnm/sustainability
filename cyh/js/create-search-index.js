/**
 * This script generates a search index by crawling the site content.
 * It would be run on a schedule or as part of the build process to update the search index.
 * 
 * To use this script:
 * 1. Install node.js if not already installed
 * 2. Install required dependencies: npm install jsdom node-fetch fs-extra
 * 3. Run: node create-search-index.js
 */

const fs = require('fs-extra');
const path = require('path');
const { JSDOM } = require('jsdom');
const fetch = require('node-fetch');

// Configuration
const baseDir = path.resolve(__dirname, '..');  // Parent directory of the js folder
const outputFile = path.join(__dirname, 'search-documents.json');
const baseUrl = '';  // Set this to your production URL if needed

// Files to index - you would customize this list or use a directory crawler
const pagesToIndex = [
  { url: 'introduction.html', tags: ['Introduction', 'History'] },
  { url: 'primary-sources.html', tags: ['Primary Sources', 'History'] },
  { url: 'teaching-modules.html', tags: ['Teaching', 'Education', 'Modules'] },
  { url: 'case-studies.html', tags: ['Case Studies', 'Research'] },
  { url: 'about.html', tags: ['About', 'Project Information'] }
];

// Function to extract content from an HTML file
async function extractContentFromFile(filePath, url, tags) {
  try {
    const fileContent = await fs.readFile(filePath, 'utf8');
    const dom = new JSDOM(fileContent);
    const document = dom.window.document;
    
    // Extract title
    const title = document.querySelector('title')?.textContent || 
                 document.querySelector('h1')?.textContent || 
                 path.basename(url, path.extname(url));
    
    // Extract content - this would need to be customized based on your HTML structure
    // This example extracts text from paragraphs, headings, and lists
    const contentElements = [
      ...document.querySelectorAll('p, h1, h2, h3, h4, h5, h6, li')
    ];
    
    const content = contentElements
      .map(el => el.textContent.trim())
      .filter(text => text.length > 0)
      .join(' ')
      .replace(/\s+/g, ' ');
    
    return {
      id: url.replace(/[^a-z0-9]/gi, '_'),
      title,
      content,
      url,
      tags
    };
  } catch (error) {
    console.error(`Error processing ${filePath}:`, error);
    // Return a minimal document to avoid breaking the indexing process
    return {
      id: url.replace(/[^a-z0-9]/gi, '_'),
      title: path.basename(url, path.extname(url)),
      content: '',
      url,
      tags
    };
  }
}

// Main function to generate the search index
async function generateSearchIndex() {
  try {
    const documents = [];
    
    for (const page of pagesToIndex) {
      const filePath = path.join(baseDir, page.url);
      
      // Check if file exists
      if (await fs.pathExists(filePath)) {
        const document = await extractContentFromFile(filePath, page.url, page.tags);
        documents.push(document);
      } else {
        console.warn(`File not found: ${filePath}`);
      }
    }
    
    // Write the search index to file
    await fs.writeJson(outputFile, documents, { spaces: 2 });
    console.log(`Search index created with ${documents.length} documents: ${outputFile}`);
  } catch (error) {
    console.error('Error generating search index:', error);
  }
}

// Run the indexer
generateSearchIndex().catch(console.error);