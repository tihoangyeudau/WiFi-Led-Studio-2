--------------------------
   Document Development
--------------------------

The documentation is written in reStructuredText. Once you are finished
making changes, you must build the documentation. To build the Wls
documentation follow the steps outlined below:

.. note:: Alternatively, you may run ``make livehtml`` in place of ``make html`` to open a browser and view your changes in
          realtime.


Linux
-------

.. code:: console

    $ cd ~/wls/docs
    $ pip install -r requirements-docs.txt
    $ make html

macOS
-------

.. code:: console

    $ source ~/wls-venv/bin/activate
    $ cd ~/wls/docs
    $ pip install -r requirements-docs.txt
    $ make html


.. Extensions used by sphinx

.. _sphinx.ext.autodoc: https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html
.. _sphinx.ext.githubpages: https://www.sphinx-doc.org/en/master/usage/extensions/githubpages.html
.. _sphinxcontrib.httpdomain: https://sphinxcontrib-httpdomain.readthedocs.io/en/stable/
.. _sphinx_rtd_theme: https://sphinx-rtd-theme.readthedocs.io/en/latest/index.html