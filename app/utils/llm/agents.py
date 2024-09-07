from dotenv import load_dotenv
load_dotenv()

from datetime import datetime
import pytz

from langchain_openai import ChatOpenAI
from langchain.agents import create_tool_calling_agent
from langchain.agents import AgentExecutor
from langchain import hub
from langchain.prompts import SystemMessagePromptTemplate
from langchain_core.messages import HumanMessage, AIMessage


from .prompts import agent_system_prompt
from .tools import *

def modify_prompt(type_prompt, ig_page):
    prompt = hub.pull("hwchase17/openai-functions-agent")
    system_message_template = SystemMessagePromptTemplate.from_template(
        type_prompt.format(
            ig_page=ig_page,
            now=datetime.now(pytz.timezone("Asia/Tokyo")).isoformat(timespec="seconds")
            )
        )
    prompt.messages[0] = system_message_template

    return prompt

def create_agent(ig_page):

    llm = ChatOpenAI(model="gpt-4o",temperature=0)
    tools = [
        retrieve_availability,
        create_new_appointment,
        retrieve_existing_appointment,
        modify_existing_appointment,
        cancel_appointment
        ]
    prompt = modify_prompt(agent_system_prompt, ig_page)

    agent_base = create_tool_calling_agent(llm, tools, prompt)
    agent = AgentExecutor(agent=agent_base, tools=tools, verbose=True)

    return agent

def clean_history(chat_history):
    history = []
    print(chat_history)
    for message in chat_history.split("_end_of_message_"):
        speaker, content = message.split(": ", 1)
        if speaker == "AI_MESSAGE":
            history.append(AIMessage(content))
        else:
            history.append(HumanMessage(content))

    return history


print(f"-----------------{__name__}-----------------")
