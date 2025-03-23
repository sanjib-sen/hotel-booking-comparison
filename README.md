# Hotel Booking App

This is a full-stack application built with FastAPI, Scrapy and React.

## Getting Started

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)

### Quick Start

1. Clone the repository
2. Run the application with Docker Compose:

```bash
docker compose up -d
```

3. Open your browser and visit:
   - **http://localhost:5173**

That's it! The application will be available at:

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000/api/
- API documentation: http://localhost:8000/api/docs

## Demo Video

[Demo Video](https://drive.google.com/drive/folders/1C73uaBC3iW_QEvNygQL280E8DDFb4Ohz?usp=sharing)

## Note on Environment Variables

Although it's not a standard practice to include .env files in a repository, they have been included here for the sake of time and assessment purposes. In a production environment, these should be properly secured and not committed to version control.

## Application Specifics

### Currency

- The application uses BDT (Bangladeshi Taka) as the currency
- A fixed conversion rate of 1 USD = 123 BDT is used for currency conversion

### Geographical Limitations

- For the sake of time and assessment, the search functionality is limited to Bangladeshi cities only

## License

This project is licensed under the terms of the MIT license.
