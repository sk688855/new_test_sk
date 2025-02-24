import json
import os
from typing import Annotated, Dict, Optional

import autogen
from testzeus_hercules.config import get_global_conf
from testzeus_hercules.core.generic_tools.tool_registry import tool
from testzeus_hercules.core.playwright_manager import PlaywrightManager
from testzeus_hercules.utils.logger import logger


def write_json(filepath: str, data: Dict) -> None:
    """Write data to a JSON file."""
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)


def _write_comparison_to_file(comparison_data: Dict, filepath: str) -> None:
    """Write comparison data to a JSON file."""
    try:
        write_json(filepath, comparison_data)
    except Exception as e:
        logger.error(f"Error writing comparison data to file: {e}")


@tool(
    agent_names=["visual_nav_agent"],
    description="Compare the current screenshot with a reference image.",
    name="compare_visual_screenshot",
)
def compare_visual_screenshot(
    reference_image_path: Annotated[str, "Path to the reference image."],
    comparison_description: Annotated[str, "Description of what to compare."],
) -> Annotated[Dict[str, str], "Result of the visual comparison."]:
    """
    Compare the current screenshot with a reference image.
    """
    try:
        browser_manager = PlaywrightManager()
        screenshot_stream = browser_manager.get_latest_screenshot_stream()
        if not screenshot_stream:
            page = browser_manager.get_current_page()
            browser_manager.take_screenshots("comparison_screenshot", page)
            screenshot_stream = browser_manager.get_latest_screenshot_stream()

        if not screenshot_stream:
            return {"error": "Failed to capture current screenshot"}

        # Create image comparison agent
        image_agent = autogen.AssistantAgent(
            name="image_comparison_agent",
            llm_config={"config_list": get_global_conf().get_llm_config()},
            system_message="You are an expert at comparing images and identifying visual differences.",
        )

        # Create user proxy for image comparison
        image_ex_user_proxy = autogen.UserProxyAgent(
            name="image_comparison_user_proxy",
            human_input_mode="NEVER",
            max_consecutive_auto_reply=1,
            code_execution_config=False,
        )

        # Prepare message for image comparison
        message = {
            "role": "user",
            "content": f"Compare these two images and describe the differences focusing on {comparison_description}:\n"
            f"1. Reference image: {reference_image_path}\n"
            f"2. Current screenshot: {screenshot_stream}\n",
        }

        # Get comparison result
        chat_response = image_ex_user_proxy.initiate_chat(image_agent, message=message)

        # Prepare comparison data
        comparison_data = {
            "reference_image": reference_image_path,
            "comparison_description": comparison_description,
            "comparison_result": chat_response.get(
                "content", "No response from comparison"
            ),
        }

        # Save comparison data if debug mode is enabled
        if get_global_conf().get_debug_mode():
            debug_dir = os.path.join(get_global_conf().get_proof_path(), "debug")
            os.makedirs(debug_dir, exist_ok=True)
            comparison_file = os.path.join(debug_dir, "visual_comparison.json")
            _write_comparison_to_file(comparison_data, comparison_file)

        return {
            "status": "success",
            "message": "Visual comparison completed successfully",
            "details": comparison_data["comparison_result"],
        }

    except Exception as e:
        logger.error(f"Error in visual comparison: {e}")
        return {"error": str(e)}


@tool(
    agent_names=["visual_nav_agent"],
    description="Validate visual features in the current view.",
    name="validate_visual_feature",
)
def validate_visual_feature(
    feature_description: Annotated[
        str, "Description of the visual feature to validate."
    ],
) -> Annotated[Dict[str, str], "Result of the visual validation."]:
    """
    Validate visual features in the current view.
    """
    try:
        browser_manager = PlaywrightManager()
        screenshot_stream = browser_manager.get_latest_screenshot_stream()
        if not screenshot_stream:
            page = browser_manager.get_current_page()
            browser_manager.take_screenshots("feature_validation", page)
            screenshot_stream = browser_manager.get_latest_screenshot_stream()

        if not screenshot_stream:
            return {"error": "Failed to capture current screenshot"}

        # Create image validation agent
        image_agent = autogen.AssistantAgent(
            name="image_validation_agent",
            llm_config={"config_list": get_global_conf().get_llm_config()},
            system_message="You are an expert at validating visual features in user interfaces.",
        )

        # Create user proxy for image validation
        image_ex_user_proxy = autogen.UserProxyAgent(
            name="image_validation_user_proxy",
            human_input_mode="NEVER",
            max_consecutive_auto_reply=1,
            code_execution_config=False,
        )

        # Prepare message for feature validation
        message = {
            "role": "user",
            "content": f"Validate the following visual feature in this screenshot:\n"
            f"Feature to validate: {feature_description}\n"
            f"Screenshot: {screenshot_stream}\n",
        }

        # Get validation result
        chat_response = image_ex_user_proxy.initiate_chat(image_agent, message=message)

        # Prepare validation data
        validation_data = {
            "feature_description": feature_description,
            "validation_result": chat_response.get(
                "content", "No response from validation"
            ),
        }

        # Save validation data if debug mode is enabled
        if get_global_conf().get_debug_mode():
            debug_dir = os.path.join(get_global_conf().get_proof_path(), "debug")
            os.makedirs(debug_dir, exist_ok=True)
            validation_file = os.path.join(debug_dir, "visual_validation.json")
            _write_comparison_to_file(validation_data, validation_file)

        return {
            "status": "success",
            "message": "Visual validation completed successfully",
            "details": validation_data["validation_result"],
        }

    except Exception as e:
        logger.error(f"Error in visual validation: {e}")
        return {"error": str(e)}
