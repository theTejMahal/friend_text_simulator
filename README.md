# Friend Text Simulator

Simulate chat with your friends based on your iMessage history. Uses GPT, Pinecone, and Streamlit. First, your conversations are loaded into the Pinecone vector database. For each query, the most relevant messages are pulled from Pinecone and used as context for the prompt to continue the conversation.

## Installation

### Clone the repository to your local machine:
git clone https://github.com/your-username/text-message-analysis.git
cd text-message-analysis
### Install the required python packages:
pip install -r requirements.txt

## Grant Permissions

Grant Full Disk Access to Terminal or your Python IDE:

- Open "System Preferences" on your Mac.
- Click on "Security & Privacy."
- Go to the "Privacy" tab.
- Scroll down and select the "Full Disk Access" folder from the left sidebar.
- Click on the lock icon in the lower-left corner to make changes. You'll be prompted to enter your administrator password.
- Click the "+" button to add an application. Navigate to and select the Terminal app or your Python IDE (e.g., PyCharm, Visual Studio Code). - - The app will be added to the list of apps with Full Disk Access permission.
- Close the "System Preferences" window.

Restart your Terminal or Python IDE to apply the changes.

## Usage

### Edit code
Add your own username, openai API key and Pinecone account details, and friend details. Everything you need to edit is marked by a #TODO.

### Run the loader.py script to load the text messages into the application. This script must be run directly from the terminal:
python loader.py

### Start the Streamlit application by running the app.py script:
streamlit run app.py

### Simulate conversations
Open your web browser and navigate to the URL provided by Streamlit (usually http://localhost:8501/) to use the application. 

## Video demo

See here for example use. 
https://user-images.githubusercontent.com/20506220/227788175-995b9a64-6a93-43e8-bc07-8df370efc6e1.mov

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues to improve the application or suggest new features.
