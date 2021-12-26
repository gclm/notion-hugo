# -*- coding:utf-8 -*-
# Twitter's Snowflake algorithm implementation which is used to generate distributed IDs.
# https://github.com/twitter-archive/snowflake/blob/snowflake-2010/src/main/scala/com/twitter/service/snowflake/IdWorker.scala

import copy
import os
import random
import time


# 获取max_worker_id
def get_max_worker_id(datacenter_id, max_worker_id):
    mp_id = str(datacenter_id) + str(os.getpid())
    return (hash(mp_id) & 0xffff) % (max_worker_id + 1)


# 获取 mac 地址
def get_mac_address():
    import uuid
    node = uuid.getnode()
    mac = uuid.UUID(int=node).hex[-12:]
    decimalismMac = [
        int(mac[0:2], 16), int(mac[2:4], 16), int(mac[4:6], 16), int(mac[6:8], 16), int(mac[8:10], 16),
        int(mac[10:12], 16)
    ]
    return decimalismMac


# 数据标识id部分
def get_datacenter_id(max_datacenter_id):
    mac = get_mac_address()
    id = ((0x000000FF & mac[len(mac) - 1]) | (0x0000FF00 & ((mac[len(mac) - 2]) << 8))) >> 6
    id = id % (max_datacenter_id + 1)
    return id


def get_next_millis(last_timestamp):
    timestamp = int(time.time() * 1000)
    while timestamp <= last_timestamp:
        timestamp = int(time.time() * 1000)
    return timestamp


class Snowflake:
    # 时间起始标记点，作为基准，一般取系统的最近时间（一旦确定不能变动）
    twepoch = 1640487409283
    # 机器标识位数
    worker_id_bits = 5
    datacenter_id_bits = 5
    max_worker_id = -1 ^ (-1 << worker_id_bits)
    max_datacenter_id = -1 ^ (-1 << datacenter_id_bits)
    # 毫秒内自增位
    sequenceBits = 12
    workerIdShift = sequenceBits
    datacenter_idShift = sequenceBits + worker_id_bits
    timestampLeftShift = sequenceBits + worker_id_bits + datacenter_id_bits
    sequenceMask = -1 ^ (-1 << sequenceBits)

    workerId = 1
    # 数据标识 ID  部分
    datacenter_id = 0
    # 并发控制
    sequence = 0
    # 上次生产ID时间戳
    last_timestamp = -1

    def __int__(self):
        self.datacenter_id = get_datacenter_id(self.max_datacenter_id)
        self.workerId = get_max_worker_id(self.datacenter_id, self.max_worker_id)

    # 获取下一个id
    @classmethod
    def get_id(cls):
        timestamp = int(time.time() * 1000)
        # 闰秒
        if timestamp < cls.last_timestamp:
            offset = cls.last_timestamp - timestamp
            if offset <= 5:
                time.sleep(offset << 1)
                timestamp = int(time.time() * 1000)
                if timestamp < cls.last_timestamp:
                    return None
            else:
                return None

        if cls.last_timestamp == timestamp:
            #  相同毫秒内，序列号自增
            cls.sequence = (cls.sequence + 1) & cls.sequenceMask
            if cls.sequence == 0:
                # 同一毫秒的序列数已经达到最大
                timestamp = get_next_millis(cls.last_timestamp)
        else:
            # 不同毫秒内，序列号置为 1 - 3 随机数
            cls.sequence = random.randrange(1, 4)

        cls.last_timestamp = copy.copy(timestamp)

        # 时间戳部分 | 数据中心部分 | 机器标识部分 | 序列号部分
        return ((timestamp - cls.twepoch) << cls.timestampLeftShift) | (
                cls.datacenter_id << cls.datacenter_idShift) | (cls.workerId << cls.workerIdShift) | cls.sequence


if __name__ == '__main__':
    snowflake = Snowflake
    for i in range(100):
        print(snowflake.get_id())
