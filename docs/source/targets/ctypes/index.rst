.. _sec-targets-ctypes:

ctypes
======

The :class:`.Ctypes` target emits a pure-Python API using the builtin
:ctypes:`Python/ctypes <>` module.

What is produced:

* :ref:`sec-targets-ctypes-sugar` for :ctypes:`Python/ctypes <>` (``ctypes_sugar.py``)

  * This is an expansion of the :ctypes:`Python/ctypes <>` module

* Utility (``util.py``)

  * Loading libraries using the :ctypes:`Python/ctypes <>` module
  * Architecture check, which ensures that the target architecture matches the
    architecture, the bindings were built on.

* Initialiser (``__init__.py``)

  * Necessary files for initialising the Python module.

* ``raw`` API containing the full :ctypes:`ctypes <>` API.

  * C typing is not abstracted away, and the user must cast Python objects 
    to :ctypes:`ctypes <>` objects themselves.

* Test (``{meta.prefix}_check.py``)

  * Imports and does basic library/loader verification of the C API Wrapper

Thus, the above files are what you should expect to see in the output-directory

System-Tools
------------

The target uses the following system-tools to format the emitted code and
verify it:

* :class:`yace.tools.Black`
* :class:`yace.tools.Isort`
* :class:`yace.tools.Python3`

.. _sec-targets-ctypes-implementation:

Implementation
--------------

.. automodule:: yace.targets.ctypes.target
   :inherited-members:
   :members:
   :undoc-members:

.. _sec-targets-ctypes-sugar:

sugar
~~~~~

.. automodule:: yace.targets.ctypes.ctypes_sugar
   :inherited-members:
   :members:
   :undoc-members:
