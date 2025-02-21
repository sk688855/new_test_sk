import asyncio
import inspect
import traceback
from dataclasses import dataclass
from typing import Annotated, Any, List, Tuple

from playwright.async_api import Page
from testzeus_hercules.core.playwright_manager import PlaywrightManager
from testzeus_hercules.core.generic_tools.tool_registry import tool, tool_registry
from testzeus_hercules.utils.dom_helper import get_element_outer_html
from testzeus_hercules.utils.dom_mutation_observer import subscribe, unsubscribe
from testzeus_hercules.utils.js_helper import get_js_with_element_finder
from testzeus_hercules.utils.logger import logger
from testzeus_hercules.utils.ui_messagetype import MessageType


async def custom_set_slider_value(page: Page, selector: str, value_to_set: float) -> None:
    """
    Sets the value of a range slider input element to a specified value.

    This function directly sets the 'value' property of a range input element identified by the given CSS selector,
    and dispatches 'input' and 'change' events to simulate user interaction.

    Args:
        page (Page): The Playwright Page object representing the browser tab in which the operation will be performed.
        selector (str): The CSS selector string used to locate the target range input element.
        value_to_set (float): The numeric value to set for the slider.

    Example:
        await custom_set_slider_value(page, '#volume', 75)
    """
    selector = f"{selector}"  # Ensures the selector is treated as a string
    try:
        result = await page.evaluate(
            get_js_with_element_finder(
                """
            (inputParams) => {
                /*INJECT_FIND_ELEMENT_IN_SHADOW_DOM*/
                const { selector, value_to_set } = inputParams;
                const element = findElementInShadowDOMAndIframes(document, selector);
                if (!element) {
                    throw new Error(`Element not found: ${selector}`);
                }
                if (element.type !== 'range') {
                    throw new Error(`Element is not a range input: ${selector}`);
                }
                // Get min, max, and step values
                const min = parseFloat(element.min) || 0;
                const max = parseFloat(element.max) || 100;
                const step = parseFloat(element.step) || 1;
                // Clamp the value within the allowed range
                value_to_set = Math.max(min, Math.min(max, value_to_set));
                // Adjust value to the nearest step
                value_to_set = min + Math.round((value_to_set - min) / step) * step;
                // Set the value
                element.value = value_to_set;
                // Dispatch input and change events to simulate user interaction
                const inputEvent = new Event('input', { bubbles: true });
                const changeEvent = new Event('change', { bubbles: true });
                element.dispatchEvent(inputEvent);
                element.dispatchEvent(changeEvent);
                return `Value set for ${selector}`;
            }
            """
            ),
            {"selector": selector, "value_to_set": value_to_set},
        )
        logger.debug(f"custom_set_slider_value result: {result}")
    except Exception as e:
        logger.error(f"Error in custom_set_slider_value, Selector: {selector}, Value: {value_to_set}. Error: {str(e)}")
        raise


async def setslider(
    entry: Annotated[
        tuple,
        "tuple containing 'selector' and 'value_to_fill' in ('selector', 'value_to_fill') format, selector is md attribute value of the dom element to interact, md is an ID and 'value_to_fill' is the value or text of the option to select",
    ]
) -> Annotated[str, "Explanation of the outcome of this operation."]:
    logger.info(f"Setting slider value: {entry}")

    selector: str = entry[0]
    value_to_set: str = entry[1]

    if "md=" not in selector:
        selector = f"[md='{selector}']"
    # Create and use the PlaywrightManager
    browser_manager = PlaywrightManager()
    page = await browser_manager.get_current_page()
    if page is None:  # type: ignore
        return "Error: No active page found. OpenURL command opens a new page."

    function_name = inspect.currentframe().f_code.co_name  # type: ignore

    await browser_manager.take_screenshots(f"{function_name}_start", page)

    await browser_manager.highlight_element(selector)

    dom_changes_detected = None

    def detect_dom_changes(changes: str):  # type: ignore
        nonlocal dom_changes_detected
        dom_changes_detected = changes  # type: ignore

    subscribe(detect_dom_changes)

    result = await do_setslider(page, selector, value_to_set)
    await asyncio.sleep(get_global_conf().get_delay_time())  # sleep to allow the mutation observer to detect changes
    unsubscribe(detect_dom_changes)
    await page.wait_for_load_state()
    await browser_manager.take_screenshots(f"{function_name}_end", page)

    if dom_changes_detected:
        return f"{result['detailed_message']}.\n As a consequence of this action, new elements have appeared in view: {dom_changes_detected}. This means that the action of setting slider value {value_to_set} is not yet executed and needs further interaction. Get all_fields DOM to complete the interaction."
    return result["detailed_message"]


async def do_setslider(page: Page, selector: str, value_to_set: float) -> dict[str, str]:
    """
    Performs the slider value setting operation on a DOM or Shadow DOM element.

    This function sets the value of a range slider input element identified by the given CSS selector.
    It applies a pulsating border effect to the element during the operation for visual feedback.

    Args:
        page (Page): The Playwright Page object representing the browser tab in which the operation will be performed.
        selector (str): The CSS selector string used to locate the target range input element.
        value_to_set: The numeric value to set for the slider.

    Returns:
        dict[str, str]: Explanation of the outcome of this operation represented as a dictionary with 'summary_message' and 'detailed_message'.

    Example:
        result = await do_setslider(page, '#volume', 75)
    """
    try:
        logger.debug(f"Looking for selector {selector} to set slider value: {value_to_set}")

        # Find the element in the DOM or Shadow DOM
        browser_manager = PlaywrightManager()
        elem_handle = await browser_manager.find_element(selector, page)

        if elem_handle is None:
            error = f"Error: Selector {selector} not found. Unable to continue."
            return {"summary_message": error, "detailed_message": error}

        logger.info(f"Found selector {selector} to set slider value")
        element_outer_html = await get_element_outer_html(elem_handle, page)

        # Use the custom function to set the slider value
        await custom_set_slider_value(page, selector, value_to_set)

        await elem_handle.focus()
        await page.wait_for_load_state()
        logger.info(f"Success. Slider value {value_to_set} set successfully in the element with selector {selector}")
        success_msg = f"Success. Slider value {value_to_set} set successfully in the element with selector {selector}"
        return {
            "summary_message": success_msg,
            "detailed_message": f"{success_msg} and outer HTML: {element_outer_html}.",
        }

    except Exception as e:
        traceback.print_exc()
        error = f"Error setting slider value in selector {selector}."
        return {"summary_message": error, "detailed_message": f"{error} Error: {e}"}


@tool(
    agent_names=["navigation_nav_agent"],
    description="used to set slider values in multiple sliders in single attempt.",
    name="bulk_set_slider",
)
async def bulk_set_slider(
    entries: Annotated[
        List[List[str]],
        "List of tuple containing 'selector' and 'value_to_fill' in [('selector', 'value_to_fill'), ..] format, selector is md attribute value of the dom element to interact, md is an ID and 'value_to_fill' is the value or text of the option to select",
    ]  # noqa: UP006
) -> Annotated[
    List[dict],
    "List of dictionaries, each containing 'selector' and the result of the operation.",
]:  # noqa: UP006
    results: List[dict[str, str]] = []  # noqa: UP006
    logger.info("Executing bulk Set Slider Command")
    for entry in entries:
        selector = entry[0]
        result = await setslider(entry)

        results.append({"selector": selector, "result": result})

    return results
