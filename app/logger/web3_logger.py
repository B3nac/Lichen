import logging

logging.basicConfig(filename = 'filename.log', level=logging.DEBUG, format = f'%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s')