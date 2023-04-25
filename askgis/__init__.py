import os

import langchain
from langchain.cache import SQLiteCache
from qgis.gui import QgisInterface

from askgis.qgis_plugin_tools.infrastructure.debugging import setup_debugpy  # noqa F401
from askgis.qgis_plugin_tools.infrastructure.debugging import setup_ptvsd  # noqa F401
from askgis.qgis_plugin_tools.infrastructure.debugging import setup_pydevd  # noqa F401
from askgis.qgis_plugin_tools.tools.custom_logging import setup_logger
from askgis.qgis_plugin_tools.tools.resources import plugin_name, profile_path

debugger = os.environ.get("QGIS_PLUGIN_USE_DEBUGGER", "").lower()
if debugger in {"debugpy", "ptvsd", "pydevd"}:
    locals()["setup_" + debugger]()


langchain.llm_cache = SQLiteCache(profile_path("langchain-cache.db"))


def classFactory(iface: QgisInterface):  # noqa N802
    from askgis.plugin import Plugin

    return Plugin(iface)


LOGGER = setup_logger(plugin_name())
