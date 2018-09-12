import pandas as pd
import os
import matplotlib.pyplot as plt
from functools import lru_cache
import numpy as np
from utils_.util_log import *
from utils_.util_date import *
from utils_.util_cache_file import *
from pandas.tseries.offsets import Week
from utils_.util_pandas import *

plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号


@timed()
def get_brand():
    brand = pd.read_csv('input/deviceid_brand.tsv', sep='\t', header=None)

    brand.columns = ['device', 'brand', 'phone_type']
    return convert_label_encode(brand, ['device'])


# Performance issue
@timed()
def get_package(limit=None):
    cache_file = './output/deviceid_package.tsv'
    if os.path.exists(cache_file):
        print('load package from cache:%s' % cache_file)
        return pd.read_csv(cache_file, sep=',')
    else:
        tmp = pd.read_csv('input/deviceid_packages.tsv', sep='\t', header=None, nrows=limit)
        tmp.columns = ['device', 'package_list']

        tmp = tmp[tmp.device.isin(get_test().iloc[:, 0])]

        package_list_all = frozenset.union(*tmp.iloc[:, 1].apply(lambda v: frozenset(v.split(','))))

        print(len(package_list_all))

        i = 1
        for package in package_list_all:
            i += 1
            print(f'{i}/{len(package_list_all)}')
            tmp[package] = tmp.apply(lambda _: int(package in _.package_list), axis=1)

        tmp.to_csv('./output/deviceid_package.tsv', index=False)

        return tmp


@timed()
def get_package_label():
    package = pd.read_csv('input/package_label.tsv', sep='\t', header=None, )
    package.columns = ['package', 'p_type', 'p_sub_type']
    return package

@timed()
def get_max_week(df):
    """
    到到每个Device使用的最多的那一周
    :param df:
    :return:
    """
    df = df.groupby(['device', 'weekbegin']).agg({'weekday':'nunique','package':'nunique'}).reset_index()

    # .to_frame().reset_index()
    # df.sort_values(['device', 'package'])

    df = df.sort_values(by=['device', 'weekday','package', 'weekbegin'], ascending=False).groupby('device').nth(0)
    df = df.reset_index()
    df.rename({'package':'package_count'}, axis=1, inplace=True)

    return df


# @timed()
# def get_percent_duration(df, groupby=['device', 'weekday'], prefix=None, span_no=6):
#     prefix = groupby[-1] if prefix is None else prefix
#     sum_duration = get_sum_duration(df, groupby, prefix)
#
#     sum_duration = reduce_time_span(sum_duration, prefix, span_no)
#
#     for col in [item for item in sum_duration.columns if f'{prefix}_span_' in item]:
#         df[f'{col}_p'] = round(df[col] / df[f'{prefix}_total'], 3)
#
#     return df

def reduce_time_span(df, prefix, span_no=4):
    span_len = 24//span_no
    print(f'columns before reduce:{df.columns}')
    for sn in range(0, span_no):
        col_list = [f'{prefix}_span24_{sn}' for sn in range(span_len*sn, span_len*(sn+1))]
        df[f'{prefix}_span_{sn}'] = df[col_list].sum(axis=1)
        # col_list.remove(f'{prefix}_span_{sn}')
        df.drop(columns=col_list, inplace=True)
    return df

@timed()
#@file_cache()
def get_sum_duration(df, groupby=['device', 'weekday'], prefix=None):
    prefix = groupby[-1] if prefix is None else prefix


    columns = [key for key in df.columns if 'span24_' in key]
    gp_map = [(key, 'sum') for key in columns if 'span24_' in key]
    gp_map = dict(gp_map)
    # print(gp_map)

    gp_map['package'] = 'nunique'
    gp_map['start_base'] = 'nunique'
    df = df.groupby(groupby).agg(gp_map)

    df['total'] = df[[key for key in columns if 'span24_' in key]].sum(axis=1)

    df.rename({'package':'pkg_cnt', 'start_base':'day_cnt'}, axis=1, inplace=True)

    df.columns = [f'{prefix}_{key}' for key in df.columns]

    print(f'The latest colums:{df.columns}')
    return df.reset_index()


