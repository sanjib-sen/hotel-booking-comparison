import React, { useEffect, useState } from "react";
import { createFileRoute, useParams, useSearch } from "@tanstack/react-router";
import {
    Box,
    Container,
    Grid,
    Heading,
    Image,
    Text,
    VStack,
    Badge,
    HStack,
    Link as ChakraLink,
    Spinner,
    Center,
    StackProps,
} from "@chakra-ui/react";
import { FaStar } from "react-icons/fa";
import { ScrappedService } from "@/client";
import { OpenAPI } from "@/client";

type ScrappedItem = {
    id: string;
    title: string;
    price_booking: number;
    url_booking: string;
    stars: number | null;
    image_url: string | null;
}

interface SearchRouteParams {
    search_id: string;
}

export const Route = createFileRoute('/_layout/search-results')({
    component: SearchResults,
    parseParams: (params): SearchRouteParams => params as SearchRouteParams,
});

function SearchResults() {
    const { search_id } = useSearch({ from: "/_layout/search-results" });
    console.log("params:", search_id);
    const [hotels, setHotels] = useState<ScrappedItem[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [status, setStatus] = useState<string>("pending");

    useEffect(() => {
        let pollInterval: NodeJS.Timeout;

        const fetchHotels = async () => {
            try {
                if (!search_id) {
                    console.error("No search ID provided");
                    throw new Error("No search ID provided");
                }

                console.log("Fetching hotels for search_id:", search_id);
                console.log("API URL:", OpenAPI.BASE);

                // First, get the history status
                const historyResponse = await ScrappedService.readScrappedHistoryById({
                    id: search_id,
                });
                console.log("History status:", historyResponse.scrape_status);
                setStatus(historyResponse.scrape_status);

                // If the status is pending, keep polling
                if (historyResponse.scrape_status === "pending") {
                    pollInterval = setInterval(fetchHotels, 5000); // Poll every 5 seconds
                    return;
                }

                // If there's an error, stop polling
                if (historyResponse.scrape_status === "error") {
                    setError("Failed to fetch hotels. Please try again.");
                    setLoading(false);
                    return;
                }

                // If no results, stop polling
                if (historyResponse.scrape_status === "no_results") {
                    setHotels([]);
                    setLoading(false);
                    return;
                }

                // Get the hotel results
                const response = await ScrappedService.readScrappedItems({
                    historyId: search_id,
                    skip: 0,
                    limit: 100,
                });

                console.log("API Response:", response);
                const responseData = (response as any).data || [];
                setHotels(responseData);
                setLoading(false);
            } catch (err) {
                console.error("Error fetching hotels:", err);
                setError(err instanceof Error ? err.message : "Failed to fetch hotels. Please try again.");
                setLoading(false);
            }
        };

        if (search_id) {
            fetchHotels();
        }

        // Cleanup function to clear the interval
        return () => {
            if (pollInterval) {
                clearInterval(pollInterval);
            }
        };
    }, [search_id]);

    if (loading) {
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
        );
    }

    if (error) {
        return (
            <Center h="100vh">
                <Text color="red.500">{error}</Text>
            </Center>
        );
    }

    return (
        <Container maxW="container.xl" py={8}>
            <Heading mb={6}>Search Results</Heading>
            <Grid
                templateColumns={{
                    base: "1fr",
                    md: "repeat(2, 1fr)",
                    lg: "repeat(3, 1fr)",
                }}
                gap={6}
            >
                {hotels.map((hotel) => (
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
                            src={hotel.image_url || "https://via.placeholder.com/300x200?text=No+Image"}
                            alt={hotel.title}
                            height="200px"
                            width="100%"
                            objectFit="cover"
                        />
                        <VStack p={4} align="stretch" gap={3}>
                            <Heading as="h3" size="md" truncate>
                                {hotel.title}
                            </Heading>

                            <HStack>
                                {hotel.stars && (
                                    <HStack gap={1}>
                                        {[...Array(Math.floor(hotel.stars))].map((_, i) => (
                                            <FaStar key={i} color="yellow.400" />
                                        ))}
                                        <Text ml={1} color="gray.600">
                                            ({hotel.stars})
                                        </Text>
                                    </HStack>
                                )}
                            </HStack>

                            <Text fontSize="xl" fontWeight="bold" color="blue.600">
                                BDT {hotel.price_booking.toLocaleString()}
                            </Text>

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
                            >
                                Book on Booking.com
                            </ChakraLink>
                        </VStack>
                    </Box>
                ))}
            </Grid>

            {hotels.length === 0 && (
                <Center h="200px">
                    <Text>No hotels found for your search criteria.</Text>
                </Center>
            )}
        </Container>
    );
}
