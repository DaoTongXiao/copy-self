# -*- coding: utf-8 -*-
import logging
import sys

# Create a logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)

logger = logging.getLogger("ReActAgent")
