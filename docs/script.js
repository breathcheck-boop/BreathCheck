const DOWNLOAD_URL = "https://github.com/breathcheck-boop/BreathCheck/raw/main/docs/BreathCheck.zip";
const ASSET_VERSION = "v=20260216";

const slides = [
  {
    src: `./assets/module1/step1.webp?${ASSET_VERSION}`,
    caption: "Step 1: Welcome + Orientation",
  },
  {
    src: `./assets/module1/step2.webp?${ASSET_VERSION}`,
    caption: "Step 2: Anxiety Basics",
  },
  {
    src: `./assets/module1/step3.webp?${ASSET_VERSION}`,
    caption: "Step 3: Fight-or-Flight",
  },
  {
    src: `./assets/module1/step4.webp?${ASSET_VERSION}`,
    caption: "Step 4: Worry Cycle",
  },
  {
    src: `./assets/module1/step5.webp?${ASSET_VERSION}`,
    caption: "Step 5: Concern vs Worry",
  },
  {
    src: `./assets/module1/step6.webp?${ASSET_VERSION}`,
    caption: "Step 6: Domains",
  },
  {
    src: `./assets/module1/step7.webp?${ASSET_VERSION}`,
    caption: "Step 7: Values to Habits",
  },
];

document.querySelectorAll("[data-download-link]").forEach((link) => {
  link.href = DOWNLOAD_URL;
  link.setAttribute("download", "BreathCheck.zip");
});

const slideImage = document.getElementById("slideImage");
const slideCaption = document.getElementById("slideCaption");
const prevBtn = document.getElementById("prevBtn");
const nextBtn = document.getElementById("nextBtn");
const dotsHost = document.getElementById("dots");

if (slideImage && slideCaption && prevBtn && nextBtn && dotsHost) {
  let current = 0;

  function render(index) {
    current = (index + slides.length) % slides.length;
    const active = slides[current];
    slideImage.src = active.src;
    slideCaption.textContent = active.caption;

    dotsHost.querySelectorAll(".dot").forEach((dot, i) => {
      dot.classList.toggle("active", i === current);
    });
  }

  function createDots() {
    slides.forEach((_slide, index) => {
      const dot = document.createElement("button");
      dot.className = "dot";
      dot.setAttribute("aria-label", `Show slide ${index + 1}`);
      dot.addEventListener("click", () => {
        render(index);
        resetAutoRotate();
      });
      dotsHost.appendChild(dot);
    });
  }

  createDots();
  render(0);

  prevBtn.addEventListener("click", () => {
    render(current - 1);
    resetAutoRotate();
  });

  nextBtn.addEventListener("click", () => {
    render(current + 1);
    resetAutoRotate();
  });

  let autoRotate = setInterval(() => render(current + 1), 5500);

  function resetAutoRotate() {
    clearInterval(autoRotate);
    autoRotate = setInterval(() => render(current + 1), 5500);
  }
}

