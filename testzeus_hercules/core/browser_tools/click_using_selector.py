from typing import Annotated, Dict, Any
import time
from playwright.sync_api import Page, Dialog
from testzeus_hercules.config import get_global_conf
from testzeus_hercules.core.playwright_manager import PlaywrightManager
from testzeus_hercules.core.generic_tools.tool_registry import tool
from testzeus_hercules.utils.dom_helper import get_element_outer_html
from testzeus_hercules.utils.logger import logger

# Store page data
_page_data = {}


def set_page_data(page: Any, data: Any) -> None:
    """Set data for a specific page."""
    _page_data[id(page)] = data


def get_page_data(page: Any) -> dict:
    """Get data for a specific page."""
    return _page_data.get(id(page), {})


@tool(
    agent_names=["click_nav_agent"],
    description="Click on an element using a selector.",
    name="click",
)
def click(
    selector: Annotated[str, "CSS selector for the element to click."],
    wait_before_execution: Annotated[
        float, "Time to wait before clicking (in seconds)."
    ] = 0.0,
    type_of_click: Annotated[
        str, "Type of click action (click, dblclick, etc.)."
    ] = "click",
    user_input_dialog_response: Annotated[
        str, "Response to any dialog that appears."
    ] = "",
) -> Annotated[Dict[str, str], "Result of the click operation."]:
    """
    Click on an element using a selector.
    """
    try:
        browser_manager = PlaywrightManager()
        page = browser_manager.get_current_page()

        # Wait before action if specified
        if wait_before_execution > 0:
            time.sleep(wait_before_execution)

        # Set up dialog handler if needed
        if user_input_dialog_response:

            def handle_dialog(dialog: Dialog) -> None:
                if user_input_dialog_response:
                    dialog.accept(user_input_dialog_response)
                else:
                    dialog.dismiss()

            page.on("dialog", handle_dialog)

        # Perform the click
        result = do_click(page, selector, wait_before_execution, type_of_click)

        # Wait after action
        time.sleep(get_global_conf().get_delay_time())

        return result

    except Exception as e:
        logger.error(f"Error in click: {str(e)}")
        return {"error": str(e)}


def do_click(
    page: Page, selector: str, wait_before_execution: float, type_of_click: str
) -> Dict[str, str]:
    """
    Helper function to perform the actual click operation.
    """
    try:
        browser_manager = PlaywrightManager()
        element = browser_manager.find_element(selector, page)
        if not element:
            return {"error": f"Element not found with selector: {selector}"}

        # Get element HTML before click for logging
        element_outer_html = get_element_outer_html(element, page)

        # Perform the click based on type
        if type_of_click == "click":
            element.click()
        elif type_of_click == "dblclick":
            element.dblclick()
        elif type_of_click == "right_click":
            element.click(button="right")
        else:
            return {"error": f"Unsupported click type: {type_of_click}"}

        return {
            "status": "success",
            "message": f"Successfully performed {type_of_click} on element: {element_outer_html}",
        }

    except Exception as e:
        logger.error(f"Error in do_click: {str(e)}")
        return {"error": str(e)}


@tool(
    agent_names=["click_nav_agent"],
    description="Click on multiple elements using selectors.",
    name="bulk_click",
)
def bulk_click(
    entries: Annotated[
        List[Dict[str, str]],
        "List of dictionaries containing 'selector' and optional 'type_of_click' keys.",
    ],
) -> Annotated[List[Dict[str, str]], "Results of the bulk click operations."]:
    """
    Click on multiple elements using selectors.
    """
    results = []
    for entry in entries:
        type_of_click = entry.get("type_of_click", "click")
        result = click(entry["selector"], type_of_click=type_of_click)
        results.append(result)
    return results
