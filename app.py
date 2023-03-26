import streamlit as st
import openai
import tiktoken
import pinecone
import warnings

# Functions
def num_tokens_from_string(string: str, encoding_model: str) -> int:
    """Returns the number of tokens in a text string."""
    try:
        encoding = tiktoken.encoding_for_model(encoding_model)
    except:
        encoding = tiktoken.get_encoding("cl100k_base")
    num_tokens = len(encoding.encode(string))
    return num_tokens

def complete(prompt,model,friend_name):
    messages = [
        {"role": "system", "content": f"You are simulating a coversation between {friend_name} and Tejal. You mimic their styles of texting as closely as possible. You will first be given example conversations and then try to complete a new conversation as true as possible to what {friend_name} and Tejal would  really say."}, # TODO: replace with your name
        {"role": "user", "content": f"{prompt}"}
    ]
    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
    )
    return response.choices[0].message["content"].strip()

def retrieve(query,embed_model,index,friend_name,limit,encoding_model):
    res = openai.Embedding.create(
        input=[query],
        engine=embed_model
    )

    # retrieve from Pinecone
    xq = res['data'][0]['embedding']

    # get relevant contexts
    res = index.query(xq, top_k=10, include_metadata=True)
    contexts = [
        x['metadata']['text'] for x in res['matches']
    ]

    # build our prompt with the retrieved contexts included
    prompt_start = (
        f"Simulate the rest of the conversation using the example chats below, matching this style very closely. Example chats:\n\n---\n\n"
    )
    prompt_end = (
        f"---\n\nUsing the style of the above conversations, what comes next? \n\n---\n\n Tejal: {query}\n\n {friend_name}: " # TODO: replace with your name
    )
    # append contexts until hitting limit
    for i in range(1, len(contexts)):
        if num_tokens_from_string("\n\n---\n\n".join(contexts[:i]),encoding_model) >= limit:
            prompt = (
                prompt_start +
                "\n\n---\n\n".join(contexts[:i-1]) + "\n\n---\n\n" +
                prompt_end
            )
            break
        elif i == len(contexts)-1:
            prompt = (
                prompt_start +
                "\n\n---\n\n".join(contexts) + "\n\n---\n\n" +
                prompt_end
            )
    return prompt

# Streamlit app
def main():
    st.title("Simulate a chat with Tejal's friends") # TODO: replace with your name

    # Initialize friends list
    friends = [
        {"friend_name": "Sam", "phone_use": "+11233455678", "index_name": 'sam-texts'}, # TODO replace with your friends
    ]

    # Dropdown menu for selecting a friend
    friend_name = st.selectbox("Select a friend", [f["friend_name"] for f in friends])

    # Text area for entering the query
    query = st.text_area("Enter your query")

    # Simulate conversation button
    if st.button("Simulate Conversation"):
        # Your notebook code to generate conversation based on the given friend and query

        warnings.filterwarnings('ignore')
        openai.api_key = "" # TODO replace with your key
        embed_model = "text-embedding-ada-002"
        model = "gpt-3.5-turbo" #gpt-4
        encoding_model = "gpt-3.5-turbo"
        limit = 3000

        # pinecone
        index_name = 'sam-texts'
        pinecone.init(
            api_key="", # TODO replace with your key
            environment="us-east-1-aws"  # TODO replace with yours, check at app.pinecone.io
        )
        index = pinecone.Index(index_name)
 
        # first we retrieve relevant items from Pinecone
        query_with_contexts = retrieve(query,embed_model,index,friend_name,limit,encoding_model)

        # Define the toggle using the beta_expander component
        with st.expander("Toggle to display full prompt"):
            # Use a try/except block to handle cases where the variable is not yet available
            try:
                st.write(query_with_contexts)
            except:
                st.write("Not yet available.")

        # then we complete the context-infused query
        response_text = complete(query_with_contexts,model,friend_name)

        st.header("Generated Conversation")
        st.write("Sam: ",response_text)



if __name__ == "__main__":
    main()