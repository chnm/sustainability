// Script to generate a comprehensive search-documents.json file
// This script will scan all HTML files and create entries for the search index

const fs = require("fs");
const path = require("path");
const cheerio = require("cheerio");

// Configuration object - can be customized for different static sites
const config = {
  // Base directory to start scanning
  baseDir: __dirname,

  // Output file path relative to baseDir
  outputPath: "js/search-documents.json",

  // Path to stopwords file relative to baseDir
  stopwordsPath: "static-search/stopwords.txt",

  // Directories to exclude from scanning (relative to baseDir)
  excludeDirs: ["node_modules", ".git", ".github", "category", "themes", "admin", "shared"],

  // File patterns to exclude (using includes check)
  excludePatterns: [
    "?output=rss2.html",
    "feed/",
    "wp-json/",
    "wp-includes/",
    "category/",
    ".htaccess_old",
    "advancedsearch.html",
    "advancedsearch?sort=alpha.html",
    "advancedsearch?sort=least.html",
    "advancedsearch?sort=most.html",
    "items/browse/",
    "exhibits/unique-experience-of-romania/primary-sources/",
    "exhibits/solidarity-comes-to-power/primary-sources/",
    "exhibits/roman-catholic-church/sources/",
    "exhibits/nationalities/primary-sources/",
    "exhibits/everyday-life/primary-sources/",
    "exhibits/economies-in-transition/primary-sources/",
  ],

  // Content type mapping based on directory patterns
  // Each entry is checked with relativePath.startsWith(key)
  contentTypeMapping: {
    "exhibits/": "Page",
    "items/": "Page",
    "items/browse/tag/": "Tag"

  },

  // Default content type if no mapping matches
  defaultContentType: "Page",

  // HTML selectors for content extraction
  selectors: {
    // Main content selectors, tried in order
    content: [
      "#content",
      "#primary",
      "main",
      "article",
      ".entry-content",
      ".post-content",
      "#exhibit-description",
      "#item-text"
    ],

    tags: [
      "#item-tags",
    ],

    // Title extraction selectors and fallbacks
    title: ["#primary-source > h3", "h3#section-title", "title", "#title", "h1", "#exhibit-title", "#title > a", "body > h2", "#primary > h2"],

    // Additional heading to prepend to title if found
    additionalHeading: ["#item-text h3", "h2.subtitle", ".episode-subtitle"],

    // Elements to remove before content extraction
    remove: [
      "script",
      "style",
      "nav",
      "header",
      "footer",
      ".sidebar",
      ".navigation",
      ".comments",
      ".widget-area",
      "head",
      "#header",
      ".exhibit-section-nav",
      "h4",
      "#searchwrap",
      "#thumb",
      "#item-data h3",
      "#module-nav",
      "#questions > ul"
    ],
  },
};

// Ensure the output directory exists
const outputDir = path.dirname(path.join(config.baseDir, config.outputPath));
if (!fs.existsSync(outputDir)) {
  console.log(`Creating output directory: ${outputDir}`);
  fs.mkdirSync(outputDir, { recursive: true });
}

// Output file path
const outputFilePath = path.join(config.baseDir, config.outputPath);

// Load stopwords from file
const stopwordsFilePath = path.join(config.baseDir, config.stopwordsPath);
let stopwords = [];
try {
  const stopwordsContent = fs.readFileSync(stopwordsFilePath, "utf8");
  stopwords = stopwordsContent
    .split("\n")
    .filter((word) => word.trim() !== "")
    .map((word) => word.trim().toLowerCase());
  console.log(`Loaded ${stopwords.length} stopwords from ${stopwordsFilePath}`);
} catch (error) {
  console.warn(
    "Could not load stopwords file, proceeding without stopwords:",
    error,
  );
}

