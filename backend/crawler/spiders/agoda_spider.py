import scrapy
from scrapy_playwright.page import PageMethod
import json
from urllib.parse import urlencode
import os
from scrapy.crawler import CrawlerProcess


class AgodaPlaywrightSpider(scrapy.Spider):
    name = "agoda_playwright_spider"
    allowed_domains = ["agoda.com"]

    custom_settings = {
        "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
        "ROBOTSTXT_OBEY": False,
        "COOKIES_ENABLED": True,
        "DOWNLOAD_DELAY": 1,  # Reduced from 2
        "TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
        "DOWNLOAD_HANDLERS": {
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        },
        "PLAYWRIGHT_LAUNCH_OPTIONS": {
            "headless": True,  # Set to True in production
            "timeout": 20 * 1000,  # Reduced from 30 seconds
        },
        "PLAYWRIGHT_BROWSER_CONTEXT_ARGS": {
            "viewport": {"width": 1920, "height": 1080},
        },
    }

    def __init__(
        self,
        location="Dhaka",
        check_in="2025-03-23",
        check_out="2025-03-25",
        rooms="1",
        adults="2",
        children="0",
        hotel_star_rating="4",
        price_from="10",
        price_to="40",
        cookies_path="cookies_agoda.json",
        *args,
        **kwargs,
    ):
        super(AgodaPlaywrightSpider, self).__init__(*args, **kwargs)
        self.location = location
        self.check_in = check_in
        self.check_out = check_out
        self.rooms = rooms
        self.adults = adults
        self.children = children
        self.hotel_star_rating = hotel_star_rating
        self.price_from = price_from
        self.price_to = price_to
        self.city_id = None
        self.cookies_path = cookies_path

    def start_requests(self):
        # Load cookies from file
        if os.path.exists(self.cookies_path):
            self.logger.info(f"Loading cookies from {self.cookies_path}")
        else:
            self.logger.warning(f"Cookies file not found at {self.cookies_path}")

        # First get the city ID
        city_search_url = f"https://www.agoda.com/api/cronos/search/GetUnifiedSuggestResult/3/1/1/0/en-us/?searchText={self.location}"

        yield scrapy.Request(
            url=city_search_url,
            callback=self.parse_city_id,
            meta={"dont_redirect": False, "handle_httpstatus_list": [301, 302]},
        )

    def parse_city_id(self, response):
        self.logger.info(f"Parsing city ID from: {response.url}")

        try:
            # Parse the JSON response
            data = json.loads(response.text)
            # Extract the city ID from the first result
            for item in data.get("ViewModelList", []):
                if item.get("Name") == self.location and item.get("ObjectId"):
                    self.city_id = item.get("ObjectId")
                    break

            if not self.city_id:
                self.logger.error(f"Could not find city ID for {self.location}")
                return

            self.logger.info(f"Found city ID for {self.location}: {self.city_id}")

            # Now that we have the city ID, construct the search URL
            search_params = {
                "city": self.city_id,
                "checkIn": self.check_in,
                "checkOut": self.check_out,
                "rooms": self.rooms,
                "adults": self.adults,
                "children": self.children,
                "hotelStarRating": self.hotel_star_rating,
                "PriceFrom": self.price_from,
                "PriceTo": self.price_to,
            }

            search_url = f"https://www.agoda.com/search?{urlencode(search_params)}"

            # First go to homepage and set cookies
            yield scrapy.Request(
                url="https://www.agoda.com/",
                callback=self.visit_homepage_with_cookies,
                meta={
                    "playwright": True,
                    "playwright_include_page": True,
                    "playwright_page_methods": [
                        # Just wait for the DOM to be ready, no need for network idle
                        PageMethod("wait_for_load_state", "domcontentloaded"),
                    ],
                    "next_url": search_url,
                },
            )
        except Exception as e:
            self.logger.error(f"Error parsing city ID: {e}")

    async def visit_homepage_with_cookies(self, response):
        page = response.meta["playwright_page"]
        next_url = response.meta["next_url"]

        try:
            # Load cookies from file and add them to the context
            if os.path.exists(self.cookies_path):
                with open(self.cookies_path, "r") as f:
                    cookies = json.load(f)

                # Add cookies to the context
                context = page.context
                for cookie in cookies:
                    await context.add_cookies([cookie])

                self.logger.info(f"Added {len(cookies)} cookies to browser context")

            # Reduced wait time after setting cookies
            await page.wait_for_timeout(1000)  # Reduced from 2000ms

            # Close this page and open a new request
            await page.close()

            # Create a new request with the cookies now set in the browser context
            yield scrapy.Request(
                url=next_url,
                callback=self.parse_search_results,
                meta={
                    "playwright": True,
                    "playwright_include_page": True,
                    "playwright_page_methods": [
                        PageMethod(
                            "set_default_navigation_timeout", 30000
                        ),  # Reduced from 60000
                        # Wait for content to be visible instead of full network idle
                        PageMethod(
                            "wait_for_selector",
                            'li[data-selenium="hotel-item"]',
                            timeout=15000,
                        ),  # Reduced from 30000
                        # Optimize scrolling - fewer pauses, quicker scrolls
                        PageMethod("evaluate", "window.scrollTo(0, 500)"),
                        PageMethod(
                            "wait_for_timeout", 300
                        ),  # Reduced wait between scrolls
                        PageMethod("evaluate", "window.scrollTo(0, 1000)"),
                        PageMethod("wait_for_timeout", 2000),
                        PageMethod("evaluate", "window.scrollTo(0, 1500)"),
                        PageMethod("wait_for_timeout", 2000),
                        PageMethod("evaluate", "window.scrollTo(0, 2000)"),
                        PageMethod("wait_for_timeout", 2000),  # Final scroll wait
                    ],
                    "handle_httpstatus_list": [400, 403, 404, 500, 503],
                },
            )
        except Exception as e:
            self.logger.error(f"Error in visit_homepage_with_cookies: {e}")
            await page.close()

    async def parse_search_results(self, response):
        page = response.meta["playwright_page"]
        try:
            self.logger.info(f"Parsing search results from: {response.url}")

            # Extract all hotel property cards
            hotel_cards = response.css('li[data-selenium="hotel-item"]')
            self.logger.info(f"Found {len(hotel_cards)} property cards")

            if len(hotel_cards) == 0:
                self.logger.warning(
                    "No hotel cards found! Possible issue with page loading or selectors."
                )
                # Save HTML for debugging
                html_content = await page.content()
                with open("empty_results_debug.html", "w", encoding="utf-8") as f:
                    f.write(html_content)
                self.logger.info(f"Current page URL: {page.url}")
                return

            for card in hotel_cards:
                # Extract title/name using the updated selector
                title = card.css('a[data-selenium="hotel-name"] span::text').get()

                # Skip hotel if no title is found
                if not title or title.strip() == "":
                    self.logger.info("Skipping hotel with no title")
                    continue

                # Extract URL from the updated anchor element
                url_element = card.css(
                    'a[data-selenium="hotel-name"]::attr(href)'
                ).get()
                url = response.urljoin(url_element) if url_element else None

                # Extract star rating by counting the SVGs in the rating container
                stars = len(card.css('div[data-testid="rating-container"] svg'))

                # Extract price using the updated selectors
                currency = card.css(
                    'div[data-element-name="final-price"] span[data-selenium="hotel-currency"]::text'
                ).get()
                price_value = card.css(
                    'div[data-element-name="final-price"] span[data-selenium="display-price"]::text'
                ).get()
                price = (
                    f"{currency} {price_value}" if currency and price_value else None
                )

                # Extract image URL from the srcset attribute
                image_element = card.css("div.Overlay img::attr(srcset)").get()
                if image_element:
                    # Parse the srcset to get the largest image URL
                    srcset_parts = image_element.split(",")
                    largest_img = (
                        srcset_parts[-1].strip().split(" ")[0] if srcset_parts else None
                    )
                    image_url = largest_img
                else:
                    # Fallback to src attribute if srcset is not available
                    image_url = card.css("div.Overlay img::attr(src)").get()

                yield {
                    "title": title,
                    "url": url,
                    "stars": stars,
                    "price": price,
                    "image_url": image_url,
                }
        except Exception as e:
            self.logger.error(f"Error parsing search results: {e}")
        finally:
            # Close the page before starting the duplicate code block
            await page.close()
            # NOTE: The duplicate code block below has been removed to fix the issue


