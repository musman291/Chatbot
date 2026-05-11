# Chatbot

This is a simple, rule-based chatbot that simulates a conversation with a bank branch manager. The chatbot is built with Python and can be run in a Docker container.

## Features

*   **Conversational Interface:** Engages users in a friendly, ELIZA-style conversation.
*   **State Management:** Tracks the conversation state to provide relevant responses.
*   **Banking Information:** Provides information about account types, required documents, fees, and card delivery.
*   **Personalization:** Addresses the user by name for a more personal touch.

## Technologies Used

*   Python 3.11
*   Docker

## Getting Started

### Prerequisites

*   Python 3.11 or later
*   Docker (optional, for containerized execution)

### Running with Docker

1.  **Build the Docker image:**
    ```sh
    docker build -t chatbot .
    ```

2.  **Run the Docker container:**
    ```sh
    docker run -it chatbot
    ```

### Running Locally

1.  **Clone the repository:**
    ```sh
    git clone https://github.com/your-username/Chatbot-main.git
    cd Chatbot-main
    ```

2.  **Run the chatbot script:**
    ```sh
    python chatbot.py
    ```

## How It Works

The chatbot operates on a system of states and rules. The conversation progresses through different states, such as `GREETING`, `GET_NAME`, `NEEDS_ASSESSMENT`, etc. For each state, there are predefined rules that match user input (using regular expressions) to generate an appropriate response.

If the user's input doesn't match any specific rules, the chatbot provides a fallback response.

## Customization

You can customize the chatbot's responses and parameters by modifying the `chatbot.py` file. Key configuration options at the top of the file include:

*   `BANK_NAME`: The name of the bank.
*   `MIN_DEPOSIT`: The minimum deposit amount.
*   `MIN_BALANCE`: The minimum balance required.
*   `SERVICE_CHARGE`: The service charge amount.

You can also add or modify the rules in the `_build_rules` method to change the chatbot's conversational flow and responses.
