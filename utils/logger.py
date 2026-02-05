import logging

## Gerador de Logs
logging.basicConfig(filename="./history.log", level= logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def logI(information: str) -> None:
    print('[Info] ',information)
    logger.info(information)

def logW(information: str) -> None:
    print('[Warning] ',information)
    logger.warning(information)

def logE(information: str) -> None:
    print('[Error] ',information)
    logger.error(information)
#/Geador de Logs
