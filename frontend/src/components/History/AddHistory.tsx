import { useMutation, useQueryClient } from "@tanstack/react-query"
import { type SubmitHandler, useForm } from "react-hook-form"
import { useState } from "react"
import { FaPlus } from "react-icons/fa"

import {
    Button,
    DialogActionTrigger,
    DialogTitle,
    Input,
    Text,
    VStack,
} from "@chakra-ui/react"

import { ScrappedService } from "@/client"
import type { ApiError } from "@/client/core/ApiError"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"
import {
    DialogBody,
    DialogCloseTrigger,
    DialogContent,
    DialogFooter,
    DialogHeader,
    DialogRoot,
    DialogTrigger,
} from "../ui/dialog"
import { Field } from "../ui/field"

interface ScrappedHistoryCreate {
    city: string
    price_min?: number | null
    price_max?: number | null
    stars?: number | null
}

const AddHistory = () => {
    const [isOpen, setIsOpen] = useState(false)
    const queryClient = useQueryClient()
    const { showSuccessToast } = useCustomToast()
    const {
        register,
        handleSubmit,
        reset,
        formState: { errors, isValid, isSubmitting },
    } = useForm<ScrappedHistoryCreate>({
        mode: "onBlur",
        criteriaMode: "all",
        defaultValues: {
            city: "",
            price_min: null,
            price_max: null,
            stars: null,
        },
    })

    const mutation = useMutation({
        mutationFn: (data: ScrappedHistoryCreate) =>
            ScrappedService.createScrappedHistory({ requestBody: data }),
        onSuccess: () => {
            showSuccessToast("History entry created successfully.")
            reset()
            setIsOpen(false)
        },
        onError: (err: ApiError) => {
            handleError(err)
        },
        onSettled: () => {
            queryClient.invalidateQueries({ queryKey: ["history"] })
        },
    })

    const onSubmit: SubmitHandler<ScrappedHistoryCreate> = (data) => {
        mutation.mutate(data)
    }

    return (
        <DialogRoot
            size={{ base: "xs", md: "md" }}
            placement="center"
            open={isOpen}
            onOpenChange={({ open }) => setIsOpen(open)}
        >
            <DialogTrigger asChild>
                <Button value="add-history" my={4}>
                    <FaPlus fontSize="16px" />
                    Add History
                </Button>
            </DialogTrigger>
            <DialogContent>
                <form onSubmit={handleSubmit(onSubmit)}>
                    <DialogHeader>
                        <DialogTitle>Add Scraping History</DialogTitle>
                    </DialogHeader>
                    <DialogBody>
                        <Text mb={4}>Fill in the details to add a new scraping history entry.</Text>
                        <VStack gap={4}>
                            <Field
                                required
                                invalid={!!errors.city}
                                errorText={errors.city?.message}
                                label="City"
                            >
                                <Input
                                    id="city"
                                    {...register("city", {
                                        required: "City is required.",
                                    })}
                                    placeholder="Enter city name"
                                    type="text"
                                />
                            </Field>

                            <Field
                                invalid={!!errors.price_min}
                                errorText={errors.price_min?.message}
                                label="Minimum Price"
                            >
                                <Input
                                    id="price_min"
                                    {...register("price_min", {
                                        valueAsNumber: true,
                                        min: { value: 0, message: "Price must be positive" },
                                    })}
                                    placeholder="Enter minimum price"
                                    type="number"
                                    min={0}
                                />
                            </Field>

                            <Field
                                invalid={!!errors.price_max}
                                errorText={errors.price_max?.message}
                                label="Maximum Price"
                            >
                                <Input
                                    id="price_max"
                                    {...register("price_max", {
                                        valueAsNumber: true,
                                        min: { value: 0, message: "Price must be positive" },
                                    })}
                                    placeholder="Enter maximum price"
                                    type="number"
                                    min={0}
                                />
                            </Field>

                            <Field
                                invalid={!!errors.stars}
                                errorText={errors.stars?.message}
                                label="Minimum Stars"
                            >
                                <Input
                                    id="stars"
                                    {...register("stars", {
                                        valueAsNumber: true,
                                        min: { value: 0, message: "Stars must be between 0 and 5" },
                                        max: { value: 5, message: "Stars must be between 0 and 5" },
                                    })}
                                    placeholder="Enter minimum stars (0-5)"
                                    type="number"
                                    min={0}
                                    max={5}
                                    step={0.1}
                                />
                            </Field>
                        </VStack>
                    </DialogBody>

                    <DialogFooter gap={2}>
                        <DialogActionTrigger asChild>
                            <Button
                                variant="subtle"
                                colorPalette="gray"
                                disabled={isSubmitting}
                            >
                                Cancel
                            </Button>
                        </DialogActionTrigger>
                        <Button
                            variant="solid"
                            type="submit"
                            disabled={!isValid}
                            loading={isSubmitting}
                        >
                            Save
                        </Button>
                    </DialogFooter>
                </form>
                <DialogCloseTrigger />
            </DialogContent>
        </DialogRoot>
    )
}

export default AddHistory 