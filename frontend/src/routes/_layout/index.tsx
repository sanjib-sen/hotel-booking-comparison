import { Box, Container, Button, VStack, Heading, Text, Input, Stack, HStack, Flex, Grid } from "@chakra-ui/react"
import { FormControl, FormLabel } from "@chakra-ui/form-control"
import { NumberInput, NumberInputField, NumberInputStepper, NumberIncrementStepper, NumberDecrementStepper } from "@chakra-ui/number-input"
import { createFileRoute, useNavigate } from "@tanstack/react-router"
import { useState } from "react"
import { ScrappedService } from "@/client"

export const Route = createFileRoute("/_layout/")({
  component: Dashboard,
})

interface FormData {
  city: string
  price_min: number
  price_max: number
  stars: number
}

function Dashboard() {
  const navigate = useNavigate()
  const [isLoading, setIsLoading] = useState(false)
  const [formData, setFormData] = useState<FormData>({
    city: "Dhaka",
    price_min: 0,
    price_max: 25000,
    stars: 3,
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)

    try {
      // Create search history
      const response = await ScrappedService.createScrappedHistory({
        requestBody: {
          city: formData.city,
          price_min: formData.price_min,
          price_max: formData.price_max,
          stars: formData.stars,
        }
      })

      if (!response.id) {
        throw new Error('No search ID returned from server');
      }

      // Redirect to search results page with the history ID
      navigate({
        to: '/search-results',
        search: { search_id: response.id.toString() }
      })
    } catch (error) {
      console.error('Error creating search history:', error)
      alert('Failed to start hotel search. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <Container maxW="container.md" py={10}>
      <VStack gap={8} align="stretch">
        <Box textAlign="center">
          <Heading size="lg" mb={2}>
            Hotel Search
          </Heading>
          <Text color="gray.600">
            Find the best hotels based on your preferences
          </Text>
        </Box>

        <Box as="form" onSubmit={handleSubmit}>
          <VStack gap={6}>
            <FormControl>
              <FormLabel>City</FormLabel>
              <Input
                value={formData.city}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setFormData({ ...formData, city: e.target.value })}
                placeholder="Enter city name"
              />
            </FormControl>

            <FormControl>
              <FormLabel>Minimum Price</FormLabel>
              <NumberInput
                value={formData.price_min}
                onChange={(value: string) => setFormData({ ...formData, price_min: Number(value) })}
                min={0}
                max={formData.price_max}
              >
                <NumberInputField />
                <NumberInputStepper>
                  <NumberIncrementStepper />
                  <NumberDecrementStepper />
                </NumberInputStepper>
              </NumberInput>
            </FormControl>

            <FormControl>
              <FormLabel>Maximum Price</FormLabel>
              <NumberInput
                value={formData.price_max}
                onChange={(value: string) => setFormData({ ...formData, price_max: Number(value) })}
                min={formData.price_min}
              >
                <NumberInputField />
                <NumberInputStepper>
                  <NumberIncrementStepper />
                  <NumberDecrementStepper />
                </NumberInputStepper>
              </NumberInput>
            </FormControl>

            <FormControl>
              <FormLabel>Star Rating</FormLabel>
              <NumberInput
                value={formData.stars}
                onChange={(value: string) => setFormData({ ...formData, stars: Number(value) })}
                min={0}
                max={5}
                step={1}
              >
                <NumberInputField />
                <NumberInputStepper>
                  <NumberIncrementStepper />
                  <NumberDecrementStepper />
                </NumberInputStepper>
              </NumberInput>
            </FormControl>

            <Button
              type="submit"
              colorScheme="blue"
              width="full"
              size="lg"
              disabled={isLoading}
            >
              {isLoading ? 'Starting Search...' : 'Search Hotels'}
            </Button>
          </VStack>
        </Box>
      </VStack>
    </Container>
  )
}
