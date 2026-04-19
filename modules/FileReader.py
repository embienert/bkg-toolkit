import os
import numpy as np
from typing import Any

import BKGToolkit.spc as spc
from BKGToolkit.DataSpecification import IOSpecification, DataIOSpecification
from BKGToolkit.ModuleManager import ModuleManager
from BKGToolkit.ProcessingModule import ProcessingModuleSpecification, ProcessingModule
from BKGToolkit.Settings import StringSetting, Settings
from BKGToolkit.Settings.types import FilesSetting, IntSetting, BoolSetting, SelectionSetting


def initialize(mm: type[ModuleManager]):
    mm.register(FileReader, "File Reader")


class DataIOError(Exception):
    pass


class FileReader(ProcessingModule):
    _TXT_EXTENSIONS = ["txt", "raman", "xy", "dat"]
    _SPC_EXTENSIONS = ["spc"]

    info = ProcessingModuleSpecification(
        name="FileReader",
        author="Martin Bienert",
        version="1.0",
        description=""
    )

    inputs = []
    outputs = [
        DataIOSpecification(name="x", dimensions=1),
        DataIOSpecification(name="ys", dimensions=2),
        IOSpecification[str](name="file name"),
        IOSpecification[str](name="file type"),
        IOSpecification[list[str]](name="header"),
        IOSpecification[str](name="x column name"),
        IOSpecification[list[str]](name="y column names"),
        IOSpecification[int](name="dataset count")
    ]

    settings = Settings(
        source=FilesSetting(name="source", default=[], allow_multiple=True),
        force_file_format=SelectionSetting(name="force file format", default="", options=["", "txt", "spc"]),
        sep=StringSetting(name="separator", default=""),
        head_rows=IntSetting(name="head row count", default=0),
        has_column_labels=BoolSetting(name="has column labels", default=True),
        has_x=BoolSetting(name="has x column", default=True),
    )

    @property
    def sep(self) -> str | None:
        if not self.settings.sep:
            return None
        return self.settings.sep

    def _process(self, *_, is_broadcast: bool = False) -> list[Any]:
        global_x: np.ndarray | None = None
        global_ys = []
        global_file_names = []
        global_file_types = []
        global_x_headers = []
        global_headers = []
        global_columns = []

        for idx, source in enumerate(self.settings.source):
            x, ys, headers, x_column, columns, ext = self._read_file(source)

            if global_x is not None:
                if len(global_x) != len(x):
                    raise DataIOError(f"Size mismatch between files 0-{idx-1} and {idx}")

                if not (global_x == x).all():
                    raise DataIOError(f"x of file {idx} did not match those of files 0-{idx-1}")

            global_x = x
            global_ys.extend(ys)
            global_file_names.append(os.path.abspath(source))
            global_file_types.append(ext)
            global_x_headers.append(x_column)
            global_headers.append(headers)
            global_columns.append(columns)

        out_ys = np.array(global_ys)

        return [
            global_x,
            out_ys,
            global_file_names,
            global_file_types,
            global_x_headers,
            global_headers,
            global_columns,
            len(out_ys)
        ]

    def _read_file(self, filename: str) -> tuple[np.ndarray, np.ndarray, list[str], str, list[str], str]:
        if self.settings.force_file_format:
            ext = self.settings.force_file_format
        else:
            _, ext = os.path.splitext(filename)
            if ext:
                ext = ext[1:]

        if ext in self._TXT_EXTENSIONS:
            x, ys, headers, x_label, labels = self._read_txt(filename)
        elif ext in self._SPC_EXTENSIONS:
            x, ys, x_label, labels = self._read_spc(filename)
            headers = []
        else:
            raise NotImplementedError(f"Import of file type '{ext}' is not supported")

        return x, ys, headers, x_label, labels, ext

    def _read_txt(self, filename: str) -> tuple[np.ndarray, np.ndarray, list[str], str, list[str]]:
        with open(filename) as in_stream:
            file_content = in_stream.read()

        lines_raw = file_content.split("\n")
        head_rows = lines_raw[:self.settings.head_rows]
        data_rows = [row for row in lines_raw[self.settings.head_rows:] if row.strip() != ""]

        column_labels = []
        if self.settings.has_column_labels:
            column_labels = data_rows[0].split(sep=self.sep)
            data_rows = data_rows[1:]

        columns = np.array([
            np.array([float(elem) for elem in row.split(sep=self.sep)])
            for row in data_rows
        ]).T

        if len(columns) == 0:
            raise DataIOError(f"File {filename} has no data")
        if len(columns) != len(column_labels):
            raise DataIOError(f"File {filename} has {len(column_labels)} columns labels, "
                              f"but only {len(columns)} columns")

        # Generate column labels if they don't exist yet
        if not column_labels:
            column_labels = [f"y{idx}" for idx in range(len(columns))]

            if self.settings.has_x:
                column_labels = ["x"] + column_labels[:-1]

        x_label = "x"
        if self.settings.has_x:
            x = columns[0]
            ys = columns[1:]

            x_label = column_labels[0]
            column_labels = column_labels[1:]
        else:
            # TODO: Leave x empty or generate range?
            x = np.arange(len(columns[0]))
            ys = columns

        return x, ys, head_rows, x_label, column_labels

    @staticmethod
    def _read_spc(filename: str) -> tuple[np.ndarray, np.ndarray, str, list[str]]:
        spc_file = spc.File(filename)

        if len(spc_file.sub) == 0:
            raise DataIOError(f"File {filename} has no data")

        if spc_file.dat_fmt.endswith("-xy"):
            x = spc_file.sub[0].x
        else:
            x = spc_file.x

        ys = np.array([subfile.y for subfile in spc_file.sub])
        labels = [str(round(subfile.subtime)) for subfile in spc_file.sub]
        x_label = spc_file.xlabel

        return x, ys, x_label, labels


if __name__ == '__main__':
    fr = FileReader(
        source=[
            r"C:\Users\mbienert\PycharmProjects\BackgroundCorrectionUI\2025-01-29_May_SN_000049_data_000002.dat",
            # r"C:\Users\mbienert\PycharmProjects\BackgroundCorrectionUI\test_data\AB29-156-A_50Hz_200mW_FLAon_60L_143402_010.spc",
            # r"C:\Users\mbienert\PycharmProjects\BackgroundCorrectionUI\test_data\AB29-156-A_50Hz_200mW_FLAon_60L_144902_100.spc"
        ],
        head_rows=23,
        has_column_labels=False,
        has_x=False,
    )

    res = fr.run()
    x, ys, file_names, file_types, headers, x_columns, columns, count = res

    print(res)
