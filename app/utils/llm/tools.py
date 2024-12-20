from datetime import datetime
from dateutil.relativedelta import relativedelta
from langchain.tools import tool
from langchain_openai import ChatOpenAI
import pandas as pd
import pytz
from ..util import *
from .prompts import check_availability_prompt
from pydantic import BaseModel, Field
from typing import Optional


###########Argument Schemas###########
class RetrieveAvailabilityInput(BaseModel):
    date_of_interest: str = Field(description="The dates that the client would like to know the availibility for. It could be a date, date range, or common expression or phrase that imply dates, such as 'the end of the week', 'tomorrow', 'next month', etc.")

class RetrieveExistingAppointmentInput(BaseModel):
    ig_page: str = Field(description="The Instagram page of the client")

class CreateNewAppointmentInput(BaseModel):
    ig_page: str = Field(description="The Instagram page of the client")
    name: str = Field(description="The name of the client")
    start_time: str = Field(description="The start time of the appointment in isoformat in Asia/Tokyo timezone")
    design: str = Field(description="The design of the tattoo")
    size: str = Field(description="The size of the tattoo")
    placement: str = Field(description="The placement of the tattoo")

class ModifyExistingAppointmentInput(BaseModel):
    ig_page: str = Field(description="The Instagram page of the client")
    orig_start_time: str = Field(description="The original start time of the appointment in isoformat in Asia/Tokyo timezone")
    new_start_time: Optional[str] = Field(description="The new start time for the appointment in isoformat in Asia/Tokyo timezone")
    new_design: Optional[str] = Field(description="The new design of the tattoo")
    new_size: Optional[str] = Field(description="The new size of the tattoo")
    new_placement: Optional[str] = Field(description="The new placement of the tattoo")

class CancelAppointmentInput(BaseModel):
    ig_page: str = Field(description="The Instagram page of the client")
    start_time: str = Field(description="The start time of the appointment in isoformat in Asia/Tokyo timezone")


###########Tools###########
def retrieve_availability(user_id, date_of_interest):
    """
    Retrieve the availability of the tattoo artist based on the provided query.

    Returns:
        The text response of the availability.
    """
    min_dt = datetime.now(pytz.timezone("Asia/Tokyo")).isoformat(timespec="seconds")
    max_dt = (datetime.now(pytz.timezone("Asia/Tokyo")) + relativedelta(days=60)).isoformat(timespec="seconds")
    events = calendar_get(min_dt, max_dt, user_id)

    try:
        df = pd.DataFrame(events)[["start","end"]]
        df = df.map(lambda x: x["dateTime"])
        df["existing appointments"] = "event" + (df.index+1).astype(str)
        df["appointment datet & time"] = "From " + df.start + " to " + df.end
        df = df.drop(["start", "end"], axis=1)
    except:
        return "直近の予約はありません。好きなお時間を指定してください。"

    availabilty_retrieval_chain = check_availability_prompt | ChatOpenAI(model="gpt-4o", temperature=0)

    availability_retrieved = availabilty_retrieval_chain.invoke({"query":date_of_interest,"df":df.to_string(), "now": min_dt})

    return availability_retrieved.content


def retrieve_existing_appointment(ig_page: str) -> str:
    """
    A function to retrieve an existing appointment of the client.

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


def create_new_appointment(user_id: str, ig_page: str, name: str, start_time: str, design: str, size: str, placement: str) -> str:
    """
    A function to create a new tattoo appointment with the provided details.

    Returns:
        str: A message indicating the status of the appointment creation.
    """
    #stat_time will be passed in isoformat in Asia/Tokyo timezone
    end_time = (datetime.strptime(start_time, '%Y-%m-%dT%H:%M:%S%z') + relativedelta(minutes=20)).isoformat(timespec="seconds")
    appointment_type = "カウンセリング"

    events = calendar_get(start_time, end_time, user_id)
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

def modify_existing_appointment(user_id: str, ig_page: str, orig_start_time: str, new_start_time=None, new_design=None, new_size=None, new_placement=None) -> str:
    """
    A function to modify an existing appointment with the option to update the start time, design, size, and placement.

    Returns:
    - str: A message indicating the status of the appointment modification process.
    """
    new_end_time = None

    if new_start_time:
        new_end_time = (datetime.strptime(new_start_time, '%Y-%m-%dT%H:%M:%S%z') + relativedelta(minutes=20)).isoformat(timespec="seconds")
        events = calendar_get(new_start_time, new_end_time, user_id)
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

def cancel_appointment(user_id: str, ig_page: str, start_time: str) -> str:
    """
    A function to cancel an appointment based on the Instagram page and start time provided.

    Returns:
    - str: A message indicating the status of the appointment cancellation.
    """
    records = airtable_get(ig_page, jst_to_utc(start_time))
    if len(records) !=1:
        return "エラーが発生しました。変更する予約を特定できません。アーティストに直接連絡してください"

    airtable_res = airtable_delete(records[0]["id"])
    try:
        calendar_delete(records[0]["fields"]["event_id"], user_id)
    except:
        return "キャンセル中にエラーが発生しました。予約は完了していません。アーティストに直接連絡してください"

    if airtable_res.status_code == 200:
        return "予約のキャンセルが完了しました。"
    else:
        return "キャンセル中にエラーが発生しました。予約は完了していません。アーティストに直接連絡してください"


print(f"-----------------{__name__}-----------------")
