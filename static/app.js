const state = {
  year: "",
  genre: "",
  minVotes: 0,
  sort: "critics_score",
  order: "desc",
  page: 1,
  pageSize: 24,
  total: 0,
  isLoading: false,
  hasMore: true,
};

const el = {
  year: document.getElementById("filter-year"),
  genre: document.getElementById("filter-genre"),
  minVotes: document.getElementById("filter-min-votes"),
  sort: document.getElementById("filter-sort"),
  order: document.getElementById("filter-order"),
  list: document.getElementById("movie-list"),
  status: document.getElementById("status"),
  sentinel: document.getElementById("scroll-sentinel"),
  loadMoreStatus: document.getElementById("load-more-status"),
  backToFilters: document.getElementById("back-to-filters"),
  filters: document.querySelector(".filters"),
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

function movieCard(movie) {
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
  return card;
}

function appendMovies(payload) {
  for (const movie of payload.results) {
    el.list.appendChild(movieCard(movie));
  }

  state.total = payload.total;
  state.hasMore = state.page * state.pageSize < payload.total;
  el.loadMoreStatus.textContent = state.hasMore ? "" : `To wszystkie filmy (${payload.total}).`;
}

let currentRequestId = 0;

async function loadNextPage() {
  if (state.isLoading || !state.hasMore) return;
  const requestId = currentRequestId;
  state.isLoading = true;
  el.loadMoreStatus.textContent = "Ładowanie kolejnych filmów...";

  try {
    const response = await fetch(`/api/movies?${buildQuery()}`);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const payload = await response.json();
    // A filter change may have started a new "generation" of requests while this
    // one was in flight - discard the now-stale response instead of appending it
    // out of order on top of the (already cleared/replaced) list.
    if (requestId !== currentRequestId) return;
    appendMovies(payload);
    state.page += 1;
  } catch (err) {
    if (requestId === currentRequestId) {
      el.loadMoreStatus.textContent = `Błąd ładowania danych: ${err.message}`;
    }
  } finally {
    if (requestId === currentRequestId) {
      state.isLoading = false;
      // IntersectionObserver only fires on a change in intersection state. If the
      // sentinel is still on-screen after this page loaded (short result set, or a
      // tall viewport), re-observing forces a fresh check so loading continues
      // instead of silently stopping until the user manually scrolls away and back.
      observer.unobserve(el.sentinel);
      observer.observe(el.sentinel);
    }
  }
}

async function resetAndLoad() {
  currentRequestId += 1;
  state.page = 1;
  state.hasMore = true;
  state.isLoading = false;
  el.list.innerHTML = "";
  el.loadMoreStatus.textContent = "";
  el.status.textContent = "Ładowanie...";

  await loadNextPage();
  el.status.textContent = state.total === 0 ? "Brak filmów spełniających kryteria." : "";
}

function onFilterChange() {
  state.year = el.year.value;
  state.genre = el.genre.value;
  state.minVotes = Number(el.minVotes.value) || 0;
  state.sort = el.sort.value;
  state.order = el.order.value;
  resetAndLoad();
}

el.year.addEventListener("change", onFilterChange);
el.genre.addEventListener("change", onFilterChange);
el.minVotes.addEventListener("change", onFilterChange);
el.sort.addEventListener("change", onFilterChange);
el.order.addEventListener("change", onFilterChange);

const observer = new IntersectionObserver(
  (entries) => {
    if (entries[0].isIntersecting) loadNextPage();
  },
  { rootMargin: "600px" }
);
observer.observe(el.sentinel);

el.backToFilters.addEventListener("click", () => {
  el.filters.scrollIntoView({ behavior: "smooth", block: "start" });
});

window.addEventListener("scroll", () => {
  el.backToFilters.classList.toggle("visible", window.scrollY > 400);
});

loadFilterOptions().then(resetAndLoad);
