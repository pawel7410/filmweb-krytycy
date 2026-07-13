const WATCHLIST_KEY = "watchlist";

function getWatchlist() {
  try {
    const raw = localStorage.getItem(WATCHLIST_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch (err) {
    console.error("Nie udało się odczytać listy do obejrzenia", err);
    return [];
  }
}

function saveWatchlist(list) {
  try {
    localStorage.setItem(WATCHLIST_KEY, JSON.stringify(list));
    return true;
  } catch (err) {
    console.error("Nie udało się zapisać listy do obejrzenia", err);
    return false;
  }
}

function isInWatchlist(id) {
  return getWatchlist().some((m) => m.id === id);
}

function addToWatchlist(movie) {
  const list = getWatchlist();
  if (list.some((m) => m.id === movie.id)) return list;
  list.push({
    id: movie.id,
    title: movie.title,
    year: movie.year,
    poster_url: movie.poster_url,
    url: movie.url,
    critics_score: movie.critics_score,
    critics_count: movie.critics_count,
    user_score: movie.user_score,
    genres: movie.genres,
    added_at: new Date().toISOString(),
  });
  saveWatchlist(list);
  return list;
}

function removeFromWatchlist(id) {
  const list = getWatchlist().filter((m) => m.id !== id);
  saveWatchlist(list);
  return list;
}
