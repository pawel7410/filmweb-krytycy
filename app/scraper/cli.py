import argparse
import logging

from app.scraper.pipeline import scrape_year


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Scrape filmweb.pl movies + critics scores for a given year."
    )
    parser.add_argument("--year", type=int, required=True, help="Release year to scrape, e.g. 2023")
    parser.add_argument(
        "--max-pages",
        type=int,
        default=None,
        help="Limit number of ranking pages (50 movies/page) - useful for quick testing",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Bypass the on-disk HTML cache and re-fetch/re-parse everything, including "
        "critics scores that were already fetched before",
    )
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    n_catalog, n_details = scrape_year(
        args.year, force_refresh=args.force, max_pages=args.max_pages
    )
    print(
        "Scraped {} movies for {}, fetched critics score for {} of them.".format(
            n_catalog, args.year, n_details
        )
    )


if __name__ == "__main__":
    main()
