Data organization
=================

Datasets
--------

.. py:currentmodule:: flexiznam.schema.datasets

Datasets constitute the most basic unit of organization in flexiznam. They
correspond to the ``dataset`` entities on Flexilims and can represent either a
single file or a collection of files. In the former case, the ``path`` attribute
of the Flexilims entry will point to the file itself. In the latter case,
``path`` will point at the parent directory.

.. note::
  Dataset ``path`` is defined relative to the root directory. See
  :ref:`below<Directory structure>` for more details.

Dataset entities have the following default attributes:

* **created**: timestamp when the dataset was generated.
* **is_raw**: ``'yes'`` or ``'no'``, depending on whether the dataset
  corresponds to raw or processed data.
* **path**: location of the data on CAMP.
* **dataset_type**: string describing the type of data represented by the dataset,
  e.g. ``'scanimage'``, ``'camera'``, or ``'ephys'``. Permitted dataset types are
  listed in config.

In addition, any custom attributes can be specified for individual datasets.

The :class:`Dataset` class provides a useful
abstraction for datasets, especially for creating entries for processed data.
See :ref:`the quick start guide<Adding processed datasets>` for more details.

You can define your own subclasses of :class:`Dataset` to handle import or
loading of different dataset types.
:class:`flexiznam.schema.microscopy_data.MicroscopyData` provides a fairly
minimal example.

Directory structure
-------------------
To protect the integrity of raw data and facilitate archiving, raw and processed
data are stored in different directory trees. The paths of the raw and processed
directories are specified in config and can be accessed through
``flexiznam.config.PARAMETERS['data_root']['raw']`` and
``flexiznam.config.PARAMETERS['data_root']['processed']``. Paths of Flexilims are
*relative to these directories*. The **is_raw** attribute of the dataset tells us
which directory tree the dataset is stored in. When using the :class:`Dataset` class,
the full path can be conveniently retrieved with
:py:attr:`Dataset.path_full` property.

Within raw and processed directories, subdirectories will typically correspond to
projects, which will in turn contain subdirectories corresponding to individual
mice.

In vivo recording and behavioral data
-------------------------------------

Behavioral and recording data is organized in **sessions**, which may be
composed of multiple **recordings**. Datasets can have either sessions or
recordings as the origin. For example, in a two-photon imaging session, all
recordings will be segmented together and the dataset containing the resulting
ROI will be assigned to the session. However, the ROI traces may be split and
assigned to individual recordings.

Sessions
^^^^^^^^
In case of in vivo recordings, a session corresponds to neurons recorded together
- if you change the imaging field of view or move the electrodes, you would
create a new session. The idea is that all the data within a given session can
be segmented / spike sorted together.

Sessions should always have a **mouse** as their **origin** and should be
stored under ``<DATA_ROOT>/<PROJECT>/<MOUSE>/<SYYYYMMDD>``. For example, a
session acquired for my_project on 4 July 2021 from mouse BRAC7777.1a would be
stored in ``<DATA_ROOT>/my_project/BRAC7777.1a/S20210704``. The name of the
session on flexilims will also follow this hierarchy. The example session would
be named ``BRAC7777.1a_S20210704_0``. The numerical index at the end is added
if multiple sessions are created on the same date - e.g. for imaging in two
different fields of view. Sessions have the following default attributes:

* **date**: YYYY-MM-DD string corresponding to the date of the recording.
* **path**: path to the session on CAMP, used primarily to decide where to store
  processed datasets. As with datasets, this is relative to ``data_root``.

Recordings
^^^^^^^^^^
During a session, you may carry out multiple **recordings**, which will be stored
as child entities of the session. A recording essentially corresponds to every
time you start acquisition on the microscope or the ephys rig. Recordings are
stored as subdirectories of the session, i.e.
``<DATA_ROOT>/<PROJECT>/<MOUSE>/<SYYYYMMDD>/RHHMMSS_PROTOCOL``, where ``HHMMSS``
is the time when the recording was started and ``PROTOCOL`` is a short string
identifying the experimental protocol. Recordings have the following attributes:

* **protocol**: short string describing the experimental protocol, e.g.
  ``retinotopy``, or ``visual_cliff``.
* **recording_type**: the modality of the recording, one of ``two_photon``,
  ``widefield``, ``intrinsic``, ``ephys``, ``behaviour``, or ``unspecified``.
* **path**: path to the recording on CAMP, used primarily to decide where to store
  processed datasets. As with datasets, this is relative to ``data_root``.


Ex vivo and other data
----------------------
Ex vivo data are organized through **sample** entities. Samples are generic
placeholders. They can correspond to, for example, the entire brain, a slide
with multiple tissue sections, a single tissue section, or an LCM cubelet.
Samples can have the **mouse** as their origin or they can  be nested, e.g.
sample ``slide_20`` can contain sample ``section_5``.

Raw data for samples can be stored directly as a subdirectory of the mouse
(e.g. ``<DATA_ROOT>/my_project/BRAC7777.1a/brain/``). In this case, the ``session:``
field should be left blank when :ref:`uploading the YAML file to Flexilims<Syncing data>`.
Alternatively, samples can also be stored in subdirectories corresponding to acquisition sessions,
e.g. ``<DATA_ROOT>/my_project/BRAC7777.1a/S20210704/brain/``, for example if you
would like to separate confocal data acquired on different days. In this case the
``session:`` field should be filled.
This only affects where :py:meth:`flexiznam.camp.sync_data.parse_yaml` searches
for datasets: on Flexilims the samples would still be direct children of the
**mouse** entity or of other samples.

.. note::
  If datasets for a given sample are acquired across multiple sessions, they would
  still have the same sample as their origin. Calling
  :py:meth:`flexiznam.main.get_children` for that sample would retrieve them all.

For nested samples, the directory structure should mirror their hierarchy (e.g.
``<DATA_ROOT>/my_project/BRAC7777.1a/brain/slide_20/section_5``). It is also
in how samples are named on flexilims - e.g. ``BRAC777.1a_brain_slide_20_section_5``.

Just like sessions and recordings, samples can have multiple datasets as children.
