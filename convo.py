import sys
import os
import openai
import logging
import json
import sqlite3
import datetime

logging.basicConfig(filename='some.log', encoding='utf-8', level=logging.DEBUG)

key = os.environ["OPENAI_API_KEY"]

client = openai.OpenAI(api_key=key)
model_version = "gpt-3.5-turbo-0125"

# Description of the FTR enums was ignored when it was a --sqlComment, but works when it is a separate sentence, weird (gpt-3.5-turbo-0125)
table_metadata = """
CREATE TYPE team AS ENUM ('Chelsea', 'Middlesbrough', 'Bournemouth', 'Burnley', 'Everton',
'Bradford City', 'West Ham', 'Nottingham Forest', 'Hull City', 'Swansea City', 'West Brom',
'Huddersfield', 'Coventry City', 'Manchester City', 'Manchester Utd', 'Blackpool', 'Reading',
'Fulham', 'Brentford', 'Portsmouth', 'Leicester City', 'Wimbledon',
'Sheffield Weds', 'Ipswich Town', 'Barnsley', 'Sunderland', 'Blackburn', 'Brighton',
'Charlton Ath', 'QPR', 'Norwich City', 'Sheffield Utd', 'Wolves', 'Tottenham', 'Aston Villa',
'Derby County', 'Oldham Athletic', 'Birmingham City', 'Stoke City', 'Wigan Athletic', 'Cardiff City',
'Newcastle Utd', 'Liverpool', 'Arsenal', 'Crystal Palace', 'Leeds United', 'Watford',
'Southampton', 'Bolton', 'Swindon Town');

CREATE TYPE game_result AS 
    ENUM ('A', 'H', 'D'); 
'A' means the away team won, 'H' means the home team won and 'D' means the result was a draw 

CREATE TABLE premier_league_matches (season_end_year SMALLINT, season_week SMALLINT, 
match_date DATE, home_team_name team, 
home_team_goals SMALLINT, away_team_name team, 
away_team_goals SMALLINT, full_time_result game_result);
"""
logging.info(f'table_metadata:{table_metadata}')

#currently just handles two layers of nesting because I am dumb and lazy
def answer_dates_to_string(ans):
    if type(ans) == datetime.date:
        return ans.isoformat()
    result = []
    if type(ans) == tuple or type(ans) == list:
        for i in ans:
            if type(i) == tuple or type(i) == list:
                result += [list(map(lambda x: x.isoformat() if type(x) == datetime.date else x, i))]
            else:
                result = list(map(lambda x: x.isoformat() if type(x) == datetime.date else x, ans))
    return result


def db_query(target_query):
    """Execute query on sqlite db using sqlite3"""

    with sqlite3.connect('cooldb.db') as conn:

        if target_query[-1] != ";":
            target_query += ";"
        print(target_query)
        logging.info(f'target_query:{target_query}')

        cursor = conn.cursor() 

        cursor.execute(target_query)

        answer = cursor.fetchall()

        answer = answer_dates_to_string(answer)

        answer = json.dumps(answer)

        cursor.close()

    print("=============================")
    print("here is the sqlite answer:")
    print(answer)
    print("=============================")
    logging.info(f'query_result:{answer}')
    return answer


def run_conversation(query):
    # Step 1: send the conversation and available functions to GPT
    prompt = f"""
        Here is the context for how the tables are structured:
        {table_metadata}
        Now please convert the query below into working SQL and execute it:
        {query}
    """
    messages = [{"role": "user", "content": prompt}]
    tools = [
        {
            "type": "function",
            "function": {
                "name": "db_query",
                "description": "Execute the given SQL query and return the results",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "target_query": {
                            "type": "string",
                            "description": "The SQL query to execute"
                        }                
                    },
                    "required": ["target_query"]
                }
            }

        }
    ]


    response = client.chat.completions.create(
        model=model_version,
        messages=messages,
        tools=tools,
        tool_choice="auto",  # auto is default, but we'll be explicit
    )
    response_message = response.choices[0].message
    print("=============================")
    print(f'here is the first gpt response message:')
    logging.info(f'gpt_response1:{response_message}')
    print(response_message)
    print("=============================")

# Step 2: check if GPT wanted to call a function
    tool_calls = response_message.tool_calls
    if tool_calls:
# Step 3: call the function
        # Note: the JSON response may not always be valid; be sure to handle errors

        available_functions = {
            "db_query": db_query,
        }  # only one function in this example, but you can have multiple

        messages.append(response_message)

        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_to_call = available_functions[function_name]
            function_args = json.loads(tool_call.function.arguments)
            function_response = function_to_call(
                target_query=function_args.get("target_query")
            )
            messages.append(
                {
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": function_response,
                }
            )  # extend conversation with function response


        second_response = client.chat.completions.create(
            model=model_version,
            messages=messages,
        )  # get a new response from the model where it can see the function response
        print("=============================")
        print("second (final) response:")
        print(second_response)
        logging.info(f'gpt_response2:{second_response}')
        print('=============================END=============================')
        return second_response


    else:
        print("apparently GPT didn't want to call a function....")



if len(sys.argv) < 2:
    print("You forgot to add a query")
elif len(sys.argv) > 2:
    print("too many arguments... you should only be asking a single query")
else:
    assert type(sys.argv[1]) == str
    run_conversation(sys.argv[1])