def run_agoda_crawler(
    location="Dhaka",
    check_in="2025-03-23",
    check_out="2025-03-25",
    rooms="1",
    adults="2",
    children="0",
    hotel_star_rating="4",
    price_from="10",
    price_to="40",
    cookies_path="cookies_agoda.json",
):
    """
    Run the Agoda crawler with the specified parameters and return the results as JSON

    Args:
        location: Location/city to search for
        check_in: Check-in date in YYYY-MM-DD format
        check_out: Check-out date in YYYY-MM-DD format
        rooms: Number of rooms
        adults: Number of adults
        children: Number of children
        hotel_star_rating: Desired hotel star rating
        price_from: Minimum price
        price_to: Maximum price
        cookies_path: Path to cookies file for authentication

    Returns:
        list: List of dictionaries containing hotel information
    """
    import tempfile
    import json
    import os

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
        AgodaPlaywrightSpider,
        location=location,
        check_in=check_in,
        check_out=check_out,
        rooms=rooms,
        adults=adults,
        children=children,
        hotel_star_rating=hotel_star_rating,
        price_from=price_from,
        price_to=price_to,
        cookies_path=cookies_path,
    )

    # Start the crawling process
    process.start()  # This will block until the crawling is finished

    # Read the results from the temporary file
    with open(temp_output.name, "r") as f:
        results = json.load(f)

    # Clean up the temporary file
    os.unlink(temp_output.name)

    # Return the collected results
    return results
