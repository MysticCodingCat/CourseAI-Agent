// Background service worker
console.log("CourseAI Background Service Worker Loaded");

chrome.action.onClicked.addListener(() => {
  chrome.tabs.create({
    url: "main.html"
  });
});