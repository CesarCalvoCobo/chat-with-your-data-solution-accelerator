import logging
import openai
import os
import json
import azure.functions as func
from gpt4all import GPT4All, Embed4All
import pandas as pd
from openai.embeddings_utils import cosine_similarity
from typing import Optional, List
from typing import Optional, List
from azure.core.credentials import AzureKeyCredential  
from azure.search.documents import SearchClient  
from azure.search.documents.indexes import SearchIndexClient  
from azure.search.documents.models import Vector  
from azure.search.documents.indexes.models import (  
    SearchIndex,  
    SearchField,  
    SearchFieldDataType,  
    SimpleField,  
    SearchableField,  
    SearchIndex,  
    SemanticConfiguration,  
    PrioritizedFields,  
    SemanticField,  
    SearchField,  
    SemanticSettings,  
    VectorSearch,  
    HnswVectorSearchAlgorithmConfiguration,  
)

from utilities.helpers.EnvHelper import EnvHelper
from utilities.helpers.AzureBlobStorageHelper import AzureBlobStorageClient

env_helper: EnvHelper = EnvHelper()
blob_client = AzureBlobStorageClient()    
container_sas = blob_client.get_container_sas()

openai.api_type = "azure"
openai.api_version = env_helper.AZURE_OPENAI_API_VERSION
openai.api_base = env_helper.OPENAI_API_BASE
openai.api_key = env_helper.OPENAI_API_KEY




# Add your Azure Cognitive Search service endpoint and index name here
service_endpoint = env_helper.AZURE_SEARCH_SERVICE
index_name = env_helper.AZURE_SEARCH_INDEX
key = env_helper.AZURE_SEARCH_KEY
credential = AzureKeyCredential(key)

# Initialize the SearchClient
search_client = SearchClient(service_endpoint, index_name, AzureKeyCredential(key))


class CustomEmbed4All(Embed4All):
    def __init__(
        self,
        model_path: str,
        model_name: str,
        n_threads: Optional[int] = None,
    ):
        """
        Constructor

        Args:
            model_path: The path to the custom GPT4All model.
            n_threads: number of CPU threads used by GPT4All. Default is None, then the number of threads are determined automatically.
        """
        self.gpt4all = GPT4All(model_path=model_path, model_name=model_name, n_threads=n_threads)

    def embed(
        self,
        text: str
    ) -> List[float]:
        """
        Generate an embedding.

        Args:
            text: The text document to generate an embedding for.

        Returns:
            An embedding of your document of text.
        """
        return self.gpt4all.model.generate_embedding(text)

def extract_terms(text):
    response = openai.ChatCompletion.create(
            engine=env_helper.AZURE_OPENAI_MODEL,
            messages = [{"role":"system","content":"Extract the important terms from the following text to send it to another query in a database but just adding the important information about materials and actions . \nJust give the output with this format : material action  \nDo not add any other character like commas, dots or similar "},{"role":"user","content":"which are the best practices to reduce aluminium wastre "},{"role":"assistant","content":"aluminium waste reduction"},{"role":"user","content":"How to recycle carton waste"},{"role":"assistant","content":"carton waste recycling"},{"role":"user","content":"How to recycle water"},{"role":"assistant","content":"water recycling"},{"role":"user","content":"How to treat metal waste"},{"role":"assistant","content":"metal waste treatment"},{"role": "user", "content": text}],
            temperature=0.5,
            max_tokens=1024,
            top_p=0.95,
            frequency_penalty=0,
            presence_penalty=0,
            stop=None
            )
    terms=  response.choices[0]['message']['content'].strip()
    return terms



def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    # Extract the query parameter
    query = req.params.get('query')
    if not query:
        try:
            req_body = req.get_json()
        except ValueError:
            pass
        else:
            query = req_body.get('query')

    if query:        
        #terms = extract_terms(query)
        MODEL_PATH = os.getcwd()
        MODEL_NAME = "ggml-all-MiniLM-L6-v2-f16.bin"

        custom_embed4all = CustomEmbed4All(model_path=MODEL_PATH, model_name=MODEL_NAME)
        query_embedding = custom_embed4all.embed(query)

        search_client = SearchClient(service_endpoint, index_name, credential=credential)
        vector = Vector(value=query_embedding, k=env_helper.AZURE_SEARCH_TOP_K, fields="content_vector")
  
        results = search_client.search(  
            search_text=None,  
            vectors= [vector],
            select=["content", "metadata", "title","source"]
        )  
     
        # Create a list to store the results
        res = []
        for result in results:
            res.append({"Content": result["content"], 
                        "Title": result["title"],                        
                        "Metadata": result["metadata"].replace("_SAS_TOKEN_PLACEHOLDER_", container_sas), 
                        "Source": result["source"].replace("_SAS_TOKEN_PLACEHOLDER_", container_sas), 
                        "Similarities": result["@search.score"]})

        # Convert the result list to json
        res_json = json.dumps(res)

        return func.HttpResponse(res_json, mimetype="application/json")
        
    else:
        return func.HttpResponse(
             "Please pass a query on the query string or in the request body",
             status_code=400
        )