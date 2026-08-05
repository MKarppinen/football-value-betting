from vbet.data.fetchers.football_data_fetcher import FootballDataFetcher


def main():
    fetcher = FootballDataFetcher()

    fetcher.print_matches("PL")


if __name__ == "__main__":
    main()