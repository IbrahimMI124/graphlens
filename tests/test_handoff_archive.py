"""Tiny stdlib archive/lock tests; never build the real research handoff."""
import hashlib
from pathlib import Path
import tarfile
import tempfile
import unittest
from unittest.mock import patch

from scripts.build_phase5_handoff import archive_files,file_digest,relative_name,resolved_requirements,require_pristine_cohort,RUN_ROOT


class HandoffArchiveTests(unittest.TestCase):
    def test_sorted_regular_members_preserve_bytes_and_sidecar_hash(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/"nested").mkdir()
            payloads={"nested/z.txt":b"line one\r\nline two\n", "a.bin":b"\0\xff\x10example"}
            for name,data in payloads.items():(root/name).write_bytes(data)
            hashes={name:file_digest(root,name) for name in payloads}
            result=archive_files(root,hashes,"output/handoff.tar")
            archive=root/"output/handoff.tar"
            with tarfile.open(archive,"r:") as bundled:
                self.assertEqual(bundled.getnames(),sorted(payloads))
                for member in bundled.getmembers():
                    self.assertTrue(member.isfile());self.assertFalse(member.issym() or member.islnk())
                    self.assertEqual(bundled.extractfile(member).read(),payloads[member.name])
            digest=hashlib.sha256(archive.read_bytes()).hexdigest()
            self.assertEqual(result["sha256"],digest)
            self.assertEqual(result["file_count"],2)
            self.assertEqual((root/"output/handoff.tar.sha256").read_text(),f"{digest}  handoff.tar\n")
            self.assertFalse(list((root/"output").glob("*.tmp-*")))

    def test_absolute_traversal_and_unnormalized_members_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            for name in ("../secret","nested/../../secret","/etc/passwd","a\\..\\secret","a//b","a/./b",""):
                with self.subTest(name=name):
                    with self.assertRaises(ValueError):archive_files(tmp,{name:"0"*64},"handoff.tar")
            self.assertFalse((Path(tmp)/"handoff.tar").exists())
            with self.assertRaisesRegex(ValueError,"inside the project"):
                archive_files(tmp,{"x":"0"*64},Path(tmp).parent/"outside.tar")

    def test_symlink_files_and_symlink_parents_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);project=root/"project";project.mkdir();outside=root/"outside";outside.mkdir()
            (outside/"private.txt").write_text("do not include")
            (project/"inside.txt").write_text("public")
            (project/"file-link.txt").symlink_to(outside/"private.txt")
            (project/"inside-link.txt").symlink_to(project/"inside.txt")
            (project/"directory-link").symlink_to(outside,target_is_directory=True)
            for name in ("file-link.txt","inside-link.txt","directory-link/private.txt"):
                with self.subTest(name=name):
                    with self.assertRaisesRegex(ValueError,"Symlinks"):
                        archive_files(project,{name:"0"*64},"handoff.tar")
            self.assertFalse((project/"handoff.tar").exists())

    def test_changed_source_before_archive_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);source=root/"a.txt";source.write_text("before")
            hashes={"a.txt":file_digest(root,"a.txt")};source.write_text("after")
            with self.assertRaisesRegex(ValueError,"changed before"):
                archive_files(root,hashes,"handoff.tar")
            self.assertFalse((root/"handoff.tar").exists())

    def test_source_change_during_archive_does_not_replace_existing_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);source=root/"a.txt";source.write_text("before")
            output=root/"handoff.tar";output.write_bytes(b"previous verified handoff")
            hashes={"a.txt":file_digest(root,"a.txt")}
            actual_addfile=tarfile.TarFile.addfile
            def change_after_copy(archive,member,fileobj=None):
                actual_addfile(archive,member,fileobj)
                source.write_text("after")
            with patch.object(tarfile.TarFile,"addfile",change_after_copy):
                with self.assertRaisesRegex(ValueError,"changed during"):
                    archive_files(root,hashes,"handoff.tar")
            self.assertEqual(output.read_bytes(),b"previous verified handoff")
            self.assertFalse((root/"handoff.tar.sha256").exists())
            self.assertFalse(list(root.glob("*.tmp-*")))

    def test_exact_public_lock_excludes_editable_and_local_paths(self):
        commit="a"*40
        text="\n".join(("# developer editable path","-e /home/user/project","--editable=/private/project",
            "-e\t/private/tab-project","/private/archive.whl","C:\\private\\archive.whl",
            "local-package @ file:///private/pkg","another @ FILE:///private/other",
            "numpy==2.4.6","torch==2.15.0+cpu",
            f"PyClause @ git+https://github.com/symbolic-kg/PyClause.git@{commit}"))
        requirements,versions=resolved_requirements(text,commit)
        self.assertEqual(versions,{"numpy":"2.4.6","torch":"2.15.0+cpu"})
        self.assertEqual(len(requirements.splitlines()),3)
        self.assertIn(f"PyClause @ git+https://github.com/symbolic-kg/PyClause.git@{commit}",requirements)
        self.assertNotIn("private",requirements);self.assertNotIn("/home",requirements)
        for bad in ("numpy>=2",f"PyClause @ git+https://github.com/symbolic-kg/PyClause.git@{'b'*40}"):
            with self.subTest(requirement=bad):
                with self.assertRaises(ValueError):resolved_requirements(bad,commit)

    def test_attempted_training_in_prepared_cohort_blocks_handoff(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);cohort=root/RUN_ROOT;cohort.mkdir(parents=True)
            (cohort/"protocol.json").write_text("{}")
            require_pristine_cohort(root)
            cell=cohort/"original/neural-0/embedding";cell.mkdir(parents=True)
            (cell/"epoch-1.pt").write_bytes(b"not transferred")
            with self.assertRaisesRegex(ValueError,"attempted/trained"):
                require_pristine_cohort(root)


if __name__=="__main__":unittest.main()
