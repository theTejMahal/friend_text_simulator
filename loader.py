import os
import openai
from tqdm.auto import tqdm
import pinecone
from time import sleep
import sqlite3
from tqdm.auto import tqdm
from datetime import datetime
import pandas as pd

# Functions
def add_speaker(messages,friend_name):
    annotated_text = []
    for index, row in messages.iterrows():
        if row['is_sent'] == 1:
            annotated_text.append(repr(f"Tejal: {row['text']}\n")) # TODO: replace with your name
        else:
            annotated_text.append(repr(f"{friend_name}: {row['text']}\n"))
    return annotated_text

def text_loader(friend_name,phone_use,index_name):

    openai.api_key = "" # TODO replace with your key
    embed_model = "text-embedding-ada-002"
    model = "gpt-3.5-turbo" #gpt-4
    encoding_model = "gpt-3.5-turbo"
    limit = 3000

    # Load the friend's text messages
    os.path.exists("/Users/yourusername/Library/Messages/chat.db") # TODO: replace with your username
    conn = sqlite3.connect('/Users/yourusername/Library/Messages/chat.db') # TODO: replace with your username
    cur = conn.cursor()
    messages = pd.read_sql_query("select *, datetime(message.date + strftime('%s', '2001-01-01') ,'unixepoch','localtime') as date_uct from message", conn)
    handles = pd.read_sql_query("select * from handle", conn)
    messages.rename(columns={'ROWID' : 'message_id'}, inplace = True)
    handles.rename(columns={'id' : 'phone_number', 'ROWID': 'handle_id'}, inplace = True)

    merge_level_1 = pd.merge(messages[['text', 'handle_id', 'date','is_sent', 'message_id']],  handles[['handle_id', 'phone_number']], on ='handle_id', how='left')
    chat_message_joins = pd.read_sql_query("select * from chat_message_join", conn)
    df_messages = pd.merge(merge_level_1, chat_message_joins[['chat_id', 'message_id']], on = 'message_id', how='left')

    ks_messages = df_messages[df_messages["phone_number"] == phone_use]

    # Define the custom epoch (January 1, 2001)
    custom_epoch = datetime(2001, 1, 1)

    # Convert the date column from nanoseconds to a readable format
    ks_messages['date_readable'] = pd.to_datetime(ks_messages['date'], unit='ns', origin=custom_epoch)

    # Extract year, month, day, and time
    ks_messages['year'] = ks_messages['date_readable'].dt.year
    ks_messages['month'] = ks_messages['date_readable'].dt.month
    ks_messages['day'] = ks_messages['date_readable'].dt.day
    ks_messages['time'] = ks_messages['date_readable'].dt.strftime('%H:%M')

    ks_messages = ks_messages.sort_values(by='date_readable', ascending=True)
    ks_messages["annotated_text"]=add_speaker(ks_messages,friend_name)
    ks_messages = ks_messages.reset_index()

    embed_model = "text-embedding-ada-002"

    # create new list of grouped data
    new_data = []

    window = 10  # number of texts to combine
    stride = 8  # number of texts to 'stride' over, used to create overlap

    for i in tqdm(range(0, len(ks_messages), stride)):
        i_end = min(len(ks_messages)-1, i+window)
        text = ' '.join(ks_messages[i:i_end]['annotated_text'])
        # create the new merged dataset
        new_data.append({
            'start': ks_messages['date_readable'][i],
            'end': ks_messages['date_readable'][i_end],
            'text': text,
            'id': ks_messages['message_id'][i]
        })
    # create pinecone index
    index_name = index_name

    # initialize connection to pinecone (get API key at app.pinecone.io)
    pinecone.init(
        api_key="", # TODO replace with your key
        environment="us-east-1-aws"  # TODO replace with yours, check at app.pinecone.io
    )

    # check if index already exists (it shouldn't if this is first time)
    if index_name not in pinecone.list_indexes():
        # if does not exist, create index
        pinecone.create_index(
            index_name,
            dimension= 1536 # the output dimensionality of the text-embedding-ada-002 model
        )
    # connect to index
    index = pinecone.Index(index_name)

    # create embeddings
    batch_size = 100  # how many embeddings we create and insert at once

    for i in tqdm(range(0, len(new_data), batch_size)):
        # find end of batch
        i_end = min(len(new_data), i+batch_size)
        meta_batch = new_data[i:i_end]
        # get ids
        ids_batch = [str(x['id']) for x in meta_batch]
        # get texts to encode
        texts = [x['text'] for x in meta_batch]
        # create embeddings (try-except added to avoid RateLimitError)
        try:
            res = openai.Embedding.create(input=texts, engine=embed_model)
        except:
            done = False
            while not done:
                sleep(5)
                try:
                    res = openai.Embedding.create(input=texts, engine=embed_model)
                    done = True
                except:
                    pass
        embeds = [record['embedding'] for record in res['data']]
        # cleanup metadata
        meta_batch = [{
            'start': x['start'],
            'end': x['end'],
            'text': x['text']
        } for x in meta_batch]
        to_upsert = list(zip(ids_batch, embeds, meta_batch))
        # upsert to Pinecone
        index.upsert(vectors=to_upsert)


if __name__ == "__main__":
    friend_name = "Sam" # TODO replace with your friend
    phone_use = "+11234567890" # TODO replace with your friend
    index_name = "sam-index" # TODO replace with your friend
    text_loader(friend_name,phone_use,index_name)