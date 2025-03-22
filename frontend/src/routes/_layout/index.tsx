import { Box, Container, Button, VStack, Heading, Text, Input, Stack, HStack, Flex, Grid } from "@chakra-ui/react"
import { FormControl, FormLabel } from "@chakra-ui/form-control"
import { NumberInput, NumberInputField, NumberInputStepper, NumberIncrementStepper, NumberDecrementStepper } from "@chakra-ui/number-input"
import { createFileRoute } from "@tanstack/react-router"
import { useState } from "react"

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
  const [formData, setFormData] = useState<FormData>({
    city: "Dhaka",
    price_min: 0,
    price_max: 25000,
    stars: 3,
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    // TODO: Handle form submission
    console.log("Form submitted:", formData)
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
              </NumberInput>
              {/* <NumberInputStepper>
                  <NumberIncrementStepper />
                  <NumberDecrementStepper />
                </NumberInputStepper> */}

            </FormControl>

            <FormControl>
              <FormLabel>Maximum Price</FormLabel>
              <NumberInput
                value={formData.price_max}
                onChange={(value: string) => setFormData({ ...formData, price_max: Number(value) })}
                min={formData.price_min}
              >
                <NumberInputField />
                {/* <NumberInputStepper>
                  <NumberIncrementStepper />
                  <NumberDecrementStepper />
                </NumberInputStepper> */}
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

            <Button type="submit" colorScheme="blue" width="full" size="lg">
              Search Hotels
            </Button>
          </VStack>
        </Box>
      </VStack >
    </Container >
  )
}