def get_train():
    columns_1  =[ #sum and percentage
        'total_day_00_0_du',
        'total_day_00_1_du',
        'total_day_00_2_du',
        'total_day_00_3_du',
        '......'
        'total_day_07_3_du',


        'maxmax_day_00_0_du',
        'max_day_00_1_du',
        'max_day_00_2_du',
        'max_day_00_3_du',
        '......'
        'max_day_07_3_du',
    ]

    columns_2 =    [

        #指定时间段,打开pak的统计时长
        'max_package_du_1',  'max_package_du_1_type', 'max_package_du_1_sub_type',
        'max_package_du_2',  'max_package_du_2_type', 'max_package_du_2_sub_type',
        'max_package_du_3',  'max_package_du_3_type', 'max_package_du_3_sub_type',

        #指定时间段,打开pak的次数
        'max_package_cnt_1',  'max_package_cnt_1_type', 'max_package_cnt_1_sub_type',
        'max_package_cnt_2',  'max_package_cnt_2_type', 'max_package_cnt_2_sub_type',
        'max_package_cnt_3',  'max_package_cnt_3_type', 'max_package_cnt_3_sub_type',

        'total_used_package_count', 'per_total_install',
        'weekly_used_package_count', 'per_weekly_install',
        'total_install_package_count',

        'package_top1 ,,,, package_top10',
        'device_brand', 'device_type'

    ]
    pass




def get_test():
    test = pd.read_csv('input/deviceid_test.tsv', sep='\t',header=None)
    return test

@timed()
def extend_cols(tmp):
    if 'package' in tmp:
        package = get_package_label()
        print(f'input df col:{tmp.columns}')
        print(f'packae col:{package.columns}')
        tmp = tmp.merge(package, how='left')

    brand = get_brand()
    print(f'column list:{tmp.columns}')
    tmp = tmp.merge(brand, how='left')

    return tmp




@timed()
#@file_cache()
def extend_time(df, span_no=24):
    # mini.start = pd.to_datetime(mini.start)
    #df['dayname'] = df.start.dt.weekday_name

    span_len = 24//span_no

    #把一天分为4个时间段
    for sn in range(0, span_no):
        # df[f'span_{sn}'] = df.apply(lambda row: get_duration(row['start'], row['close'], sn), axis=1)

        print(f'Try to cal for range#{sn} with span_len: {span_len}')
        # df['start_base']  = df['start'].dt.date
        df['check_start'] = df['start'].dt.date + pd.DateOffset(hours=span_len * (sn))
        df['check_close'] = df['start'].dt.date + pd.DateOffset(hours=span_len * (sn + 1))

        df['merge_begin'] = df[['check_start', 'start']].max(axis=1)
        df['merge_end'] = df[['check_close', 'close']].min(axis=1)

        df[f'span24_{sn}'] = (df['merge_end'] - df['merge_begin']) / np.timedelta64(1, 'D')

        #去除负值
        df[f'span24_{sn}'][df[f'span24_{sn}'] <= 0] = 0
        df

    df.drop(columns = ['check_start', 'check_close', 'merge_begin','merge_end'], inplace=True)
    print(f'Output columns for extend_time is {df.columns}')
    return df

# def extend_sum_duration_df(df, groupby=['device', 'weekday'], prefix=None):
#     total = get_sum_duration(df, ['device'], 'total')
#
#     max_week = get_max_week(df)
#
#     merge = df.merge(max_week, on=['device', 'weekbegin'])
#
#     max = get_sum_duration(merge, ['device'], 'max')
#
#     return pd.concat( [total, max], axis=1 ).reset_index()


def extend_package_df(df):
    p = df.groupby(['device', 'package'])['start_base'].nunique().reset_index()
    p = p.pivot(index='device', columns='package', values='start_base').reset_index()
    print(f'Device_Package: convert {df.shape} to {p.shape} ')
    return p


