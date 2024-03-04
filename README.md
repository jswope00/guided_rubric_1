# Interactive Article Review Assistant

This application leverages OpenAI's GPT-4 model to guide users through a critical analysis of assets, like a scholarly journal articles. It prompts users with questions about an article, provides feedback on their responses, and scores their understanding based on a predefined rubric.

## Key Features

- **Interactive Q&A**: Engages users with a series of questions created by the educator.
- **AI-Powered Feedback**: Utilizes OpenAI's GPT-4 to generate immediate, constructive feedback on user responses.
- **Rubric-Based Scoring**: Evaluates user responses against a custom rubric to ensure a thorough analysis of the article.
- **Progress Tracking**: Dynamically tracks user progress through the questions and feedback loops.
- **Visual and Animated Feedback**: Incorporates Lottie animations and images to enhance user engagement and provide visual cues for feedback.

## Setup and Installation

1. **Clone the Repository**: Start by cloning this repository to your local machine.

2. **Install Dependencies**: Install the required Python packages using pip:
    ```bash
    pip install -r requirements.txt
    ```

3. **Configure OpenAI API Key**: 
    - Create a `.env` file in the root directory of your project.
    - Add your OpenAI API key to the `.env` file:
        ```
        OPENAI_API_KEY='your_api_key_here'
        ```

4. **Run the Application**: Navigate to the directory containing the application and run it using Streamlit:
    ```bash
    streamlit run main.py
    ```

## Using the Application

- **Start the Application**: After launching, the app will guide you to input your responses to a series of questions based on a specified article.
- **View PDF**: A link to the target article PDF is provided within the app for reference.
- **Answer Questions**: Type your answers directly into the input fields. The app will provide feedback and a score based on your responses.
- **Progress Through the Review**: Your progress is saved as you move through the questions. You can skip questions.

## Contribution and Support

- **Contribute**: Contributions to improve the application or extend its capabilities are welcome! Please submit pull requests or open issues for bugs and feature requests.
- **Support**: If you encounter any problems or have suggestions, please open an issue in the repository.

## License

This project is licensed under the MIT License - see the LICENSE.md file for details.
