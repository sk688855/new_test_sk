import importlib
import pkgutil
import sys
from pathlib import Path

from testzeus_hercules.config import get_global_conf

# Get the current directory path
package_path = Path(__file__).parent

# Only load browser tools if we're not using Appium
if get_global_conf().get_device_manager() == "playwright":
    # Dynamically import all modules
    for _, module_name, _ in pkgutil.iter_modules([str(package_path)]):
        # Construct the full module path
        full_module_name = f"testzeus_hercules.core.tools.{module_name}"
        # Import the module
        module = importlib.import_module(full_module_name)
        # Add all objects from the module to the current namespace
        for attribute_name in dir(module):
            # Skip private attributes
            if not attribute_name.startswith("_"):
                globals()[attribute_name] = getattr(module, attribute_name)
