from urllib.parse import urljoin

import scrapy
from scrapy.utils.reactor import install_reactor

install_reactor("twisted.internet.asyncioreactor.AsyncioSelectorReactor")


class BookingSpider(scrapy.Spider):
    name = "booking_spider"
    allowed_domains = ["booking.com"]

    # Add headers to mimic a browser
    custom_settings = {
        "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
        "ROBOTSTXT_OBEY": False,
        "COOKIES_ENABLED": True,
        "DOWNLOAD_DELAY": 2,
        "TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
    }

    def __init__(
        self,
        location="Dhaka, Bangladesh",
        checkin="2025-03-22",
        checkout="2025-03-23",
        adults="2",
        rooms="1",
        children="0",
        price_range="BDT-5500-19500-1",
        hotel_class="4",
        *args,
        **kwargs,
    ):
        super(BookingSpider, self).__init__(*args, **kwargs)
        self.location = location
        self.checkin = checkin
        self.checkout = checkout
        self.adults = adults
        self.rooms = rooms
        self.children = children
        self.price_range = price_range
        self.hotel_class = hotel_class
        self.results = []

    def start_requests(self):
        url = "https://www.booking.com/searchresults.html"

        # Build filter string for price and class
        filters = []
        if self.price_range:
            filters.append(f"price%3D{self.price_range}")
        if self.hotel_class:
            filters.append(f"class%3D{self.hotel_class}")

        filter_string = "%3B".join(filters) if filters else ""

        params = {
            "ss": self.location,
            "checkin": self.checkin,
            "checkout": self.checkout,
            "group_adults": self.adults,
            "no_rooms": self.rooms,
            "group_children": self.children,
        }

        # Add filters if they exist
        if filter_string:
            params["nflt"] = filter_string

        # Convert params to query string manually
        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        full_url = f"{url}?{query_string}"

        self.logger.info(f"Starting request to: {full_url}")
        yield scrapy.Request(
            url=full_url,
            callback=self.parse,
            meta={"dont_redirect": False, "handle_httpstatus_list": [301, 302]},
            errback=self.handle_error,
        )

    def parse(self, response):
        try:
            # Debug the URL actually being crawled
            self.logger.info(f"Parsing URL: {response.url}")

            # Extract all hotel property cards
            hotel_cards = response.css('div[data-testid="property-card"]')
            self.logger.info(f"Found {len(hotel_cards)} property cards")

            for card in hotel_cards:
                try:
                    # Extract title
                    title = card.css('div[data-testid="title"]::text').get()

                    # Extract URL
                    url = card.css('a[data-testid="title-link"]::attr(href)').get()
                    if url:
                        url = urljoin(response.url, url).split("?")[0]

                    # Extract rating/stars (count the star SVGs)
                    stars = len(card.css("span.fcd9eec8fb.d31eda6efc.c25361c37f"))

                    # Extract image URL
                    image_url = card.css('img[data-testid="image"]::attr(src)').get()

                    # Extract price using data-testid
                    price_element = card.css(
                        'span[data-testid="price-and-discounted-price"]::text'
                    ).get()
                    price = (
                        price_element.replace("BDT", "").replace(",", "").strip()
                        if price_element
                        else None
                    )

                    if title and url:  # Only yield if we have at least title and URL
                        result = {
                            "title": title,
                            "url": url,
                            "stars": stars,
                            "image_url": image_url,
                            "price": price,
                        }
                        self.results.append(result)
                        yield result
                except Exception as e:
                    self.logger.error(f"Error parsing hotel card: {e}")
                    continue

        except Exception as e:
            self.logger.error(f"Error in parse method: {e}")
            yield None

    def handle_error(self, failure):
        self.logger.error(f"Request failed: {failure.value}")
        return None
