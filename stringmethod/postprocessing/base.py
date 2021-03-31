import os
from dataclasses import dataclass

from stringmethod.config import Config
from .. import mpi


@dataclass
class AbstractPostprocessor(object):
    postprocessing_dir: str

    def run(self):
        mpi.run_on_root_then_broadcast(
            lambda: self._do_run(), self.__class__.__name__
        )

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
        return "{}".format(self.postprocessing_dir)

    @classmethod
    def from_config(clazz, config: Config, **kwargs):
        """returns a new instance of the class"""
        return clazz(postprocessing_dir=config.postprocessing_dir, **kwargs)
