import json
from pathlib import Path
import tempfile
import unittest
from kgc.io import digest
from kgc.research.structure_extensions import declare_frozen_extension,frozen_families


class ExtensionTests(unittest.TestCase):
    def fixture(self,path):
        protocol={"secondary_frozen_families":["general"],"conditions":["original","removed"],
            "source_graph_sha256":{"original":"original-hash","removed":"removed-hash"},"query_limit_facts":None}
        (path/"protocol.json").write_text(json.dumps(protocol))
        (path/"native-vocabulary.json").write_text('{"entities":["aa","bb"],"relations":["r"]}')
        source=path/"constants.rules";source.write_text("20\t10\t.5\tr(X,bb) <= s(X,aa)\n")
        return protocol,{"constants":{"path":str(source),"sha256":digest(source),"n_rules":1}}

    def test_extension_preserves_protocol_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);protocol,sources=self.fixture(p);before=(p/"protocol.json").read_bytes()
            self.assertEqual(frozen_families(p,protocol),["general"])
            record=declare_frozen_extension(p,["constants"],sources)
            self.assertEqual(declare_frozen_extension(p,["constants"],sources),record)
            self.assertEqual((p/"protocol.json").read_bytes(),before)
            self.assertEqual(frozen_families(p,protocol),["general","constants"])

    def test_extension_rejects_changed_protocol_vocabulary_or_catalog(self):
        for field in ("protocol","vocabulary","catalog"):
            with self.subTest(field=field),tempfile.TemporaryDirectory() as tmp:
                p=Path(tmp);protocol,sources=self.fixture(p)
                declare_frozen_extension(p,["constants"],sources)
                target={"protocol":p/"protocol.json","vocabulary":p/"native-vocabulary.json","catalog":p/"constants.rules"}[field]
                target.write_text(target.read_text()+"\n")
                with self.assertRaises(ValueError):frozen_families(p,protocol)

    def test_zero_or_all_family_cannot_be_silently_added(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);self.fixture(p)
            with self.assertRaises(ValueError):declare_frozen_extension(p,["zero"])
            with self.assertRaises(ValueError):declare_frozen_extension(p,["all"])
            self.assertFalse((p/"frozen-family-extension.json").exists())
