const calculator = document.getElementById("price-calculator");

if (calculator) {
  calculator.addEventListener("submit", (event) => {
    event.preventDefault();

    const type = document.getElementById("project-type").value;
    const design = document.getElementById("design-level").value;
    const pages = Number(document.getElementById("pages-count").value) || 1;
    const needCopy = document.getElementById("need-copy").checked;
    const needAnim = document.getElementById("need-anim").checked;

    const typeMap = {
      landing: { base: 90000, days: 10 },
      corporate: { base: 170000, days: 20 },
      ecommerce: { base: 270000, days: 32 },
      webapp: { base: 390000, days: 45 }
    };

    const designMap = {
      basic: 1,
      premium: 1.25,
      luxury: 1.5
    };

    const selectedType = typeMap[type];
    const designCoef = designMap[design];

    let price = selectedType.base * designCoef;
    let days = selectedType.days + Math.max(0, pages - 3) * 1.6;

    if (needCopy) {
      price += 25000;
      days += 4;
    }

    if (needAnim) {
      price += 35000;
      days += 5;
    }

    const minPrice = Math.round(price * 0.92);
    const maxPrice = Math.round(price * 1.12);
    const minWeeks = Math.max(2, Math.floor(days / 5));
    const maxWeeks = Math.ceil((days * 1.2) / 5);

    document.getElementById("result-price").textContent = `от ${minPrice.toLocaleString("ru-RU")} до ${maxPrice.toLocaleString("ru-RU")} ₽`;
    document.getElementById("result-time").textContent = `${minWeeks}-${maxWeeks} недель`;
  });
}

const filterButtons = document.querySelectorAll(".filter-btn");
const portfolioCards = document.querySelectorAll(".portfolio-card");

if (filterButtons.length && portfolioCards.length) {
  filterButtons.forEach((button) => {
    button.addEventListener("click", () => {
      filterButtons.forEach((btn) => btn.classList.remove("active"));
      button.classList.add("active");

      const currentFilter = button.dataset.filter;
      portfolioCards.forEach((card) => {
        const category = card.dataset.category;
        const showCard = currentFilter === "all" || category === currentFilter;
        card.style.display = showCard ? "block" : "none";
      });
    });
  });
}
