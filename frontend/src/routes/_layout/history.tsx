import {
  Button,
  Container,
  EmptyState,
  Flex,
  Heading,
  Table,
  VStack,
} from "@chakra-ui/react"
import { useQuery } from "@tanstack/react-query"
import { createFileRoute, useNavigate } from "@tanstack/react-router"
import { FiSearch } from "react-icons/fi"
import { z } from "zod"

import { ScrappedService } from "@/client"
import PendingItems from "@/components/Pending/PendingItems"
import {
  PaginationItems,
  PaginationNextTrigger,
  PaginationPrevTrigger,
  PaginationRoot,
} from "@/components/ui/pagination.tsx"

const historySearchSchema = z.object({
  page: z.number().catch(1),
})

const PER_PAGE = 5

function getHistoryQueryOptions({ page }: { page: number }) {
  return {
    queryFn: () =>
      ScrappedService.readScrappedHistory({
        skip: (page - 1) * PER_PAGE,
        limit: PER_PAGE,
      }),
    queryKey: ["history", { page }],
  }
}

export const Route = createFileRoute("/_layout/history")({
  component: History,
  validateSearch: (search) => historySearchSchema.parse(search),
})

function HistoryTable() {
  const navigate = useNavigate({ from: Route.fullPath })
  const { page } = Route.useSearch()

  const { data, isLoading, isPlaceholderData } = useQuery({
    ...getHistoryQueryOptions({ page }),
    placeholderData: (prevData) => prevData,
  })

  const setPage = (page: number) =>
    navigate({
      search: (prev: { [key: string]: string }) => ({ ...prev, page }),
    })

  const historyItems = data?.data ?? []
  const count = data?.count ?? 0

  // Helper function to check if history item has viewable results
  const hasViewableResults = (status: string) => {
    return !(
      status === "pending" ||
      status.includes("failed") ||
      status === "error" ||
      status === "no_results"
    )
  }

  if (isLoading) {
    return <PendingItems />
  }

  if (historyItems.length === 0) {
    return (
      <EmptyState.Root>
        <EmptyState.Content>
          <EmptyState.Indicator>
            <FiSearch />
          </EmptyState.Indicator>
          <VStack textAlign="center">
            <EmptyState.Title>You don't have any history yet</EmptyState.Title>
            <EmptyState.Description>
              Add a new history entry to get started
            </EmptyState.Description>
          </VStack>
        </EmptyState.Content>
      </EmptyState.Root>
    )
  }

  return (
    <>
      <Table.Root size={{ base: "sm", md: "md" }}>
        <Table.Header>
          <Table.Row>
            <Table.ColumnHeader w="sm">ID</Table.ColumnHeader>
            <Table.ColumnHeader w="sm">City</Table.ColumnHeader>
            <Table.ColumnHeader w="sm">Price Range</Table.ColumnHeader>
            <Table.ColumnHeader w="sm">Stars</Table.ColumnHeader>
            <Table.ColumnHeader w="sm">Status</Table.ColumnHeader>
            <Table.ColumnHeader w="sm">Scraped Time</Table.ColumnHeader>
            <Table.ColumnHeader w="sm">Actions</Table.ColumnHeader>
          </Table.Row>
        </Table.Header>
        <Table.Body>
          {historyItems?.map((item) => (
            <Table.Row
              key={item.id}
              opacity={isPlaceholderData ? 0.5 : 1}
              cursor={
                hasViewableResults(item.scrape_status)
                  ? "pointer"
                  : "not-allowed"
              }
              _hover={{
                bg: hasViewableResults(item.scrape_status)
                  ? "gray.100"
                  : "transparent",
                _dark: {
                  bg: hasViewableResults(item.scrape_status)
                    ? "gray.700"
                    : "transparent",
                },
              }}
              onClick={() => {
                if (!hasViewableResults(item.scrape_status)) {
                  return
                }
                navigate({
                  to: "/search-results",
                  search: { search_id: item.id },
                })
              }}
            >
              <Table.Cell truncate maxW="sm">
                {item.id}
              </Table.Cell>
              <Table.Cell truncate maxW="sm">
                {item.city}
              </Table.Cell>
              <Table.Cell truncate maxW="sm">
                {item.price_min ? `$${item.price_min}` : "N/A"} -{" "}
                {item.price_max ? `$${item.price_max}` : "N/A"}
              </Table.Cell>
              <Table.Cell truncate maxW="sm">
                {item.stars ? `${item.stars} ⭐` : "N/A"}
              </Table.Cell>
              <Table.Cell truncate maxW="sm">
                {item.scrape_status}
              </Table.Cell>
              <Table.Cell truncate maxW="sm">
                {new Date(item.scrapped_time).toLocaleDateString()}
              </Table.Cell>
              <Table.Cell>
                <Button
                  size="sm"
                  colorScheme="blue"
                  onClick={(e) => {
                    e.stopPropagation()
                    navigate({
                      to: "/search-results",
                      search: { search_id: item.id },
                    })
                  }}
                  disabled={!hasViewableResults(item.scrape_status)}
                >
                  View Results
                </Button>
              </Table.Cell>
            </Table.Row>
          ))}
        </Table.Body>
      </Table.Root>
      <Flex justifyContent="flex-end" mt={4}>
        <PaginationRoot
          count={count}
          pageSize={PER_PAGE}
          onPageChange={({ page }) => setPage(page)}
        >
          <Flex>
            <PaginationPrevTrigger />
            <PaginationItems />
            <PaginationNextTrigger />
          </Flex>
        </PaginationRoot>
      </Flex>
    </>
  )
}

function History() {
  return (
    <Container maxW="full">
      <Heading size="lg" pt={12}>
        Scraping History
      </Heading>
      {/* <AddHistory /> */}
      <HistoryTable />
    </Container>
  )
}
