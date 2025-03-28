import { ScrappedService } from "@/client"
import { OpenAPI } from "@/client"
import { toaster } from "@/components/ui/toaster"
import {
  Badge,
  Box,
  Button,
  Center,
  Link as ChakraLink,
  Container,
  Grid,
  HStack,
  Heading,
  Image,
  Spinner,
  Text,
  VStack,
} from "@chakra-ui/react"
import { createFileRoute, useSearch } from "@tanstack/react-router"
import { useCallback, useEffect, useState } from "react"
import { FaStar } from "react-icons/fa"
import { HiTag } from "react-icons/hi"

type ScrappedItem = {
  id: string
  title: string
  price_booking: number
  price_agoda: number | null
  url_booking: string
  url_agoda: string | null
  stars: number | null
  image_url: string | null
}

interface SearchRouteParams {
  search_id: string
}

export const Route = createFileRoute("/_layout/search-results")({
  component: SearchResults,
  parseParams: (params): SearchRouteParams => params as SearchRouteParams,
})

function SearchResults() {
  const { search_id } = useSearch({ from: "/_layout/search-results" })
  const [hotels, setHotels] = useState<ScrappedItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [status, setStatus] = useState<string>("pending")
  const [bookmarkedItems, setBookmarkedItems] = useState<Set<string>>(new Set())
  const [bookmarkLoading, setBookmarkLoading] = useState<Set<string>>(new Set())

  // Fetch existing bookmarks
  const fetchBookmarks = useCallback(async () => {
    try {
      const response = await ScrappedService.readBookmarkedItems({
        skip: 0,
        limit: 100,
      })

      const bookmarkedSet = new Set<string>()
      if (Array.isArray(response)) {
        response.forEach((bookmark) => {
          if (bookmark.scrapped_item_id) {
            bookmarkedSet.add(bookmark.scrapped_item_id)
          }
        })
      }
      setBookmarkedItems(bookmarkedSet)
    } catch (err) {
      console.error("Error fetching bookmarks:", err)
    }
  }, [])

  const toggleBookmark = async (itemId: string) => {
    if (!itemId) return

    try {
      setBookmarkLoading((prev) => new Set(prev).add(itemId))

      if (bookmarkedItems.has(itemId)) {
        // Remove bookmark
        await ScrappedService.deleteBookmark({
          itemId: itemId,
        })
        setBookmarkedItems((prev) => {
          const newSet = new Set(prev)
          newSet.delete(itemId)
          return newSet
        })
        toaster.create({
          title: "Bookmark removed",
          description: "The hotel has been removed from your bookmarks",
          type: "success",
        })
      } else {
        // Add bookmark
        await ScrappedService.bookmarkScrappedItem({
          itemId: itemId,
        })
        setBookmarkedItems((prev) => new Set(prev).add(itemId))
        toaster.create({
          title: "Hotel bookmarked",
          description: "The hotel has been added to your bookmarks",
          type: "success",
        })
      }
    } catch (err) {
      console.error("Error toggling bookmark:", err)
      toaster.create({
        title: "Bookmark action failed",
        description: "There was an error while updating your bookmark",
        type: "error",
      })
    } finally {
      setBookmarkLoading((prev) => {
        const newSet = new Set(prev)
        newSet.delete(itemId)
        return newSet
      })
    }
  }

  useEffect(() => {
    let pollInterval: NodeJS.Timeout

    const fetchHotels = async () => {
      try {
        if (!search_id) {
          console.error("No search ID provided")
          throw new Error("No search ID provided")
        }

        console.log("Fetching hotels for search_id:", search_id)
        console.log("API URL:", OpenAPI.BASE)

        // First, get the history status
        const historyResponse = await ScrappedService.readScrappedHistoryById({
          id: search_id,
        })
        console.log("History status:", historyResponse.scrape_status)
        setStatus(historyResponse.scrape_status)

        // If the status is pending or still running Agoda spider, keep polling
        if (
          historyResponse.scrape_status === "pending" ||
          historyResponse.scrape_status === "booking_spider_completed" ||
          historyResponse.scrape_status === "running_agoda_spider"
        ) {
          // Get any available booking.com results while waiting for Agoda
          const response = await ScrappedService.readScrappedItems({
            historyId: search_id,
            skip: 0,
            limit: 100,
          })

          console.log("Partial API Response:", response)
          const responseData = (response as any).data || []
          setHotels(responseData)

          // Continue polling
          return // Don't clear the interval, continue polling
        }

        // For status "completed", "failed", "error", or "no_results" - stop polling
        if (pollInterval) {
          clearInterval(pollInterval)
        }

        // If there's an error, stop polling
        if (
          historyResponse.scrape_status.includes("failed") ||
          historyResponse.scrape_status === "error"
        ) {
          setError("Failed to fetch hotels. Please try again.")
          setLoading(false)
          return
        }

        // If no results, stop polling
        if (historyResponse.scrape_status === "no_results") {
          setHotels([])
          setLoading(false)
          return
        }

        // Get the hotel results
        const response = await ScrappedService.readScrappedItems({
          historyId: search_id,
          skip: 0,
          limit: 100,
        })

        console.log("API Response:", response)
        const responseData = (response as any).data || []
        setHotels(responseData)
        setLoading(false)
      } catch (err) {
        console.error("Error fetching hotels:", err)
        setError(
          err instanceof Error
            ? err.message
            : "Failed to fetch hotels. Please try again.",
        )
        setLoading(false)
        // Stop polling on error
        if (pollInterval) {
          clearInterval(pollInterval)
        }
      }
    }

    if (search_id) {
      fetchHotels()
      fetchBookmarks()

      // Start polling only for initial fetch
      pollInterval = setInterval(fetchHotels, 5000) // Poll every 5 seconds
    }

    // Cleanup function to clear the interval
    return () => {
      if (pollInterval) {
        clearInterval(pollInterval)
      }
    }
  }, [search_id, fetchBookmarks])

  // Helper function to determine which price is better
  const getBestPrice = (
    priceBooking: number,
    priceAgoda: number | null,
  ): "booking" | "agoda" | null => {
    if (!priceAgoda) return "booking"
    return priceAgoda < priceBooking ? "agoda" : "booking"
  }

  if (loading && hotels.length === 0) {
    return (
      <Center h="100vh">
        <VStack gap={4}>
          <Spinner size="xl" />
          <Text>Searching for hotels...</Text>
          <Text fontSize="sm" color="gray.500">
            Status: {status}
          </Text>
        </VStack>
      </Center>
    )
  }

  if (error) {
    return (
      <Center h="100vh">
        <Text color="red.500">{error}</Text>
      </Center>
    )
  }

  return (
    <Container maxW="container.xl" py={8}>
      <Heading mb={6}>Search Results</Heading>

      {status !== "completed" && (
        <Box
          mb={6}
          p={4}
          bg="blue.50"
          _dark={{ bg: "blue.900" }}
          borderRadius="md"
        >
          <HStack>
            <Spinner size="sm" />
            <Text>
              Loading Booking.com results... Agoda prices will be added when
              available.
            </Text>
          </HStack>
        </Box>
      )}

      <Grid
        templateColumns={{
          base: "1fr",
          md: "repeat(2, 1fr)",
          lg: "repeat(3, 1fr)",
        }}
        gap={6}
      >
        {hotels.map((hotel) => {
          const bestPrice = getBestPrice(hotel.price_booking, hotel.price_agoda)
          const isBookmarked = bookmarkedItems.has(hotel.id)
          const isBookmarkLoading = bookmarkLoading.has(hotel.id)

          return (
            <Box
              key={hotel.id}
              borderWidth="1px"
              borderRadius="lg"
              overflow="hidden"
              shadow="md"
              transition="transform 0.2s"
              _hover={{ transform: "translateY(-4px)" }}
            >
              <Image
                src={
                  hotel.image_url ||
                  "https://via.placeholder.com/300x200?text=No+Image"
                }
                alt={hotel.title}
                height="200px"
                width="100%"
                objectFit="cover"
              />
              <VStack p={4} align="stretch" gap={3}>
                <Heading as="h3" size="md">
                  {hotel.title}
                </Heading>

                <HStack justify="space-between">
                  <HStack gap={1}>
                    {hotel.stars && (
                      <HStack gap={1}>
                        {[...Array(Math.floor(hotel.stars))].map((_, i) => (
                          <FaStar key={i} color="gold" />
                        ))}
                        <Text ml={1} color="gray.600">
                          ({hotel.stars})
                        </Text>
                      </HStack>
                    )}
                  </HStack>
                  <Button
                    aria-label="Bookmark hotel"
                    size="sm"
                    colorScheme={isBookmarked ? "blue" : "gray"}
                    loading={isBookmarkLoading}
                    onClick={() => toggleBookmark(hotel.id)}
                  >
                    {isBookmarked ? "Unbookmark" : "Bookmark"}
                  </Button>
                </HStack>

                <VStack align="stretch">
                  <HStack justify="space-between">
                    <Text fontSize="xl" fontWeight="bold" color="blue.600">
                      Booking: BDT {hotel.price_booking.toLocaleString()}
                    </Text>
                    {bestPrice === "booking" && (
                      <Badge variant="solid" colorScheme="green">
                        <HStack>
                          <HiTag />
                          <Text>Best Price</Text>
                        </HStack>
                      </Badge>
                    )}
                  </HStack>

                  {hotel.price_agoda && hotel.url_agoda && (
                    <HStack justify="space-between">
                      <Text fontSize="xl" fontWeight="bold" color="purple.600">
                        Agoda: BDT {hotel.price_agoda.toLocaleString()}
                      </Text>
                      {bestPrice === "agoda" && (
                        <Badge variant="solid" colorScheme="green">
                          <HStack>
                            <HiTag />
                            <Text>Best Price</Text>
                          </HStack>
                        </Badge>
                      )}
                    </HStack>
                  )}
                </VStack>

                <ChakraLink
                  href={hotel.url_booking}
                  target="_blank"
                  rel="noopener noreferrer"
                  color="white"
                  bg="blue.500"
                  px={4}
                  py={2}
                  borderRadius="md"
                  textAlign="center"
                  _hover={{ bg: "blue.600" }}
                  display="block"
                  mb={2}
                >
                  Book on Booking.com
                </ChakraLink>

                {hotel.url_agoda && (
                  <ChakraLink
                    href={hotel.url_agoda}
                    target="_blank"
                    rel="noopener noreferrer"
                    color="white"
                    bg="purple.500"
                    px={4}
                    py={2}
                    borderRadius="md"
                    textAlign="center"
                    _hover={{ bg: "purple.600" }}
                    display="block"
                  >
                    Book on Agoda.com
                  </ChakraLink>
                )}
              </VStack>
            </Box>
          )
        })}
      </Grid>

      {hotels.length === 0 && (
        <Center h="200px">
          <Text>No hotels found for your search criteria.</Text>
        </Center>
      )}
    </Container>
  )
}
