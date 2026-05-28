import random
import simpy

SEED = 42
SIM_DURATION = 60000
T_ARRIVAL_MEAN = 6
T_ARRIVAL_DEV = 3

total_pkts = 0
drop_pkts = 0
boost_count = 0

drop_series = 0
tx_delay = 5.0
is_boosted = False


def packet_flow(env, pkt_id, ch1, ch2):
    global drop_series, tx_delay, is_boosted, drop_pkts, boost_count

    t_start = env.now

    with ch1.request() as req:
        yield req
        yield env.timeout(tx_delay)

    with ch2.request() as req:
        yield req
        yield env.timeout(tx_delay)

    latency = env.now - t_start
    show_log = pkt_id % 100 == 0

    if latency > 10.0:
        drop_pkts += 1
        drop_series += 1

        if show_log:
            print(f"[{env.now:.1f} мс] Пакет {pkt_id} УНИЧТОЖЕН (Задержка: {latency:.1f} мс, Серия потерь: {drop_series})")

        if drop_series > 10 and not is_boosted:
            is_boosted = True
            tx_delay = 4.0
            boost_count += 1
            print(f"[{env.now:.1f} мс] >>> ДОП. РЕСУРС ВКЛЮЧЕН (Задержка канала: 4.0 мс)")
    else:
        if show_log:
            print(f"[{env.now:.1f} мс] Пакет {pkt_id} ДОСТАВЛЕН (Задержка: {latency:.1f} мс)")

        drop_series = 0
        if is_boosted:
            is_boosted = False
            tx_delay = 5.0
            print(f"[{env.now:.1f} мс] >>> ДОП. РЕСУРС ОТКЛЮЧЕН (Задержка канала: 5.0 мс)")


def traffic_gen(env, ch1, ch2):
    global total_pkts
    pkt_id = 0
    while True:
        dt = random.randint(T_ARRIVAL_MEAN - T_ARRIVAL_DEV, T_ARRIVAL_MEAN + T_ARRIVAL_DEV)
        yield env.timeout(dt)
        pkt_id += 1
        total_pkts += 1
        env.process(packet_flow(env, pkt_id, ch1, ch2))


def main():
    random.seed(SEED)
    env = simpy.Environment()

    ch1 = simpy.Resource(env, capacity=1)
    ch2 = simpy.Resource(env, capacity=1)

    env.process(traffic_gen(env, ch1, ch2))
    env.run(until=SIM_DURATION)

    t_sec = SIM_DURATION / 1000.0
    f_drop = drop_pkts / t_sec
    f_boost = boost_count / t_sec

    print("\n--- РЕЗУЛЬТАТЫ МОДЕЛИРОВАНИЯ ---")
    print(f"Всего сгенерировано пакетов: {total_pkts}")
    print(f"Всего уничтожено пакетов: {drop_pkts}")
    print(f"Количество активаций доп. ресурса: {boost_count}")
    print(f"Частота уничтожения пакетов (F_drop): {f_drop:.4f} пак/сек")
    print(f"Частота подключения доп. ресурса (F_boost): {f_boost:.4f} раз/сек")


if __name__ == "__main__":
    main()
