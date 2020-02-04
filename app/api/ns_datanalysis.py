#!/usr/bin/env python
# -*- coding: utf-8 -*-

import io
import re
import os
import bs4
import sys
import time
import json
import tarfile
import rarfile
import inspect
import platform
import datetime
import sshtunnel
import sqlalchemy
import collections
import numpy as np
import pandas as pd
from sqlalchemy import exc

from config import Config

if sys.version_info >= (3, 6):
    import zipfile
else:
    import zipfile36 as zipfile


def _decorator_func_time(func):
    def wrapper(*args, **kwargs):
        start = time.time()
        res = func(*args, **kwargs)
        endtime = time.time()
        msecs = endtime - start
        Config.LOGGER.warning('running time of {0} is {1} s'.format(str(func).split(' ')[1], msecs))
        return res
    return wrapper


def datetime_str():
    dt = datetime.datetime.now()
    return dt.strftime('%Y-%m-%d %H:%M:%S')


def get_cur_filename():
    s = inspect.stack()
    return s[1][1]


def get_cur_lineno():
    s = inspect.stack()
    return s[1][2]


def get_cur_func():
    s = inspect.stack()
    return s[1][3]


def __get_txt_file_dtype(file_name, seperator=',', encoding='utf-8', dtype='object'):
    file_name = __string_coding(file_name)
    try:
        with io.open(file_name, 'r', encoding=encoding) as f:
            content = f.read()
            phony_data = io.BytesIO(content.encode('utf-8'))
            cols = pd.read_csv(phony_data, sep=seperator, header=None,
                               encoding='utf-8', nrows=1, engine='python').values.tolist()[0]
            new_dtype = dict(zip(cols, [dtype for _ in cols]))
            return new_dtype
    except Exception as e:
        Config.LOGGER.error('__get_txt_file_dtype errr: {}'.format(str(e)))
        return None


def read_txt_file(file_name, seperator=',', header=0, parse_dates=None, date_parser=pd.to_datetime,
                  encoding='utf-8', chunksize=None, dtype=None):
    file_name = __string_coding(file_name)
    Config.LOGGER.warning('Reading txt file: {}'.format(file_name))
    if dtype:
        dtype = __get_txt_file_dtype(file_name, seperator, encoding=encoding, dtype='object')
    try:
        with io.open(file_name, 'r', encoding=encoding) as f:
            content = f.read()
            content = content.replace('\\N', '')
            phony_data = io.BytesIO(content.encode('utf-8'))
            df = pd.read_csv(phony_data, sep=seperator, header=header, parse_dates=parse_dates, date_parser=date_parser,
                             encoding='utf-8', chunksize=chunksize, dtype=dtype, engine='python')
            return df
    except Exception as e:
        Config.LOGGER.error('read_txt_file errr: {}'.format(str(e)))
        return None


def __read_txt_file_wrapper(file_name, args):
    arg_values = [',', 0, None, pd.to_datetime, 'utf-8', None, None]
    for i, v in enumerate(args):
        arg_values[i] = v
    return read_txt_file(file_name, arg_values[0], arg_values[1], arg_values[2], arg_values[3], arg_values[4],
                         arg_values[5], arg_values[6])


def read_csv_file(file_name, seperator=',', header='infer', names=None, parse_dates=None, date_parser=pd.to_datetime,
                  encoding='utf-8', index_col=0):
    file_name = __string_coding(file_name)
    Config.LOGGER.warning('Reading csv file: {}'.format(file_name))
    try:
        df = pd.read_csv(file_name, sep=seperator, header=header, names=names, parse_dates=parse_dates,
                         date_parser=date_parser, encoding=encoding, engine='python')
        df.replace('\\N', np.nan, inplace=True)
        if 0 < index_col <= df.shape[1]:
            df.set_index(df.columns.values.tolist()[index_col-1], inplace=True)
        return df
    except Exception as e:
        Config.LOGGER.error('read_csv_file error: ' + str(e))
        return None


def __read_csv_file_wrapper(file_name, args):
    arg_values = [',', 'infer', None, None, pd.to_datetime, 'utf-8', 0]
    for i, v in enumerate(args):
        arg_values[i] = v
    return read_csv_file(file_name, arg_values[0], arg_values[1], arg_values[2], arg_values[3],
                         arg_values[4], arg_values[5], arg_values[6])


