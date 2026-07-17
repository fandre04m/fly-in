

class Extractor:
    def load_config(self, config_file: str) -> None:
        try:
            with open(config_file) as f:
                print(f)
        except FileNotFoundError as e:
            print(f"{e}")


def main() -> None:
    extractor = Extractor()
    extractor.load_config("../config.txt")


main()
