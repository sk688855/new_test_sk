import asyncio
from typing import Annotated, Dict, Optional
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.remote.webdriver import WebDriver
from testzeus_hercules.config import get_global_conf
from testzeus_hercules.core.appium_manager import AppiumManager
from testzeus_hercules.core.generic_tools.tool_registry import tool
from testzeus_hercules.telemetry import EventData, EventType, add_event
from testzeus_hercules.utils.logger import logger

@tool(
    agent_names=["navigation_nav_agent"],
    description="Performs long press on element identified by identifier.",
    name="long_press_by_id"
)
async def long_press_by_id(
    duration: Annotated[int, "Duration of long press in milliseconds"] = 1000,
    resource_id: Annotated[str, "Resource ID of the element (Android: resource-id, iOS: name)"] = None,
    accessibility_id: Annotated[str, "Accessibility ID of the element (Android: content-desc, iOS: accessibilityIdentifier)"] = None,
    start_x: Annotated[int, "Start X coordinate"] = None,
    start_y: Annotated[int, "Start Y coordinate"] = None,
    end_x: Annotated[int, "End X coordinate"] = None,
    end_y: Annotated[int, "End Y coordinate"] = None,
    wait_before_action: Annotated[float, "Wait time before action in seconds"] = 0.0,
) -> Annotated[str, "Long press result"]:
    """
    Perform a long press on an element identified by its resource ID, accessibility ID, or coordinates.
    """
    if not any([resource_id, accessibility_id, all([start_x, start_y, end_x, end_y])]):
        raise RuntimeError("Must provide either resource_id, accessibility_id, or complete coordinates")

    bounds_data = None
    if all([start_x, start_y, end_x, end_y]):
        bounds_data = {
            "start_x": start_x,
            "start_y": start_y,
            "end_x": end_x,
            "end_y": end_y
        }

    logger.info(
        "Executing long_press_by_id with " +
        (f'resource_id: "{resource_id}", ' if resource_id else "") +
        (f'accessibility_id: "{accessibility_id}", ' if accessibility_id else "") +
        (f"bounds: ({start_x},{start_y}) to ({end_x},{end_y})" if bounds_data else "") +
        f", duration: {duration}ms"
    )
    add_event(EventType.INTERACTION, EventData(detail="long_press_by_id"))

    appium_manager = AppiumManager()
    if not appium_manager.driver:
        raise RuntimeError("No active Appium session. Please initialize a session first.")

    if wait_before_action > 0:
        await asyncio.sleep(wait_before_action)

    # Directly call long_press_by_id with all parameters
    await appium_manager.long_press_by_id(
        duration=duration,
        res_id=resource_id,
        accessibility_id=accessibility_id,
        bounds_data=bounds_data
    )

    await asyncio.sleep(get_global_conf().get_delay_time())
    
    success_msg = (
        "Successfully performed long press " +
        (f'on element with Resource ID: "{resource_id}", ' if resource_id else "") +
        (f'Accessibility ID: "{accessibility_id}", ' if accessibility_id else "") +
        (f"Bounds: ({start_x},{start_y}) to ({end_x},{end_y})" if bounds_data else "") +
        f"for {duration}ms. Any context menus or responses to the long press have been processed."
    )
    logger.info(success_msg)
    return success_msg