import os
from dataclasses import dataclass

from stringmethod.config import Config
from .. import mpi


@dataclass
class AbstractPostprocessor(object):
    config: Config

    def run(self):
        mpi.run_on_root_then_broadcast(lambda: self._do_run(), self.__class__.__name__)

    def _do_run(self) -> bool:
        pass

    def persist(self):
        if mpi.is_master():
            if not os.path.exists(self._get_out_dir()):
                os.makedirs(self._get_out_dir())
            self._do_persist()

    def _do_persist(self):
        pass

    def _get_out_dir(self) -> str:
        return "{}".format(self.config.postprocessing_dir)
