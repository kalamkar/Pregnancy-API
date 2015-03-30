'''
Created on Mar 27, 2015

@author: abhi
'''

import logging

def write_error(response, code, message):
    response.headers['Content-Type'] = 'text/plain'
    response.status_int = code
    response.out.write(message)
    logging.warn("Error %d: %s" % (code, message))