def read_xls_file(file_name, header=0, encoding='utf-8'):
    file_name = __string_coding(file_name)
    Config.LOGGER.warning('Reading xls file: {}'.format(file_name))
    try:
        with io.open(file_name, 'r', encoding=encoding) as f:
            cur_platform = platform.system()
            if cur_platform == 'Windows':
                soup = bs4.BeautifulSoup(f.read(), 'lxml')
                for span_tag in soup.find_all('span'):
                    span_tag.unwrap()
                df = pd.read_html(str(soup), header=header)
            elif cur_platform == 'Linux':
                df = pd.read_html(f.read(), header=header)
            else:
                Config.LOGGER.error('read_xls_file error: unkown platform [{}]'.format(cur_platform))
                return None
    except Exception as e:
        Config.LOGGER.error('read_xls_file error: ' + str(e))
        return None
    return df[0]


def __read_xls_file_wrapper(file_name, args):
    arg_values = [0, 'utf-8']
    for i, v in enumerate(args):
        arg_values[i] = v
    return read_xls_file(file_name, arg_values[0], arg_values[1])


def read_xlsx_file(file_name, header=0, sheet_name=0, index_col=None, dtype=None):
    file_name = __string_coding(file_name)
    Config.LOGGER.warning('Reading xlsx file: {}'.format(file_name))
    try:
        df = pd.read_excel(file_name, header=header, index_col=index_col, sheet_name=sheet_name, dtype=dtype)
    except Exception as e:
        Config.LOGGER.error('read_xlsx_file error: ' + str(e))
        return None

    df.rename(columns=lambda x: x if x.strip() != '' else 'index')
    new_cols = [x.strip('\t ') for x in df.columns.values.tolist()]
    df = df_set_cols(df, new_cols)
    return df


def __read_xlsx_file_wrapper(file_name, args):
    arg_values = [0, 0, None, None]
    for i, v in enumerate(args):
        arg_values[i] = v
    return read_xlsx_file(file_name, arg_values[0], arg_values[1], arg_values[2], arg_values[3])


def read_file_to_df(file_path, *args):
    file_op = {'.txt': __read_txt_file_wrapper, '.csv': __read_csv_file_wrapper,
               '.xls': __read_xls_file_wrapper, '.xlsx': __read_xlsx_file_wrapper}
    file_ext = os.path.splitext(os.path.basename(file_path))[1]
    if file_ext not in file_op.keys():
        Config.LOGGER.error('read_file_to_df error: file extension is not supported')
        return None
    df = file_op[file_ext](file_name=file_path, args=args)
    return df


def read_table_to_df(tb_name):
    if not db_is_table_exists(tb_name):
        Config.LOGGER.error('read_table_to_df error: [{}] does not exist!'.format(tb_name))
        return None
    with __ssh_tunnel_db() as server:
        conn_str = __ssh_tunnel_conn_str(server)
        return __db_read(conn_str, tb_name)


def write_df_to_table(df, tb_name):
    with __ssh_tunnel_db() as server:
        conn_str = __ssh_tunnel_conn_str(server)
        __db_write(conn_str, tb_name, df)


def write_df_to_file(df, file_path, index=False, header=True, encoding='utf-8'):
    try:
        df.to_csv(file_path, index=index, header=header, encoding=encoding)
    except Exception as e:
        Config.LOGGER.error('write_df_to_file error: {}'.format(str(e)))


def write_file_to_table(file_path, *args):
    tb_name = args[0]
    df = read_file_to_df(file_path, *(args[1:]))
    if isinstance(df, pd.DataFrame):
        write_df_to_table(df, tb_name)


def write_table_to_file(tb_name, file_path):
    df = read_table_to_df(tb_name)
    if isinstance(df, pd.DataFrame):
        write_df_to_file(df, file_path)


def rar_extractall(file, target_path=None, del_flag=True):
    file = __string_coding(file)
    target_path = __string_coding(target_path) if target_path else os.path.abspath(os.path.dirname(file))

    try:
        with rarfile.RarFile(file) as rar_file:
            rar_file.extractall(target_path)
        if del_flag:
            os.remove(file)
    except Exception as e:
        Config.LOGGER.error('rar_extractall error: {}'.format(str(e)))


def __rar_extractall_wrapper(file, args):
    arg_values = [None, True]
    for i, v in enumerate(args):
        arg_values[i] = v
    return rar_extractall(file, arg_values[0], arg_values[1])


def __rm_file(file_path):
    if os.path.isdir(file_path):
        files = os.listdir(file_path)
        for f in files:
            __rm_file(f)
    else:
        os.remove(file_path)