// Function to recursively find all HTML files
function findHtmlFiles(dir, fileList = []) {
  try {
    const files = fs.readdirSync(dir);

    files.forEach((file) => {
      const filePath = path.join(dir, file);

      // Skip if the file doesn't exist or is not accessible
      if (!fs.existsSync(filePath)) {
        return;
      }

      const stat = fs.statSync(filePath);

      // Skip excluded directories
      if (config.excludeDirs.some((exclude) => file === exclude)) {
        return;
      }

      // Skip files matching exclude patterns
      if (
        config.excludePatterns.some((pattern) => filePath.includes(pattern))
      ) {
        return;
      }

      if (stat.isDirectory()) {
        // Recursively scan subdirectories
        fileList = findHtmlFiles(filePath, fileList);
      } else if (file.endsWith(".html")) {
        // Add HTML files to the list
        fileList.push(filePath);
      }
    });
  } catch (error) {
    console.error(`Error scanning directory ${dir}:`, error);
  }

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
  const filteredWords = words.filter((word) => {
    // Clean word of punctuation for comparison
    const cleanWord = word.replace(/[^\w]/g, "");
    return cleanWord !== "" && !stopwords.includes(cleanWord);
  });

  // Join back into a string
  return filteredWords.join(" ");
}

// Function to determine content type based on file path
function determineContentType(relativePath) {
  // Check for content type mapping matches
  for (const [pattern, type] of Object.entries(config.contentTypeMapping)) {
    if (relativePath.startsWith(pattern)) {
      return type;
    }
  }

  // Fall back to default content type
  return config.defaultContentType;
}

// Function to extract content from HTML files
function extractContentFromHtml(filePath) {
  try {
    const html = fs.readFileSync(filePath, "utf8");
    const $ = cheerio.load(html);

    // Remove scripts, styles, and other non-content elements
    config.selectors.remove.forEach((selector) => {
      $(selector).remove();
    });

    // Get the title using configured selectors
    let title = "";
    for (const selector of config.selectors.title) {
      const titleText = $(selector).first().text().trim();
      if (titleText) {
        title = titleText;
        break;
      }
    }

    // If no title found, use the filename
    if (!title) {
      title = path.basename(filePath, ".html").replace(/-/g, " ");
    }

    // Look for additional heading to prepend to the title
    for (const selector of config.selectors.additionalHeading) {
      const headingText = $(selector).first().text().trim();
      if (headingText && !title.includes(headingText)) {
        title = `${headingText} - ${title}`;
        break;
      }
    }

    // Extract main content using configured selectors
    let mainContent = "";
    for (const selector of config.selectors.content) {
      const content = $(selector).text().trim();
      if (content) {
        mainContent = content;
        break;
      }
    }

    // Fall back to body if no content found with selectors
    if (!mainContent) {
      mainContent = $("body").text().trim();
    }

    // Clean up the content (remove extra whitespace)
    const contentWithStopwords = mainContent.replace(/\s+/g, " ").trim();

    // Remove stopwords from content
    let content = removeStopwords(contentWithStopwords);

    // Make the URL relative to the baseDir
    const relativePath = path.relative(config.baseDir, filePath);

    // Ensure question marks in the URL are properly encoded
    //const encodedRelativePath = relativePath.replace(/\?/g, "%3F");
    const encodedRelativePath = "/" + relativePath

    // Determine content type based on file path
    const contentType = determineContentType(relativePath);

    // Extract tags from meta keywords or specific tag elements
    let tags = [];

    // Check for item-tags div with an unordered list
    if ($("#item-tags ul li").length > 0) {
      $("#item-tags ul li").each((index, element) => {
        // Get the text content but remove the trailing comma if present
        const tagText = $(element).text().trim();
        const tag = tagText.replace(/,\s*$/, "").trim();
        if (tag) tags.push(tag);
      });
    }
    // Check for p.categories with category links
    else if ($("p.categories a").length > 0) {
      $("p.categories a").each((index, element) => {
        const tag = $(element).text().trim();
        if (tag) tags.push(tag);
      });
    }
    // Then check for meta keywords if no item-tags found
    else if ($('meta[name="keywords"]').attr("content")) {
      tags = $('meta[name="keywords"]')
        .attr("content")
        .split(",")
        .map((tag) => tag.trim());
    }
    // Check for category links
    else if ($(".cat-links a").length > 0) {
      $(".cat-links a").each((index, element) => {
        const tag = $(element).text().trim();
        if (tag) tags.push(tag);
      });
    }
    // Check for tag links
    else if ($(".tags-links a").length > 0) {
      $(".tags-links a").each((index, element) => {
        const tag = $(element).text().trim();
        if (tag) tags.push(tag);
      });
    }

    // Create the document entry
    const document = {
      title,
      content,
      url: encodedRelativePath,
      tags: tags,
      contentType: contentType,
    };

    // Add publication date if available (common in blogs/podcasts)
    const datePublished =
      $('meta[property="article:published_time"]').attr("content") ||
      $("time.published").attr("datetime") ||
      $("time.entry-date").attr("datetime");

    if (datePublished) {
      document.date = datePublished;
    }

    return document;
  } catch (error) {
    console.error(`Error processing file ${filePath}:`, error);
    return null;
  }
}

