from .tap import TAPScraper
from .iberia import IberiaScraper
from .british_airways import BritishAirwaysScraper
from .flying_blue import FlyingBlueScraper
from .turkish import TurkishScraper
from .lufthansa import LufthansaScraper
from .aer_lingus import AerLingusScraper


def get_all_scrapers():
    return [
        TAPScraper(),
        IberiaScraper(),
        BritishAirwaysScraper(),
        FlyingBlueScraper(),
        TurkishScraper(),
        LufthansaScraper(),
        AerLingusScraper(),
    ]
