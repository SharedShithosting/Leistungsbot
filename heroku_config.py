################################################################################################
################################################################################################
# "THE BEER-WARE LICENSE" (Revision 42):
# @eckphi wrote this file. As long as you retain this notice you
# can do whatever you want with this stuff. If we meet some day, and you think
# this stuff is worth it, you can buy me a beer in return Poul-Henning Kamp
################################################################################################
################################################################################################
import os

class Var(object):
    APP_ID = int(os.environ.get("APP_ID", 13242285))
    # 6 is a placeholder
    API_HASH = os.environ.get("API_HASH", "60f71bfe3b2f6e386597050b61ae03d7")
