"""
What to do about "static" and "const"? The filter_typedecl.template currently
ignores them, except for the special-case "c_char_p".

"""

import copy
import ctypes
import logging as log
import shutil
import textwrap
from pathlib import Path

from yace.emitters import Emitter
from yace.errors import TransformationError
from yace.targets.target import Target
from yace.tools import Black, Isort, Python3
from yace.transformations import Camelizer, DependencyWalker, Modulizer


def wrap(text, indent="", width=72):
    return "\n".join(textwrap.wrap(text, width=width, subsequent_indent=indent))


def sizeof(ctypes_member: str):
    return ctypes.sizeof(getattr(ctypes, ctypes_member))


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

        def map_sym(sym: str):
            return model.sym_mapping[sym] if sym in model.sym_mapping else sym

        filters = {
            "wrap": wrap,
            "sizeof": sizeof,
            "map_sym": map_sym,
        }

        output = (self.output / model.meta.prefix).resolve()
        output.mkdir(parents=True, exist_ok=True)

        lib_path = (output / "lib").resolve()
        lib_path.mkdir(parents=True, exist_ok=True)
        
        # Copy the generic ctypes-sugar from resources
        sugar_path = (output / "ctypes_sugar.py").resolve()
        shutil.copyfile(Path(__file__).parent / sugar_path.name, sugar_path)
        self.sources.append(sugar_path)

        # Generate raw bindings in raw.py
        def emit_typespec(typespec):
            return typespec.python_c_spelling()
        
        def emit_sym(entity):
            return entity.typ.python_sym_spelling(model.sym_mapping.get(entity.sym, entity.sym))

        filters["emit_typespec"] = emit_typespec
        filters["emit_sym"] = emit_sym

        raw_path = (output / "raw.py").resolve()
        with raw_path.open("w") as file:
            file.write(
                self.emitter.render(
                    "file_api",
                    {
                        "meta": model.meta,
                        "entities": model.entities,
                        "headers": self.headers,
                        "isRaw": True,
                        "imports": {}
                    },
                    filters,
                )
            )
        self.sources.append(raw_path)

        def emit_typespec(typespec):
            return typespec.python_spelling(model.sym_mapping)

        filters["emit_typespec"] = emit_typespec


        # Generate the pythonic bindings / Python API
        for module, entities in self.modules.items():
            module_path = (lib_path / f"{module}.py").resolve()
            imports = self.module_imports[module]

            with module_path.open("w") as file:
                file.write(
                    self.emitter.render(
                        "file_api",
                        {
                            "meta": model.meta,
                            "entities": entities,
                            "headers": self.headers,
                            "isRaw": False,
                            "imports": imports,
                            "module": module
                        },
                        filters,
                    )
                )
            self.sources.append(module_path)
        

        # Generate helper files
        files = [
            ((output / "util.py").resolve(), "util", {}),
            (
                (output / f"{model.meta.prefix}_check.py").resolve(),
                "file_check",
                {"meta": model.meta},
            ),
            (
                (output / "__init__.py").resolve(),
                "init",
                {"meta": model.meta},
            ),
        ]

        for path, template, args in files:
            with path.open("w") as file:
                file.write(self.emitter.render(template, args, filters))
                self.sources.append(path)
        
        with (lib_path / "__init__.py").open("w") as file:
            file.write("")
            self.sources.append((lib_path / "__init__.py"))

    def format(self):
        """
        Run 'black' and 'isort' on self.sources
        """

        for tool in ["black", "isort"]:
            self.tools[tool].run([str(path) for path in self.sources])

    def check(self):
        """Build generated sources and run the generated test-program"""

        log.info("Not there yet...")
