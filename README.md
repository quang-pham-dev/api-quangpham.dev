# QuangPham.dev API

QuangPham.dev is a web application that provides authentication and protected routes for users and administrators. This README outlines the API endpoints and provides instructions for setting up and running the project.

## Project Setup

### Prerequisites

- Docker
- Docker Compose

### Installation

1. Clone the repository:

   ```
   git clone https://github.com/quang-pham-dev/quangpham.dev.git
   cd quangpham.dev
   ```

2. Create a `.env` file in the root directory and add necessary environment variables:

   ```
   DB_USER=your_db_user
   DB_PASSWORD=your_db_password
   DB_NAME=your_db_name
   ```

3. Build and start the Docker containers:
   ```
   docker-compose up --build
   ```

The application will be available at http://localhost:5000.

## API Endpoints

### Authentication

| Method | Endpoint                       | Description                  |
| ------ | ------------------------------ | ---------------------------- |
| POST   | `/api/v1/auth/register`        | Register a new user          |
| POST   | `/api/v1/auth/login`           | User login                   |
| POST   | `/api/v1/auth/refresh`         | Refresh authentication token |
| POST   | `/api/v1/auth/forgot-password` | Request password reset       |
| POST   | `/api/v1/auth/reset-password`  | Reset password               |
| GET    | `/api/v1/auth/oauth/google`    | Google OAuth login           |
| GET    | `/api/v1/auth/oauth/github`    | GitHub OAuth login           |

### Protected Routes

| Method | Endpoint                           | Description                         | Access                          |
| ------ | ---------------------------------- | ----------------------------------- | ------------------------------- |
| GET    | `/api/v1/protected/user-info`      | Retrieve user information           | Authenticated users             |
| GET    | `/api/v1/protected/admin-only`     | Admin-specific functionality        | Administrators only             |
| GET    | `/api/v1/protected/user-and-admin` | General authenticated functionality | Users and administrators        |
| GET    | `/api/v1/protected/no-guests`      | Restricted access functionality     | Authenticated users (no guests) |

Note: All protected routes require a valid authentication token.

## Development

To run the project in development mode with live reloading:

```
docker-compose up
```

## Testing

Run the tests using:

```
docker-compose run web pytest
```

## Deployment

For production deployment, ensure you set appropriate environment variables and use a production-ready web server like Gunicorn.

## Contributing

Please read CONTRIBUTING.md for details on our code of conduct and the process for submitting pull requests.

## License

This project is licensed under the MIT License - see the LICENSE.md file for details.