def extend_feature( span_no=6, input=None, trunc_long_time=False, mini=False):
    prefix='tol'
    df = extend_time_span(version=1, trunc_long_time=trunc_long_time, mini=mini,
                          groupby=['device'], prefix=prefix)
    df = reduce_time_span(df, prefix, span_no)
    df = extend_percent(df, prefix)

    df = extend_cols(df)
    if input is not None:
        df = input.merge(df, how='left')
    return df

def extend_percent(df, prefix):
    for col in [item for item in df.columns if f'{prefix}_span_' in item]:
        df[f'{col}_p'] = round(df[col] / df[f'{prefix}_total'], 3)
    return df

@timed()
@file_cache()
def extend_time_span(version=1, trunc_long_time=False, mini=False, groupby=['device', 'weekday'], prefix=None):
    rootdir = './output/start_close/'
    list = os.listdir(rootdir)  # 列出文件夹下所有的目录与文件
    list = sorted(list, reverse=True)

    duration_list = []
    for i in range(0, len(list)):
        path = os.path.join(rootdir, list[i])
        if os.path.isfile(path) and 'csv' in path:
            print(f"Try to summary file:{path}")
            df = get_start_closed(path)
            df = split_days_all(df, trunc_long_time)
            df = extend_time(df, span_no=24)
            df = get_sum_duration(df, groupby, prefix=prefix)
            if len(df) > 0 :
                duration_list.append(df)
                if mini:
                    print('Return mini for testing')
                    break
            else:
                print(f'The df is None for file:{path}')

    return pd.concat(duration_list)




@file_cache()
@timed()
def extend_package(version):
    rootdir = './output/start_close/'
    list = os.listdir(rootdir)  # 列出文件夹下所有的目录与文件
    list = sorted(list, reverse=True)

    tmp_list = []
    for i in range(0, len(list)):
        path = os.path.join(rootdir, list[i])
        if os.path.isfile(path) and 'csv' in path:
            print(f"Try to summary file:{path}")
            df = get_start_closed(path)
            df = split_days_all(df)
            df = extend_package_df(df)
            if len(df) > 0 :
                tmp_list.append(df)
            else:
                print(f'The df is None for file:{path}')

    return pd.concat(tmp_list)


@timed()
#@file_cache()
def split_days_all(tmp, trunc_long_time=None):
    if trunc_long_time == True:
        trunc_week_sn =2
        # 超长记录,截取后面的数据, 最多保留2个星期,最少保留一个完整的星期
        tmp['start_tmp'] = (tmp.close - Week(trunc_week_sn, weekday=0)).dt.date.astype('datetime64[ns]')
        tmp.start = tmp[['start', 'start_tmp']].max(axis=1)
        tmp.drop( columns=['start_tmp'] , inplace=True )

    tmp.duration = (tmp.close - tmp.start) / np.timedelta64(1, 'D')

    old_len = len(tmp)
    print(f'Out loop: The original Df size is {old_len}')
    tmp = split_days(tmp, 50)
    tmp = split_days(tmp, 1)
    print(f'Out loop: The new Df size is {len(tmp)}, old df size is {old_len}')

    tmp['start_base'] = tmp['start'].dt.date
    tmp['weekday'] = tmp.start.dt.weekday
    tmp['weekbegin'] = (tmp['start'] -
                        tmp['start'].dt.weekday.astype('timedelta64[D]')).dt.date


    tmp.duration = round(tmp.duration, 6)

    tmp = tmp.sort_values(by = ['device','package','start'])

    return tmp

