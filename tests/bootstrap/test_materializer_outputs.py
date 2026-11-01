"""Real bootstrap wrapper output checks; fixtures never edit the installation."""

from contextlib import contextmanager
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
MACHINE = Path("bootstrap/machine/x86_64-linux")
STAGE0 = Path("bootstrap/stage0/x86_64-linux")
B0 = Path("bootstrap/compiler/b0")
C0 = Path("bootstrap/compiler/c0")
BX = B0 / "x86_64-linux"
CX = C0 / "x86_64-linux"
# label, builder, source, pin, output seed, additional consumed inputs
SPECS = (
    ("machine", MACHINE / "materialize.sh", MACHINE / "hex0.hex",
     MACHINE / "hex0.sha256", MACHINE / "hex0.seed", ()),
    ("stage0", STAGE0 / "materialize.sh", STAGE0 / "stage0.hex",
     STAGE0 / "stage0.sha256", STAGE0 / "stage0.seed", (MACHINE / "hex0.seed",)),
    ("b0", BX / "materialize.sh", B0 / "compiler.nql0",
     BX / "b0.sha256", BX / "b0.seed", (STAGE0 / "stage0.seed",)),
    ("c0", CX / "materialize.sh", C0 / "compiler.nq",
     CX / "c0.sha256", CX / "c0.seed", (BX / "b0.seed",)),
    ("successor", CX / "materialize-successor.sh", C0 / "successor.nq",
     CX / "c0-successor.sha256", CX / "c0-successor.seed",
     (CX / "compile.sh", CX / "c0.seed", CX / "c0.sha256")),
    ("adapter", CX / "compile.sh", C0 / "successor.nq",
     CX / "c0.sha256", CX / "c0-successor.seed", (CX / "c0.seed",)),
)


class MaterializerFixture:
    @contextmanager
    def fixture(self, spec):
        with tempfile.TemporaryDirectory(prefix="bootstrap-output-") as directory:
            tree = Path(directory) / "installation with spaces"
            for relative in {spec[1], spec[2], spec[3], *spec[5]}:
                target = tree / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(ROOT / relative, target)
            yield tree

    def command(self, spec, tree, output=None):
        command = ["bash", str(tree / spec[1])]
        if spec[0] == "adapter":
            command.append(str(tree / spec[2]))
        if output is not None:
            command.append(str(output))
        return command

    def run_builder(self, spec, tree, output=None, env=None):
        return subprocess.run(self.command(spec, tree, output), cwd=tree,
                              env=env, capture_output=True, timeout=30)

    def snapshot(self, path):
        return path.read_bytes(), path.stat().st_mode & 0o7777

    def protected(self, spec, tree):
        return [tree / path for path in dict.fromkeys((spec[1], spec[2], spec[3], *spec[5]))]

    def assert_rejected(self, result, tree, message):
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(result.stdout, b"")
        self.assertIn(message, result.stderr)
        self.assertFalse([p for p in tree.rglob(".*") if ".tmp." in p.name],
                         "failed publication retained a candidate")


    def shim(self, tree, command, action, output, source, spec):
        commands = tree / "host commands"
        commands.mkdir()
        real = shutil.which(command)
        self.assertIsNotNone(real)
        prefixes = {"machine": ".hex0.seed.tmp.", "stage0": ".stage0.seed.tmp.",
                    "b0": ".b0.seed.tmp.", "c0": ".c0.seed.tmp.",
                    "successor": ".c0-successor.tmp.", "adapter": ".c0.tmp."}
        shim = commands / command
        shim.write_text(f"#!{sys.executable}\n"
                        "from pathlib import Path\nimport os,subprocess,sys\n"
                        f"output=Path({str(output)!r})\nsource=Path({str(source)!r})\n"
                        f"real={real!r}\n"
                        + ("if Path(sys.argv[-1]) != output:os.execv(real,[real,*sys.argv[1:]])\n"
                           if command == "mv" else
                           f"if not Path(sys.argv[-1]).name.startswith({prefixes[spec[0]]!r}):os.execv(real,[real,*sys.argv[1:]])\n")
                        + ("subprocess.run([real,*sys.argv[1:]],check=True)\n" if command == "chmod" else "")
                        + "output.unlink(missing_ok=True)\n"
                        + ("output.symlink_to(source)\n" if action == "link" else "output.mkdir()\n")
                        + ("os.execv(real,[real,*sys.argv[1:]])\n" if command == "mv" else ""))
        shim.chmod(0o755)
        return {**os.environ, "PATH": str(commands) + os.pathsep + os.environ["PATH"]}


