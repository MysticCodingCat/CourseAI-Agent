// A lightweight Markdown parser for CourseAI Demo
// Supports: # Headers, * List, **Bold**, > Blockquote

const SimpleMarkdown = {
  parse: function (text) {
    if (!text) return "";

    // Escape HTML to prevent XSS
    let html = text
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");

    // Headers
    html = html.replace(/^# (.*$)/gim, '<h1>$1</h1>');
    html = html.replace(/^## (.*$)/gim, '<h2>$1</h2>');
    html = html.replace(/^### (.*$)/gim, '<h3>$1</h3>');

    // Blockquotes
    html = html.replace(/^\> (.*$)/gim, '<blockquote>$1</blockquote>');

    // Bold
    html = html.replace(/\*\*(.*)\*\*/gim, '<strong>$1</strong>');
    
    // Lists (Simple bullet points)
    // Look for lines starting with * or -
    html = html.replace(/^\s*[\*\-] (.*$)/gim, '<ul><li>$1</li></ul>');
    // Fix nested uls (crude way but works for visual)
    html = html.replace(/<\/ul>\s*<ul>/gim, '');

    // Paragraphs (Double newlines)
    html = html.replace(/\n\n/gim, '<br><br>');
    html = html.replace(/\n/gim, '<br>');

    return html;
  }
};

// Expose to global window
window.SimpleMarkdown = SimpleMarkdown;
