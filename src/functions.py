from dotenv import load_dotenv
load_dotenv()


from datetime import datetime
import pytz
from dateutil.relativedelta import relativedelta
import pandas as pd

from langchain.tools import tool
from langchain_openai import ChatOpenAI
from langchain.agents import create_tool_calling_agent
from langchain.agents import AgentExecutor
from langchain import hub
from langchain.prompts import SystemMessagePromptTemplate
from langchain_core.messages import HumanMessage, AIMessage
from langchain.globals import set_debug, set_verbose

from celery import shared_task

from prompts import agent_system_prompt, check_availability_prompt, extraction_prompt
from app_config import create_flask
from instagrapi import Client

from util import *

flask_app = create_flask()
celery_app = flask_app.extensions["celery"]
instagram_bot = Client()
instagram_bot.login("mizuki1187", "$Ii8783219")
# set_debug(True)
# set_verbose(True)

@tool
def retrieve_availability(date_of_interest):
    """
    Retrieve the availability of the tattoo artist based on the provided query.

    Args:
        date_of_interest: The dates that the client would like to know the availibility for. It could be a date, date range, or common expression or phrase that imply dates, such as "the end of the week", "tomorrow", "next month", etc.

    Returns:
        The text response of the availability.
    """
    min_dt = datetime.now(pytz.timezone("Asia/Tokyo")).isoformat(timespec="seconds")
    max_dt = (datetime.now(pytz.timezone("Asia/Tokyo")) + relativedelta(days=60)).isoformat(timespec="seconds")
    events = calendar_get(min_dt, max_dt)

    try:
        df = pd.DataFrame(events)[["start","end"]]
        df = df.map(lambda x: x["dateTime"])
        df["existing appointments"] = "event" + (df.index+1).astype(str)
        df["appointment datet & time"] = "From " + df.start + " to " + df.end
        df = df.drop(["start", "end"], axis=1)
    except:
        return "直近の予約はありません。好きなお時間を指定してください。"

    availabilty_retrieval_chain = check_availability_prompt | ChatOpenAI(model="gpt-4o", temperature=0)
    extraction_chain = extraction_prompt | ChatOpenAI(model="gpt-4o", temperature=0)

    availability_retrieved = availabilty_retrieval_chain.invoke({"query":date_of_interest,"df":df.to_string(), "now": min_dt})
    extracted = extraction_chain.invoke({"input":availability_retrieved.content})

    return availability_retrieved.content


@tool
def retrieve_existing_appointment(ig_page: str) -> str:
    """
    A function to retrieve an existing appointment of the client.

    Args:
        ig_page (str): The Instagram page of the client

    Returns:
        str: A message indicating the existing appointment for the client
    """
    records = airtable_get(ig_page) # Modify to retirieving only appointments after the current day

    if len(records) == 0:
        return "既存の予約はありません"

    times = {"start_time": []}
    now = datetime.now(pytz.timezone("Asia/Tokyo")).isoformat()
    for record in records:
        utc_str = record["fields"]["start_time"]
        jst_str = utc_to_jst(utc_str)
        if jst_str > now:
            times["start_time"].append(jst_str)

    if len(times["start_time"]) == 0:
        return "No appointment found thats after the current day"

    return f"{record["fields"]["name"]}さんの既存の予約はこちら: {times}"

