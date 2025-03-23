import { ScrappedService } from "@/client"
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
import { createFileRoute } from "@tanstack/react-router"
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

export const Route = createFileRoute("/_layout/bookmarks")({
  component: Bookmarks,
})

function Bookmarks() {
  const [bookmarkedHotels, setBookmarkedHotels] = useState<ScrappedItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [bookmarkLoading, setBookmarkLoading] = useState<Set<string>>(new Set())

  const fetchBookmarkedHotels = useCallback(async () => {
    setLoading(true)
    setError(null)

    try {
      // Step 1: Get all bookmarked items
      const bookmarksResponse = await ScrappedService.readBookmarkedItems({
        skip: 0,
        limit: 100,
      })

      if (!Array.isArray(bookmarksResponse) || bookmarksResponse.length === 0) {
        setBookmarkedHotels([])
        setLoading(false)
        return
      }
      // Step 2: Fetch details for each bookmarked item
      const hotelPromises = bookmarksResponse.map(async (bookmark) => {
        try {
          const hotelData = await ScrappedService.readScrappedItem({
            itemId: bookmark.scrapped_item_id,
          })
          return hotelData
        } catch (err) {
          console.error(
            `Error fetching hotel with ID ${bookmark.scrapped_item_id}:`,
            err,
          )
          return null
        }
      })

      const hotels = await Promise.all(hotelPromises)
      setBookmarkedHotels(
        hotels.filter((hotel) => hotel !== null) as ScrappedItem[],
      )
    } catch (err) {
      console.error("Error fetching bookmarked hotels:", err)
      setError(
        err instanceof Error
          ? err.message
          : "Failed to fetch bookmarked hotels",
      )
    } finally {
      setLoading(false)
    }
  }, [])

  const removeBookmark = async (itemId: string) => {
    if (!itemId) return

    try {
      setBookmarkLoading((prev) => new Set(prev).add(itemId))

      // Remove bookmark
      await ScrappedService.deleteBookmark({
        itemId: itemId,
      })

      // Remove from state
      setBookmarkedHotels((prev) => prev.filter((hotel) => hotel.id !== itemId))

      toaster.create({
        title: "Bookmark removed",
        description: "The hotel has been removed from your bookmarks",
        type: "success",
      })
    } catch (err) {
      console.error("Error removing bookmark:", err)
      toaster.create({
        title: "Bookmark removal failed",
        description: "There was an error while removing your bookmark",
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
    fetchBookmarkedHotels()
  }, [fetchBookmarkedHotels])

  // Helper function to determine which price is better
  const getBestPrice = (
    priceBooking: number,
    priceAgoda: number | null,
  ): "booking" | "agoda" | null => {
    if (!priceAgoda) return "booking"
    return priceAgoda < priceBooking ? "agoda" : "booking"
  }

  if (loading) {
    return (
      <Center h="100vh">
        <VStack gap={4}>
          <Spinner size="xl" />
          <Text>Loading your bookmarked hotels...</Text>
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
      <Heading mb={6}>Your Bookmarked Hotels</Heading>

      {bookmarkedHotels.length === 0 ? (
        <Center h="200px">
          <VStack>
            <Text>You haven't bookmarked any hotels yet.</Text>
            <ChakraLink href="/" fontWeight="bold" color="blue.500">
              Search for hotels to bookmark
            </ChakraLink>
          </VStack>
        </Center>
      ) : (
        <Grid
          templateColumns={{
            base: "1fr",
            md: "repeat(2, 1fr)",
            lg: "repeat(3, 1fr)",
          }}
          gap={6}
        >
          {bookmarkedHotels.map((hotel) => {
            const bestPrice = getBestPrice(
              hotel.price_booking,
              hotel.price_agoda,
            )
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
                      aria-label="Remove bookmark"
                      size="sm"
                      colorScheme="red"
                      loading={isBookmarkLoading}
                      onClick={() => removeBookmark(hotel.id)}
                    >
                      Remove
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
                        <Text
                          fontSize="xl"
                          fontWeight="bold"
                          color="purple.600"
                        >
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
      )}
    </Container>
  )
}
