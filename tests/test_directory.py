from manual_trader.manual_scan import ManualScan
import os

def test_get_dirs():
    ms = ManualScan("data")
    symbols = ms.get_symbols()
    print(symbols)
    files = ms.read_objects(os.path.join("data", "manual", "EURUSD", "objects"), "EURUSD")
    print(files)

def test_run():
    ms = ManualScan('data')
    ms.run()
    assert ms.objects['EURUSD'] is not None
    assert ms.prices["EURUSD"] is not None