@tool
def create_new_appointment(ig_page: str, name: str, start_time: str, design: str, size: str, placement: str) -> str:
    """
    A function to create a new tattoo appointment with the provided details.

    Args:
        ig_page (str): The Instagram page of the client.
        name (str): The name of the client.
        start_time (str): The start time of the appointment in isoformat in Asia/Tokyo timezone.
        design (str): The design of the tattoo.
        size (str): The size of the tattoo.
        placement (str): The placement of the tattoo.

    Returns:
        str: A message indicating the status of the appointment creation.
    """
    #stat_time will be passed in isoformat in Asia/Tokyo timezone
    end_time = (datetime.strptime(start_time, '%Y-%m-%dT%H:%M:%S%z') + relativedelta(minutes=20)).isoformat(timespec="seconds")
    appointment_type = "カウンセリング"

    events = calendar_get(start_time, end_time)
    if len(events) != 0:
        return "新しい予約が今入ってしまいました。別の時間を選んでください"

    airtable_res = airtable_upsert(ig_page=ig_page,
                                   name=name,
                                   start_time=start_time,
                                   end_time=end_time,
                                   design=design,
                                   size=size,
                                   placement=placement,
                                   appointment_type=appointment_type
                                   )
    if airtable_res.status_code == 200:
        return "予約が完了しました。"
    else:
        return "予約作成中にエラーが発生しました。予約は完了していません。アーティストに直接連絡してください"

@tool
def modify_existing_appointment(ig_page: str, orig_start_time: str, new_start_time=None, new_design=None, new_size=None, new_placement=None) -> str:
    """
    A function to modify an existing appointment with the option to update the start time, design, size, and placement.
    Parameters:
    - ig_page(str): The Instagram page associated with the appointment.
    - orig_start_time(str): The original start time of the appointment in isoformat in Asia/Tokyo timezone.
    - new_start_time(str): The new start time for the appointment in isoformat in Asia/Tokyo timezone.
    - new_design(str): The new design of the tattoo.
    - new_size(str): The new size of the tattoo.
    - new_placement(str): The new placement of the tattoo.
   Note: new_start_time, new_design, new_size, new_placement are optional parameters that are passed to the function when there's a change in the appointment details. Default to None

    Returns:
    - str: A message indicating the status of the appointment modification process.
    """
    new_end_time = None

    if new_start_time:
        new_end_time = (datetime.strptime(new_start_time, '%Y-%m-%dT%H:%M:%S%z') + relativedelta(minutes=20)).isoformat(timespec="seconds")
        events = calendar_get(new_start_time, new_end_time)
        if len(events) != 0:
            return "その時間に予約が入っています。別の時間を選んでください"

    records = airtable_get(ig_page, jst_to_utc(orig_start_time))
    if len(records) !=1:
        return "エラーが発生しました。変更する予約を特定できません。アーティストに直接連絡してください"

    record_id = records[0]["id"]
    airtable_res = airtable_upsert(start_time=new_start_time,
                        end_time=new_end_time,
                        design=new_design,
                        size=new_size,
                        placement=new_placement,
                        record_id=record_id)

    if airtable_res.status_code == 200:
        return "予約変更が完了しました。"
    else:
        return "変更中にエラーが発生しました。予約は完了していません。アーティストに直接連絡してください"

@tool
def cancel_appointment(ig_page: str, start_time: str) -> str:
    """
    A function to cancel an appointment based on the Instagram page and start time provided.
    Parameters:
    - ig_page (str): The Instagram page associated with the appointment.
    - start_time (str): The start time of the appointment in isoformat in Asia/Tokyo timezone.

    Returns:
    - str: A message indicating the status of the appointment cancellation.
    """
    records = airtable_get(ig_page, jst_to_utc(start_time))
    if len(records) !=1:
        return "エラーが発生しました。変更する予約を特定できません。アーティストに直接連絡してください"

    airtable_res = airtable_delete(records[0]["id"])
    try:
        calendar_delete(records[0]["fields"]["event_id"])
    except:
        return "キャンセル中にエラーが発生しました。予約は完了していません。アーティストに直接連絡してください"

    if airtable_res.status_code == 200:
        return "予約のキャンセルが完了しました。"
    else:
        return "キャンセル中にエラーが発生しました。予約は完了していません。アーティストに直接連絡してください"



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
@shared_task
def get_response(query, chat_history, ig_page):
    agent_executor = create_agent(ig_page)
    clean_chat_history = clean_history(chat_history)
    response = agent_executor.invoke({
        "chat_history": clean_chat_history,
        "input": query,
    })

    return response["output"]