def zip_extractall(file, target_path=None, del_flag=True):
    file = __string_coding(file)
    target_path = __string_coding(target_path) if target_path else os.path.abspath(os.path.dirname(file))

    try:
        with zipfile.ZipFile(file, 'r') as zip_file:
            zip_file.extractall(target_path)
        if del_flag:
            __rm_file(file)
    except Exception as e:
        Config.LOGGER.error('zip_extractall error: {}'.format(str(e)))


def __zip_extractall_wrapper(file, args):
    arg_values = [None, True]
    for i, v in enumerate(args):
        arg_values[i] = v
    return zip_extractall(file, arg_values[0], arg_values[1])


def tar_extractall(file, target_path=None, compress_flag='', del_flag=True):
    open_flag = 'r:' + compress_flag
    file = __string_coding(file)
    target_path = __string_coding(target_path) if target_path else os.path.abspath(os.path.dirname(file))

    try:
        with tarfile.open(file, open_flag) as tar_file:
            tar_file.extractall(path=target_path)
        if del_flag:
            __rm_file(file)
    except Exception as e:
        Config.LOGGER.error('tar_extractall error: ' + str(e))


def __tar_extractall_wrapper(file, args):
    arg_values = [None, '', True]
    for i, v in enumerate(args):
        arg_values[i] = v
    return tar_extractall(file, arg_values[0], arg_values[1], arg_values[2])


def __targz_extractall_wrapper(file, args):
    arg_values = [None, 'gz', True]
    for i, v in enumerate(args):
        arg_values[i] = v
    return tar_extractall(file, arg_values[0], arg_values[1], arg_values[2])


def extract_compressed_file(file, *args):
    file_op = {'.zip': __zip_extractall_wrapper, '.rar': __rar_extractall_wrapper,
               '.tar': __tar_extractall_wrapper, '.gz': __targz_extractall_wrapper}
    file_ext = os.path.splitext(os.path.basename(file))[1]
    if file_ext not in file_op.keys():
        return
    file_op[file_ext](file, args=args)


def tar_compress(file_path, target_file=None, compress_flag='', del_flag=False):
    open_flag = 'w:' + compress_flag
    file_path = __string_coding(file_path)
    origin_name = file_path if os.path.isdir(file_path) else os.path.splitext(file_path)[0]
    target_name = (origin_name + '.tar.' + compress_flag) if len(compress_flag) else (origin_name + '.tar')
    target_file = __string_coding(target_file) if target_file else target_name

    try:
        with tarfile.open(target_file, open_flag) as tar_file:
            tar_file.add(file_path)
        if del_flag:
            __rm_file(file_path)
    except Exception as e:
        Config.LOGGER.error('tar_compress error: {}'.format(str(e)))


def dict_from_file(file):
    def __struct_list_to_set(dict_of_set):
        if not isinstance(dict_of_set, dict):
            return dict_of_set
        for k, v in dict_of_set.items():
            if isinstance(v, list):
                dict_of_set[k] = set(v)
        return dict_of_set

    try:
        with io.open(file, 'r', encoding='utf-8') as f:
            d = json.loads(f.read(), object_pairs_hook=collections.OrderedDict)
        return __struct_list_to_set(d)
    except Exception as e:
        Config.LOGGER.error('dict_from_file error: {}'.format(str(e)))
        return None


class __SetEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, set):
            return list(obj)
        return json.JSONEncoder.default(self, obj)


def dict_to_file(d, file, cls=__SetEncoder):
    try:
        with io.open(file, 'w', encoding='utf-8') as f:
            f.write(json.dumps(d, indent=True, cls=cls))
    except Exception as e:
        Config.LOGGER.error('dict_to_file error: {}'.format(str(e)))


def df_from_dict(dict_of_dict, orient='index'):
    return pd.DataFrame.from_dict(dict_of_dict, orient=orient).reset_index(drop=False)


def df_to_dict(df, col, orient='index'):
    return df.set_index(col).to_dict(orient=orient)


def df_from_matrix(list_of_list, cols):
    df = pd.DataFrame(list_of_list, columns=cols)
    return df


def df_select(df, col_list):
    df_ret = df[col_list]
    return df_ret.infer_objects()


def df_set_cols(df, new_cols):
    old_cols = df.columns.values.tolist()
    df.rename(columns=dict(zip(old_cols, new_cols)), inplace=True)
    return df


def df_add_col(df, new_col, default_value=None):
    df[new_col] = default_value
    return df


def df_col_parse(df, col, parse_func):
    result = []
    for i in range(len(df)):
        result.append(parse_func(df.at[i, col]))
    return result


