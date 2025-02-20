import json
import os
from typing import Any

from testzeus_hercules.utils.logger import logger


class AgentsLLMConfig:
    # Mapping from environment keys to model config keys
    KEY_MAPPING_ENV_MODEL: dict[str, str] = {
        "LLM_MODEL_NAME": "model",
        "LLM_MODEL_API_KEY": "api_key",
        "LLM_MODEL_BASE_URL": "base_url",
        "LLM_MODEL_API_TYPE": "api_type",
        "LLM_MODEL_API_VERSION": "api_version",
        "LLM_MODEL_PROJECT_ID": "gcp_project_id",
        "LLM_MODEL_REGION": "gcp_region",
    }

    # Mapping from environment keys to LLM config keys
    KEY_MAPPING_ENV_LLM: dict[str, str] = {
        "LLM_MODEL_TEMPERATURE": "temperature",
        "LLM_MODEL_TOP_P": "top_p",
    }

    # Mapping from file keys to model config keys
    KEY_MAPPING_FILE: dict[str, str] = {
        "model_name": "model",
        "model_api_key": "api_key",
        "model_base_url": "base_url",
        "model_client_host": "client_host",
        "model_native_tool_calls": "native_tool_calls",
        "model_hide_tools": "hide_tools",
        "model_api_type": "api_type",
        "model_project_id": "gcp_project_id",
        "model_region": "gcp_region",
        "model_api_version": "api_version",
        "model_aws_region": "aws_region",
        "model_aws_access_key": "aws_access_key",
        "model_aws_secret_key": "aws_secret_key",
        "model_aws_profile_name": "aws_profile_name",
        "model_aws_session_token": "aws_session_token",
        "model_pricing": "price",
    }

    def __init__(self, llm_config: dict[str, Any] | None = None) -> None:

        if llm_config:
            self.config: dict[str, Any] = self.load_config_from_api(llm_config)
        else:
            self.config = self._load_config()

    def _load_config(self) -> dict[str, Any]:
        config_file = os.getenv("AGENTS_LLM_CONFIG_FILE")
        config_file_ref_key = os.getenv("AGENTS_LLM_CONFIG_FILE_REF_KEY")

        if config_file:
            try:
                with open(config_file, "r") as file:  # noqa: UP015
                    file_config = json.load(file)

                if config_file_ref_key:
                    if config_file_ref_key in file_config:
                        logger.info(f"Loading configuration from: {config_file} with key: {config_file_ref_key}")
                        raw_config = file_config[config_file_ref_key]

                        # Process configurations for both planner_agent and nav_agent
                        planner_config = self._normalize_config(raw_config.get("planner_agent", {}))
                        navigation_nav_config = self._normalize_config(raw_config.get("nav_agent", {}))
                        config = {
                            "planner_agent": planner_config,
                            "nav_agent": navigation_nav_config,
                            "mem_agent": self._normalize_config(raw_config.get("mem_agent", {})),
                            "helper_agent": self._normalize_config(raw_config.get("helper_agent", {})),
                            "other_settings": {
                                k: v
                                for k, v in raw_config.items()
                                if k
                                not in [
                                    "planner_agent",
                                    "nav_agent",
                                    "mem_agent",
                                    "helper_agent",
                                ]
                            },
                        }
                        logger.info(f"Using configuration key '{config_file_ref_key}' from the config file.")
                    else:
                        logger.error(f"Key '{config_file_ref_key}' not found in the configuration file.")
                        raise KeyError(f"Key '{config_file_ref_key}' not found in the configuration file.")
                else:
                    logger.error("AGENTS_LLM_CONFIG_FILE_REF_KEY is not provided.")
                    raise ValueError("AGENTS_LLM_CONFIG_FILE_REF_KEY must be provided if AGENTS_LLM_CONFIG_FILE is set.")

            except Exception as e:
                logger.error(f"Error loading configuration file: {e}")
                raise e
        else:
            logger.info("Loading configuration from environment variables")
            # Load configurations from environment variables
            normalized_config = self._normalize_config_from_env()

            config = {
                "planner_agent": normalized_config,
                "nav_agent": normalized_config,
                "mem_agent": normalized_config,
                "helper_agent": normalized_config,
            }

        return config

    def load_config_from_api(self, llm_config: dict[str, Any]) -> dict[str, Any]:
        """
        Load configuration from a JSON provided during execution.

        Parameters
        ----------
        config_string : dict[str,Any]
            A JSON representing the configuration.

        Returns
        -------
        dict[str, Any]
            The loaded and normalized configuration.
        """
        try:

            logger.info("Loading LLM configuration provided via API.")

            # Process configurations for both planner_agent and nav_agent
            planner_config = self._normalize_config(llm_config.get("planner_agent", {}))
            navigation_nav_config = self._normalize_config(llm_config.get("nav_agent", {}))

            config = {
                "planner_agent": planner_config,
                "nav_agent": navigation_nav_config,
                "mem_agent": self._normalize_config(llm_config.get("mem_agent", {})),
                "helper_agent": self._normalize_config(llm_config.get("helper_agent", {})),
                "other_settings": {k: v for k, v in llm_config.items() if k not in ["planner_agent", "nav_agent", "mem_agent", "helper_agent"]},
            }

            return config

        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON string: {e}")
            raise e

    def _normalize_config(self, agent_config: dict[str, Any]) -> dict[str, Any]:
        """Normalize agent-specific config from a file, grouping keys into model_config_params, llm_config_params, and other_settings."""
        model_config = {}
        llm_config_params = {}
        other_settings = {}

        for k, v in agent_config.items():
            if k in self.KEY_MAPPING_FILE:
                model_config[self.KEY_MAPPING_FILE[k]] = v
            elif k == "llm_config_params":
                llm_config_params = v  # Keep llm_config_params as is
            else:
                other_settings[k] = v

        return {
            "model_config_params": model_config,
            "llm_config_params": llm_config_params,
            "other_settings": other_settings,
        }

    def _normalize_config_from_env(self) -> dict[str, Any]:
        """Normalize config from environment variables, adding defaults for 'temperature', 'top_p', and 'seed' based on model name."""
        model_config = {}
        llm_config_params = {}
        other_settings = {}

        # Populate model_config_params
        for original_key, mapped_key in self.KEY_MAPPING_ENV_MODEL.items():
            value = os.getenv(original_key)
            if value is not None:
                model_config[mapped_key] = value

        # Populate llm_config_params
        for original_key, mapped_key in self.KEY_MAPPING_ENV_LLM.items():
            value = os.getenv(original_key)
            if value is not None:
                llm_config_params[mapped_key] = value

        # Capture other settings that start with 'LLM_MODEL'
        for original_key in os.environ:
            if original_key.startswith("LLM_MODEL") and original_key not in self.KEY_MAPPING_ENV_MODEL:
                other_settings[original_key] = os.getenv(original_key)

        # Apply defaults for 'temperature', 'top_p', 'seed' if not present
        model_name: str = model_config.get("model", "").lower()  # type: ignore

        if model_name.startswith("o"):  #
            pass
        elif model_name.startswith("gpt"):  # type: ignore
            llm_config_params.setdefault("temperature", 0.0)  # type: ignore
            llm_config_params.setdefault("top_p", 0.001)  # type: ignore
            # llm_config_params.setdefault("seed", 12345)  # type: ignore
        else:
            llm_config_params.setdefault("temperature", 0.1)  # type: ignore
            llm_config_params.setdefault("top_p", 0.1)  # type: ignore

        return {
            "model_config_params": model_config,
            "llm_config_params": llm_config_params,
            "other_settings": other_settings,
        }

    def get_planner_agent_config(self) -> dict[str, Any]:
        return self.config["planner_agent"]

    def get_nav_agent_config(self) -> dict[str, Any]:
        return self.config["nav_agent"]

    def get_mem_agent_config(self) -> dict[str, Any]:
        return self.config["mem_agent"]

    def get_helper_agent_config(self) -> dict[str, Any]:
        return self.config["helper_agent"]

    def get_full_config(self) -> dict[str, Any]:
        return self.config


# Example usage
# if __name__ == "__main__":
#     config = AgentsLLMConfig()

#     planner_config = config.get_planner_agent_config()
#     navigation_nav_config = config.get_nav_agent_config()
