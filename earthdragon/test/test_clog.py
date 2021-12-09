from earthdragon.clog import clogger


def test_clogger():
    logger = clogger()
    assert logger.name == 'earthdragon.test.test_clog'