def df_col_to_set(df, col):
    return set(df[col])


def df_isna(df, x, y):
    return pd.isna(df.at[x, y])


def df_replace(to_replace=None, value=None, inplace=False, regex=False):
    return pd.DataFrame.replace(to_replace=to_replace, value=value, inplace=inplace, regex=regex)


def df_range(df, by, low=None, high=None):
    if low and high:
        return df[(df[by] >= low) & (df[by] <= high)]
    elif low:
        return df[df[by] >= low]
    elif high:
        return df[df[by] <= high]
    else:
        return df


def df_filter(df, col, val_list, filter_out=False):
    if val_list:
        df_ret = df.loc[~df[col].isin(val_list)] if filter_out else df.loc[df[col].isin(val_list)]
    else:
        df_ret = df.loc[df[col].isnull()] if filter_out else df.loc[df[col].notnull()]
    return df_ret.reset_index(drop=True)


def df_sort(df, by, ascending=True, inplace=False):
    return df.sort_values(by=by, ascending=ascending, inplace=inplace).reset_index(drop=True)


def df_merge(df1, df2, on=None, left_on=None, right_on=None, how='inner', sort='False',
             copy=False, suffixes=('_x', '_y')):
    return pd.merge(df1, df2, on=on, left_on=left_on, right_on=right_on, how=how,
                    sort=sort, copy=copy, suffixes=suffixes).reset_index(drop=True)


def df_concat(*args):
    df_list = list(args)
    return pd.concat(df_list, axis=0, sort=False, copy=False, ignore_index=True)


def df_col_concat(*args):
    df_list = list(args)
    return pd.concat(df_list, axis=1, sort=False, copy=False, ignore_index=False)


def df_map(df, map_func):
    return df.applymap(map_func)


def df_col_map(df, col, map_func):
    df[col] = df.apply(map_func, axis=1)
    return df


def df_type_convert(df, target_cols, target_type='str'):
    if target_type == 'datetime':
        df[target_cols] = df[target_cols].apply(pd.to_datetime, errors='coerce')
    elif target_type == 'number':
        df[target_cols] = df[target_cols].apply(pd.to_numeric, errors='coerce')
    else:
        for col in target_cols:
            df[col] = df[col].astype(dtype=target_type, errors='ignore')
    return df


def df_clean(df):
    df_ret = df.dropna(axis=0, how='all')
    df_ret = df_ret.dropna(axis=1, how='all')
    df_ret.drop_duplicates(inplace=True)
    return df_ret.reset_index(drop=True)


def db_change(new_db):
    sql_str = 'USE {}'.format(new_db)
    db_execute_sql(sql_str)
    Config.MYSQL_DB = new_db


def db_get_tables():
    table_list = []
    sql_str = 'SHOW TABLES'

    result = db_execute_sql(sql_str)
    if result:
        for i in range(len(result)):
            table_list.append(result[i][0])
    return table_list


def db_is_table_exists(table_name):
    table_list = db_get_tables()
    if table_name in table_list:
        return True
    else:
        return False


def db_drop_table(table_name):
    table_list = db_get_tables()
    if table_name in table_list:
        sql_str = 'DROP TABLE {}'.format(table_name)
        db_execute_sql(sql_str)


def db_drop_table_rex(rex_str):
    tb_name_rex = re.compile(rex_str)
    table_list = db_get_tables()
    for tb in table_list:
        tb_name_match = tb_name_rex.search(tb)
        if tb_name_match:
            sql_str = 'DROP TABLE {}'.format(tb)
            db_execute_sql(sql_str)


def db_execute_sql(sql_str):
    with __ssh_tunnel_db() as server:
        conn_str = __ssh_tunnel_conn_str(server)
        return __db_execulte_sql(conn_str, sql_str)


def recursive_path_process(dir_name, ext_list, operation, exclude_flag=False, *args):
    r = []
    if not os.path.exists(dir_name):
        Config.LOGGER.error('recursive_path_process error: {} does not exist'.format(dir_name))
        return
    files = os.listdir(dir_name)
    for f in files:
        f = __string_coding(f)
        cur_file = os.path.join(dir_name, f)
        if os.path.isdir(cur_file):
            r.extend(recursive_path_process(cur_file, ext_list, operation, exclude_flag, *args))
        elif os.path.splitext(os.path.basename(f))[1] in ext_list:
            if not exclude_flag:
                r.append(operation(cur_file, *args))
        elif exclude_flag:
            r.append(operation(cur_file, *args))
    return r