// Main function to generate the search index
async function generateSearchIndex() {
  try {
    console.log("Finding HTML files...");
    const htmlFiles = findHtmlFiles(config.baseDir);
    console.log(`Found ${htmlFiles.length} HTML files.`);

    console.log("Extracting content from HTML files...");
    if (stopwords.length > 0) {
      console.log(
        `Will filter out ${stopwords.length} stopwords from content.`,
      );
    } else {
      console.log(
        "No stopwords loaded, proceeding without stopword filtering.",
      );
    }

    // Create a map to track normalized URLs to avoid duplicates
    const urlMap = new Map();

    const searchDocuments = htmlFiles
      .map((filePath, index) => {
        if (index % 100 === 0) {
          console.log(`Processing file ${index + 1}/${htmlFiles.length}...`);
        }

        const documentContent = extractContentFromHtml(filePath);
        if (documentContent) {
          // Normalize URL by removing index.html to avoid duplicates
          const normalizedUrl = documentContent.url.replace(/\/index\.html$/, '/');
          
          // Skip if we've already processed this normalized URL
          if (urlMap.has(normalizedUrl)) {
            return null;
          }
          
          // Mark this URL as processed
          urlMap.set(normalizedUrl, true);
          
          // Log sample of content with stopwords removed (first file only)
          if (index === 0 && stopwords.length > 0) {
            const beforeWords = documentContent.content.split(/\s+/).length;
            const sampleBefore = documentContent.content
              .split(/\s+/)
              .slice(0, 20)
              .join(" ");
            console.log(
              `\nSample content after stopword removal (first 20 words): "${sampleBefore}..."`,
            );
            console.log(
              `Content length after stopword removal: ${beforeWords} words\n`,
            );
          }

          return {
            id: index + 1,
            ...documentContent,
          };
        }
        return null;
      })
      .filter(Boolean); // Remove any null entries

    console.log(
      `Successfully extracted content from ${searchDocuments.length} files.`,
    );

    // Group documents by content type
    const contentTypeCounts = {};
    searchDocuments.forEach((doc) => {
      contentTypeCounts[doc.contentType] =
        (contentTypeCounts[doc.contentType] || 0) + 1;
    });

    console.log("Content type breakdown:");
    Object.entries(contentTypeCounts).forEach(([type, count]) => {
      console.log(`  ${type}: ${count} documents`);
    });

    // Write the search documents to the output file
    fs.writeFileSync(outputFilePath, JSON.stringify(searchDocuments, null, 2));
    console.log(`Search index written to ${outputFilePath}`);
    console.log(
      `Output file size: ${(fs.statSync(outputFilePath).size / 1024 / 1024).toFixed(2)} MB`,
    );
    console.log(
      `Search index includes stopword filtering: ${stopwords.length > 0 ? "Yes" : "No"}`,
    );
  } catch (error) {
    console.error("Error generating search index:", error);
  }
}

// Run the function
generateSearchIndex();

