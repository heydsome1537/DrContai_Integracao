# Pluggy Integration Dr.Contaí

## Getting Started

Follow these steps to set up and run the project:

### 1. Backend Setup
1. Navigate to the `backend` folder.
2. Execute the `server.py` script:
    ```sh
    python server.py
    ```

### 2. Ngrok Setup
1. Run ngrok to generate an HTTPS address:
    ```sh
    ngrok http 5000
    ```
2. Go to [Pluggy Dashboard](https://dashboard.pluggy.ai/).
3. Navigate to `Applications` and configure a webhook with the event `item/created`.

### 3. Frontend Setup
1. Execute the frontend and connect an account.

### 4. Dashboard Setup
1. Locate the generated files and update their location in `dashboard.py`.
2. Run the Streamlit script:
    ```sh
    streamlit run dashboard.py
    ```

## Additional Information
For more details, refer to the project documentation or contact the project maintainers.