#@timed()
def split_days(tmp, threshold_days = 100):
    threshold_days = max(1,threshold_days)
    print(f'The input df#{len(tmp)} before split, with max duration:{tmp.duration.max()} '
                                 f'and  threshold_days@{threshold_days}')

    # 检查是否有需要截断的数据, 如果没有直接Return, 或者进入小循环
    tmp_todo_big = tmp[tmp.duration > threshold_days]
    if len(tmp_todo_big) == 0 and tmp.duration.max() <= threshold_days:
        print(f'Final return with:{len(tmp)}')
        return tmp


    # 创建新记录,截取最近的时间段(大段)
    tmp_todo_big.start = tmp_todo_big.start.dt.date + pd.DateOffset(threshold_days)
    tmp_todo_big.duration = (tmp_todo_big.close - tmp_todo_big.start) / np.timedelta64(1, 'D')
    tmp_big = split_days(tmp_todo_big, threshold_days)

    # inpu中,已经小于阀值天的
    tmp_small_p1         = tmp[tmp.duration <= threshold_days]
    # 旧记录,保留早期的时间段(小段)
    tmp_small_p2   = tmp[tmp.duration > threshold_days]
    tmp_small_p2.close    = tmp_small_p2.start.dt.date + pd.DateOffset(threshold_days)
    #tmp_small_p2.duration = (tmp_small_p2.close - tmp_small_p2.start) / np.timedelta64(1, 'D')
    tmp_small = pd.concat([tmp_small_p1, tmp_small_p2])
    tmp_small.duration = (tmp_small.close - tmp_small.start) / np.timedelta64(1, 'D')

    print(f'max duration:{tmp_small_p2.duration.max()} with small threshold:{threshold_days}')

    tmp = tmp_big.append(tmp_small)

    #tmp = tmp.sort_values('duration', ascending=False)
    tmp.reset_index(drop=True, inplace=True)

    print(f'The output df#{len(tmp)} after split')

    return tmp

@timed()
#@file_cache()
def get_start_closed(file=None):


    start_close = pd.read_csv(file,
                              # index_col=0 ,
                              nrows=None,
                              header=None )

    if len(start_close) == 0 :
        return pd.DataFrame()

    start_close.columns = ['device', 'package', 'start_t', 'close_t']

    print(f'Sort the df#{len(start_close)} by device(begin)')
    start_close.sort_values('device', inplace=True)
    print(f'Sort the df by device(end)')

    # start_close.index.name = 'device'


    start_close['start'] = pd.to_datetime(start_close.loc[:, 'start_t'], unit='ms')
    start_close['close'] = pd.to_datetime(start_close.loc[:, 'close_t'], unit='ms')

    len_original = len(start_close)
    start_close = start_close[start_close.start < pd.to_datetime('now')]
    #去除部分异常数据
    print(f'Remove {len_original-len(start_close)} records data')

    # start_close.groupby('device')[['package']].count()
    start_close['duration'] = (start_close.close - start_close.start) / np.timedelta64(1, 'D')

    return start_close

def split_start_close(split_no=40, prefix='deviceid_package_start_close'):

    file = 'input/deviceid_package_start_close.tsv'

    df = pd.read_csv(file, sep='\t',
                              # index_col=0 ,
                              nrows=None,
                              header=None )
    df.columns = ['device', 'package', 'start_t', 'close_t']

    print(f'Sort the df#{len(df)} by device(begin)')
    df.sort_values(by=['device', 'package', 'start_t'], inplace=True)
    df.reset_index(drop=True, inplace=True)
    print(f'Sort the df by device(end)')


    if len(df)%split_no == 0:
        size = len(df) //split_no
    else:
        size = len(df) // (split_no -1)

    print(f'The default size of the file is {size}')

    end_adjust = 0
    for i in range(0,split_no):
        begin_adjust = end_adjust
        end_adjust = adjust_split_end(df,  min(size*(i+1), len(df)) )
        file = f'output/start_close/{prefix}_{split_no}_{str(i).rjust(2,"0")}_{begin_adjust}_{end_adjust}.csv'
        print(f'Split df to file#{i}:{file}')
        if end_adjust > begin_adjust:
            df[begin_adjust : end_adjust].to_csv(file, index=None, header=False )

def adjust_split_end(df,  end):
    id = df.iat[end-1, 0]
    id_rec = df[df.iloc[:,0]==id]
    print(f'{len(id_rec)} , {id_rec.index.max()}, {id_rec.index.max()} ')
    end_adjust = id_rec.index.max() + 1
    print(f'Adjust original end from {end} to {end_adjust} for id:{id}')
    return end_adjust


