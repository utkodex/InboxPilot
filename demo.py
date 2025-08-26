# from config.config_loader import load_config

# config=load_config()

# google_sheet_link = config["google_sheet"]["google_sheet_link"]
# credentials_json = config["google_sheet"]["credentials_json"]

# print(google_sheet_link)
# print(credentials_json)

# ---------------------------------------------------------------------------------------------

# below code is to check the logging config
# from logger import logging

# logging.debug("This is a debug message.")
# logging.info("This is an info message.")
# logging.warning("This is a warning message.")
# logging.error("This is an error message.")
# logging.critical("This is a critical message.")

# ---------------------------------------------------------------------------------------------

# below code is to check the exception config
from logger import logging
from exception import MyException
import sys

try:
    a = 1+'Z'
except Exception as e:
    logging.info(e)
    raise MyException(e, sys) from e