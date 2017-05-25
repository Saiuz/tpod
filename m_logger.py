import logging
import pygogo as gogo

def get_logger(logger_name):
    levels = ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
    going = gogo.Gogo('tpod',
                      low_formatter=gogo.formatters.fixed_formatter,
                      high_level='error', levels=levels)
    return going.get_logger(logger_name)

