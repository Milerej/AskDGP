# DGP Chatbot

A chatbot application powered by OpenAI, designed to assist users with inquiries related to the Digital Governance Platform (DGP). This application leverages natural language processing and data from an IT Service Management (ITSM) platform to provide accurate and timely responses.

## Features

- **Natural Language Processing**: Understands and interprets user queries in natural language.
- **Fuzzy Matching**: Uses fuzzy string matching to provide relevant responses even with slight variations in user input.
- **Data Retrieval**: Accesses and processes data stored in an Amazon S3 bucket.
- **User-Friendly Interface**: Built with Streamlit for an interactive user experience.
- **Case Logging**: Offers assistance in logging helpdesk cases for unresolved queries.

## Installation

To set up the project locally, follow these steps:

1. **Clone the repository**:
    ```bash
    git clone <repository-url>
    cd <repository-name>
    ```

2. **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3. **Set up environment variables**:
    Create a `.env` file in the root directory and add the following variables:
    ```
    OPENAI_API_KEY=<your-openai-api-key>
    ACCESS_KEY=<your-aws-access-key-id>
    SECRET_ACCESS_KEY=<your-aws-secret-access-key>
    REGION_NAME=<your-aws-region>
    bucket_name=<your-s3-bucket-name>
    ```

4. **Run the application**:
    ```bash
    streamlit run app.py
    ```

## Usage

1. Open your web browser and navigate to `http://localhost:8501`.
2. Enter your query in the chat interface.
3. The chatbot will provide responses based on the data retrieved from the ITSM platform.
4. Use the suggestions provided in the sidebar for common queries.

## Technologies

- **Python**: Programming language used for development.
- **Streamlit**: Framework for building the web application.
- **OpenAI API**: For natural language processing capabilities.
- **Boto3**: AWS SDK for Python to interact with Amazon S3.
- **FuzzyWuzzy**: Library for fuzzy string matching.

## Contributing

Contributions are welcome! Please follow these steps to contribute:

1. Fork the repository.
2. Create a new branch for your feature or fix.
3. Make your changes and commit them.
4. Push your branch and submit a pull request.

## License

This project is licensed under the MIT License. 

## Contact

For any inquiries or feedback, please reach out to 
Soh Zhi Qi (soh_zhi_qi@tech.gov.sg)
Jere Lim (lim_keng_aik@tech.gov.sg)
Ang Hwee Tuck (ang_hwee_tuck@sport.gov.sg)
