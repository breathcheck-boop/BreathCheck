const slides = [
  {
    src: "assets/module1/step1.webp",
    caption: "Step 1: Welcome + Orientation",
  },
  {
    src: "assets/module1/step2.webp",
    caption: "Step 2: Anxiety Basics",
  },
  {
    src: "assets/module1/step3.webp",
    caption: "Step 3: Fight-or-Flight",
  },
  {
    src: "assets/module1/step4.webp",
    caption: "Step 4: Worry Cycle",
  },
  {
    src: "assets/module1/step5.webp",
    caption: "Step 5: Concern vs Worry",
  },
  {
    src: "assets/module1/step6.webp",
    caption: "Step 6: Domains",
  },
  {
    src: "assets/module1/step7.webp",
    caption: "Step 7: Values to Habits",
  },
];

const slideImage = document.getElementById("slideImage");
const slideCaption = document.getElementById("slideCaption");
const prevBtn = document.getElementById("prevBtn");
const nextBtn = document.getElementById("nextBtn");
const dotsHost = document.getElementById("dots");

let current = 0;

function render(index) {
  current = (index + slides.length) % slides.length;
  const active = slides[current];
  slideImage.src = active.src;
  slideCaption.textContent = active.caption;

  const dots = dotsHost.querySelectorAll(".dot");
  dots.forEach((dot, i) => {
    dot.classList.toggle("active", i === current);
  });
}

function createDots() {
  slides.forEach((_slide, index) => {
    const dot = document.createElement("button");
    dot.className = "dot";
    dot.setAttribute("aria-label", `Show slide ${index + 1}`);
    dot.addEventListener("click", () => render(index));
    dotsHost.appendChild(dot);
  });
}

createDots();
render(0);

prevBtn.addEventListener("click", () => render(current - 1));
nextBtn.addEventListener("click", () => render(current + 1));

let autoRotate = setInterval(() => render(current + 1), 5500);

function resetAutoRotate() {
  clearInterval(autoRotate);
  autoRotate = setInterval(() => render(current + 1), 5500);
}

prevBtn.addEventListener("click", resetAutoRotate);
nextBtn.addEventListener("click", resetAutoRotate);
dotsHost.addEventListener("click", resetAutoRotate);
