const state = {
  year: "",
  genre: "",
  minVotes: 0,
  sort: "critics_score",
  order: "desc",
  page: 1,
  pageSize: 24,
};

const el = {
  year: document.getElementById("filter-year"),
  genre: document.getElementById("filter-genre"),
  minVotes: document.getElementById("filter-min-votes"),
  sort: document.getElementById("filter-sort"),
  order: document.getElementById("filter-order"),
  list: document.getElementById("movie-list"),
  status: document.getElementById("status"),
  prevPage: document.getElementById("prev-page"),
  nextPage: document.getElementById("next-page"),
  pageInfo: document.getElementById("page-info"),
};

async function loadFilterOptions() {
  const [years, genres] = await Promise.all([
    fetch("/api/years").then((r) => r.json()),
    fetch("/api/genres").then((r) => r.json()),
  ]);

  for (const year of years) {
    const opt = document.createElement("option");
    opt.value = year;
    opt.textContent = year;
    el.year.appendChild(opt);
  }

  for (const genre of genres) {
    const opt = document.createElement("option");
    opt.value = genre.name;
    opt.textContent = genre.name;
    el.genre.appendChild(opt);
  }
}

function buildQuery() {
  const params = new URLSearchParams();
  if (state.year) params.set("year", state.year);
  if (state.genre) params.set("genre", state.genre);
  if (state.minVotes) params.set("min_critics_votes", state.minVotes);
  params.set("sort", state.sort);
  params.set("order", state.order);
  params.set("page", state.page);
  params.set("page_size", state.pageSize);
  return params.toString();
}

function renderMovies(payload) {
  el.list.innerHTML = "";
  for (const movie of payload.results) {
    const card = document.createElement("a");
    card.className = "movie-card";
    card.href = movie.url;
    card.target = "_blank";
    card.rel = "noopener";

    const genres = movie.genres.map((g) => g.name).join(", ");
    const criticsScore = movie.critics_score != null ? movie.critics_score.toFixed(1) : "-";
    const userScore = movie.user_score != null ? movie.user_score.toFixed(1) : "-";

    card.innerHTML = `
      <img src="${movie.poster_url || ""}" alt="" loading="lazy" />
      <div class="movie-card__body">
        <div class="movie-card__title">${movie.title}</div>
        <div class="movie-card__meta">${movie.year} &middot; ${genres}</div>
        <div class="movie-card__scores">
          <span class="score--critics">★ ${criticsScore} (${movie.critics_count ?? 0} krytyków)</span>
          <span class="score--user">${userScore} userzy</span>
        </div>
      </div>
    `;
    el.list.appendChild(card);
  }

  const totalPages = Math.max(1, Math.ceil(payload.total / payload.page_size));
  el.pageInfo.textContent = `Strona ${payload.page} z ${totalPages} (${payload.total} filmów)`;
  el.prevPage.disabled = payload.page <= 1;
  el.nextPage.disabled = payload.page >= totalPages;
}

async function refresh() {
  el.status.textContent = "Ładowanie...";
  try {
    const response = await fetch(`/api/movies?${buildQuery()}`);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const payload = await response.json();
    renderMovies(payload);
    el.status.textContent = payload.total === 0 ? "Brak filmów spełniających kryteria." : "";
  } catch (err) {
    el.status.textContent = `Błąd ładowania danych: ${err.message}`;
  }
}

function onFilterChange() {
  state.year = el.year.value;
  state.genre = el.genre.value;
  state.minVotes = Number(el.minVotes.value) || 0;
  state.sort = el.sort.value;
  state.order = el.order.value;
  state.page = 1;
  refresh();
}

el.year.addEventListener("change", onFilterChange);
el.genre.addEventListener("change", onFilterChange);
el.minVotes.addEventListener("change", onFilterChange);
el.sort.addEventListener("change", onFilterChange);
el.order.addEventListener("change", onFilterChange);

el.prevPage.addEventListener("click", () => {
  if (state.page > 1) {
    state.page -= 1;
    refresh();
  }
});
el.nextPage.addEventListener("click", () => {
  state.page += 1;
  refresh();
});

loadFilterOptions().then(refresh);
