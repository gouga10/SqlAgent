from langchain.agents import tool
from langchain_openai import ChatOpenAI
from langchain_community.utilities.sql_database import SQLDatabase
from langchain_community.tools.sql_database.tool import (
    InfoSQLDatabaseTool,
    ListSQLDatabaseTool,
    QuerySQLCheckerTool,
    QuerySQLDataBaseTool,
)
from langchain_core.agents import AgentAction, AgentFinish

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents.output_parsers.openai_tools import OpenAIToolsAgentOutputParser
from langchain.agents import AgentExecutor
from langchain.agents.format_scratchpad.openai_tools import (
    format_to_openai_tool_messages,
)
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import os
from dotenv import load_dotenv
from typing import List, Optional, Tuple
load_dotenv()

db = SQLDatabase.from_uri("sqlite:///coaches.db")
llm = ChatOpenAI(
    temperature=0, 
    model="gpt-4o-mini",  
    api_key=os.getenv("OPENAI_API_KEY")
)


#Check the available tables in the database
@tool("list_tables")
def list_tables() -> str:
    """List the available tables in the database"""
    db = SQLDatabase.from_uri("sqlite:///coaches.db")

    return ListSQLDatabaseTool(db=db).invoke("")

#Get the schema and sample rows for the specified tables
@tool("tables_schema")
def tables_schema(tables: str) -> str:
    """
    Input is a comma-separated list of tables, output is the schema and sample rows
    for those tables. Be sure that the tables actually exist by calling `list_tables` first!
    Example Input: table1, table2, table3
    """
    db = SQLDatabase.from_uri("sqlite:///coaches.db")

    return InfoSQLDatabaseTool(db=db).invoke(tables)

#Execute a SQL query against the database
@tool("execute_sql")
def execute_sql(sql_query: str) -> str:
    """Execute a SQL query against the database. Returns the result"""
    db = SQLDatabase.from_uri("sqlite:///coaches.db")
    result = QuerySQLDataBaseTool(db=db, return_direct=True).invoke(sql_query)

    return result

#Check the correctness of a SQL query
@tool("check_sql")
def check_sql(sql_query: str) -> str:
    """
    Use this tool to double check if your query is correct before executing it.
    Always use this tool before executing a query with `execute_sql`.

    """
    db = SQLDatabase.from_uri("sqlite:///coaches.db")
    llm = ChatOpenAI(
    temperature=0, 
    model="gpt-4o-mini",  
    api_key=os.getenv("OPENAI_API_KEY")
)
    return QuerySQLCheckerTool(db=db, llm=llm).invoke({"query": sql_query})

tools = [list_tables, tables_schema, execute_sql, check_sql]
llm_with_tools = llm.bind_tools(tools)


prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
             """
You are a SQL Database Developer tasked with retrieving and returning information from the database using the provided tools based on user query , you need simple to return the same output as the execute_sql tool, incorporating contextual understanding from past user queries: {context}.
- **Context Awareness**:
    - Compare the new query with the most recent past query in the context.
    - If the new query aligns with the most recent past query, leverage the existing context for continuity.
    - If the new query differs significantly, prioritize the new query, resetting the context to ensure accurate and focused results.

### Tools:
- `list_tables`: To view all available tables in the database.
- `tables_schema`: To understand the structure of specific tables.
- `execute_sql`: To run SQL queries and retrieve data.
- `check_sql`: To verify the correctness of SQL queries before executing them.

### Guidelines:
1. **Focus**: 
   - Use the tools to fetch the required information based on the user query.
   - Directly return the exact output of the `execute_sql` tool.

2. **Output Requirements**:
   - Provide the raw result as it is returned by the `execute_sql` tool.
   - Do not include any additional formatting, context, or commentary.

3. **Behavior**:
   - If a query is invalid or cannot be executed, return only the error message or result from the tools.
   - Do not attempt to explain the issue or rephrase the output.

4. **Expected Output Example**:
   ```plaintext
   
""",
        ),
        ("user", "{query}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ]
)
agent = (
    {
        "query": lambda x: x["query"],
        "context": lambda x: x["context"],
        "agent_scratchpad": lambda x: format_to_openai_tool_messages(
            x["intermediate_steps"]
        ),
    }
    | prompt
    | llm_with_tools
    | OpenAIToolsAgentOutputParser()
)
class DirectSQLAgentExecutor(AgentExecutor):
    def _get_tool_return(
        self, next_step_output: Tuple[AgentAction, str]
    ) -> Optional[AgentFinish]:
        """Override to force return after successful SQL execution but continue on errors"""
        agent_action, observation = next_step_output
        
        if agent_action.tool == "execute_sql":
            if "Error: (sqlite3.OperationalError)" in observation:
                return None
            else:
                return AgentFinish(
                    return_values={"output": observation},
                    log=""
                )
        return None

agent_executor = DirectSQLAgentExecutor(agent=agent, tools=tools, verbose=True,return_intermediate_steps=True,early_stopping_method="force")

def query_coach_database(query: str, context: str):
    result = agent_executor._call({"query": query, "context": context})
    return result




prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
You are a professional Coach manager Dealership Assistant. Your role is to help users explore and understand the available coaches based on the database context provided to you. The database context contains information about various coaches that match the user's query. Your task is to present the full context in a clear, engaging, and visually appealing way.
Database context information below :
----------------------------------------------------------------
context : 
{sql_context}
----------------------------------------------------------------
### Instructions for Generating Responses:
1. **Understand the Context:**
   - The context provided contains the relevant rows from the database based on the user's query.
   - Each row represents a coach and some key details about it.

2. **Present the Information:**
   - Format your response to ensure it's easy to read and visually appealing:
     - Use **tables** for listing multiple coaches.
     - Use **bullet points** for highlighting key features or details about a single coach.
     - Provide links to purchase pages where available.
   - Make the response friendly, professional, and helpful.
   - List all available coaches from the provided context without omitting any entries. Ensure every coach in the context is included in the response, with no summaries or selective omissions.
   

3. **Error Handling:**
   - If the context contains no relevant rows, respond with a polite and helpful message:
     - Suggest alternative options or clarify the constraints (e.g., budget or brand).

Your goal is to act as an expert assistant and deliver responses that make the user’s coach finding experience easier .
            """,
        ),
        ("user", "{query}"),
        
    ]
)

output_parser = StrOutputParser()

chain = prompt | llm | StrOutputParser()
def database_context(user_query: str, context: str) -> str:
    result = query_coach_database(user_query, context)
    sql_context = result['output']
    return sql_context
def generate(user_query: str , sql_context: str) -> str:
    """
    Generate AI response dynamically.
    """
    
    response = chain.invoke({"query": user_query, "sql_context": sql_context})
    
    return response


