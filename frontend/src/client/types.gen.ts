// This file is auto-generated by @hey-api/openapi-ts

export type Body_login_login_access_token = {
  grant_type?: string | null
  username: string
  password: string
  scope?: string
  client_id?: string | null
  client_secret?: string | null
}

export type BookMarkedScrappedItem = {
  id?: string
  owner_id: string
  bookmarked_at?: string
  scrapped_item_id: string
}

export type HTTPValidationError = {
  detail?: Array<ValidationError>
}

export type ItemCreate = {
  title: string
  description?: string | null
}

export type ItemPublic = {
  title: string
  description?: string | null
  id: string
  owner_id: string
}

export type ItemsPublic = {
  data: Array<ItemPublic>
  count: number
}

export type ItemUpdate = {
  title?: string | null
  description?: string | null
}

export type Message = {
  message: string
}

export type NewPassword = {
  token: string
  new_password: string
}

export type PrivateUserCreate = {
  email: string
  password: string
  full_name: string
  is_verified?: boolean
}

export type ScrappedItem = {
  title: string
  price_booking: number
  url_booking: string
  stars?: number | null
  image_url?: string | null
  id?: string
  price_agoda?: number | null
  url_agoda?: string | null
  created_at?: string
  updated_at?: string
  history_id: string
}

export type ScrappedItemCreate = {
  title: string
  price_booking: number
  url_booking: string
  stars?: number | null
  image_url?: string | null
}

export type ScrappedItemPublic = {
  title: string
  price_booking: number
  url_booking: string
  stars: number | null
  image_url: string | null
  id: string
  price_agoda: number | null
  url_agoda: string | null
}

export type ScrappedItemsHistoriesPublic = {
  city?: string
  price_min?: number | null
  price_max?: number | null
  stars?: number | null
  data: Array<ScrappedItemsHistoryPublic>
  count: number
}

export type ScrappedItemsHistory = {
  city?: string
  price_min?: number | null
  price_max?: number | null
  stars?: number | null
  id?: string
  owner_id: string
  scrape_status: string
  scrapped_time?: string
}

export type ScrappedItemsHistoryCreate = {
  city?: string | null
  price_min?: number | null
  price_max?: number | null
  stars?: number | null
}

export type ScrappedItemsHistoryPublic = {
  city?: string
  price_min: number | null
  price_max: number | null
  stars: number | null
  id: string
  owner_id: string
  scrapped_time: string
  scrape_status: string
}

export type ScrappedItemsPublic = {
  data: Array<ScrappedItemPublic>
  count: number
}

export type Token = {
  access_token: string
  token_type?: string
}

export type UpdatePassword = {
  current_password: string
  new_password: string
}

export type UserCreate = {
  email: string
  is_active?: boolean
  is_superuser?: boolean
  full_name?: string | null
  password: string
}

export type UserPublic = {
  email: string
  is_active?: boolean
  is_superuser?: boolean
  full_name?: string | null
  id: string
}

export type UserRegister = {
  email: string
  password: string
  full_name?: string | null
}

export type UsersPublic = {
  data: Array<UserPublic>
  count: number
}

export type UserUpdate = {
  email?: string | null
  is_active?: boolean
  is_superuser?: boolean
  full_name?: string | null
  password?: string | null
}

export type UserUpdateMe = {
  full_name?: string | null
  email?: string | null
}

export type ValidationError = {
  loc: Array<string | number>
  msg: string
  type: string
}

export type ItemsReadItemsData = {
  limit?: number
  skip?: number
}

export type ItemsReadItemsResponse = ItemsPublic

export type ItemsCreateItemData = {
  requestBody: ItemCreate
}

export type ItemsCreateItemResponse = ItemPublic

export type ItemsReadItemData = {
  id: string
}

export type ItemsReadItemResponse = ItemPublic

export type ItemsUpdateItemData = {
  id: string
  requestBody: ItemUpdate
}

export type ItemsUpdateItemResponse = ItemPublic

export type ItemsDeleteItemData = {
  id: string
}

export type ItemsDeleteItemResponse = Message

export type LoginLoginAccessTokenData = {
  formData: Body_login_login_access_token
}

export type LoginLoginAccessTokenResponse = Token

export type LoginTestTokenResponse = UserPublic

export type LoginRecoverPasswordData = {
  email: string
}

export type LoginRecoverPasswordResponse = Message

export type LoginResetPasswordData = {
  requestBody: NewPassword
}

export type LoginResetPasswordResponse = Message

export type LoginRecoverPasswordHtmlContentData = {
  email: string
}

export type LoginRecoverPasswordHtmlContentResponse = string

export type PrivateCreateUserData = {
  requestBody: PrivateUserCreate
}

export type PrivateCreateUserResponse = UserPublic

export type ScrappedReadScrappedHistoryData = {
  limit?: number
  skip?: number
}

export type ScrappedReadScrappedHistoryResponse = ScrappedItemsHistoriesPublic

export type ScrappedCreateScrappedHistoryData = {
  requestBody: ScrappedItemsHistoryCreate
}

export type ScrappedCreateScrappedHistoryResponse = ScrappedItemsHistory

export type ScrappedReadScrappedHistoryByIdData = {
  id: string
}

export type ScrappedReadScrappedHistoryByIdResponse = ScrappedItemsHistory

export type ScrappedReadScrappedItemsData = {
  historyId: string
  limit?: number
  skip?: number
}

export type ScrappedReadScrappedItemsResponse = ScrappedItemsPublic

export type ScrappedCreateScrappedItemData = {
  historyId: string
  requestBody: ScrappedItemCreate
}

export type ScrappedCreateScrappedItemResponse = ScrappedItem

export type ScrappedBookmarkScrappedItemData = {
  itemId: string
}

export type ScrappedBookmarkScrappedItemResponse = BookMarkedScrappedItem

export type ScrappedDeleteBookmarkData = {
  itemId: string
}

export type ScrappedDeleteBookmarkResponse = Message

export type ScrappedReadBookmarkedItemsData = {
  limit?: number
  skip?: number
}

export type ScrappedReadBookmarkedItemsResponse = Array<BookMarkedScrappedItem>

export type UsersReadUsersData = {
  limit?: number
  skip?: number
}

export type UsersReadUsersResponse = UsersPublic

export type UsersCreateUserData = {
  requestBody: UserCreate
}

export type UsersCreateUserResponse = UserPublic

export type UsersReadUserMeResponse = UserPublic

export type UsersDeleteUserMeResponse = Message

export type UsersUpdateUserMeData = {
  requestBody: UserUpdateMe
}

export type UsersUpdateUserMeResponse = UserPublic

export type UsersUpdatePasswordMeData = {
  requestBody: UpdatePassword
}

export type UsersUpdatePasswordMeResponse = Message

export type UsersRegisterUserData = {
  requestBody: UserRegister
}

export type UsersRegisterUserResponse = UserPublic

export type UsersReadUserByIdData = {
  userId: string
}

export type UsersReadUserByIdResponse = UserPublic

export type UsersUpdateUserData = {
  requestBody: UserUpdate
  userId: string
}

export type UsersUpdateUserResponse = UserPublic

export type UsersDeleteUserData = {
  userId: string
}

export type UsersDeleteUserResponse = Message

export type UtilsTestEmailData = {
  emailTo: string
}

export type UtilsTestEmailResponse = Message

export type UtilsHealthCheckResponse = boolean
