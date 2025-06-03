"""
What to do about "static" and "const"? The filter_typedecl.template currently
ignores them, except for the special-case "c_char_p".

"""

import copy
import logging as log
import shutil
from pathlib import Path

from yace.emitters import Emitter
from yace.errors import TransformationError
from yace.targets.target import Target
from yace.tools import Black, Isort, Python3
from yace.transformations import Camelizer, DependencyWalker, Modulizer


class Ctypes(Target):
    """
    Several helper functions
    """

    NAME = "ctypes"
    PYTHON_KEYWORDS = [
        "and",
        "as",
        "assert",
        "async",
        "break",
        "class",
        "continue",
        "def",
        "del",
        "elif",
        "else",
        "except",
        "False",
        "finally",
        "for",
        "from",
        "global",
        "if",
        "import",
        "in",
        "is",
        "lambda",
        "None",
        "nonlocal",
        "not",
        "or",
        "pass",
        "raise",
        "return",
        "True",
        "try",
        "while",
        "with",
        "yield",
    ]

    def __init__(self, output):
        super().__init__(Ctypes.NAME, output)

        self.emitter = Emitter(Path(__file__).parent)

        self.tools = {
            "black": Black(self.output),
            "isort": Isort(self.output),
            "python": Python3(self.output),
        }

    def transform(self, model):
        """
        Transform the given model

        * Transform symbols according to :class:`yace.transformation.CStyle`

        That it currently the only thing done to the **yace** IR.
        """

        transformed = copy.deepcopy(model)

        walker = Modulizer(transformed)
        status = walker.walk()
        if not all([res for res in status]):
            raise TransformationError("The transformation to Python modules failed")
        self.modules = walker.modules
        self.module_imports = walker.module_imports

        walker = DependencyWalker(transformed)
        status = walker.walk()
        if not all([res for res in status]):
            raise TransformationError("The transformation to Python modules failed")
        walker.topological_sort()

        walker = Camelizer(transformed)
        walker.disallowed_syms = self.PYTHON_KEYWORDS
        status = walker.walk()
        if not all([res for res in status]):
            raise TransformationError("The CStyle transformation failed")

        return transformed

    def emit(self, model):
        """Emit code"""

        # Copy the generic ctypes-sugar from resources
        sugar_path = (self.output / "ctypes_sugar.py").resolve()
        shutil.copyfile(Path(__file__).parent / sugar_path.name, sugar_path)
        self.sources.append(sugar_path)

        # Generate the bindings / Python API
        files = [
            ((self.output / f"{model.meta.prefix}.py").resolve(), "file_api"),
            ((self.output / f"{model.meta.prefix}_check.py").resolve(), "file_check"),
        ]
        for path, template in files:
            with path.open("w") as file:
                file.write(
                    self.emitter.render(
                        template,
                        {
                            "meta": model.meta,
                            "entities": model.entities,
                            "headers": self.headers,
                        },
                        {},
                    )
                )
            self.sources.append(path)

    def format(self):
        """
        Run 'black' and 'isort' on self.sources
        """

        for tool in ["black", "isort"]:
            self.tools[tool].run([str(path) for path in self.sources])

    def check(self):
        """Build generated sources and run the generated test-program"""

        log.info("Not there yet...")
