# !/usr/bin/env python
# -*- coding:utf-8 -*-

from flask import Blueprint

"""
from .ns_datanalysis import datetime_str, get_cur_filename, get_cur_lineno, get_cur_func,\
    read_txt_file, read_csv_file, read_xls_file, read_xlsx_file, read_file_to_df, read_table_to_df,\
    write_df_to_table, write_df_to_file, write_file_to_table, write_table_to_file,\
    rar_extractall, zip_extractall, tar_extractall, extract_compressed_file, tar_compress,\
    dict_from_file, dict_to_file, df_from_dict, df_to_dict, df_from_matrix,\
    df_select, df_set_cols, df_add_col, df_col_parse, df_col_to_set, df_isna, df_replace,\
    df_range, df_filter, df_sort, df_merge, df_concat, df_col_concat, df_map, df_col_map,\
    df_type_convert, df_clean, \
    db_change, db_get_tables, db_is_table_exists, db_drop_table, db_drop_table_rex, db_execute_sql,\
    recursive_path_process
from .ns_graph import NsGraph
"""

api = Blueprint(name='api', import_name=__name__)

try:
    from . import ns_datanalysis, ns_graph, authentication, errors, interfaces
except Exception:
    raise

"""
__all__ = ['datetime_str', 'get_cur_filename', 'get_cur_lineno', 'get_cur_func',
           'read_txt_file', 'read_csv_file', 'read_xls_file', 'read_xlsx_file', 'read_file_to_df', 'read_table_to_df',
           'write_df_to_table', 'write_df_to_file', 'write_file_to_table', 'write_table_to_file',
           'rar_extractall', 'zip_extractall', 'tar_extractall', 'extract_compressed_file', 'tar_compress',
           'dict_from_file', 'dict_to_file', 'df_from_dict', 'df_to_dict', 'df_from_matrix',
           'df_select', 'df_set_cols', 'df_add_col', 'df_col_parse', 'df_col_to_set', 'df_isna', 'df_replace',
           'df_range', 'df_filter',  'df_sort', 'df_merge', 'df_concat', 'df_col_concat', 'df_map', 'df_col_map',
           'df_type_convert', 'df_clean',
           'db_change', 'db_get_tables', 'db_is_table_exists', 'db_drop_table', 'db_drop_table_rex', 'db_execute_sql',
           'recursive_path_process',
           'NsGraph']
"""
