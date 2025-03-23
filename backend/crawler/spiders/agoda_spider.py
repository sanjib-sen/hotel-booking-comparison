import json
import os
from urllib.parse import urlencode

import scrapy
from scrapy_playwright.page import PageMethod


class AgodaSpider(scrapy.Spider):
    name = "agoda_spider"
    allowed_domains = ["agoda.com"]

    # Add headers to mimic a browser and configure Playwright
    custom_settings = {
        "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
        "ROBOTSTXT_OBEY": False,
        "COOKIES_ENABLED": True,
        "DOWNLOAD_DELAY": 2,
        "TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
        "DOWNLOAD_HANDLERS": {
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        },
        "PLAYWRIGHT_LAUNCH_OPTIONS": {
            "headless": True,
            "timeout": 30 * 1000,
        },
        "PLAYWRIGHT_BROWSER_CONTEXT_ARGS": {
            "viewport": {"width": 1920, "height": 1080},
        },
    }

    def __init__(
        self,
        location="Dhaka",
        checkin="2025-03-23",
        checkout="2025-03-25",
        adults="2",
        rooms="1",
        children="0",
        hotel_star_rating="4",
        price_from="10",
        price_to="40",
        cookies_path="cookies_agoda.json",
        *args,
        **kwargs,
    ):
        super(AgodaSpider, self).__init__(*args, **kwargs)
        self.location = location
        self.checkin = checkin
        self.checkout = checkout
        self.adults = adults
        self.rooms = rooms
        self.children = children
        self.hotel_star_rating = hotel_star_rating
        self.price_from = int(int(price_from) / 122)
        self.price_to = int(int(price_to) / 122)
        self.cookies_path = cookies_path
        self.city_id = None
        self.results = []

    def start_requests(self):
        # First get the city ID
        city_search_url = f"https://www.agoda.com/api/cronos/search/GetUnifiedSuggestResult/3/1/1/0/en-us/?searchText={self.location}"

        self.logger.info(f"Starting request to: {city_search_url}")
        yield scrapy.Request(
            url=city_search_url,
            callback=self.parse_city_id,
            meta={"dont_redirect": False, "handle_httpstatus_list": [301, 302]},
            errback=self.handle_error,
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
                "checkIn": self.checkin,
                "checkOut": self.checkout,
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
                        PageMethod("wait_for_load_state", "domcontentloaded"),
                    ],
                    "next_url": search_url,
                },
                errback=self.handle_error,
            )
        except Exception as e:
            self.logger.error(f"Error parsing city ID: {e}")

    async def visit_homepage_with_cookies(self, response):
        page = response.meta["playwright_page"]
        next_url = response.meta["next_url"]

        try:
            # Load cookies from file and add them to the context
            if os.path.exists(self.cookies_path):
                with open(self.cookies_path) as f:
                    cookies = json.load(f)

                # Add cookies to the context
                context = page.context
                await context.add_cookies(cookies)
                self.logger.info(f"Added {len(cookies)} cookies to browser context")
            else:
                self.logger.warning(f"Cookies file not found at {self.cookies_path}")

            # Small wait after setting cookies
            await page.wait_for_timeout(1000)

            # Close this page
            await page.close()

            # Create a new request with the cookies now set in the browser context
            yield scrapy.Request(
                url=next_url,
                callback=self.parse_search_results,
                meta={
                    "playwright": True,
                    "playwright_include_page": True,
                    "playwright_page_methods": [
                        PageMethod("set_default_navigation_timeout", 30000),
                        # Wait for hotel items to be visible
                        PageMethod(
                            "wait_for_selector",
                            'li[data-selenium="hotel-item"]',
                            timeout=15000,
                        ),
                        # Scroll progressively to load lazy-loaded content
                        PageMethod("evaluate", "window.scrollTo(0, 500)"),
                        PageMethod("wait_for_timeout", 1000),
                        PageMethod("evaluate", "window.scrollTo(0, 1000)"),
                        PageMethod("wait_for_timeout", 1000),
                        PageMethod("evaluate", "window.scrollTo(0, 1500)"),
                        PageMethod("wait_for_timeout", 1000),
                        PageMethod("evaluate", "window.scrollTo(0, 2000)"),
                        PageMethod("wait_for_timeout", 1000),
                    ],
                    "handle_httpstatus_list": [400, 403, 404, 500, 503],
                },
                errback=self.handle_error,
            )
        except Exception as e:
            self.logger.error(f"Error in visit_homepage_with_cookies: {e}")
            if page and not page.is_closed():
                await page.close()

    async def parse_search_results(self, response):
        page = response.meta["playwright_page"]

        try:
            self.logger.info(f"Parsing search results from: {response.url}")

            # Extract all hotel property cards
            hotel_cards = response.css('li[data-selenium="hotel-item"]')
            self.logger.info(f"Found {len(hotel_cards)} property cards")

            if not hotel_cards:
                self.logger.warning(
                    "No hotel cards found! Possible issue with page loading or selectors."
                )
                # Save HTML for debugging
                html_content = await page.content()
                with open("debug_empty_results.html", "w", encoding="utf-8") as f:
                    f.write(html_content)
                self.logger.info(
                    f"Saved debug HTML for review. Current page URL: {page.url}"
                )
                return

            for card in hotel_cards:
                try:
                    # Extract title/name
                    title = card.css('a[data-selenium="hotel-name"] span::text').get()
                    if not title or title.strip() == "":
                        continue

                    # Extract URL
                    url_element = card.css(
                        'a[data-selenium="hotel-name"]::attr(href)'
                    ).get()
                    url = (
                        response.urljoin(url_element).split("?")[0]
                        if url_element
                        else None
                    )

                    # Extract star rating
                    stars = len(card.css('div[data-testid="rating-container"] svg'))

                    price_value = card.css(
                        'div[data-element-name="final-price"] span[data-selenium="display-price"]::text'
                    ).get()
                    price = price_value

                    # Extract image URL
                    image_element = card.css("div.Overlay img::attr(srcset)").get()
                    if image_element:
                        # Parse the srcset to get the largest image URL
                        srcset_parts = image_element.split(",")
                        largest_img = (
                            srcset_parts[-1].strip().split(" ")[0]
                            if srcset_parts
                            else None
                        )
                        image_url = largest_img
                    else:
                        # Fallback to src attribute
                        image_url = card.css("div.Overlay img::attr(src)").get()

                    if title and url:  # Only yield if we have at least title and URL
                        result = {
                            "title": title,
                            "url": url,
                            "stars": stars,
                            "price": price,
                            "image_url": image_url,
                        }
                        self.results.append(result)
                        yield result
                except Exception as e:
                    self.logger.error(f"Error parsing hotel card: {e}")
                    continue
        except Exception as e:
            self.logger.error(f"Error in parse_search_results: {e}")
        finally:
            if page and not page.is_closed():
                await page.close()

    def handle_error(self, failure):
        self.logger.error(f"Request failed: {failure.value}")
        return None
