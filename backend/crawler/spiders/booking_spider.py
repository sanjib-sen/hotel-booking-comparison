import scrapy
from scrapy.crawler import CrawlerProcess
from urllib.parse import urljoin
import tempfile
import json
import os


class BookingSpider(scrapy.Spider):
    name = "booking_spider"
    allowed_domains = ["booking.com"]

    # Add headers to mimic a browser
    custom_settings = {
        "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
        "ROBOTSTXT_OBEY": False,
        "COOKIES_ENABLED": True,
        "DOWNLOAD_DELAY": 2,
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

        yield scrapy.Request(
            url=full_url,
            callback=self.parse,
            meta={"dont_redirect": False, "handle_httpstatus_list": [301, 302]},
        )

    def parse(self, response):
        # Debug the URL actually being crawled
        self.logger.info(f"Parsing URL: {response.url}")

        # Extract all hotel property cards
        hotel_cards = response.css('div[data-testid="property-card"]')
        self.logger.info(f"Found {len(hotel_cards)} property cards")

        for card in hotel_cards:
            # Extract title
            title = card.css('div[data-testid="title"]::text').get()

            # Extract URL
            url = card.css('a[data-testid="title-link"]::attr(href)').get()
            if url:
                url = urljoin(response.url, url)

            # Extract rating/stars (count the star SVGs)
            stars = len(card.css("span.fcd9eec8fb.d31eda6efc.c25361c37f"))

            # Extract image URL
            image_url = card.css('img[data-testid="image"]::attr(src)').get()

            # Extract price using data-testid
            price = card.css(
                'span[data-testid="price-and-discounted-price"]::text'
            ).get()

            yield {
                "title": title,
                "url": url,
                "stars": stars,
                "image_url": image_url,
                "price": price,
            }


# Updated function that returns JSON results instead of writing to a file
def run_booking_crawler(
    location="Dhaka, Bangladesh",
    checkin="2025-03-22",
    checkout="2025-03-23",
    adults="2",
    rooms="1",
    children="0",
    price_range="BDT-5500-19500-1",
    hotel_class="4",
):
    """
    Run the Booking.com crawler with the specified parameters and return the results as JSON

    Args:
        location: Location/city to search for
        checkin: Check-in date in YYYY-MM-DD format
        checkout: Check-out date in YYYY-MM-DD format
        adults: Number of adults
        rooms: Number of rooms
        children: Number of children
        price_range: Price range filter string (e.g., 'BDT-5500-19500-1')
        hotel_class: Hotel star rating (e.g., '4')

    Returns:
        list: List of dictionaries containing hotel information
    """
    # Create a temporary file to store the output
    temp_output = tempfile.NamedTemporaryFile(delete=False, suffix=".json", mode="w+t")
    temp_output.close()

    # Configure crawler settings to write to the temporary file
    process = CrawlerProcess(
        {
            "FEED_FORMAT": "json",
            "FEED_URI": f"file://{temp_output.name}",
        }
    )

    # Add our spider to crawl
    process.crawl(
        BookingSpider,
        location=location,
        checkin=checkin,
        checkout=checkout,
        adults=adults,
        rooms=rooms,
        children=children,
        price_range=price_range,
        hotel_class=hotel_class,
    )

    # Start the crawling process
    process.start()  # The script will block here until the crawling is finished

    # Read the results from the temporary file
    with open(temp_output.name, "r") as f:
        results = json.load(f)

    # Clean up the temporary file
    os.unlink(temp_output.name)

    # Return the collected results
    return results
