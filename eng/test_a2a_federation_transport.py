import copy,importlib.util,unittest
from pathlib import Path
SCRIPT=Path(__file__).with_name("validate_a2a_federation_transport.py")
spec=importlib.util.spec_from_file_location("v",SCRIPT); v=importlib.util.module_from_spec(spec); spec.loader.exec_module(v)
class Tests(unittest.TestCase):
    def setUp(self):
        self.m=v.load(v.MANIFEST); self.c=v.load(v.ROLE_CONTRACT)
    def bad(self,fn):
        m=copy.deepcopy(self.m); fn(m)
        with self.assertRaises(ValueError): v.validate(m,copy.deepcopy(self.c))
    def test_good(self):
        r=v.validate(copy.deepcopy(self.m),copy.deepcopy(self.c))
        self.assertEqual(r["services"],5); self.assertEqual(r["provider_execution"],"NOT_INVOKED")
    def test_commit_pin(self): self.bad(lambda m:m["services"][1].__setitem__("commit","0"*40))
    def test_unique_ports(self): self.bad(lambda m:m["services"][1].__setitem__("port",m["services"][0]["port"]))
    def test_maker_mcp(self): self.bad(lambda m:m["services"][2]["health"].__setitem__("mcp","CONNECTED"))
    def test_checker_mutation(self): self.bad(lambda m:m["services"][3]["health"].__setitem__("mutation","ALLOWED"))
    def test_reflector_dispatch(self): self.bad(lambda m:m["services"][4]["health"].__setitem__("next_cycle_dispatch",True))
if __name__=="__main__": unittest.main()
