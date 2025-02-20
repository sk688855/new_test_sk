import asyncio
from typing import Any

import autogen  # type: ignore
from testzeus_hercules.core.playwright_manager import PlaywrightManager
from testzeus_hercules.telemetry import EventData, EventType, add_event
from testzeus_hercules.utils.logger import logger
from testzeus_hercules.utils.ui_messagetype import MessageType


def final_reply_callback_user_proxy(
    recipient: autogen.ConversableAgent,
    messages: list[dict[str, Any]],
    sender: autogen.Agent,
    config: dict[str, Any],
) -> tuple[bool, Any]:
    """
    Callback function that is called each time the user proxy agent receives a message.
    It picks the last message from the list of messages and checks if it contains the termination signal.
    If the termination signal is found, it extracts the final response and outputs it.

    Args:
        recipient (autogen.ConversableAgent): The recipient of the message.
        messages (Optional[list[dict[str, Any]]]): The list of messages received by the agent.
        sender (Optional[autogen.Agent]): The sender of the message.
        config (Optional[Any]): Additional configuration parameters.

    Returns:
        Tuple[bool, None]: A tuple indicating whether the processing should stop and the response to be sent.
    """
    global last_agent_response
    last_message = messages[-1]
    logger.debug(f"Post Process Message (User Proxy):{last_message}")
    if last_message.get("content") and "##TERMINATE##" in last_message["content"]:
        last_agent_response = last_message["content"].replace("##TERMINATE##", "").strip()
        if last_agent_response:
            logger.debug("*****Final Reply*****")
            logger.debug(f"Final Response: {last_agent_response}")
            logger.debug("*********************")
            return True, None

    return False, None


def final_reply_callback_planner_agent(message: str, message_type: MessageType = MessageType.STEP, stake_id: str = "", helper_name: str = "", is_assert: bool = False, is_passed: bool = False, assert_summary: str = "", is_terminated: bool = False, is_completed: bool = False, final_response: str = ""):  # type: ignore
    add_event(EventType.STEP, EventData(detail=message_type.value))
    return False, None  # required to ensure the agent communication flow continues
