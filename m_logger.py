import logging
import pygogo as gogo

def get_logger(name):
    levels = ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
    log_frmt = (
       '%(asctime)-4s %(name) %(levelname)-8s %(message)s')

    formatter = logging.Formatter(log_frmt)
    going = gogo.Gogo(low_formatter=formatter, high_level='error', levels=levels)
    return going.get_logger(name)