class MaterializerOutputTests(MaterializerFixture, unittest.TestCase):
    def test_MO01_required_inputs_cannot_be_output(self):
        for spec in SPECS:
            for relative in dict.fromkeys((spec[1], spec[2], spec[3], *spec[5])):
                with self.subTest(component=spec[0], path=str(relative)), self.fixture(spec) as tree:
                    path = tree / relative
                    before = {p: self.snapshot(p) for p in self.protected(spec, tree)}
                    result = self.run_builder(spec, tree, path)
                    self.assert_rejected(result, tree, b"output would replace")
                    self.assertEqual({p: self.snapshot(p) for p in before}, before)

    def test_MO02_symbolic_and_parent_aliases_are_rejected(self):
        for spec in SPECS:
            for kind in ("symbolic", "parent"):
                with self.subTest(component=spec[0], kind=kind), self.fixture(spec) as tree:
                    source = tree / spec[2]
                    before = self.snapshot(source)
                    alias = tree / "alias"
                    if kind == "symbolic":
                        alias.symlink_to(source)
                    else:
                        alias.symlink_to(source.parent, target_is_directory=True)
                        alias = alias / source.name
                    self.assert_rejected(self.run_builder(spec, tree, alias), tree,
                                         b"output would replace")
                    self.assertEqual(self.snapshot(source), before)

    def test_MO03_default_and_independent_outputs_keep_pinned_bytes(self):
        for spec in SPECS:
            with self.subTest(component=spec[0]), self.fixture(spec) as tree:
                expected = (ROOT / spec[4]).read_bytes()
                before = {p: self.snapshot(p) for p in self.protected(spec, tree)}
                output = tree / spec[4]
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_bytes(b"old output")
                args = output if spec[0] == "adapter" else None
                default = self.run_builder(spec, tree, args)
                self.assertEqual(default.returncode, 0, default.stderr)
                self.assertEqual(output.read_bytes(), expected)
                self.assertEqual(output.stat().st_mode & 0o777, 0o755)
                independent = tree / "independent output"
                again = self.run_builder(spec, tree, independent)
                self.assertEqual(again.returncode, 0, again.stderr)
                self.assertEqual(independent.read_bytes(), expected)
                self.assertEqual(hashlib.sha256(expected).hexdigest(),
                                 (ROOT / spec[4]).with_suffix(".sha256").read_text().split()[0])
                self.assertEqual({p: self.snapshot(p) for p in before}, before)

    def test_MO04_destination_alias_is_rechecked_before_publication(self):
        for spec in SPECS:
            with self.subTest(component=spec[0]), self.fixture(spec) as tree:
                output, source = tree / "output", tree / spec[2]
                before = self.snapshot(source)
                env = self.shim(tree, "chmod", "link", output, source, spec)
                self.assert_rejected(self.run_builder(spec, tree, output, env), tree,
                                     b"output would replace")
                self.assertEqual(self.snapshot(source), before)
                self.assertTrue(output.is_symlink())

    def test_MO05_output_directories_and_late_directory_are_rejected(self):
        for spec in SPECS:
            for phase in ("initial", "chmod", "mv"):
                with self.subTest(component=spec[0], phase=phase), self.fixture(spec) as tree:
                    output = tree / "output"
                    if phase == "initial":
                        output.mkdir()
                        env = None
                    else:
                        env = self.shim(tree, phase, "directory", output, tree / spec[2], spec)
                    result = self.run_builder(spec, tree, output, env)
                    message = b"cannot install" if phase == "mv" else b"is a directory"
                    self.assert_rejected(result, tree, message)
                    self.assertTrue(output.is_dir())
                    self.assertEqual(list(output.iterdir()), [])

    def test_MO06_extra_arguments_are_rejected_before_output(self):
        for spec in SPECS:
            with self.subTest(component=spec[0]), self.fixture(spec) as tree:
                output = tree / "output"
                output.write_bytes(b"previous output")
                result = subprocess.run(self.command(spec, tree, output) + ["extra"],
                                        capture_output=True, timeout=30)
                self.assert_rejected(result, tree, b"usage:")
                self.assertEqual(output.read_bytes(), b"previous output")


class MaterializerHardlinkTests(MaterializerFixture, unittest.TestCase):
    # Linux qualification runs this with real hard links. Android denial is an
    # explicit unsupported gate, never a mocked alias or successful skip.
    def test_MO07_hardlink_aliases_are_rejected(self):
        for spec in SPECS:
            with self.subTest(component=spec[0]), self.fixture(spec) as tree:
                source, alias = tree / spec[2], tree / "hard alias"
                subprocess.run(["ln", "--", str(source), str(alias)], check=True,
                               capture_output=True, timeout=5)
                self.assertTrue(source.samefile(alias))
                before = self.snapshot(source)
                self.assert_rejected(self.run_builder(spec, tree, alias), tree,
                                     b"output would replace")
                self.assertEqual(self.snapshot(source), before)
                self.assertTrue(source.samefile(alias))


if __name__ == "__main__":
    unittest.main()
