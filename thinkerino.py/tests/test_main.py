from thinkerino.main import helloAPI, runTest

def test_hello():
    assert helloAPI('gigi') == 'Hello gigi', "How can we fail this?"


def test_other():
    res = runTest()
    print ("res:", res)