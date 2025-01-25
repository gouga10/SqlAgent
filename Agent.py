from dotenv import load_dotenv
import time
from langchain_agent import  database_context
import requests
load_dotenv()



# This function is used to format the user query and the SQL context to be used by the GPT-4o-mini model
def Formatter (user_query,sql_context):
  api_key = "sk-proj-RVeMAP3fDG7ZLJxAyA6FT3BlbkFJyyaPG2cD0BBs5L0h67Wi"
  headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {api_key}"
  }
  payload2 = {
    "model": "gpt-4o-mini",
    "messages": [
  {
    "role": "user",
    "content": [
    {
          "type": "text",
          "text": f"""
                You are a Fitness coaches Manager. you will be provided with a user query and the response to that user query from the SQL Database that represents the info you will use to answer.
                User Query: {user_query}
                SQL Context: {sql_context}                  
 """
    }
       
   ]
  }     
                ],
    "max_tokens": 5000
            }
      
  response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload2)
  gpt_output=response.json()['choices'][0]['message']['content']
  return gpt_output

# This function is used to generate the Sql query from the user input and then Reformat the answer from the GPT-4o-mini model
def generate_response(user_query):
    """
    Generate AI response dynamically.
    """
  
    sql_context = database_context(user_query=user_query, context=None)
    response =  Formatter(user_query,sql_context)
    return response
 

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import time
from typing import Dict, Any, Optional, List
from fastapi.responses import FileResponse
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
app = FastAPI()

class QueryRequest(BaseModel):
    query: str



#End point API to generate the answer

@app.post("/generate")
async def generate_answer_endpoint(request: QueryRequest) -> Dict[str, Any]:
    
        start_time = time.time()

        
        user_query = request.query
        response=generate_response(user_query)
        
        print("--- %s seconds ---" % (time.time() - start_time))
        return {
            "response": str(response)
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)





#To Try the system you can use the below curl command
#curl -X POST "http://localhost:8001/generate" -H "Content-Type: application/json" -d '{"query": "what coaches are available in dubai"}'