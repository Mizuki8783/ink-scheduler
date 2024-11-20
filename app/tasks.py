from celery import shared_task
from .utils.llm.agents import create_agent, clean_history

@shared_task
def get_response(query, chat_history, ig_page, user_id):
    agent_executor = create_agent(ig_page, user_id)
    clean_chat_history = clean_history(chat_history)
    response = agent_executor.invoke({
        "chat_history": clean_chat_history,
        "input": query,
    })

    return response["output"]

print(f"-----------------{__name__}-----------------")
