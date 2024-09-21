# Cowrywise Library Book Manager

## Overview
The Cowrywise Library Book Manager is a RESTful API designed to manage user enrollment, book catalogue, and administrative tasks within a library system. It allows users to enroll, borrow books, retrieve available books, and enables admins to manage the library's catalogue.

It is an assessment project for the Backend/DevOps/Infra application advertised at: 
https://cowrywise.breezy.hr/p/b8872b4dea60-backend-engineer-infrastructure-api-engineer-devops

Developer: [JekayinOluwa Olabemiwo](https://github.com/J-rayX)

## Features
- User enrollment
- Borrowing books
- Retrieving book details
- Admin functionalities for adding and removing books
- Filtering available books

## Table of Contents
- [Installation](#installation)
- [Usage](#usage)
- [API Endpoints](#api-endpoints)
- [Quickstart Guide](#quickstart-guide)
- [Postman Collection](#postman-collection)
- [Service Communication](#service-communication)
- [Docker Setup](#docker-setup)
- [Contributing](#contributing)
- [License](#license)

## Installation

### Prerequisites
- Python 3.x
- Django
- Django REST Framework
- RabbitMQ (for message queuing)
- Docker (to run containers and deploy)

### Steps
1. Clone the repository:
   ```bash
   git clone https://github.com/J-rayX/cowrywise-library-book-manager.git
   cd cowrywise-library-book-manager
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up the database:
   ```bash
   python manage.py migrate
   ```

5. Create a superuser (for admin access):
   ```bash
   python manage.py createsuperuser
   ```

6. Run the development server:
   ```bash
   python manage.py runserver
   ```

## Usage
You can interact with the API using tools like Postman or cURL. Refer to the [API Endpoints](#api-endpoints) section for details on available endpoints.


## API Endpoints

### User Enrollment
- **POST** `/users/enroll/` - Enroll a new user.
- **GET** `/books/<int:book_id>/` - Retrieve details of a specific book.
- **POST** `/books/borrow/<int:book_id>/` - Borrow a book.
- **GET** `/books/available/` - Retrieve a list of all available books.
- **GET** `/books/filter/` - Filter books based on query parameters, `publisher` and `category`.

### Admin API
- **POST** `/books/add/` - Add a new book.
- **DELETE** `/books/remove/<int:book_id>/` - Remove a book.
- **GET** `books/unavailable/` : **List borrowed books** i.e books not available for borrow.
- **GET** `/users/` - List all library users.
- **GET** `/users/borrow/` - Fetch all users with the books they borrowed.


## Quickstart Guide
This quickstart guide demonstrates how to use the `enroll` and `add book` endpoints of the Cowrywise Library Book Manager API using cURL.

## Prerequisites

- Ensure you have cURL installed on your machine.
- The API server should be running and accessible.

## 1. User Enrollment

To enroll a new user, use the following cURL command:


### cURL Command
```curl
bash
curl -X POST http://<your-api-host>/users/enroll/ \
-H "Content-Type: application/json" \
-d '{
"email": "jkaylight@gmail.com",
"firstname": "Jekayin-Oluwa",
"lastname": "Olabemiwo"
}'
```

### Expected Response

If successful, you should receive a response like:
```json
{
"message": "New user, Jekayin-Oluwa Olabemiwo enrolled! 🔥"
}
```



## 2. Admin Add Book

To add a new book as an admin, use the following cURL command:

### cURL Command
```bash

curl -X POST http://<your-api-host>/books/add/ \
-H "Content-Type: application/json" \
-d '{
"title": "Determination Unshakable",
"author": "Goodluck Jonathan",
"publisher": "Clear-Coast",
"category": "Writing"
}'
```


### Expected Response

If successful, you should receive a response like:
```json
{
"message": "Book successfully added."
}
```

By now, you have successfully used the `enroll` and `add book` endpoints of the Cowrywise Library Book Manager API using cURL. Adjust the `<your-api-host>` placeholder with the actual host where the API is deployed.



## Postman Collection
You can copy or download the Postman collection JSON file for the Cowrywise Library Manager API from the following link:
[Cowrywise Library Manager API.postman_collection.json](https://github.com/J-rayX/cowrywise-library-book-manager/Cowrywise%20Library%20Manager%20API.postman_collection.json)

Then, import the downloaded file in your Postman to view the full documention on all endpoints with example requests and responses.


## Database Management and Inter-Service Communication

The Frontend API and Admin API communicate changes made to each other as they use different data stores. RabbitMQ powers the event-driven messaging system between the two services.

## Database Usage

- **Frontend API:** Uses PostgreSQL
- **Admin API:** Uses MySQL

### Frontend Database Structure
- **User Table:** Stores user information.
- **UserBook Table:** Saves the newly added books from the Admin API.
- **Borrowing Table:** Keeps track of book borrowings.

### Admin Database Structure
- **Book Table:** Stores information about books.
- **AdminUser Table:** Saves the newly enrolled users from the Frontend API.
- **AdminBorrowing Table:** Keeps track of user borrowings from the Frontend API.

## Communication Points

1. **User Enrollment:**
   - The newly added user information is queued as a message on the `user_enrolled` RabbitMQ queue.
   - The message is then consumed by the Admin API's `consume_user_enrolled` consumer.
   - The consumed user detail is saved in the `AdminUser` table.

2. **Book Borrowing:**
   - When a user borrows a book through the Frontend API, the details of the book, including its new availability status and return date, are queued on the `book_borrowed` queue.
   - The queued message is then consumed by the `consume_borrowed` consumer in the `consumer.py` file of the `Admin_API` project.

3. **Book Addition and Removal:**
   - The library admin can add and remove new books through the Admin API.
   - These actions are queued in the `book_added` and `book_removed` queues, respectively.
   - They are then consumed from the Frontend API consumers, `consume_book_added` and `consume_book_removed`, respectively.

---

This structure provides a clear overview of how the Frontend API and Admin API interact, along with their respective database structures and communication points.


## Docker Setup
To run the application in a Docker container, ensure you have Docker installed. Use the following commands:

1. Build the Docker image:
   ```bash
   docker build -t cowrywise-library-book-manager .
   ```

2. Run the Docker container:
   ```bash
   docker run -p 8000:8000 cowrywise-library-book-manager
   ```

## Contributing
Contributions are welcome! Please follow these steps:
1. Fork the repository.
2. Create a new branch (`git checkout -b feature-branch`).
3. Make your changes and commit them (`git commit -m 'Add new feature'`).
4. Push to the branch (`git push origin feature-branch`).
5. Create a pull request.

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.