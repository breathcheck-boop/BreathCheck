const DOWNLOAD_URL = "https://github.com/breathcheck-boop/BreathCheck/releases/latest";

document.querySelectorAll("[data-download-link]").forEach((link) => {
  link.href = DOWNLOAD_URL;
});
