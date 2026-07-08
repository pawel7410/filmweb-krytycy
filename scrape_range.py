import argparse
import logging
import time
import traceback

from app.scraper.pipeline import scrape_year

LOG_FILE = "scrape_range.log"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Scrape a contiguous range of years, one after another, logging progress to a file."
    )
    parser.add_argument("--start-year", type=int, default=1950)
    parser.add_argument("--end-year", type=int, default=2021)
    parser.add_argument(
        "--force", action="store_true", help="Re-fetch everything, ignoring the HTML cache and already-fetched critics scores"
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[logging.FileHandler(LOG_FILE, encoding="utf-8"), logging.StreamHandler()],
    )
    logger = logging.getLogger("scrape_range")

    years = list(range(args.start_year, args.end_year + 1))
    logger.info("Starting batch scrape: %d years (%d-%d)", len(years), args.start_year, args.end_year)

    ok_count = 0
    failed_years = []

    for year in years:
        started = time.monotonic()
        try:
            n_catalog, n_details = scrape_year(year, force_refresh=args.force)
        except Exception:
            logger.error("Year %d FAILED, skipping. Traceback:\n%s", year, traceback.format_exc())
            failed_years.append(year)
            continue

        elapsed = time.monotonic() - started
        ok_count += 1
        logger.info(
            "Year %d done: %d movies in catalog, %d critics scores fetched (%.0fs)",
            year, n_catalog, n_details, elapsed,
        )

    logger.info(
        "Batch scrape finished. %d/%d years OK. Failed years: %s",
        ok_count, len(years), failed_years or "none",
    )


if __name__ == "__main__":
    main()