class __dummy_ssh_tunnel:
    def __init__(self):
        return

    def __enter__(self):
        return

    def __exit__(self, *args):
        return


def __ssh_tunnel_db():
    if Config.SSH_TUNNEL_SWITCH:
        return sshtunnel.SSHTunnelForwarder((Config.MYSQL_HOST, Config.SSH_TUNNEL_PORT),
                                            ssh_username=Config.SSH_TUNNEL_USR,
                                            ssh_password=Config.SSH_TUNNEL_PWD,
                                            # ssh_pkey = server_pkey,
                                            remote_bind_address=(Config.LOCALHOST, Config.MYSQL_PORT))
    else:
        return __dummy_ssh_tunnel()


def __ssh_tunnel_conn_str(server):
    if server:
        return Config.MYSQL_CONN_STR.format(Config.MYSQL_USR, Config.MYSQL_PWD, Config.LOCALHOST,
                                            server.local_bind_port, Config.MYSQL_DB, Config.MYSQL_CHARSET)
    else:
        return Config.MYSQL_CONN_STR.format(Config.MYSQL_USR, Config.MYSQL_PWD, Config.MYSQL_HOST, Config.MYSQL_PORT,
                                            Config.MYSQL_DB, Config.MYSQL_CHARSET)


def __db_read(conn_str, table_name):
    # Connect to db
    Config.LOGGER.warning('Reading from db: {0}.{1}'.format(Config.MYSQL_DB, table_name))
    try:
        db_engine = sqlalchemy.create_engine(conn_str, server_side_cursors=True)
    except sqlalchemy.exc.OperationalError as e:
        Config.LOGGER.error('create_engine error: ' + str(e))
        return None
    except sqlalchemy.exc.InternalError as e:
        Config.LOGGER.error('create_engine error: ' + str(e))
        return None

    # Read from db
    try:
        sql = table_name
        chunks = pd.read_sql(sql, con=db_engine, chunksize=100000)
        result = list(chunks)
        if not len(result):
            return pd.DataFrame()
        return pd.concat(result, axis=0, sort=False, copy=False, ignore_index=True)
    except sqlalchemy.exc.OperationalError as e:
        Config.LOGGER.error('read_sql error: ' + str(e))
        return None


def __db_write(conn_str, table_name, df, index=False, if_exists='append'):
    # Connect to db
    Config.LOGGER.warning('Writing to db: {0}.{1}'.format(Config.MYSQL_DB, table_name))
    try:
        db_engine = sqlalchemy.create_engine(conn_str, server_side_cursors=True)
    except sqlalchemy.exc.OperationalError as e:
        Config.LOGGER.error('create_engine error: ' + str(e))
        return
    except sqlalchemy.exc.InternalError as e:
        Config.LOGGER.error('create_engine error: ' + str(e))
        return

    # Write to db
    try:
        df.to_sql(name=table_name, con=db_engine, if_exists=if_exists, index=index, chunksize=100000)
    except Exception as e:
        Config.LOGGER.error('to_sql error: ' + str(e))


def __db_execulte_sql(conn_str, sql_str):
    # Connect to database
    Config.LOGGER.warning('Executing sql: {0}'.format(sql_str))
    try:
        db_engine = sqlalchemy.create_engine(conn_str, server_side_cursors=True)
    except sqlalchemy.exc.OperationalError as e:
        Config.LOGGER.error('create_engine error: ' + str(e))
        return
    except sqlalchemy.exc.InternalError as e:
        Config.LOGGER.error('create_engine error: ' + str(e))
        return

    # Execute SQL string
    try:
        result = db_engine.execute(sql_str)
        if result.returns_rows:
            return result.fetchall()
        else:
            return result
    except sqlalchemy.exc.OperationalError as e:
        Config.LOGGER.error('sql execute error: ' + str(e))


def __string_coding(string):
    # import chardet
    # coding_mode = chardet.detect(string.encode())['encoding']
    # return string.encode(coding_mode).decode()
    """
    codecs = ['utf-8', 'cp1252', 'gbk', 'gb18030', 'latin-1', 'ascii']
    for c in codecs:
        try:
            return string.encode(c).decode()
        except UnicodeEncodeError:
            pass
        except UnicodeDecodeError:
            pass
    Config.LOGGER.error('__string_coding error: unknown coding character set.')
    """
    return string.encode('utf8', 'surrogateescape').\
        decode('utf8', 'surrogateescape')
